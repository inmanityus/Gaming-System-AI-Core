# Deploy Services to AWS
# Creates Docker images and deploys to ECS/EKS/Lambda

param(
    [string]$AWSProfile = "default",
    [string]$AWSRegion = "us-east-1",
    [string]$ECRRepository = "bodybroker-services"
)

$ErrorActionPreference = "Stop"

Write-Host "[AWS DEPLOY] Deploying Services to AWS..." -ForegroundColor Cyan
Write-Host "[REGION] $AWSRegion" -ForegroundColor White
Write-Host "[PROFILE] $AWSProfile" -ForegroundColor White

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] AWS CLI not found - install from https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Get AWS account ID
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Getting AWS account ID..." -ForegroundColor White
$accountId = aws sts get-caller-identity --profile $AWSProfile --region $AWSRegion --query Account --output text
if (-not $accountId) {
    Write-Host "[ERROR] Cannot get AWS account ID - check credentials" -ForegroundColor Red
    exit 1
}
Write-Host "[ACCOUNT] $accountId" -ForegroundColor Green

$ecrUri = "$accountId.dkr.ecr.$AWSRegion.amazonaws.com/$ECRRepository"

# Create ECR repository if it doesn't exist
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Checking ECR repository..." -ForegroundColor White
$repoExists = aws ecr describe-repositories --repository-names $ECRRepository --profile $AWSProfile --region $AWSRegion 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Creating ECR repository..." -ForegroundColor White
    aws ecr create-repository --repository-name $ECRRepository --profile $AWSProfile --region $AWSRegion | Out-Null
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ ECR repository created" -ForegroundColor Green
}
else {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ ECR repository exists" -ForegroundColor Green
}

# Login to ECR
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Logging into ECR..." -ForegroundColor White
aws ecr get-login-password --region $AWSRegion --profile $AWSProfile | docker login --username AWS --password-stdin $ecrUri
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] ECR login failed" -ForegroundColor Red
    exit 1
}
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Logged into ECR" -ForegroundColor Green

# Build and push Docker images for each service
$buildFailures = @()
$services = @(
    "story_teller",
    "ai_integration",
    "model_management",
    "event_bus",
    "time_manager",
    "weather_manager"
)

foreach ($service in $services) {
    $servicePath = "services\$service"
    if (-not (Test-Path $servicePath)) {
        Write-Host "[SKIP] Service $service not found, skipping..." -ForegroundColor Yellow
        continue
    }

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Building $service Docker image..." -ForegroundColor Cyan
    
    # Check for Dockerfile
    if (-not (Test-Path "$servicePath\Dockerfile")) {
        Write-Host "[WARNING] No Dockerfile found for $service - creating default..." -ForegroundColor Yellow
        # Create default Dockerfile
        @"
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
"@ | Out-File "$servicePath\Dockerfile" -Encoding utf8
    }

    # Ensure a stub requirements file exists so Docker build does not fail
    if (-not (Test-Path "$servicePath\requirements.txt")) {
        "" | Out-File "$servicePath\requirements.txt" -Encoding utf8
    }

    # Build image
    $imageTag = "{0}:{1}-latest" -f $ecrUri, $service
    docker build -t $imageTag "$servicePath" 2>&1 | Write-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker build failed for $service" -ForegroundColor Red
        $buildFailures += "$service (build)"
        continue
    }

    # Push image
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Pushing $service to ECR..." -ForegroundColor White
    docker push $imageTag 2>&1 | Write-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker push failed for $service" -ForegroundColor Red
        $buildFailures += "$service (push)"
        continue
    }

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ $service deployed to ECR" -ForegroundColor Green
}

Write-Host ""
if ($buildFailures.Count -eq 0) {
    Write-Host "[AWS DEPLOY] ✅ Services deployed to AWS ECR" -ForegroundColor Green
    Write-Host "[NEXT] Deploy services to ECS/EKS/Lambda using infrastructure scripts" -ForegroundColor Cyan
} else {
    Write-Host "[AWS DEPLOY] ⚠️  Completed with issues" -ForegroundColor Yellow
    Write-Host "  Failed components:" -ForegroundColor Yellow
    foreach ($failure in $buildFailures) {
        Write-Host "   - $failure" -ForegroundColor Red
    }
    exit 1
}




