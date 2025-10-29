# Model Setup Instructions
**Last Updated**: January 29, 2025  
**Purpose**: Step-by-step setup for all required model providers

---

## 1. AZURE AI (Microsoft MAI Models)

### Prerequisites
- Microsoft Azure account
- Azure subscription with billing enabled

### Step-by-Step Setup

**1. Create Azure Account & Subscription**
```
1. Go to: https://azure.microsoft.com/free/
2. Sign up with Microsoft account
3. Verify identity (credit card may be required for verification)
4. Create new subscription (or use existing)
```

**2. Create Azure AI Foundry Resource**
```
1. Go to Azure Portal: https://portal.azure.com
2. Click "Create a resource"
3. Search: "Azure AI Foundry"
4. Click "Create"
5. Fill in:
   - Subscription: [Your subscription]
   - Resource group: [Create new: "ai-gaming-core"]
   - Region: Choose nearest to your servers (e.g., East US, West Europe)
   - Name: "body-broker-ai-foundry"
   - Pricing tier: Standard (check costs)
6. Click "Review + create" → "Create"
7. Wait ~3-5 minutes for deployment
```

**3. Get API Key**
```
1. Go to Azure Portal → Your AI Foundry resource
2. Left sidebar: "Keys and Endpoint"
3. Copy "KEY 1" or "KEY 2" (keep secret!)
4. Copy "ENDPOINT" URL
```

**4. Install Azure CLI (Optional but Recommended)**
```powershell
# Windows (PowerShell as Administrator)
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi
Start-Process msiexec.exe -ArgumentList '/I AzureCLI.msi /quiet' -Wait

# Verify
az --version

# Login
az login

# Set subscription
az account set --subscription "Your Subscription Name or ID"
```

**5. Test Azure AI API**
```powershell
# Using PowerShell
# IMPORTANT: Use the endpoint from Azure Portal's "Keys and Endpoint" section
# Format should be: https://{resource-name}.openai.azure.com (NO trailing slash)
$endpoint = "https://YOUR-ENDPOINT.openai.azure.com"  # NO trailing slash here
$apiKey = "YOUR-KEY"
$deploymentName = "MAI-DS-R1"  # Your deployment name (case-sensitive)

$headers = @{
    "api-key" = $apiKey
    "Content-Type" = "application/json"
}

$body = @{
    messages = @(
        @{
            role = "user"
            content = "Test message"
        }
    )
} | ConvertTo-Json -Depth 10

# Construct URI properly - endpoint has NO trailing slash
$uri = "$endpoint/openai/deployments/$deploymentName/chat/completions?api-version=2024-02-15-preview"

Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
```

**6. Environment Variables**
```powershell
# Add to your .env file or system environment
$env:AZURE_AI_ENDPOINT = "https://YOUR-ENDPOINT.openai.azure.com"
$env:AZURE_AI_API_KEY = "YOUR-KEY"
```

**Note**: MAI-1-preview may require application/whitelist. Check Azure portal for available models in your region.

---

## 2. OLLAMA MODELS (Local)

### Your Current Setup
You already have:
- Qwen3:235B (142GB - very large!)
- Various other models

### Recommended Downloads

**For Tier 1 NPCs (Zombies/Ghouls):**
```powershell
ollama pull phi3:mini
ollama pull tinyllama
ollama pull qwen2.5:3b
```

**For Tier 2 NPCs (Vampires/Werewolves):**
```powershell
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull qwen2.5:7b
```

**For Specialized Tasks:**
```powershell
ollama pull qwen2.5-coder:7b  # Coding/specialized tasks
ollama pull deepseek-r1:distill  # Reasoning
```

### Check Available Models in Ollama Library
```powershell
# Visit: https://ollama.com/library
# Or use Ollama API to search
ollama list  # Shows what you have
```

---

## 3. QWEN (Alibaba) - Direct API

**Option A: Hugging Face (Download)**
```
1. Go to: https://huggingface.co/Qwen
2. Find model (e.g., Qwen/Qwen2.5-7B-Instruct)
3. Sign up account
4. Get access token: Settings → Access Tokens → New token
5. Use with Ollama or download directly
```

**Option B: Alibaba Cloud API**
```
1. Go to: https://www.aliyun.com/product/dashscope
2. Sign up (requires Alibaba Cloud account)
3. Activate DashScope service
4. Get API key from console
5. Use Qwen API endpoint
```

**PowerShell Setup:**
```powershell
$env:DASHSCOPE_API_KEY = "your-api-key"
# API endpoint: https://dashscope.aliyun.com/api/v1/services/ai/generation/text-generation
```

---

## 4. DEEPSEEK (Already in Ollama)

You can pull more DeepSeek models:
```powershell
ollama pull deepseek-r1
ollama pull deepseek-v3:latest
ollama pull deepseek-coder
```

Or use DeepSeek API directly:
```
1. Go to: https://platform.deepseek.com
2. Sign up account
3. Get API key
4. Add to environment
```

---

## 5. KIMI (ByteDance/Moonshot)

**API Access:**
```
1. Go to: https://platform.moonshot.cn
2. Register account
3. Add payment/billing
4. Get API key
5. Models: Kimi K2, Kimi K1.5, etc.
```

**PowerShell:**
```powershell
$env:MOONSHOT_API_KEY = "your-api-key"
# Base URL: https://api.moonshot.cn/v1
```

---

## 6. GLM (Zhipu AI)

**Setup:**
```
1. Go to: https://open.bigmodel.cn
2. Register and verify
3. Get API key
4. Models: GLM-4.5, GLM-4, etc.
```

```powershell
$env:ZHIPU_API_KEY = "your-api-key"
```

---

## 7. SERVER LIMITATIONS CHECK

**Run this to check your server capacity:**
```powershell
# Check GPU memory
nvidia-smi

# Check available disk space
Get-PSDrive C

# Check RAM
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize
```

**If models too large for server:**
- Use AWS SageMaker for training/fine-tuning
- Use smaller quantized models (4-bit, 8-bit)
- Deploy models to AWS (EC2 with GPUs or SageMaker endpoints)

---

## 8. AWS SAGEMAKER SETUP (For Training/Learning)

**Prerequisites:**
- AWS account
- Appropriate permissions

**Step-by-Step:**
```
1. Go to: https://aws.amazon.com
2. Create account (if needed)
3. Go to IAM: https://console.aws.amazon.com/iam
4. Create user with SageMakerFullAccess policy
5. Create access keys (Access Key ID + Secret)
6. Install AWS CLI:
   - Windows: Download MSI from aws.amazon.com/cli
   - Or: winget install Amazon.AWSCLI
7. Configure:
   aws configure
   # Enter Access Key ID
   # Enter Secret Access Key
   # Region: us-east-1 (or your preference)
   # Output format: json
```

**Verify:**
```powershell
aws sts get-caller-identity
aws sagemaker list-models
```

---

## 9. ENVIRONMENT VARIABLES SUMMARY

Add all to your `.env` file or system environment:

```bash
# Azure AI
AZURE_AI_ENDPOINT=https://...
AZURE_AI_API_KEY=...

# OpenAI (for GPT-5)
OPENAI_API_KEY=...

# Anthropic (Claude)
ANTHROPIC_API_KEY=...

# Google (Gemini)
GOOGLE_API_KEY=...

# Qwen/DashScope
DASHSCOPE_API_KEY=...

# Moonshot (Kimi)
MOONSHOT_API_KEY=...

# Zhipu (GLM)
ZHIPU_API_KEY=...

# DeepSeek
DEEPSEEK_API_KEY=...

# AWS (for SageMaker)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

---

## 10. QUICK TEST SCRIPTS

**Test Ollama:**
```powershell
ollama run qwen2.5:7b "Hello, test message"
```

**Test Azure (PowerShell):**
```powershell
$headers = @{"api-key"="$env:AZURE_AI_API_KEY"; "Content-Type"="application/json"}
$body = '{"messages":[{"role":"user","content":"test"}]}' | ConvertTo-Json
Invoke-RestMethod -Uri "$env:AZURE_AI_ENDPOINT/openai/deployments/MAI-1-preview/chat/completions?api-version=2024-02-15-preview" -Method POST -Headers $headers -Body $body
```

---

## NEXT STEPS

1. Set up Azure AI Foundry
2. Download recommended Ollama models
3. Get API keys for Chinese models (Qwen, Kimi, etc.)
4. Configure AWS for SageMaker (training system)
5. Test all connections
6. Document which models work best for your use case

**If server limitations block local models → Use AWS EC2 with GPUs or SageMaker endpoints for inference.**

