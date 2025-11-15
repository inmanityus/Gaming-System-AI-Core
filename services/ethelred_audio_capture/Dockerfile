FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy shared modules from build context
COPY shared /app/shared

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Create media storage directory
RUN mkdir -p /media/audio && chown appuser:appuser /media/audio

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8089  # FastAPI
EXPOSE 8090  # Prometheus metrics

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:8089/health || exit 1

# Run the service
CMD ["python", "-u", "capture_service.py"]
