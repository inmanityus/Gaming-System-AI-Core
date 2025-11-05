# AWS Deployment Script for Language System
# Deploys language system services to AWS

param(
    [string]$Region = "us-east-1",
    [string]$Environment = "production",
    [switch]$SkipTests = $false
)

Write-Host "=== AWS Language System Deployment ===" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Step 1: Run tests locally
if (-not $SkipTests) {
    Write-Host "`n[1/5] Running tests..." -ForegroundColor Green
    python -m pytest tests/language_system/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tests failed! Aborting deployment." -ForegroundColor Red
        exit 1
    }
    Write-Host "All tests passed!" -ForegroundColor Green
}

# Step 2: Build Docker image
Write-Host "`n[2/5] Building Docker image..." -ForegroundColor Green
$imageName = "language-system:$Environment"
docker build -t $imageName -f infrastructure/docker/language-system.Dockerfile .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

# Step 3: Tag and push to ECR
Write-Host "`n[3/5] Pushing to ECR..." -ForegroundColor Green
$ecrRepo = "language-system"
$awsAccountId = aws sts get-caller-identity --query Account --output text
$ecrUri = "${awsAccountId}.dkr.ecr.${Region}.amazonaws.com/${ecrRepo}:${Environment}"

docker tag $imageName $ecrUri
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $ecrUri
docker push $ecrUri

# Step 4: Deploy to ECS/Fargate
Write-Host "`n[4/5] Deploying to ECS..." -ForegroundColor Green
aws ecs update-service --cluster language-system-cluster --service language-system-service --force-new-deployment --region $Region

# Step 5: Wait for deployment and verify
Write-Host "`n[5/5] Waiting for deployment..." -ForegroundColor Green
Start-Sleep -Seconds 30

# Test endpoints
$baseUrl = "https://language-system.${Region}.amazonaws.com"
Write-Host "Testing endpoints..." -ForegroundColor Yellow

$healthCheck = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET
if ($healthCheck.StatusCode -eq 200) {
    Write-Host "Health check passed!" -ForegroundColor Green
} else {
    Write-Host "Health check failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Service URL: $baseUrl" -ForegroundColor Green

