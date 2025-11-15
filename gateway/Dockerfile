FROM python:3.11-slim

WORKDIR /app

# Copy SDK and generated protos
COPY sdk /app/sdk
COPY generated /app/generated

# Copy gateway code
COPY gateway/http_nats_gateway.py /app/
COPY gateway/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set Python path
ENV PYTHONPATH=/app/sdk:/app/generated:/app

# Expose port
EXPOSE 8000

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV NATS_URL=nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222
ENV NATS_TIMEOUT_SECONDS=30

# Run gateway
CMD ["python", "/app/http_nats_gateway.py"]

