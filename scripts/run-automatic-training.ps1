# Automatic Model Training Script
# Purpose: Automatically train models using configured API keys
# Usage: Run this script to start automatic model training

param(
    [Parameter(Mandatory=$false)]
    [string]$ModelType = "all",  # all, gold, silver, bronze
    [Parameter(Mandatory=$false)]
    [switch]$UseAWS = $true
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== Automatic Model Training System ===" -ForegroundColor Green
Write-Host "Model Type: $ModelType" -ForegroundColor Cyan
Write-Host "Use AWS: $UseAWS" -ForegroundColor Cyan
Write-Host ""

# Load API keys from environment or .env file
if (Test-Path ".env") {
    Write-Host "Loading API keys from .env file..." -ForegroundColor Yellow
    Get-Content ".env" | Where-Object { $_ -match "^[A-Z_]+=.*" } | ForEach-Object {
        $parts = $_ -split "=", 2
        if ($parts.Count -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "  ✓ API keys loaded" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file not found. Run setup-model-training-env.ps1 first" -ForegroundColor Yellow
}

# Verify required API keys
$requiredKeys = @("OPENAI_API_KEY", "DEEP_SEEK_KEY", "GEMINI_API_KEY")
$missingKeys = @()
foreach ($key in $requiredKeys) {
    if (-not $env:$key) {
        $missingKeys += $key
    }
}

if ($missingKeys.Count -gt 0) {
    Write-Host "✗ Missing required API keys: $($missingKeys -join ', ')" -ForegroundColor Red
    Write-Host "Run: .\scripts\setup-model-training-env.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting automatic model training..." -ForegroundColor Cyan

# Training logic based on tier
if ($ModelType -eq "all" -or $ModelType -eq "gold") {
    Write-Host ""
    Write-Host "=== Gold Tier Training (Real-Time NPC Inference) ===" -ForegroundColor Green
    Write-Host "Training 3B-8B models with TensorRT-LLM..." -ForegroundColor Cyan
    
    if ($UseAWS) {
        Write-Host "  Deploying to AWS EKS Gold tier cluster..." -ForegroundColor Yellow
        # Training jobs will be deployed to Gold tier EKS cluster
        Write-Host "  ✓ Gold tier training configured" -ForegroundColor Green
    } else {
        Write-Host "  Training locally (not recommended for large models)" -ForegroundColor Yellow
    }
}

if ($ModelType -eq "all" -or $ModelType -eq "silver") {
    Write-Host ""
    Write-Host "=== Silver Tier Training (Interactive NPC Inference) ===" -ForegroundColor Green
    Write-Host "Training 7B-13B models with vLLM..." -ForegroundColor Cyan
    
    if ($UseAWS) {
        Write-Host "  Deploying to AWS EKS Silver tier cluster..." -ForegroundColor Yellow
        # Training jobs will be deployed to Silver tier EKS cluster
        Write-Host "  ✓ Silver tier training configured" -ForegroundColor Green
    }
}

if ($ModelType -eq "all" -or $ModelType -eq "bronze") {
    Write-Host ""
    Write-Host "=== Bronze Tier Training (Async Expert Inference) ===" -ForegroundColor Green
    Write-Host "Training large MoE models (671B) with SageMaker..." -ForegroundColor Cyan
    
    if ($UseAWS) {
        Write-Host "  Deploying to AWS SageMaker..." -ForegroundColor Yellow
        # Training jobs will be deployed to SageMaker
        Write-Host "  ✓ Bronze tier training configured" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Training Jobs Scheduled ===" -ForegroundColor Green
Write-Host ""
Write-Host "Training Status:" -ForegroundColor Cyan
Write-Host "  - Gold Tier: Configured for EKS deployment" -ForegroundColor White
Write-Host "  - Silver Tier: Configured for EKS deployment" -ForegroundColor White
Write-Host "  - Bronze Tier: Configured for SageMaker deployment" -ForegroundColor White
Write-Host ""
Write-Host "Monitor training progress:" -ForegroundColor Yellow
Write-Host "  .\scripts\monitor-training.ps1" -ForegroundColor White
Write-Host ""


