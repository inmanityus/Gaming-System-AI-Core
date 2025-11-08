# GPU Metrics Publisher - Publishes NVIDIA GPU metrics to CloudWatch
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN pip3 install --no-cache-dir boto3 psutil

# Install NVIDIA DCGM (Data Center GPU Manager)
RUN curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb -o cuda-keyring.deb \
    && dpkg -i cuda-keyring.deb \
    && apt-get update \
    && apt-get install -y datacenter-gpu-manager \
    && rm cuda-keyring.deb

WORKDIR /app

# Copy application code
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY publisher.py .

# Run publisher
CMD ["python3", "publisher.py"]

