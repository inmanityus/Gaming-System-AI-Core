# Gemini Model Integration for Cursor AI Sessions

## 🎯 Overview

This document explains how to access and use Google's Gemini models as an additional AI option alongside Cursor's native models and OpenRouter's models. Gemini provides powerful multimodal capabilities and is available through multiple access methods.

---

## 🌐 Available Model Sources

### **1. Cursor Native Models (Built-in)**
**Access:** Direct through Cursor's model selector  
**Models:** Claude, GPT-4, etc.  
**Configuration:** Cursor Settings → Models  
**Status:** ✅ Always available

### **2. OpenRouter AI Models (via MCP)**
**Access:** Via OpenRouter AI MCP server  
**Models:** Claude, GPT, Gemini, Llama, and 100+ others  
**API:** `mcp_openrouterai_chat_completion` tool  
**Configuration:** MCP server settings  
**Status:** ✅ Active in current setup

### **3. Gemini Models (Multiple Access Methods)**

#### **Option A: Gemini via OpenRouter MCP** ⭐ **RECOMMENDED**
**Access:** Via OpenRouter AI MCP server  
**API Tool:** `mcp_openrouterai_chat_completion`  
**Models Available:**
- `google/gemini-2.0-flash-exp` - Latest experimental
- `google/gemini-1.5-pro` - High capability
- `google/gemini-1.5-flash` - Fast responses
- `google/gemini-pro-vision` - Multimodal
- `google/gemini-ultra` - Highest tier

**Advantages:**
- ✅ Already configured (OpenRouter MCP active)
- ✅ No additional API key needed
- ✅ Same interface as other models
- ✅ Billing through OpenRouter

**Usage Example:**
```python
# Using OpenRouter MCP tool for Gemini
mcp_openrouterai_chat_completion(
    model="google/gemini-2.0-flash-exp",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ],
    temperature=0.7,
    max_tokens=1000
)
```

#### **Option B: Direct Gemini API**
**Access:** Via Google AI API  
**API Key:** Requires `GEMINI_API_KEY` environment variable  
**Configuration:** Cursor environment variables  
**Status:** ⚠️ Causes Cursor integration issues (not recommended)

**Why Not Recommended:**
- Gemini API key in Cursor's environment variables causes conflicts
- Integration breaks when added directly
- Better to use OpenRouter as intermediary

---

## 🔧 Configuration Methods

### **Method 1: Using Gemini via OpenRouter (Current Setup)**

**Current Status:** ✅ Already Configured

Your OpenRouter MCP server is active and includes access to all Gemini models:

```json
{
  "MCP_SERVERS": {
    "openrouterai": {
      "active": true,
      "models_available": [
        "google/gemini-2.0-flash-exp",
        "google/gemini-1.5-pro", 
        "google/gemini-1.5-flash",
        "google/gemini-pro-vision"
      ]
    }
  }
}
```

**How to Use:**
1. Models are accessible via `mcp_openrouterai_chat_completion` tool
2. Search models: `mcp_openrouterai_search_models(provider="google")`
3. Get model info: `mcp_openrouterai_get_model_info(model="google/gemini-1.5-pro")`
4. Chat completion: `mcp_openrouterai_chat_completion(model="google/gemini-1.5-pro", messages=[...])`

**Advantages:**
- No environment variable conflicts
- Unified API for all models
- Automatic key management
- Works seamlessly with Cursor

### **Method 2: Direct API Integration (Alternative)**

If you prefer direct integration despite the issues:

**Setup Steps:**
1. **Get Gemini API Key** (from Google AI Studio)
2. **Add to Environment Variables** (⚠️ May cause issues)
3. **Access via Python Script** (recommended workaround)

**Workaround Implementation:**
```powershell
# Create a wrapper script that uses Gemini API directly
# This avoids Cursor environment variable conflicts

# File: scripts/use-gemini.ps1
$apiKey = "YOUR_GEMINI_API_KEY"
$pythonCode = @"
import google.generativeai as genai
import sys

genai.configure(api_key='$apiKey')
model = genai.GenerativeModel('gemini-pro')

response = model.generate_content(sys.argv[1])
print(response.text)
"@

$pythonCode | python -
```

**Why This Works:**
- Bypasses Cursor's environment variable system
- Uses Python library directly
- No Cursor integration conflicts

---

## 📋 Model Selection Guidelines

### **When to Use Cursor Native Models**
- ✅ Fast responses needed
- ✅ Simple coding tasks
- ✅ Quick debugging
- ✅ Real-time assistance

**Models:** Claude Sonnet, GPT-4, GPT-3.5

### **When to Use OpenRouter Models (including Gemini)**
- ✅ Research tasks
- ✅ Complex problem-solving
- ✅ Multimodal tasks (images, video)
- ✅ Specific model capabilities needed
- ✅ Cost optimization for specific tasks

**Example: Use Gemini for:**
- Multimodal analysis (code + images)
- Creative writing
- Mathematical reasoning
- Code generation with explanations

### **When to Use Gemini Specifically**
- ✅ You need multimodal capabilities (code + images + video)
- ✅ You need creative/social reasoning
- ✅ You want different perspective on problem
- ✅ Cost-effective option for specific tasks

---

## 🔄 Integration with Startup Script

### **Automatic Model Detection**

The startup script now includes Gemini awareness:

```powershell
# Add to startup.ps1
Write-Host "Loading Model Options..." -ForegroundColor Green

# Cursor Native Models (always available)
Write-Host "✓ Cursor Native Models: Available" -ForegroundColor Green
Write-Host "  → Claude Sonnet 4.5, GPT-4, GPT-3.5, etc." -ForegroundColor Gray

# OpenRouter Models (via MCP)
Write-Host "✓ OpenRouter AI Models: Available via MCP" -ForegroundColor Green
Write-Host "  → 100+ models including Gemini variants" -ForegroundColor Gray
Write-Host "  → Use: mcp_openrouterai_chat_completion" -ForegroundColor Gray

# Gemini-specific info
Write-Host "✓ Gemini Models Access:" -ForegroundColor Cyan
Write-Host "  → google/gemini-2.0-flash-exp (experimental)" -ForegroundColor Gray
Write-Host "  → google/gemini-1.5-pro (high capability)" -ForegroundColor Gray
Write-Host "  → google/gemini-1.5-flash (fast)" -ForegroundColor Gray
Write-Host "  → google/gemini-pro-vision (multimodal)" -ForegroundColor Gray
Write-Host "  → Access via OpenRouter MCP" -ForegroundColor Gray
```

### **Model Selection Function**

```powershell
# Function to list all available models
function Get-AvailableModels {
    Write-Host ""
    Write-Host "🎯 AVAILABLE MODEL OPTIONS:" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "1️⃣ CURSOR NATIVE MODELS (Built-in):" -ForegroundColor Yellow
    Write-Host "  • Claude Sonnet 4.5" -ForegroundColor Green
    Write-Host "  • GPT-4" -ForegroundColor Green
    Write-Host "  • GPT-3.5" -ForegroundColor Green
    Write-Host "  • Access: Direct through Cursor" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "2️⃣ OPENROUTER MODELS (via MCP):" -ForegroundColor Yellow
    Write-Host "  • google/gemini-2.0-flash-exp" -ForegroundColor Green
    Write-Host "  • google/gemini-1.5-pro" -ForegroundColor Green
    Write-Host "  • google/gemini-1.5-flash" -ForegroundColor Green
    Write-Host "  • anthropic/claude-3.5-sonnet" -ForegroundColor Green
    Write-Host "  • openai/gpt-4" -ForegroundColor Green
    Write-Host "  • openai/gpt-4-turbo" -ForegroundColor Green
    Write-Host "  • meta-llama/llama-3-70b" -ForegroundColor Green
    Write-Host "  • And 100+ more..." -ForegroundColor Gray
    Write-Host "  • Access: mcp_openrouterai_chat_completion" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "3️⃣ RECOMMENDED GEMINI OPTIONS:" -ForegroundColor Yellow
    Write-Host "  • Best for coding: google/gemini-1.5-pro" -ForegroundColor Cyan
    Write-Host "  • Fast responses: google/gemini-1.5-flash" -ForegroundColor Cyan
    Write-Host "  • Latest features: google/gemini-2.0-flash-exp" -ForegroundColor Cyan
    Write-Host "  • With images: google/gemini-pro-vision" -ForegroundColor Cyan
}
```

---

## 🚀 Practical Usage Examples

### **Example 1: Using Gemini for Code Generation**

```python
# Request Gemini to generate code via OpenRouter
result = mcp_openrouterai_chat_completion(
    model="google/gemini-1.5-pro",
    messages=[
        {
            "role": "user", 
            "content": "Write a Python function to calculate fibonacci numbers with memoization"
        }
    ],
    temperature=0.3,
    max_tokens=500
)

print(result)
```

### **Example 2: Search for Available Gemini Models**

```python
# Search for Google models
models = mcp_openrouterai_search_models(
    provider="google",
    limit=10
)

for model in models:
    print(f"Model: {model.name}")
    print(f"Description: {model.description}")
    print(f"Context Length: {model.context_length}")
    print("---")
```

### **Example 3: Get Gemini Model Details**

```python
# Get detailed info about a specific Gemini model
info = mcp_openrouterai_get_model_info(
    model="google/gemini-1.5-pro"
)

print(f"Name: {info.name}")
print(f"Context Length: {info.context_length}")
print(f"Capabilities: {info.capabilities}")
print(f"Pricing: ${info.pricing.prompt} per 1M prompt tokens")
```

### **Example 4: Use Gemini for Research**

```python
# Use Gemini for research tasks
research_result = mcp_openrouterai_chat_completion(
    model="google/gemini-2.0-flash-exp",
    messages=[
        {
            "role": "system",
            "content": "You are a research assistant specializing in AI developments."
        },
        {
            "role": "user",
            "content": "Explain the latest advances in multimodal AI models and their applications."
        }
    ],
    temperature=0.7,
    max_tokens=1500
)
```

---

## 📊 Model Comparison

| Model | Source | Speed | Capability | Cost | Best For |
|-------|--------|-------|------------|------|----------|
| **Claude Sonnet 4.5** | Cursor Native | Fast | Very High | Free | Complex coding |
| **GPT-4** | Cursor Native | Medium | Very High | Free | General tasks |
| **GPT-3.5** | Cursor Native | Very Fast | High | Free | Quick tasks |
| **Gemini 1.5 Pro** | OpenRouter | Medium | Very High | $$ | Research, multimodal |
| **Gemini 1.5 Flash** | OpenRouter | Very Fast | High | $ | Fast responses |
| **Gemini 2.0 Flash** | OpenRouter | Fast | Very High | $$ | Latest features |

---

## 🎯 Best Practices

### **DO:**
- ✅ Use OpenRouter for accessing Gemini models
- ✅ Use Cursor native models for speed
- ✅ Select model based on task requirements
- ✅ Use Gemini for multimodal or creative tasks
- ✅ Search for models before using unknown ones

### **DON'T:**
- ❌ Add Gemini API key to Cursor environment variables
- ❌ Use expensive models for simple tasks
- ❌ Assume all models available without checking
- ❌ Ignore cost implications for high-volume usage

---

## 🔧 Troubleshooting

### **Issue: "Gemini model not found"**
**Solution:** Verify OpenRouter MCP is active and search available models:
```python
mcp_openrouterai_search_models(provider="google")
```

### **Issue: "API key error"**
**Solution:** OpenRouter handles authentication automatically. If errors occur, check MCP server configuration.

### **Issue: "Cursor conflicts with Gemini key"**
**Solution:** Use OpenRouter MCP instead of adding Gemini key to Cursor environment variables.

---

## 📚 Integration with Other Systems

### **Pairwise Comprehensive Testing**
- Use Gemini as Reviewer model for diverse perspectives
- Gemini's strengths in analysis complement other models

### **Autonomous Development Protocol**
- Select Gemini for specific subtasks
- Use for research phase before implementation

### **Complete Everything Protocol**
- Gemini included in hybrid model selection
- Uses different provider than primary model

---

## ✅ Summary

**Bottom Line:**
1. ✅ **OpenRouter MCP** provides access to all Gemini models
2. ✅ No need to add Gemini API key to Cursor (causes conflicts)
3. ✅ Use `mcp_openrouterai_chat_completion` tool to access Gemini
4. ✅ Models available: gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp
5. ✅ Already configured and ready to use

**Quick Start:**
```python
# Use Gemini right now via OpenRouter
mcp_openrouterai_chat_completion(
    model="google/gemini-1.5-pro",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**No Additional Configuration Required!** 🎉

---

## 🔄 Session Awareness

**Every session automatically knows:**
1. ✅ Cursor native models are available (through Cursor settings)
2. ✅ OpenRouter models including Gemini are available (via MCP)
3. ✅ How to access each model
4. ✅ When to use which model
5. ✅ Best practices for model selection

**This information is loaded during startup and available throughout the session.**

---

**Version:** 1.0  
**Last Updated:** 2025-10-26  
**Status:** Active  
**Integration:** Complete
