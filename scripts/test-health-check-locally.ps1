# Test Health Check Locally Before Deploying

Write-Host "Testing health check implementation..." -ForegroundColor Cyan

# Build test image
Write-Host "`nBuilding test image..."
docker build -f services/ai_integration/Dockerfile.nats -t test-health-check . --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build successful"

# Run container with health port mapped
Write-Host "`nStarting container..."
$containerId = docker run -d -p 8080:8080 --name test-health-svc test-health-check 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Container failed to start: $containerId" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started: $($containerId.Substring(0,12))"

# Wait for startup
Write-Host "`nWaiting 15 seconds for service to initialize..."
Start-Sleep -Seconds 15

# Check if port is listening
Write-Host "`nChecking if port 8080 is listening..."
$portTest = Test-NetConnection -ComputerName localhost -Port 8080 -WarningAction SilentlyContinue

if ($portTest.TcpTestSucceeded) {
    Write-Host "✅ Port 8080 is listening" -ForegroundColor Green
    
    # Try HTTP request
    Write-Host "`nTesting HTTP endpoint..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5
        Write-Host "✅ Health check responded: $($response.StatusCode) $($response.Content)" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ HTTP request failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Port 8080 is not responding" -ForegroundColor Red
}

# Show logs
Write-Host "`nContainer logs:"
docker logs test-health-svc 2>&1 | Select-Object -Last 20

# Cleanup
Write-Host "`nCleaning up..."
docker stop test-health-svc 2>&1 | Out-Null
docker rm test-health-svc 2>&1 | Out-Null

Write-Host "✅ Cleanup complete"

