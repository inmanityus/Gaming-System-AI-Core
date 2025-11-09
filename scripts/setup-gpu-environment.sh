#!/bin/bash
# Setup GPU environment on AWS instance

set -e

echo "Setting up GPU environment for Body Broker training..."

# Update system
sudo apt-get update
sudo apt-get install -y git python3-pip redis-server postgresql-client

# Install Python dependencies
pip3 install -r requirements-complete.txt

# Install vLLM
pip3 install vllm>=0.4.0

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Clone/sync code
# (Code transfer via SCP or git pull)

# Start vLLM server
echo "Starting vLLM server..."
nohup python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --quantization awq \
  --dtype float16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9 \
  --enable-lora \
  --max-loras 35 \
  --max-lora-rank 64 \
  --host 0.0.0.0 \
  --port 8000 > vllm.log 2>&1 &

echo "✅ GPU environment setup complete"
echo "vLLM server starting (check vllm.log for progress)"

