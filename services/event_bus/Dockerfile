FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY event_bus/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy all needed services for cross-service imports
COPY state_manager/ ./services/state_manager/
COPY event_bus/ ./services/event_bus/

# Set PYTHONPATH so 'from services.X' imports work
ENV PYTHONPATH=/app

EXPOSE 8000

# Run service from services/ directory
WORKDIR /app/services
CMD ["python", "-m", "uvicorn", "event_bus.server:app", "--host", "0.0.0.0", "--port", "8000"]
