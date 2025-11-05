# Setup Automatic Model Training Environment
# Purpose: Configure API keys securely for automatic model training system
# Usage: Run once to set up environment variables for model training

param(
    [Parameter(Mandatory=$false)]
    [switch]$UseAWSSecretsManager = $false
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== Setting Up Automatic Model Training Environment ===" -ForegroundColor Green
Write-Host ""

# API Keys from handoff document
$apiKeys = @{
    "APIFY_TOKEN" = "apify_api_tn8I6MNj5PPCyZc3r8GxiImFRxTs5I0ES4uY"
    "DEEP_SEEK_KEY" = "sk-8f06a7580b7a4738b36652b9a16a056a"
    "EXA_API_KEY" = "a0ca7dd6-a907-43a1-a2a6-4a2ee839e0ba"
    "GEMINI_API_KEY" = "AIzaSyCzl8VuqkPPD5J3LLYmwm2Mrq1I3kw_YGA"
    "GLM_KEY" = "3a1fe2b198eb41ce99eef8cbfde2c6c9.Vqd5EsdtFKBLi3WB"
    "OPEN_AI_KEY" = "sk-proj-_kr_M010dSlMTovqc78xFGlYEKLeObWPGHuDEX5gJUFSBX0TSyLxqKu3tT0VcWFrw9HBLvmO3FT3BlbkFJsLiQ3kfjg_6Mmm-0imx6rRzOCkfOcXJYhrXYPJW9LidAh1NRkEckYhX5EFh1pihHj0h0myftk"
    "OPENAI_API_KEY" = "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"
    "OPENAI_BASE_URL" = "https://openrouter.ai/api/v1"
    "PERPLEXITY_API_KEY" = "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"
    "REF_API_KEY" = "ref-e2c7a605610109f10851"
}

if ($UseAWSSecretsManager) {
    Write-Host "Using AWS Secrets Manager for secure storage..." -ForegroundColor Cyan
    
    # Create secrets in AWS Secrets Manager
    $secretName = "gaming-ai-model-training-api-keys"
    $secretValue = $apiKeys | ConvertTo-Json -Compress
    
    try {
        # Check if secret exists
        $existingSecret = aws secretsmanager describe-secret --secret-id $secretName --region us-east-1 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Updating existing secret: $secretName" -ForegroundColor Yellow
            aws secretsmanager update-secret --secret-id $secretName --secret-string $secretValue --region us-east-1
        } else {
            Write-Host "  Creating new secret: $secretName" -ForegroundColor Yellow
            aws secretsmanager create-secret --name $secretName --secret-string $secretValue --description "API keys for Gaming AI Core automatic model training" --region us-east-1
        }
        Write-Host "  ✓ Secrets stored in AWS Secrets Manager" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed to store secrets in AWS Secrets Manager: $_" -ForegroundColor Red
        Write-Host "  Falling back to local .env file..." -ForegroundColor Yellow
        $UseAWSSecretsManager = $false
    }
}

if (-not $UseAWSSecretsManager) {
    Write-Host "Using local .env file for API keys..." -ForegroundColor Cyan
    
    # Create .env file with API keys
    $envFile = Join-Path $projectRoot ".env"
    $envContent = @"
# Automatic Model Training API Keys
# These keys are used for automatic model training and inference
# DO NOT commit this file to git - it is in .gitignore

"@
    
    foreach ($key in $apiKeys.GetEnumerator()) {
        $envContent += "$($key.Key)=$($key.Value)`n"
    }
    
    $envContent | Set-Content -Path $envFile -Encoding UTF8
    Write-Host "  ✓ API keys saved to .env file" -ForegroundColor Green
    Write-Host "  ⚠ IMPORTANT: .env file is git-ignored but should be backed up securely" -ForegroundColor Yellow
}

# Set environment variables for current session
foreach ($key in $apiKeys.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($key.Key, $key.Value, "User")
}

Write-Host ""
Write-Host "=== Model Training Environment Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "API Keys configured:" -ForegroundColor Cyan
Write-Host "  - Apify Token" -ForegroundColor White
Write-Host "  - DeepSeek Key" -ForegroundColor White
Write-Host "  - Exa API Key" -ForegroundColor White
Write-Host "  - Gemini API Key" -ForegroundColor White
Write-Host "  - GLM Key" -ForegroundColor White
Write-Host "  - OpenAI Keys (OpenRouter)" -ForegroundColor White
Write-Host "  - Perplexity API Key" -ForegroundColor White
Write-Host "  - Ref API Key" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run automatic training: .\scripts\run-automatic-training.ps1" -ForegroundColor White
Write-Host "  2. Monitor training: .\scripts\monitor-training.ps1" -ForegroundColor White
Write-Host ""


