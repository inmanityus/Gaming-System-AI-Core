# Gold Tier AI Inference - Real-time NPC interactions
# Model: Qwen2.5-3B-Instruct-AWQ (4-bit quantized for speed)
# Target: <16ms per token latency

FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install vLLM with CUDA support
RUN pip3 install --no-cache-dir \
    vllm==0.4.2 \
    fastapi==0.104.0 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.0.0 \
    boto3==1.34.0

# Copy server code
COPY server.py .
COPY config.json .

# Expose port
EXPOSE 8000

# Environment variables (will be set by ECS task definition)
ENV MODEL_NAME="Qwen/Qwen2.5-3B-Instruct-AWQ"
ENV GPU_MEMORY_UTILIZATION="0.85"
ENV MAX_MODEL_LEN="4096"
ENV MAX_NUM_SEQS="8"
ENV TENSOR_PARALLEL_SIZE="1"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run vLLM server
CMD ["python3", "server.py"]

