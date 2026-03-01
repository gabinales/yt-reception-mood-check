"""
feedback.py
-----------
Local feedback store for sentiment corrections — **SQLite edition**.

When the user corrects a comment's sentiment on the results page,
the correction is saved to ``feedback.db``.  On subsequent analyses
the stored corrections are applied as overrides **before** the model
runs — so the app "learns" from your corrections instantly.

The store also keeps simple keyword→sentiment associations extracted
from corrected comments, which are used as tie-breakers when the
model's confidence is low.

Using SQLite instead of a JSON file gives us:
- Atomic writes (no corruption on concurrent requests)
- Efficient lookups even with thousands of corrections
- Compatibility with Railway / Render persistent volumes
"""

import os
import re
import sqlite3
from pathlib import Path

# Allow overriding the DB path via env var (useful for Railway volumes).
# Falls back to /data/feedback.db if the Railway mount exists, else local.
def _resolve_db_path() -> Path:
    env = os.environ.get("FEEDBACK_DB")
    if env:
        return Path(env)
    railway_mount = Path("/data")
    if railway_mount.is_dir():
        return railway_mount / "feedback.db"
    return Path(__file__).parent / "feedback.db"

_DB_PATH = _resolve_db_path()

# ── Database helpers ───────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    """Return a connection with WAL mode and auto-create tables."""
    conn = sqlite3.connect(str(_DB_PATH), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            comment_key  TEXT PRIMARY KEY,
            sentiment    TEXT NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            word       TEXT PRIMARY KEY,
            sentiment  TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _normalise(text: str) -> str:
    """Normalise comment text for lookup (lowercase, collapse whitespace)."""
    return re.sub(r"\s+", " ", text.strip().lower())


_STOPS = frozenset({
    "this", "that", "with", "from", "have", "were", "been", "they",
    "their", "them", "will", "would", "could", "should", "about",
    "just", "like", "what", "when", "your", "some", "than", "very",
    "more", "also", "into", "only", "here", "there",
})


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful words (>3 chars) from a comment."""
    words = re.findall(r"[a-zA-ZÀ-ÿ]{4,}", text.lower())
    return [w for w in words if w not in _STOPS]


# ── Public API (same signatures as the old JSON version) ───────

def save_correction(comment: str, corrected_sentiment: str) -> None:
    """
    Save the user's correction for a specific comment.

    Also extracts keywords and associates them with the corrected
    sentiment to help with similar future comments.
    """
    sentiment = corrected_sentiment.upper()
    key = _normalise(comment)

    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO corrections (comment_key, sentiment) VALUES (?, ?)",
            (key, sentiment),
        )
        for word in _extract_keywords(comment):
            conn.execute(
                "INSERT OR REPLACE INTO keywords (word, sentiment) VALUES (?, ?)",
                (word, sentiment),
            )
        conn.commit()
    finally:
        conn.close()


def get_correction(comment: str) -> str | None:
    """Return the user's corrected sentiment for a comment, or None."""
    key = _normalise(comment)
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT sentiment FROM corrections WHERE comment_key = ?", (key,)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_keyword_hint(comment: str) -> str | None:
    """
    Check if keyword associations suggest a sentiment.

    Returns a sentiment label if multiple keywords agree, else None.
    """
    words = _extract_keywords(comment)
    if not words:
        return None

    conn = _get_conn()
    try:
        placeholders = ",".join("?" for _ in words)
        rows = conn.execute(
            f"SELECT word, sentiment FROM keywords WHERE word IN ({placeholders})",
            words,
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return None

    votes: dict[str, int] = {}
    for _, label in rows:
        votes[label] = votes.get(label, 0) + 1

    best = max(votes, key=votes.get)  # type: ignore[arg-type]
    return best if votes[best] >= 2 else None


def get_stats() -> dict:
    """Return summary stats about stored feedback."""
    conn = _get_conn()
    try:
        total_corr = conn.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]
        total_kw = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    finally:
        conn.close()
    return {
        "total_corrections": total_corr,
        "total_keywords": total_kw,
    }
