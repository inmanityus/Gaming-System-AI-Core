# Configure API Keys for Gaming System AI Core
# This script sets up environment variables for all API providers

Write-Host "=== Configuring API Keys ===" -ForegroundColor Cyan

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "[WARNING] .env file already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/N)"
    if ($overwrite -ne "y") {
        Write-Host "Cancelled" -ForegroundColor Red
        exit
    }
}

# Azure AI Configuration
Write-Host "`nSetting up Azure AI..." -ForegroundColor Green
$AZURE_AI_ENDPOINT = "https://ai-gaming-core.openai.azure.com"
$AZURE_AI_API_KEY = Read-Host "Enter Azure AI API Key (or press Enter to skip)"
$env:AZURE_AI_ENDPOINT = $AZURE_AI_ENDPOINT
if ($AZURE_AI_API_KEY) {
    $env:AZURE_AI_API_KEY = $AZURE_AI_API_KEY
    Write-Host "[OK] Azure AI configured" -ForegroundColor Green
}

# OpenAI Direct
Write-Host "`nSetting up OpenAI Direct..." -ForegroundColor Green
$OPENAI_API_KEY = Read-Host "Enter OpenAI API Key (or press Enter to skip)"
if ($OPENAI_API_KEY) {
    $env:OPENAI_API_KEY = $OPENAI_API_KEY
    $env:OPENAI_BASE_URL = "https://api.openai.com/v1"
    Write-Host "[OK] OpenAI Direct configured" -ForegroundColor Green
}

# DeepSeek Direct
Write-Host "`nSetting up DeepSeek Direct..." -ForegroundColor Green
$DEEPSEEK_API_KEY = Read-Host "Enter DeepSeek API Key (or press Enter to skip)"
if ($DEEPSEEK_API_KEY) {
    $env:DEEPSEEK_API_KEY = $DEEPSEEK_API_KEY
    $env:DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    Write-Host "[OK] DeepSeek Direct configured" -ForegroundColor Green
}

# Anthropic/Claude
Write-Host "`nSetting up Anthropic (Claude)..." -ForegroundColor Green
$ANTHROPIC_API_KEY = Read-Host "Enter Anthropic API Key (or press Enter to skip)"
if ($ANTHROPIC_API_KEY) {
    $env:ANTHROPIC_API_KEY = $ANTHROPIC_API_KEY
    Write-Host "[OK] Anthropic configured" -ForegroundColor Green
}

# Gemini
Write-Host "`nSetting up Google Gemini..." -ForegroundColor Green
$GEMINI_API_KEY = Read-Host "Enter Gemini API Key (or press Enter to skip)"
if ($GEMINI_API_KEY) {
    $env:GEMINI_API_KEY = $GEMINI_API_KEY
    Write-Host "[OK] Gemini configured" -ForegroundColor Green
}

# OpenRouter
Write-Host "`nSetting up OpenRouter AI..." -ForegroundColor Green
$OPENROUTER_API_KEY = Read-Host "Enter OpenRouter API Key (or press Enter to skip)"
if ($OPENROUTER_API_KEY) {
    $env:OPENROUTER_API_KEY = $OPENROUTER_API_KEY
    $env:OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    Write-Host "[OK] OpenRouter configured" -ForegroundColor Green
}

# Generate .env file
Write-Host "`nGenerating .env file..." -ForegroundColor Cyan
@"
# Azure AI Configuration
AZURE_AI_ENDPOINT=$AZURE_AI_ENDPOINT
AZURE_AI_API_KEY=$AZURE_AI_API_KEY
AZURE_DEPLOYMENT_MAI_DS_R1=MAI-DS-R1
AZURE_DEPLOYMENT_DEEPSEEK=DeepSeek-V3.1
AZURE_DEPLOYMENT_SORA=sora

# OpenAI Direct
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek Direct
DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Anthropic/Claude
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Google Gemini
GEMINI_API_KEY=$GEMINI_API_KEY

# OpenRouter AI
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
"@ | Out-File -FilePath ".env" -Encoding utf8

Write-Host "`n✅ Configuration complete!" -ForegroundColor Green
Write-Host "Environment variables set for this session" -ForegroundColor Gray
Write-Host ".env file created (add to .gitignore)" -ForegroundColor Gray

