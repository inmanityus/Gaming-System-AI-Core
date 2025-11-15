# Build and Deploy Service to AWS ECS
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$ServicePath,
    
    [Parameter(Mandatory=$true)]
    [string]$DockerfileName,
    
    [Parameter(Mandatory=$false)]
    [string]$ECRRepository = "bodybroker-services/$ServiceName",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$AccountId = "695353648052"
)

Write-Host "Building and deploying $ServiceName..." -ForegroundColor Cyan

# Check if AWS CLI is configured
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Error "AWS CLI not configured. Please run 'aws configure'"
    exit 1
}

# Login to ECR
Write-Host "Logging in to ECR..." -ForegroundColor Yellow
$loginCommand = aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

# Build Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
$imageName = "${ECRRepository}:latest"
$ecrUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$imageName"

# Navigate to service directory
Push-Location $ServicePath
try {
    # Build the image
    docker build -f $DockerfileName -t $imageName .
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }
    
    # Tag for ECR
    docker tag $imageName $ecrUri
    
    # Push to ECR
    Write-Host "Pushing to ECR..." -ForegroundColor Yellow
    docker push $ecrUri
    if ($LASTEXITCODE -ne 0) {
        throw "Docker push failed"
    }
    
    Write-Host "Successfully pushed $ServiceName to ECR" -ForegroundColor Green
    Write-Host "Image URI: $ecrUri" -ForegroundColor Cyan
    
} finally {
    Pop-Location
}

# Check if ECS service exists
Write-Host "Checking ECS service..." -ForegroundColor Yellow
$cluster = "language-system-cluster"  # Using existing cluster
$serviceName = "$ServiceName-service"

$existingService = aws ecs describe-services `
    --cluster $cluster `
    --services $serviceName `
    --region $Region `
    --query "services[?status=='ACTIVE']" `
    --output json | ConvertFrom-Json

if ($existingService.Count -gt 0) {
    Write-Host "Updating existing ECS service..." -ForegroundColor Yellow
    
    # Force new deployment
    aws ecs update-service `
        --cluster $cluster `
        --service $serviceName `
        --force-new-deployment `
        --region $Region
        
    Write-Host "Service update initiated" -ForegroundColor Green
} else {
    Write-Host "Service does not exist. Please create the task definition and service manually." -ForegroundColor Yellow
    Write-Host "Image URI for task definition: $ecrUri" -ForegroundColor Cyan
}

Write-Host "Deployment complete!" -ForegroundColor Green
