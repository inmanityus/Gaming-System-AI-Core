FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Copy shared modules (if included in build context)
COPY shared /app/shared

# Expose port (if needed for health checks or API)
EXPOSE 8101

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8101/health || exit 1

# Run the service
CMD ["python", "-m", "ingest_service"]
