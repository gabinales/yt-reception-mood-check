"""
analyzer.py
-----------
Comment cleaning and sentiment analysis using a transformer model
(cardiffnlp/twitter-roberta-base-sentiment-latest) **combined with
a local feedback/correction store**.

Priority order for each comment:
1. Exact-match correction from feedback store → use directly.
2. Keyword hint from feedback (low-confidence model results only).
3. Transformer model prediction.
"""

import re
from transformers import pipeline
from feedback import get_correction, get_keyword_hint

# Load the sentiment-analysis pipeline once at module level.
_classifier = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
    top_k=1,
    truncation=True,
    max_length=512,
)

# Map model output labels → our canonical names
_LABEL_MAP = {
    "positive": "POSITIVE",
    "negative": "NEGATIVE",
    "neutral": "NEUTRAL",
}

# Below this confidence the keyword hint (from feedback) can override
_LOW_CONFIDENCE = 0.55

# ── Cleaning helpers ───────────────────────────────────────────

def _clean(text: str) -> str:
    """
    Clean a single comment.

    - Remove URLs
    - Remove HTML tags & entities
    - Collapse whitespace
    - Strip leading/trailing spaces
    """
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&\w+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ── Public API ─────────────────────────────────────────────────

def analyse_comments(raw_comments: list[str]) -> list[dict]:
    """
    Clean and classify a list of raw comment strings.

    For each comment the priority is:
    1. Exact-match user correction (from feedback store).
    2. Model prediction (with keyword-hint override when confidence is low).

    Returns
    -------
    list[dict]
        Each dict contains:
            - ``comment``   : cleaned comment text
            - ``sentiment`` : "POSITIVE" | "NEGATIVE" | "NEUTRAL"
            - ``score``     : model confidence (0-1 float)
            - ``source``    : "feedback" | "model" | "keyword"
    """
    # Clean all comments
    cleaned = []
    for raw in raw_comments:
        c = _clean(raw)
        if c:
            cleaned.append(c)

    if not cleaned:
        return []

    # Separate comments that already have feedback corrections
    needs_model: list[tuple[int, str]] = []  # (index, text)
    results: list[dict | None] = [None] * len(cleaned)

    for i, text in enumerate(cleaned):
        correction = get_correction(text)
        if correction:
            results[i] = {
                "comment": text,
                "sentiment": correction,
                "score": 1.0,
                "source": "feedback",
            }
        else:
            needs_model.append((i, text))

    # Run the model only on comments that don't have corrections
    if needs_model:
        texts = [t for _, t in needs_model]
        try:
            predictions = _classifier(texts, batch_size=16)
        except Exception:
            predictions = []
            for text in texts:
                try:
                    predictions.append(_classifier(text)[0])
                except Exception:
                    predictions.append([{"label": "neutral", "score": 0.0}])

        for (idx, text), preds in zip(needs_model, predictions):
            top = preds[0] if isinstance(preds, list) else preds
            label = _LABEL_MAP.get(top["label"].lower(), "NEUTRAL")
            score = round(top["score"], 4)
            source = "model"

            # If model confidence is low, check keyword hints from feedback
            if score < _LOW_CONFIDENCE:
                hint = get_keyword_hint(text)
                if hint:
                    label = hint
                    source = "keyword"

            results[idx] = {
                "comment": text,
                "sentiment": label,
                "score": score,
                "source": source,
            }

    return [r for r in results if r is not None]
