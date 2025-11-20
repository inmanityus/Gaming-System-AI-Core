#!/bin/bash
# Smoke test script for microservices
# Usage: ./smoke-test-service.sh <service-name>

set -euo pipefail

SERVICE_NAME="${1:-}"
CONTAINER_NAME="${SERVICE_NAME}-smoke-test"
MAX_WAIT_SECONDS=30
CHECK_INTERVAL=1

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service-name>"
    exit 1
fi

echo "Starting smoke test for service: $SERVICE_NAME"

# Function to check if container is healthy
check_container_health() {
    local container_name=$1
    
    # Check if container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        return 1
    fi
    
    # Check container logs for startup indicators
    local logs=$(docker logs "$container_name" 2>&1 || echo "")
    
    # Check for successful startup patterns
    if echo "$logs" | grep -qE "(started|listening|ready|connected|initialized|startup complete)"; then
        echo "✓ Service started successfully"
        return 0
    fi
    
    # Check for error patterns
    if echo "$logs" | grep -qE "(ImportError|ModuleNotFoundError|SyntaxError|IndentationError|NameError|AttributeError)"; then
        echo "✗ Python import/syntax errors detected:"
        echo "$logs" | grep -E "(ImportError|ModuleNotFoundError|SyntaxError|IndentationError|NameError|AttributeError)" | head -5
        return 2
    fi
    
    if echo "$logs" | grep -qE "(FATAL|CRITICAL|Traceback|Exception|Error in startup)"; then
        echo "✗ Fatal errors detected during startup:"
        echo "$logs" | grep -E "(FATAL|CRITICAL|Traceback|Exception|Error)" | head -5
        return 2
    fi
    
    # Still waiting
    return 1
}

# Stop any existing container with the same name
if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# Run the container
echo "Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -e POSTGRES_HOST=localhost \
    -e POSTGRES_PORT=5432 \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=test_password \
    -e POSTGRES_DB=test_db \
    -e REDIS_URL=redis://localhost:6379 \
    -e NATS_URL=nats://localhost:4222 \
    -e AWS_DEFAULT_REGION=us-east-1 \
    -e AWS_ACCESS_KEY_ID=test \
    -e AWS_SECRET_ACCESS_KEY=test \
    -e PYTHONUNBUFFERED=1 \
    "local/$SERVICE_NAME:smoke"

# Wait for service to start
echo "Waiting for service to start (max ${MAX_WAIT_SECONDS}s)..."
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT_SECONDS ]; do
    if check_container_health "$CONTAINER_NAME"; then
        echo ""
        echo "✓ Smoke test PASSED for $SERVICE_NAME"
        
        # Show last few log lines
        echo ""
        echo "Last log entries:"
        docker logs "$CONTAINER_NAME" 2>&1 | tail -10
        
        # Cleanup
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1
        exit 0
    fi
    
    # Check if container exited
    if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo ""
        echo "✗ Container exited prematurely!"
        echo ""
        echo "Exit code:"
        docker inspect "$CONTAINER_NAME" --format='{{.State.ExitCode}}'
        echo ""
        echo "Full logs:"
        docker logs "$CONTAINER_NAME" 2>&1
        
        # Cleanup
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1
        exit 1
    fi
    
    echo -n "."
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

echo ""
echo "✗ Service failed to start within ${MAX_WAIT_SECONDS} seconds"
echo ""
echo "Container logs:"
docker logs "$CONTAINER_NAME" 2>&1

# Cleanup
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

exit 1
