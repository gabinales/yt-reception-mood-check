"""
scraper.py
----------
YouTube comment scraper using yt-dlp (YouTube's own InnerTube API).

This approach is 100% reliable — it fetches every comment and reply
via API pagination instead of trying to scrape a dynamically rendered
DOM, which is inherently unreliable.
"""

import yt_dlp


def scrape_comments(video_url: str) -> dict:
    """
    Fetch ALL comments (top-level + replies) from a YouTube video.

    Uses yt-dlp to call YouTube's InnerTube API directly — no browser,
    no DOM, no lazy-load timing issues.

    Parameters
    ----------
    video_url : str
        Full YouTube video URL (e.g. https://www.youtube.com/watch?v=...).

    Returns
    -------
    dict with keys:
        - ``comments``  : deduplicated list of comment strings
        - ``title``     : video title
        - ``thumbnail`` : URL of the best available thumbnail
    """
    ydl_opts = {
        "skip_download": True,
        "extract_flat": False,
        # Enable comment extraction
        "getcomments": True,
        "extractor_args": {
            "youtube": {
                # Sort by top comments; fetch all pages of comments & replies
                "comment_sort": ["top"],
                "max_comments": ["all", "all", "all", "all"],
            }
        },
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    raw_comments: list = info.get("comments") or []

    # Flatten: each item has a "text" key
    seen: set[str] = set()
    comments: list[str] = []
    for c in raw_comments:
        text = (c.get("text") or "").strip()
        if text and text not in seen:
            seen.add(text)
            comments.append(text)

    # Pick the best thumbnail (yt-dlp returns the highest-res one in `thumbnail`)
    thumbnail = info.get("thumbnail") or ""

    return {
        "comments": comments,
        "title": info.get("title") or "",
        "thumbnail": thumbnail,
    }
