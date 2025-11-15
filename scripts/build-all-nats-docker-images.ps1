# Build All NATS Service Docker Images
# Builds 22 service images and pushes to ECR

param(
    [string]$Region = "us-east-1",
    [string]$AccountId = "695353648052",
    [switch]$Push = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Building All NATS Service Docker Images ===" -ForegroundColor Cyan
Write-Host "Region: $Region"
Write-Host "Account: $AccountId"
Write-Host "Push to ECR: $Push"

$ecrRepo = "$AccountId.dkr.ecr.$Region.amazonaws.com/bodybroker-services"

# Services with nats_server.py
$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "time_manager", "weather_manager", "auth",
    "settings", "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "language_system",
    "environmental_narrative", "story_teller", "body_broker_integration"
)

# Login to ECR if pushing
if ($Push) {
    Write-Host "`nLogging in to ECR..." -ForegroundColor Yellow
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ecrRepo
}

$built = 0
$failed = 0

foreach ($service in $services) {
    $servicePath = "services\$service"
    $dockerfilePath = "$servicePath\Dockerfile.nats"
    
    Write-Host "`n=== Building $service-nats ===" -ForegroundColor Yellow
    
    # Create Dockerfile if doesn't exist
    if (-not (Test-Path $dockerfilePath)) {
        Write-Host "Creating Dockerfile.nats..."
        
        $dockerfile = @"
FROM python:3.11-slim

WORKDIR /app

# Copy SDK and generated protos
COPY sdk /app/sdk
COPY generated /app/generated

# Copy service
COPY services/$service /app/services/$service

# Install dependencies
RUN pip install --no-cache-dir \
    nats-py>=2.9.0 \
    protobuf>=5.29.0 \
    opentelemetry-api>=1.20.0 \
    opentelemetry-sdk>=1.20.0 \
    opentelemetry-exporter-otlp-proto-grpc>=1.20.0

# Set Python path
ENV PYTHONPATH=/app/sdk:/app/generated:/app

# Environment variables
ENV NATS_URL=nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222
ENV SERVICE_NAME=$service-nats

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ps aux | grep -q '[p]ython.*nats_server.py' || exit 1

# Run service
CMD ["python", "services/$service/nats_server.py"]
"@
        
        Set-Content -Path $dockerfilePath -Value $dockerfile
    }
    
    # Build image
    try {
        Write-Host "Building Docker image..."
        docker build -f $dockerfilePath -t "$service-nats:latest" . 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed"
        }
        
        # Tag for ECR
        $tagName = "$service-nats".Replace("_", "-")
        docker tag "$service-nats:latest" "$ecrRepo/$tagName:latest"
        
        Write-Host "  ✅ Built: $tagName" -ForegroundColor Green
        $built++
        
        # Push if requested
        if ($Push) {
            Write-Host "  Pushing to ECR..."
            docker push "$ecrRepo/$tagName:latest" 2>&1 | Out-Null
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  ⚠️ Push failed" -ForegroundColor Yellow
            } else {
                Write-Host "  ✅ Pushed to ECR" -ForegroundColor Green
            }
        }
    }
    catch {
        Write-Host "  ❌ Failed: $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n=== Build Summary ===" -ForegroundColor Cyan
Write-Host "Built: $built/$($services.Count)" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($Push) {
    Write-Host "`n✅ Images pushed to ECR"
    Write-Host "Next: Deploy to ECS with scripts\deploy-nats-services-to-ecs.ps1"
} else {
    Write-Host "`nTo push to ECR, run with -Push flag"
}

