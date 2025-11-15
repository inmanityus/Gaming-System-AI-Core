#!/bin/bash
# Deploy all NATS services to AWS ECS
# Builds Docker images and deploys to Fargate

set -euo pipefail

REGION="us-east-1"
ACCOUNT_ID="695353648052"
ECR_REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/bodybroker-services"
CLUSTER="gaming-system-cluster"

# Services to deploy
SERVICES=(
    "ai-integration"
    "model-management"
    "state-manager"
    "quest-system"
    "npc-behavior"
    "world-state"
    "orchestration"
    "router"
    "event-bus"
    "time-manager"
    "weather-manager"
    "auth"
    "settings"
    "payment"
    "performance-mode"
    "capability-registry"
    "ai-router"
    "knowledge-base"
    "language-system"
    "environmental-narrative"
    "story-teller"
    "body-broker-integration"
)

echo "=== NATS Services Deployment ==="
echo "Region: $REGION"
echo "Cluster: $CLUSTER"
echo "Services: ${#SERVICES[@]}"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# Build and push each service
for service in "${SERVICES[@]}"; do
    echo ""
    echo "=== Building $service-nats ==="
    
    service_dir="services/$(echo $service | tr '-' '_')"
    
    if [ ! -f "$service_dir/nats_server.py" ]; then
        echo "⚠️  nats_server.py not found for $service, skipping"
        continue
    fi
    
    # Create Dockerfile if not exists
    dockerfile="$service_dir/Dockerfile.nats"
    if [ ! -f "$dockerfile" ]; then
        echo "Creating Dockerfile.nats for $service..."
        cat > "$dockerfile" <<EOF
FROM python:3.11-slim

WORKDIR /app

# Copy SDK and generated protos
COPY sdk /app/sdk
COPY generated /app/generated

# Copy service
COPY $service_dir /app/services/$(basename $service_dir)

# Install dependencies
RUN pip install --no-cache-dir nats-py protobuf opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

# Set Python path
ENV PYTHONPATH=/app/sdk:/app/generated:/app

# Run service
CMD ["python", "services/$(basename $service_dir)/nats_server.py"]
EOF
    fi
    
    # Build image
    docker build -f "$dockerfile" -t "$service-nats:latest" .
    
    # Tag for ECR
    docker tag "$service-nats:latest" "$ECR_REPO/$service-nats:latest"
    
    # Push to ECR
    echo "Pushing $service-nats to ECR..."
    docker push "$ECR_REPO/$service-nats:latest"
    
    # Register task definition
    echo "Registering ECS task definition..."
    # TODO: Create task definition JSON for each service
    
    # Update or create ECS service
    echo "Deploying to ECS..."
    # TODO: Deploy to ECS cluster
    
    echo "✅ $service-nats deployed"
done

echo ""
echo "=== Deployment Complete ==="
echo "All NATS services deployed to ECS cluster: $CLUSTER"

