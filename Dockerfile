# Visions AI - Cloud Run Deployment
# v3.1.0 - Gemini 3 Multi-Model Cascade
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install FastAPI, Uvicorn, and Gunicorn for production
RUN pip install --no-cache-dir fastapi uvicorn[standard] gunicorn

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run with Gunicorn + UvicornWorker for FastAPI ASGI support
# Using UvicornWorker for ASGI (FastAPI) compatibility
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "300", "visions.api.app:app"]
