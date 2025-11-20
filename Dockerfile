FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

# Copy application code
COPY services/ ./services/
COPY .env.example .env

# Expose port
EXPOSE 8000

# Health check using urllib (no external dependencies)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run the application
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]