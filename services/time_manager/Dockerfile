FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Create proto module directory
RUN mkdir -p proto

# Note: Compiled protobuf files (events_pb2.py) should be in service directory
# Run: docker run --rm -v ./services/proto:/proto python:3.11 python -m grpc_tools.protoc ...

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
