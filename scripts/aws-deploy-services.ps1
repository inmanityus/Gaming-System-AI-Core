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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
"@ | Out-File "$servicePath\Dockerfile" -Encoding utf8
    }

    # Build image
    $imageTag = "$ecrUri:$service-latest"
    docker build -t $imageTag "$servicePath" 2>&1 | Write-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker build failed for $service" -ForegroundColor Red
        continue
    }

    # Push image
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Pushing $service to ECR..." -ForegroundColor White
    docker push $imageTag 2>&1 | Write-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker push failed for $service" -ForegroundColor Red
        continue
    }

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ $service deployed to ECR" -ForegroundColor Green
}

Write-Host ""
Write-Host "[AWS DEPLOY] ✅ Services deployed to AWS ECR" -ForegroundColor Green
Write-Host "[NEXT] Deploy services to ECS/EKS/Lambda using infrastructure scripts" -ForegroundColor Cyan




