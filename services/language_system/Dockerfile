# Language System Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared dependencies
COPY services/shared /app/services/shared

# Copy localization service (needed as dependency)
COPY services/localization /app/services/localization

# Copy language system service
COPY services/language_system /app/services/language_system

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Run the service
CMD ["python", "-m", "services.language_system.server"]