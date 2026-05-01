# ── Backend Docker image ──────────────────────────────────────────────────────
# Uses Python slim to keep image small
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers model so it's baked into the image
# This avoids downloading on every cold start
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy backend source
COPY backend/ ./backend/

# Create data directories
RUN mkdir -p data/uploads data/index

# Expose port
EXPOSE 7860

# Hugging Face Spaces uses port 7860 by default
# For local Docker use port 8000 (override with docker run -p 8000:7860)
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "7860"]
