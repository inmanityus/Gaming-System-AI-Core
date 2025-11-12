# Fix ECS Services - Rebuild and Redeploy Failing Services
# Fixes ModuleNotFoundError by ensuring shared dependencies are included in Docker images

param(
    [string]$AWSRegion = "us-east-1",
    [string]$ECRRepository = "bodybroker-services",
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== FIX ECS SERVICES ===" -ForegroundColor Cyan
Write-Host "Region: $AWSRegion" -ForegroundColor White

# Get AWS account ID
$accountId = aws sts get-caller-identity --region $AWSRegion --query Account --output text
$ecrUri = "$accountId.dkr.ecr.$AWSRegion.amazonaws.com/$ECRRepository"

# Failing services that need to be fixed
$failingServices = @(
    "world-state",
    "language-system",
    "settings",
    "model-management",
    "quest-system",
    "payment",
    "performance-mode",
    "ai-integration",
    "router",
    "environmental-narrative"
)

# Map ECS service names to directory names (ECS uses hyphens, directories use underscores)
$serviceNameMap = @{
    "world-state" = "world_state"
    "language-system" = "language_system"
    "model-management" = "model_management"
    "quest-system" = "quest_system"
    "performance-mode" = "performance_mode"
    "ai-integration" = "ai_integration"
    "environmental-narrative" = "environmental_narrative"
}

# Login to ECR
Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Logging into ECR..." -ForegroundColor White
aws ecr get-login-password --region $AWSRegion | docker login --username AWS --password-stdin $ecrUri
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] ECR login failed" -ForegroundColor Red
    exit 1
}
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ Logged into ECR" -ForegroundColor Green

if (-not $SkipBuild) {
    # Fix Dockerfiles to include shared dependencies
    Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Fixing Dockerfiles..." -ForegroundColor Cyan
    
    foreach ($service in $failingServices) {
        $dirName = if ($serviceNameMap.ContainsKey($service)) { $serviceNameMap[$service] } else { $service }
        $servicePath = "services\$dirName"
        
        if (-not (Test-Path $servicePath)) {
            Write-Host "[SKIP] Service $service ($dirName) not found" -ForegroundColor Yellow
            continue
        }
        
        $dockerfilePath = "$servicePath\Dockerfile"
        if (-not (Test-Path $dockerfilePath)) {
            Write-Host "[SKIP] No Dockerfile for $service" -ForegroundColor Yellow
            continue
        }
        
        Write-Host "[FIX] Updating Dockerfile for $service..." -ForegroundColor White
        
        # Create updated Dockerfile with shared dependencies
        # Note: Building from services/ directory with -f flag so paths are relative to services/
        $newDockerfile = @"
FROM python:3.11-slim

WORKDIR /app

# Copy shared dependencies (relative to services/)
COPY state_manager/ ./state_manager/

# Copy service-specific files (relative to services/service_name/)
COPY $dirName/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY $dirName/ .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
"@
        
        $newDockerfile | Out-File $dockerfilePath -Encoding utf8 -Force
        Write-Host "[✓] Updated Dockerfile for $service" -ForegroundColor Green
    }
    
    # Build and push Docker images
    Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Building and pushing Docker images..." -ForegroundColor Cyan
    
    foreach ($service in $failingServices) {
        $dirName = if ($serviceNameMap.ContainsKey($service)) { $serviceNameMap[$service] } else { $service }
        $servicePath = "services\$dirName"
        
        if (-not (Test-Path $servicePath)) {
            continue
        }
        
        Write-Host "`n[BUILD] $service..." -ForegroundColor Cyan
        
        # Build from services directory so we can access shared folders
        $imageTag = "$ecrUri`:$($dirName)-latest"
        
        Push-Location services
        try {
            docker build -t $imageTag -f "$dirName\Dockerfile" . 2>&1 | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Docker build failed for $service" -ForegroundColor Red
                continue
            }
            
            # Push image
            Write-Host "[PUSH] $service to ECR..." -ForegroundColor White
            docker push $imageTag 2>&1 | Write-Host
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Docker push failed for $service" -ForegroundColor Red
                continue
            }
            
            Write-Host "[✓] $service deployed to ECR" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    }
}

# Force ECS to redeploy services with new images
Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Force redeploying ECS services..." -ForegroundColor Cyan

foreach ($service in $failingServices) {
    Write-Host "[REDEPLOY] $service..." -ForegroundColor White
    
    aws ecs update-service `
        --cluster gaming-system-cluster `
        --service $service `
        --force-new-deployment `
        --region $AWSRegion `
        --no-cli-pager `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] $service redeployment triggered" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to redeploy $service" -ForegroundColor Red
    }
}

Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Waiting 60 seconds for services to start..." -ForegroundColor White
Start-Sleep -Seconds 60

# Check service status
Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Checking service status..." -ForegroundColor Cyan

$fixedCount = 0
$stillFailingCount = 0

foreach ($service in $failingServices) {
    $serviceInfo = aws ecs describe-services `
        --cluster gaming-system-cluster `
        --services $service `
        --region $AWSRegion `
        --query "services[0].[serviceName,runningCount,desiredCount]" `
        --output text
    
    $parts = $serviceInfo -split "`t"
    $name = $parts[0]
    $running = $parts[1]
    $desired = $parts[2]
    
    if ($running -eq $desired -and $running -gt 0) {
        Write-Host "[✓] $name : $running/$desired running" -ForegroundColor Green
        $fixedCount++
    } else {
        Write-Host "[✗] $name : $running/$desired running" -ForegroundColor Red
        $stillFailingCount++
    }
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Fixed: $fixedCount services" -ForegroundColor Green
Write-Host "Still failing: $stillFailingCount services" -ForegroundColor $(if ($stillFailingCount -eq 0) { "Green" } else { "Red" })

if ($stillFailingCount -eq 0) {
    Write-Host "`n✓ ALL SERVICES HEALTHY" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nCheck CloudWatch logs for remaining failures:" -ForegroundColor Yellow
    Write-Host "  aws logs tail /ecs/gaming-system/<service-name> --region $AWSRegion --since 10m" -ForegroundColor White
    exit 1
}

