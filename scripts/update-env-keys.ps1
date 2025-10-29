# Update .env with provided API keys
# Run this to configure your environment with the actual keys

Write-Host "=== Updating .env File ===" -ForegroundColor Cyan

# Your actual keys (from your message)
$envVars = @{
    # Azure AI
    AZURE_AI_ENDPOINT = "https://ai-gaming-core.openai.azure.com"
    AZURE_AI_API_KEY = "7j51TXZmlmBd4vVFVPwLXIMbqffLcVyfnisUCuQwQ2zh5gpaLgBMJQQJ99BJAC4f1cMXJ3w3AAAAACOGjiNj"
    AZURE_DEPLOYMENT_MAI_DS_R1 = "MAI-DS-R1"
    AZURE_DEPLOYMENT_DEEPSEEK = "DeepSeek-V3.1"
    AZURE_DEPLOYMENT_SORA = "sora"
    
    # OpenAI Direct
    OPENAI_API_KEY = "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"
    OPENAI_BASE_URL = "https://api.openai.com/v1"
    
    # DeepSeek Direct
    DEEPSEEK_API_KEY = "sk-8f06a7580b7a4738b36652b9a16a056a"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    
    # Anthropic
    ANTHROPIC_API_KEY = "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"
    
    # Gemini
    GEMINI_API_KEY = "AIzaSyCzl8VuqkPPD5J3LLYmwm2Mrq1I3kw_YGA"
    
    # OpenRouter
    OPENROUTER_API_KEY = "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"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Hugging Face
    HUGGINGFACE_API_KEY = "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"
    
    # Moonshot AI (Kimi)
    MOONSHOT_API_KEY = "sk-riQgHmK41YMUoq6Csa41S2BwvQi0FNBvVkgw3Rb3C1YhWgMI"
    MOONSHOT_ORG_ID = "org-77be2905893d44cb98f0fd55a4c1c42a"
    MOONSHOT_ORG_FOUNDER_ID = "d419k09toomfonttopfg"
    MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"
    
    # GLM (Zhipu AI)
    GLM_API_KEY = "3a1fe2b198eb41ce99eef8cbfde2c6c9.Vqd5EsdtFKBLi3WB"
    GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
}

# Backup existing .env if it exists
if (Test-Path ".env") {
    Copy-Item ".env" ".env.backup"
    Write-Host "[OK] Backed up existing .env" -ForegroundColor Green
}

# Create .env file
$envContent = @"
# Azure AI Configuration
AZURE_AI_ENDPOINT=$($envVars.AZURE_AI_ENDPOINT)
AZURE_AI_API_KEY=$($envVars.AZURE_AI_API_KEY)
AZURE_DEPLOYMENT_MAI_DS_R1=$($envVars.AZURE_DEPLOYMENT_MAI_DS_R1)
AZURE_DEPLOYMENT_DEEPSEEK=$($envVars.AZURE_DEPLOYMENT_DEEPSEEK)
AZURE_DEPLOYMENT_SORA=$($envVars.AZURE_DEPLOYMENT_SORA)

# OpenAI Direct (NOT OpenRouter)
OPENAI_API_KEY=$($envVars.OPENAI_API_KEY)
OPENAI_BASE_URL=$($envVars.OPENAI_BASE_URL)

# DeepSeek Direct
DEEPSEEK_API_KEY=$($envVars.DEEPSEEK_API_KEY)
DEEPSEEK_BASE_URL=$($envVars.DEEPSEEK_BASE_URL)

# Anthropic/Claude
ANTHROPIC_API_KEY=$($envVars.ANTHROPIC_API_KEY)

# Google Gemini
GEMINI_API_KEY=$($envVars.GEMINI_API_KEY)

# OpenRouter AI (Fallback/Alternative)
OPENROUTER_API_KEY=$($envVars.OPENROUTER_API_KEY)
OPENROUTER_BASE_URL=$($envVars.OPENROUTER_BASE_URL)

# Hugging Face
HUGGINGFACE_API_KEY=$($envVars.HUGGINGFACE_API_KEY)

# Moonshot AI (Kimi)
MOONSHOT_API_KEY=$($envVars.MOONSHOT_API_KEY)
MOONSHOT_ORG_ID=$($envVars.MOONSHOT_ORG_ID)
MOONSHOT_ORG_FOUNDER_ID=$($envVars.MOONSHOT_ORG_FOUNDER_ID)
MOONSHOT_BASE_URL=$($envVars.MOONSHOT_BASE_URL)

# GLM (Zhipu AI)
GLM_API_KEY=$($envVars.GLM_API_KEY)
GLM_BASE_URL=$($envVars.GLM_BASE_URL)
"@

$envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline

Write-Host "`n✅ .env file updated with all API keys!" -ForegroundColor Green
Write-Host "`n📋 Configured Providers:" -ForegroundColor Cyan
Write-Host "  ✅ Azure AI (MAI-DS-R1, DeepSeek-V3.1, Sora)" -ForegroundColor Green
Write-Host "  ✅ OpenAI Direct" -ForegroundColor Green
Write-Host "  ✅ DeepSeek Direct" -ForegroundColor Green
Write-Host "  ✅ Anthropic (Claude)" -ForegroundColor Green
Write-Host "  ✅ Google Gemini" -ForegroundColor Green
Write-Host "  ✅ OpenRouter AI" -ForegroundColor Green

Write-Host "`n🧪 Test all providers:" -ForegroundColor Cyan
Write-Host "  .\scripts\test-all-providers.ps1" -ForegroundColor Gray

Write-Host "`n⚠️  Security Note: .env is in .gitignore and will NOT be committed" -ForegroundColor Yellow

