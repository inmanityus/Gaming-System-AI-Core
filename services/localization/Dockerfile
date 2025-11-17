# Localization Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared dependencies
COPY services/shared /app/services/shared

# Copy service code
COPY services/localization /app/services/localization

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Run the service
CMD ["python", "-m", "services.localization.server"]
