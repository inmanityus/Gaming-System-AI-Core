#!/usr/bin/env pwsh
<#
.SYNOPSIS
Build and push Docker image to ECR

.DESCRIPTION
Builds the Gaming System AI Core Docker image and pushes it to AWS ECR
#>

param(
    [string]$Tag = "latest",
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"

# Configuration
$ECR_REPOSITORY = "gaming-system-ai-core"
$AWS_ACCOUNT_ID = "695353648052"
$AWS_REGION = "us-east-1"
$ECR_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

Write-Host "🚀 Building Docker image for Gaming System AI Core" -ForegroundColor Cyan

# Ensure we're in the project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Create .env.example if it doesn't exist
if (-not (Test-Path ".env.example")) {
    Write-Host "📝 Creating .env.example file" -ForegroundColor Yellow
    @"
# Gaming System AI Core Environment Variables
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gaming_system_ai_core
DB_USER=postgres
DB_PASSWORD=changeme
REDIS_HOST=localhost
REDIS_PORT=6379
"@ | Out-File -FilePath ".env.example" -Encoding UTF8
}

# Log in to ECR
Write-Host "🔐 Logging in to ECR..." -ForegroundColor Yellow
$loginCommand = aws ecr get-login-password --region $AWS_REGION
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get ECR login token" -ForegroundColor Red
    exit 1
}

$loginCommand | docker login --username AWS --password-stdin $ECR_URI
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to login to ECR" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Successfully logged in to ECR" -ForegroundColor Green

# Build the Docker image
Write-Host "🏗️  Building Docker image..." -ForegroundColor Yellow
$imageTag = "${ECR_URI}:${Tag}"

docker build -t $imageTag .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker image built successfully: $imageTag" -ForegroundColor Green

# Push to ECR if not skipped
if (-not $SkipPush) {
    Write-Host "📤 Pushing image to ECR..." -ForegroundColor Yellow
    docker push $imageTag
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push image to ECR" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Image pushed successfully to ECR" -ForegroundColor Green
    
    # Tag as latest if not already
    if ($Tag -ne "latest") {
        $latestTag = "${ECR_URI}:latest"
        docker tag $imageTag $latestTag
        docker push $latestTag
        Write-Host "✅ Also tagged and pushed as 'latest'" -ForegroundColor Green
    }
    
    # Output the image URI for use in deployment
    Write-Host "`n📋 Image URI for deployment:" -ForegroundColor Cyan
    Write-Host $imageTag -ForegroundColor White
} else {
    Write-Host "⏭️  Skipping push to ECR (--SkipPush flag set)" -ForegroundColor Yellow
}

Write-Host "`n✨ Docker build process complete!" -ForegroundColor Green
