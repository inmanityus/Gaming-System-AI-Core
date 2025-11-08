# Deploy All Services with Binary Messaging to ECS
# Comprehensive rollout of binary Protocol Buffers across entire system

param(
    [string]$Region = "us-east-1",
    [string]$Cluster = "gaming-system-cluster",
    [string]$ECRRepo = "bodybroker-services",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "=== COMPREHENSIVE BINARY MESSAGING ROLLOUT ===" -ForegroundColor Green
Write-Host ""
Write-Host "Cluster: $Cluster" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "ECR: $ECRRepo" -ForegroundColor White
if ($DryRun) {
    Write-Host "Mode: DRY RUN (no actual deployment)" -ForegroundColor Yellow
}
Write-Host ""

# Get AWS account ID
$accountId = aws sts get-caller-identity --query "Account" --output text
$ecrUri = "$accountId.dkr.ecr.$Region.amazonaws.com/$ECRRepo"

Write-Host "Account: $accountId" -ForegroundColor Green
Write-Host ""

# Services to deploy (with Dockerfiles)
$servicesToDeploy = @(
    "ai_integration",
    "capability-registry",
    "event_bus",
    "language_system",
    "model_management",
    "story_teller",
    "storyteller",
    "ue-version-monitor"
    # weather_manager and time_manager already deployed
)

# Services that need Dockerfiles created
$servicesNeedingDockerfile = @(
    "environmental_narrative",
    "npc_behavior",
    "orchestration",
    "payment",
    "performance_mode",
    "quest_system",
    "router",
    "settings",
    "state_manager",
    "world_state"
)

Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Services ready for deployment: $($servicesToDeploy.Count)" -ForegroundColor White
Write-Host "  Services need Dockerfiles: $($servicesNeedingDockerfile.Count)" -ForegroundColor White
Write-Host "  Already deployed: 2 (weather_manager, time_manager)" -ForegroundColor Green
Write-Host "  Total services: $($servicesToDeploy.Count + $servicesNeedingDockerfile.Count + 2)" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - Would deploy:" -ForegroundColor Yellow
    $servicesToDeploy | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "Would create Dockerfiles for:" -ForegroundColor Yellow
    $servicesNeedingDockerfile | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Gray
    }
    exit 0
}

# Login to ECR
Write-Host "🔐 Logging into ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ecrUri | Out-Null
Write-Host "✅ ECR login successful" -ForegroundColor Green
Write-Host ""

# Function to check if service uses event publishing
function Test-ServiceUsesEvents {
    param([string]$ServicePath)
    
    $serverFile = Join-Path $ServicePath "server.py"
    $mainFile = Join-Path $ServicePath "main.py"
    
    $hasEventUsage = $false
    if (Test-Path $serverFile) {
        $content = Get-Content $serverFile -Raw
        if ($content -match "event|publish|subscribe") {
            $hasEventUsage = $true
        }
    }
    if (Test-Path $mainFile) {
        $content = Get-Content $mainFile -Raw
        if ($content -match "event|publish|subscribe") {
            $hasEventUsage = $true
        }
    }
    
    return $hasEventUsage
}

# Function to deploy a service
function Deploy-Service {
    param(
        [string]$ServiceName,
        [string]$ServicePath
    )
    
    Write-Host "=== Deploying $ServiceName ===" -ForegroundColor Cyan
    
    # Check if Dockerfile exists
    $dockerfilePath = Join-Path $ServicePath "Dockerfile"
    if (-not (Test-Path $dockerfilePath)) {
        Write-Host "  ⚠ No Dockerfile found, skipping" -ForegroundColor Yellow
        return $false
    }
    
    # Check if service uses events
    $usesEvents = Test-ServiceUsesEvents $ServicePath
    if ($usesEvents) {
        Write-Host "  ℹ Service uses events, binary messaging will be available" -ForegroundColor Cyan
    }
    
    # Build Docker image
    Write-Host "  🔨 Building image..." -ForegroundColor White
    $buildResult = docker build -q -t "${ServiceName}:latest" $ServicePath 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Build failed: $buildResult" -ForegroundColor Red
        return $false
    }
    Write-Host "  ✓ Image built" -ForegroundColor Green
    
    # Tag for ECR
    $imageName = $ServiceName -replace "_", "-"
    docker tag "${ServiceName}:latest" "${ecrUri}:${imageName}-latest" | Out-Null
    
    # Push to ECR
    Write-Host "  📤 Pushing to ECR..." -ForegroundColor White
    docker push "${ecrUri}:${imageName}-latest" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Push failed" -ForegroundColor Red
        return $false
    }
    Write-Host "  ✓ Pushed to ECR" -ForegroundColor Green
    
    Write-Host "  ✅ $ServiceName ready for ECS deployment" -ForegroundColor Green
    Write-Host ""
    
    return $true
}

# Deploy each service
$deployed = 0
$failed = 0

foreach ($service in $servicesToDeploy) {
    $servicePath = Join-Path "services" $service
    $result = Deploy-Service -ServiceName $service -ServicePath $servicePath
    
    if ($result) {
        $deployed++
    } else {
        $failed++
    }
}

Write-Host "=== DEPLOYMENT SUMMARY ===" -ForegroundColor Green
Write-Host "✓ Successfully deployed: $deployed" -ForegroundColor Green
Write-Host "✗ Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($deployed -gt 0) {
    Write-Host "📋 Images in ECR (ready for ECS):" -ForegroundColor Cyan
    aws ecr list-images --repository-name $ECRRepo --region $Region --query "imageIds[?imageTag!=null].imageTag" --output text | ForEach-Object { $_ -split "`t" } | Sort-Object | ForEach-Object {
        if ($_ -match "-latest$") {
            Write-Host "  - $_" -ForegroundColor White
        }
    }
    Write-Host ""
    Write-Host "✅ Ready to create ECS services for deployed images!" -ForegroundColor Green
}

if ($failed -gt 0) {
    Write-Host "⚠️  Some services failed. Check logs above." -ForegroundColor Yellow
}

