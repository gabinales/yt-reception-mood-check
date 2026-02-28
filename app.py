from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from scraper import scrape_comments
from analyzer import analyse_comments
from feedback import save_correction, get_stats

app = Flask(__name__)
app.secret_key = "yt-mood-check-secret"


@app.route("/", methods=["GET"])
def index():
    """Main page – URL input form."""
    stats = get_stats()
    return render_template("index.html", feedback_stats=stats)


@app.route("/analyse", methods=["POST"])
def analyse():
    """Receive the YouTube URL, scrape, analyse, and show results."""
    video_url = request.form.get("video_url", "").strip()

    if not video_url:
        flash("Please enter a valid YouTube video URL.", "error")
        return redirect(url_for("index"))

    # --- scrape ---
    try:
        scraped = scrape_comments(video_url)
    except Exception as exc:
        flash(f"Scraping failed: {exc}", "error")
        return redirect(url_for("index"))

    raw_comments = scraped["comments"]
    video_title = scraped["title"]
    video_thumbnail = scraped["thumbnail"]

    if not raw_comments:
        flash("No comments found for this video.", "error")
        return redirect(url_for("index"))

    # --- analyse ---
    results = analyse_comments(raw_comments)

    # Count sentiments for the summary
    pos = sum(1 for r in results if r["sentiment"] == "POSITIVE")
    neg = sum(1 for r in results if r["sentiment"] == "NEGATIVE")
    neu = sum(1 for r in results if r["sentiment"] == "NEUTRAL")

    return render_template(
        "results.html",
        results=results,
        video_url=video_url,
        video_title=video_title,
        video_thumbnail=video_thumbnail,
        total=len(results),
        positive=pos,
        negative=neg,
        neutral=neu,
    )


@app.route("/feedback", methods=["POST"])
def feedback():
    """API endpoint — save a sentiment correction from the user."""
    data = request.get_json(silent=True)
    if not data or "comment" not in data or "sentiment" not in data:
        return jsonify({"error": "Missing comment or sentiment"}), 400

    sentiment = data["sentiment"].upper()
    if sentiment not in ("POSITIVE", "NEGATIVE", "NEUTRAL"):
        return jsonify({"error": "Invalid sentiment"}), 400

    save_correction(data["comment"], sentiment)
    return jsonify({"ok": True, "sentiment": sentiment})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
