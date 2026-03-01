# YouTube Reception Mood Check

A web application that fetches every public comment from a YouTube video and performs multilingual sentiment analysis to gauge the overall mood of the reception. Comments are classified as **Positive**, **Negative**, or **Neutral** and displayed with colour-coded cards, interactive filters, and a visual breakdown chart.

---

## Features

- 🎬 **Video card** — thumbnail, title, and direct link displayed above the results
- 💬 **Full comment extraction** — uses YouTube's own API via yt-dlp (no browser, no DOM tricks)
- 🌍 **Multilingual AI model** — XLM-RoBERTa trained on ~198 M tweets; handles Brazilian Portuguese, English, Spanish, French, German, Italian, Arabic, and Hindi
- 📊 **Sentiment bar chart** — clickable segments filter the list instantly
- 🔍 **Filter bar** — filter by All / Positive / Negative / Neutral with live counts
- 🏷️ **User corrections** — click any sentiment badge to correct it; saved to SQLite and applied on future analyses
- ⏱️ **Wait-time estimate** — live elapsed timer + typical duration guide shown during analysis
- 📄 **About & Privacy pages** — footer links to both

---

## Tech Stack

| Layer              | Technology                                                   |
|--------------------|--------------------------------------------------------------|
| Backend            | Python 3.10+, Flask 3                                        |
| Comment scraping   | **yt-dlp** (YouTube InnerTube API — no browser required)    |
| Sentiment analysis | HuggingFace Transformers · `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` |
| Feedback storage   | **SQLite** (WAL mode, persistent across restarts)            |
| Frontend           | Vanilla HTML / CSS / JavaScript (Jinja2 templates)           |
| Production server  | Gunicorn                                                     |

---

## How It Works

```
┌─────────────────┐   ┌──────────────────┐   ┌────────────────────┐   ┌────────────────┐
│  Paste YouTube  │──▶│  yt-dlp fetches  │──▶│  XLM-RoBERTa runs  │──▶│  Results page  │
│  video URL      │   │  all comments    │   │  sentiment per     │   │  with filters  │
└─────────────────┘   │  via InnerTube   │   │  comment           │   └────────────────┘
                      └──────────────────┘   └────────────────────┘
```

1. **Input** — Paste a YouTube video URL and click **Analyse**.
2. **Scrape** — yt-dlp talks directly to YouTube's InnerTube API and returns all accessible comments (top-level + replies) without opening a browser.
3. **Analyse** — Each comment is checked against the user-correction store first; if not found, it is classified by the multilingual transformer model.
4. **Display** — A video card, percentage bar, filter buttons, and colour-coded comment cards are shown.

---

## Project Structure

```
yt-comments-mood-check/
├── app.py                  # Flask routes (/, /analyse, /feedback, /about, /privacy)
├── scraper.py              # yt-dlp comment + metadata fetcher
├── analyzer.py             # Comment cleaning & XLM-RoBERTa sentiment analysis
├── feedback.py             # SQLite-backed user-correction store
├── templates/
│   ├── index.html          # Home page (URL input, loading state)
│   ├── results.html        # Results page (chart, filters, comment cards)
│   ├── about.html          # About page
│   └── privacy.html        # Terms & Privacy page
├── static/
│   └── style.css           # Full stylesheet
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn start command (Railway / Heroku)
├── railway.toml            # Railway deploy config + persistent volume mount
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- No browser, no ChromeDriver — yt-dlp handles everything over HTTP

### Installation

```bash
# Clone the repository
git clone https://github.com/youruser/yt-comments-mood-check.git
cd yt-comments-mood-check

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

The first time the app runs, HuggingFace will download the XLM-RoBERTa model (~1.1 GB) and cache it locally.

### Running Locally

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## Usage

1. Paste a YouTube video URL (e.g. `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).
2. Click **Analyse**. A live elapsed timer and typical wait-time guide are shown.
3. Browse the results — click the percentage bar segments or the filter buttons to narrow down by sentiment.
4. Disagree with a label? Click the sentiment badge on any comment card to correct it. Corrections are saved to SQLite and used on all future analyses.

### Typical Wait Times

| Comments | Approximate time |
|----------|-----------------|
| ~100     | < 1 min         |
| ~500     | ~4 min          |
| ~1 000   | ~8 min          |
| ~5 000   | ~40 min         |

> **Note:** YouTube's displayed comment count can differ slightly from the number returned by the API. Deleted, spam-filtered, and held-for-review comments are included in YouTube's counter but are not returned by the API.

---

## Key Dependencies

| Package                              | Purpose                                      |
|--------------------------------------|----------------------------------------------|
| `flask`                              | Web framework                                |
| `gunicorn`                           | Production WSGI server                       |
| `yt-dlp`                             | YouTube comment & metadata extraction        |
| `transformers`                       | HuggingFace pipeline for sentiment analysis  |
| `torch`                              | PyTorch backend for the transformer model    |
| `scipy`                              | Used internally by the transformers pipeline |

---

## Configuration

| Environment Variable | Default                         | Description                                        |
|----------------------|---------------------------------|----------------------------------------------------|
| `FEEDBACK_DB`        | `/data/feedback.db` (if `/data` exists) or `./feedback.db` | Path to the SQLite feedback database |

On Railway, set `FEEDBACK_DB` to a path inside your persistent volume (e.g. `/data/feedback.db`) or let the app auto-detect the `/data` mount.

---

## Deploying to Railway (free tier)

1. Push your repository to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. In the service settings, add a **Volume** mounted at `/data` — this is where `feedback.db` lives and survives redeploys.
4. Railway auto-detects Python via Nixpacks, installs from `requirements.txt`, and runs the `Procfile`.
5. The first cold start takes ~60–90 s while the model loads; subsequent requests are fast.

**Required files (already included):**

```
# Procfile
web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1
```

```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1"
healthcheckPath = "/"
restartPolicyType = "on_failure"

[[mounts]]
mountPath = "/data"
```

---

## Sentiment Results

| Sentiment | Card colour  |
|-----------|-------------|
| Positive  | 🟢 Green    |
| Negative  | 🔴 Red      |
| Neutral   | ⚪ Gray     |

---

## Limitations

- Scraping speed depends on internet connection and video comment count.
- YouTube may throttle or rate-limit automated API access; use responsibly.
- The AI model accuracy varies with highly idiomatic slang or mixed-language comments.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

