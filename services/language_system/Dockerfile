FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/language_system/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (need to copy from project root to maintain imports)
COPY services/ services/
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "services.language_system.api.server:app", "--host", "0.0.0.0", "--port", "8003"]

