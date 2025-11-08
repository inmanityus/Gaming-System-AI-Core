# Silver Tier AI Inference - Interactive dialogue
# Model: Llama-3.1-8B-Instruct-INT8 (quantized)
# Target: 80-250ms latency, tool use enabled

FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install --no-cache-dir \
    vllm==0.4.2 \
    fastapi==0.104.0 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.0.0 \
    boto3==1.34.0

COPY server.py .
COPY config.json .

EXPOSE 8000

ENV MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
ENV GPU_MEMORY_UTILIZATION="0.90"
ENV MAX_MODEL_LEN="8192"
ENV MAX_NUM_SEQS="4"
ENV TENSOR_PARALLEL_SIZE="1"
ENV QUANTIZATION="int8"

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "server.py"]

