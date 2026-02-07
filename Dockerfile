# ---- Study-Notion Docker Image ----
FROM python:3.12-slim

# Install system dependencies (ffmpeg for yt-dlp, deno for JS runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl unzip && \
    curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (Docker cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for persistent data
RUN mkdir -p instance logs static/uploads/course_thumbnails \
    static/uploads/profile_pics static/uploads/media

# Expose port
EXPOSE 5000

# Environment defaults (override in docker-compose or docker run)
ENV SECRET_KEY=study-notion-docker-secret-2026
ENV GEMINI_API_KEY=""
ENV FLASK_ENV=production

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main:create_app()"]
