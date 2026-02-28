"""
feedback.py
-----------
Local feedback store for sentiment corrections.

When the user corrects a comment's sentiment on the results page,
the correction is saved to ``feedback_data.json``.  On subsequent
analyses the stored corrections are applied as overrides **before**
the model runs — so the app "learns" from your corrections instantly.

The store also keeps simple keyword-sentiment associations extracted
from corrected comments, which are used as tie-breakers when the
model's confidence is low.
"""

import json
import os
import re
from pathlib import Path

_FEEDBACK_FILE = Path(__file__).parent / "feedback_data.json"

# ── In-memory cache (loaded once, written on every update) ─────
_feedback: dict | None = None


def _load() -> dict:
    """Load feedback from disk (or initialise empty)."""
    global _feedback
    if _feedback is not None:
        return _feedback

    if _FEEDBACK_FILE.exists():
        try:
            with open(_FEEDBACK_FILE, "r", encoding="utf-8") as f:
                _feedback = json.load(f)
        except (json.JSONDecodeError, OSError):
            _feedback = {"corrections": {}, "keywords": {}}
    else:
        _feedback = {"corrections": {}, "keywords": {}}

    # Ensure structure
    _feedback.setdefault("corrections", {})
    _feedback.setdefault("keywords", {})
    return _feedback


def _save() -> None:
    """Persist feedback to disk."""
    data = _load()
    with open(_FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _normalise(text: str) -> str:
    """Normalise comment text for lookup (lowercase, collapse whitespace)."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful words (>3 chars) from a comment."""
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    # Filter out very common stop-words
    stops = {
        "this", "that", "with", "from", "have", "were", "been", "they",
        "their", "them", "will", "would", "could", "should", "about",
        "just", "like", "what", "when", "your", "some", "than", "very",
        "more", "also", "into", "only", "here", "there",
    }
    return [w for w in words if w not in stops]


# ── Public API ─────────────────────────────────────────────────

def save_correction(comment: str, corrected_sentiment: str) -> None:
    """
    Save the user's correction for a specific comment.

    Also extracts keywords and associates them with the corrected
    sentiment to help with similar future comments.
    """
    data = _load()
    key = _normalise(comment)
    data["corrections"][key] = corrected_sentiment.upper()

    # Store keyword → sentiment associations
    for word in _extract_keywords(comment):
        data["keywords"][word] = corrected_sentiment.upper()

    _save()


def get_correction(comment: str) -> str | None:
    """
    Return the user's corrected sentiment for a comment, or None.
    """
    data = _load()
    key = _normalise(comment)
    return data["corrections"].get(key)


def get_keyword_hint(comment: str) -> str | None:
    """
    Check if keyword associations suggest a sentiment.

    Returns a sentiment label if multiple keywords agree, else None.
    """
    data = _load()
    keywords_map = data.get("keywords", {})
    if not keywords_map:
        return None

    words = _extract_keywords(comment)
    votes: dict[str, int] = {}
    for w in words:
        if w in keywords_map:
            label = keywords_map[w]
            votes[label] = votes.get(label, 0) + 1

    if not votes:
        return None

    # Return the label with the most keyword votes (minimum 2 matches)
    best = max(votes, key=votes.get)  # type: ignore[arg-type]
    if votes[best] >= 2:
        return best
    return None


def get_stats() -> dict:
    """Return summary stats about stored feedback."""
    data = _load()
    return {
        "total_corrections": len(data["corrections"]),
        "total_keywords": len(data["keywords"]),
    }
