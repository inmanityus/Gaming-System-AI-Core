#!/bin/bash
set -euo pipefail

SERVICE_NAME=$1
DOCKERFILE_PATH=$2
SERVICE_PATH=$(dirname "$DOCKERFILE_PATH")

# Optional parameters
PORT=${3:-8000}
HEALTH_ENDPOINT=${4:-/health}
TIMEOUT=${5:-60}

if [ -z "$SERVICE_NAME" ] || [ -z "$DOCKERFILE_PATH" ]; then
  echo "Usage: $0 <service_name> <dockerfile_path> [port] [health_endpoint] [timeout]"
  exit 1
fi

IMAGE_NAME="local/${SERVICE_NAME}:smoke-test-$$"
CONTAINER_NAME="${SERVICE_NAME}-smoke-test-$$"
NETWORK_NAME="smoke-test-network-$$"

echo "========================================="
echo "Smoke Testing: $SERVICE_NAME"
echo "========================================="
echo "Docker image: $IMAGE_NAME"
echo "Container: $CONTAINER_NAME"
echo "Port: $PORT"
echo "Health endpoint: $HEALTH_ENDPOINT"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    docker network rm "$NETWORK_NAME" 2>/dev/null || true
}
trap cleanup EXIT

# Create isolated network
echo "Creating test network..."
docker network create "$NETWORK_NAME"

# Build the Docker image
echo "Building Docker image..."
if ! docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME" --build-arg SERVICE_PATH="$SERVICE_PATH" .; then
    echo "❌ Docker build failed for $SERVICE_NAME"
    exit 1
fi

# Scan the image for vulnerabilities (basic check)
echo "Scanning image for critical vulnerabilities..."
if command -v trivy &> /dev/null; then
    trivy image --severity CRITICAL --exit-code 1 "$IMAGE_NAME" || {
        echo "⚠️  WARNING: Critical vulnerabilities found in image"
    }
fi

# Run mock dependencies if needed
if [ -f "$SERVICE_PATH/smoke-test-deps.yml" ]; then
    echo "Starting mock dependencies..."
    docker-compose -f "$SERVICE_PATH/smoke-test-deps.yml" -p "smoke-$SERVICE_NAME" up -d
fi

# Run the container with proper configuration
echo "Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -p "${PORT}:${PORT}" \
    -e "SERVICE_NAME=${SERVICE_NAME}" \
    -e "ENVIRONMENT=smoke-test" \
    -e "LOG_LEVEL=debug" \
    -e "NATS_ENABLED=false" \
    -e "DB_CONNECTION_ENABLED=false" \
    --health-cmd="curl -f http://localhost:${PORT}${HEALTH_ENDPOINT} || exit 1" \
    --health-interval=5s \
    --health-timeout=3s \
    --health-retries=10 \
    "$IMAGE_NAME"

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Check if container is still running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container failed to start"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

# Monitor container health
echo "Monitoring container health..."
start_time=$(date +%s)
health_check_passed=false

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $TIMEOUT ]; then
        echo "❌ Timeout: Container did not become healthy within ${TIMEOUT}s"
        break
    fi
    
    # Check container status
    container_status=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "not-found")
    
    if [ "$container_status" != "running" ]; then
        echo "❌ Container is not running (status: $container_status)"
        break
    fi
    
    # Check container health
    health_status=$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "none")
    
    if [ "$health_status" == "healthy" ]; then
        echo "✅ Container is healthy!"
        health_check_passed=true
        break
    elif [ "$health_status" == "unhealthy" ]; then
        echo "❌ Container is unhealthy"
        break
    fi
    
    # Manual health check as backup
    if curl -s -f "http://localhost:${PORT}${HEALTH_ENDPOINT}" > /dev/null 2>&1; then
        echo "✅ Manual health check passed"
        health_check_passed=true
        break
    fi
    
    echo "Waiting for health check... (${elapsed}s elapsed, status: $health_status)"
    sleep 5
done

# Perform additional smoke tests if healthy
if [ "$health_check_passed" = true ]; then
    echo ""
    echo "Running additional smoke tests..."
    
    # Test 1: Check response headers
    echo -n "Testing response headers... "
    headers=$(curl -s -I "http://localhost:${PORT}${HEALTH_ENDPOINT}")
    if echo "$headers" | grep -q "Content-Type"; then
        echo "✅ Pass"
    else
        echo "❌ Fail: No Content-Type header"
    fi
    
    # Test 2: Check JSON response
    echo -n "Testing JSON health response... "
    health_response=$(curl -s "http://localhost:${PORT}${HEALTH_ENDPOINT}")
    if echo "$health_response" | jq -e '.status' > /dev/null 2>&1; then
        echo "✅ Pass"
        echo "  Status: $(echo "$health_response" | jq -r '.status // "unknown"')"
    else
        echo "❌ Fail: Invalid JSON response"
    fi
    
    # Test 3: Check OpenAPI/Swagger endpoint if exists
    echo -n "Testing OpenAPI endpoint... "
    if curl -s -f "http://localhost:${PORT}/openapi.json" > /dev/null 2>&1; then
        echo "✅ Pass"
    elif curl -s -f "http://localhost:${PORT}/docs" > /dev/null 2>&1; then
        echo "✅ Pass (Swagger UI available)"
    else
        echo "⚠️  Skip: No OpenAPI endpoint found"
    fi
    
    # Test 4: Check metrics endpoint if exists
    echo -n "Testing metrics endpoint... "
    if curl -s -f "http://localhost:${PORT}/metrics" > /dev/null 2>&1; then
        echo "✅ Pass"
    else
        echo "⚠️  Skip: No metrics endpoint found"
    fi
    
    # Test 5: Service-specific tests
    if [ -f "$SERVICE_PATH/smoke-tests.sh" ]; then
        echo ""
        echo "Running service-specific tests..."
        bash "$SERVICE_PATH/smoke-tests.sh" "http://localhost:${PORT}"
    fi
fi

# Display logs
echo ""
echo "Container logs (last 50 lines):"
echo "================================"
docker logs --tail 50 "$CONTAINER_NAME"

# Display resource usage
echo ""
echo "Resource usage:"
echo "==============="
docker stats --no-stream "$CONTAINER_NAME"

# Cleanup mock dependencies
if [ -f "$SERVICE_PATH/smoke-test-deps.yml" ]; then
    docker-compose -f "$SERVICE_PATH/smoke-test-deps.yml" -p "smoke-$SERVICE_NAME" down
fi

# Exit with appropriate code
if [ "$health_check_passed" = true ]; then
    echo ""
    echo "✅ Smoke test PASSED for $SERVICE_NAME"
    exit 0
else
    echo ""
    echo "❌ Smoke test FAILED for $SERVICE_NAME"
    exit 1
fi
