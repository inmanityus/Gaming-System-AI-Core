# Build and Push All NATS Service Images
# Comprehensive script to rebuild and push all 22 NATS services

param(
    [int]$ParallelBuilds = 3
)

$ErrorActionPreference = "Continue"

cd "E:\Vibe Code\Gaming System\AI Core"

$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "time_manager", "weather_manager", "auth",
    "settings", "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "language_system",
    "environmental_narrative", "story_teller", "body_broker_integration"
)

$ecrRepo = "695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services"

Write-Host "=== Building and Pushing 22 NATS Services ===" -ForegroundColor Cyan
Write-Host "Parallel builds: $ParallelBuilds"

$built = 0
$pushed = 0
$failed = 0

foreach ($service in $services) {
    $imageName = $service.Replace("_", "-")
    $dockerfilePath = "services/$service/Dockerfile.nats"
    
    Write-Host "`nProcessing $imageName..." -ForegroundColor Yellow
    
    if (-not (Test-Path $dockerfilePath)) {
        Write-Host "  ❌ Dockerfile not found: $dockerfilePath" -ForegroundColor Red
        $failed++
        continue
    }
    
    # Build
    Write-Host "  Building..."
    $buildOutput = docker build -f $dockerfilePath -t "$imageName-nats:latest" . 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Build failed" -ForegroundColor Red
        Write-Host "  Error: $buildOutput"
        $failed++
        continue
    }
    
    Write-Host "  ✅ Built" -ForegroundColor Green
    $built++
    
    # Tag
    docker tag "$imageName-nats:latest" "$ecrRepo/$imageName-nats:latest"
    
    # Push
    Write-Host "  Pushing to ECR..."
    $pushOutput = docker push "$ecrRepo/$imageName-nats:latest" 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Push failed" -ForegroundColor Red
        Write-Host "  Error: $pushOutput"
        $failed++
        continue
    }
    
    Write-Host "  ✅ Pushed" -ForegroundColor Green
    $pushed++
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Built: $built/22" -ForegroundColor $(if ($built -eq 22) { "Green" } else { "Yellow" })
Write-Host "Pushed: $pushed/22" -ForegroundColor $(if ($pushed -eq 22) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($pushed -eq 22) {
    Write-Host "`n✅ All images successfully pushed to ECR!" -ForegroundColor Green
    Write-Host "`nNext step: Update ECS services with new images"
    Write-Host "  pwsh -File scripts\update-all-nats-services.ps1"
} else {
    Write-Host "`n⚠️ Some images failed. Review errors above." -ForegroundColor Yellow
}

