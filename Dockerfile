FROM python:3.10-slim

WORKDIR /app

# System dependencies (yt-dlp benefits from ffmpeg for post-processing)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the XLM-RoBERTa model at build time to avoid cold-start delays
RUN python -c "\
from transformers import pipeline; \
pipeline('sentiment-analysis', \
         model='cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual')"

# Copy application code
COPY . .

# Hugging Face Spaces routes external traffic to port 7860
EXPOSE 7860

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--timeout", "600", "--workers", "1"]
