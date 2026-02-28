# YouTube Comment Section Mood Check

A web application that scrapes YouTube video comments and performs sentiment analysis to gauge the overall mood of the comment section. Comments are classified as **Positive**, **Negative**, or **Neutral** and displayed with color-coded backgrounds for quick visual insight.

---

## Tech Stack

| Layer           | Technology              |
|-----------------|-------------------------|
| Backend         | Python, Flask           |
| Web Scraping    | Selenium (latest)       |
| Sentiment Analysis | NLP / Sentiment model |
| Frontend        | HTML, CSS (Jinja2 templates) |

## How It Works

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Paste YouTube │────▶│ Scrape comments│────▶│ Clean & Analyse│────▶│ Display results│
│  video URL     │     │ via Selenium   │     │ (sentiment)    │     │ color-coded    │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
```

1. **Input** — On the main page, enter or paste a YouTube video URL whose comments you want to analyse.
2. **Trigger** — Click the **Analyse Comments** button.
3. **Scrape** — Selenium launches a headless browser, navigates to the video, scrolls through the comment section, and collects all visible comments.
4. **Process** — The raw comments are cleaned (removing noise, special characters, etc.) and fed through a sentiment analysis model.
5. **Results** — The results page displays every scraped comment alongside its detected sentiment, colour-coded for clarity:

| Sentiment | Background Colour |
|-----------|-------------------|
| Positive  | 🟢 Green          |
| Negative  | 🔴 Red            |
| Neutral   | ⚪ Gray           |

## Screenshots

> _Screenshots will be added once the UI is finalised._

## Project Structure

```
yt-comments-mood-check/
├── app.py                  # Flask application entry point
├── scraper.py              # Selenium-based YouTube comment scraper
├── analyzer.py             # Comment cleaning & sentiment analysis
├── templates/
│   ├── index.html          # Main page (URL input form)
│   └── results.html        # Results page (colour-coded comments)
├── static/
│   └── style.css           # Stylesheet
├── requirements.txt        # Python dependencies
├── LICENSE
└── README.md
```

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Google Chrome** (or Chromium) installed
- **ChromeDriver** matching your Chrome version (Selenium 4+ can auto-manage drivers via `webdriver-manager`)

### Installation

```bash
# Clone the repository
git clone https://github.com/gabinales/yt-comments-mood-check.git
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

### Running the App

```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000`.

## Usage

1. Paste a YouTube video URL into the input field (e.g. `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).
2. Click **Analyse Comments**.
3. Wait while the scraper collects and processes comments (this may take a moment depending on the number of comments).
4. View the results — each comment card is colour-coded by sentiment.

## Key Dependencies

| Package             | Purpose                                |
|---------------------|----------------------------------------|
| `flask`             | Web framework                          |
| `selenium`          | Browser automation / comment scraping  |
| `webdriver-manager` | Automatic ChromeDriver management      |
| `textblob` / `vaderSentiment` | Sentiment analysis            |

> The exact sentiment library will depend on the implementation chosen.

## Configuration

| Environment Variable | Default           | Description                     |
|----------------------|-------------------|---------------------------------|
| `FLASK_PORT`         | `5000`            | Port the Flask server runs on   |
| `HEADLESS`           | `True`            | Run Chrome in headless mode     |
| `MAX_SCROLL`         | `10`              | Max scroll iterations for scraping |

## Limitations

- Scraping speed depends on internet connection and video comment count.
- YouTube may throttle or block automated access; use responsibly.
- Sentiment analysis accuracy varies with comment language and slang.
- Only top-level comments are scraped (replies may not be included by default).

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request
