# API Keys Configuration Guide
**Project**: "The Body Broker" Gaming Core  
**Last Updated**: January 29, 2025

---

## CONFIGURED API PROVIDERS

### ✅ Azure AI (Deployed Models)
- **Endpoint**: `https://ai-gaming-core.openai.azure.com`
- **Models Deployed**:
  - `MAI-DS-R1` - Microsoft AI model
  - `DeepSeek-V3.1` - DeepSeek reasoning model
  - `sora` - Video generation model
- **API Key**: Configured via Azure Portal
- **Use Case**: Orchestration layer, video generation

### ✅ OpenAI Direct
- **API Key**: Direct OpenAI key (NOT OpenRouter)
- **Base URL**: `https://api.openai.com/v1`
- **Available Models**: GPT-5, GPT-4, GPT-3.5, etc.
- **Use Case**: Primary orchestration (Layer 4), Tier 3 NPCs
- **Priority**: HIGH (best models available)

### ✅ DeepSeek Direct
- **API Key**: Direct DeepSeek key
- **Base URL**: `https://api.deepseek.com/v1`
- **Available Models**: DeepSeek V3.1, DeepSeek R1, DeepSeek Coder
- **Use Case**: Reasoning tasks, coding, specialized inference
- **Priority**: HIGH (excellent for reasoning)

### ✅ Anthropic (Claude)
- **API Key**: Direct Anthropic key
- **Available Models**: Claude Sonnet 4.5, Claude Opus 4.1
- **Use Case**: Primary orchestration (Layer 4), complex reasoning
- **Priority**: HIGH (excellent for complex tasks)

### ✅ Google Gemini
- **API Key**: Direct Gemini key
- **Available Models**: Gemini 2.5 Pro, Gemini 2.5 Flash
- **Use Case**: Multi-modal tasks, reasoning, orchestration
- **Priority**: MEDIUM-HIGH

### ✅ OpenRouter AI (Fallback/Alternative)
- **API Key**: OpenRouter key
- **Base URL**: `https://openrouter.ai/api/v1`
- **Available Models**: Access to multiple providers
- **Use Case**: Fallback, alternative models, cost optimization
- **Priority**: MEDIUM (fallback option)

---

## MODEL SELECTION STRATEGY

### Layer 4: Orchestration (Cloud LLMs)

**Primary Orchestration** (Story Direction, Battle Coordination):
1. **Claude Sonnet 4.5** (via Anthropic) - Best for complex orchestration
2. **GPT-5/GPT-4** (via OpenAI Direct) - Excellent for general orchestration
3. **DeepSeek V3.1** (via DeepSeek Direct or Azure) - Great for reasoning
4. **Gemini 2.5 Pro** (via Gemini) - Good for multi-modal coordination

**Secondary/Validation**:
- GPT-3.5 Turbo (via OpenAI Direct) - Cost-effective validation
- OpenRouter models - Fallback options

### Layer 3: NPC Dialogue

**Tier 3 NPCs** (Major Characters):
- GPT-4/GPT-5 (via OpenAI Direct)
- Claude Sonnet 4.5 (via Anthropic)

**Tier 2 NPCs** (Elite NPCs):
- Local Ollama models (Llama-3.1-8B, Mistral-7B)
- DeepSeek V3.1 (via API if needed)

**Tier 1 NPCs** (Generic):
- Local Ollama models (Phi-3-mini, Qwen-3B)

### Specialized Tasks

**Reasoning/Complex Logic**:
- DeepSeek V3.1 (Azure or Direct API)
- Claude Opus 4.1 (via Anthropic)

**Video Generation**:
- Sora (via Azure)

---

## ENVIRONMENT VARIABLES

### Required Variables

```bash
# Azure AI
AZURE_AI_ENDPOINT=https://ai-gaming-core.openai.azure.com
AZURE_AI_API_KEY=your-azure-key
AZURE_DEPLOYMENT_MAI_DS_R1=MAI-DS-R1
AZURE_DEPLOYMENT_DEEPSEEK=DeepSeek-V3.1
AZURE_DEPLOYMENT_SORA=sora

# OpenAI Direct
OPENAI_API_KEY=sk-proj-your-key
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek Direct
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key

# Gemini
GEMINI_API_KEY=AIzaSy-your-key

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

---

## QUICK SETUP

### Option 1: Interactive Setup Script
```powershell
.\scripts\configure-api-keys.ps1
```

### Option 2: Manual .env File
Copy `.env.example` to `.env` and fill in your keys.

---

## COST OPTIMIZATION

### Cost Tiers (Approximate)

| Provider | Model | Cost/1K Tokens | Priority |
|----------|-------|----------------|----------|
| OpenAI | GPT-5 | $0.01-0.03 | HIGH |
| OpenAI | GPT-4 | $0.01-0.03 | HIGH |
| OpenAI | GPT-3.5 | $0.0005-0.002 | HIGH (validation) |
| Anthropic | Claude 4.5 | $0.003-0.015 | HIGH |
| DeepSeek | V3.1 | $0.0007-0.0014 | HIGH |
| Gemini | 2.5 Pro | $0.0005-0.002 | MEDIUM |
| OpenRouter | Various | Varies | MEDIUM (fallback) |
| Azure | Models | Varies | MEDIUM |

### Optimization Strategy

1. **Use Claude 4.5 or GPT-5** for critical orchestration (20% of tasks)
2. **Use GPT-4o-mini or GPT-3.5** for secondary tasks (70%)
3. **Use DeepSeek V3.1** for reasoning-heavy tasks
4. **Use Local Ollama** for 80% of NPC dialogue
5. **Use OpenRouter** as fallback only

---

## TESTING ALL PROVIDERS

Test scripts are available:
- `scripts/test-azure-ai.ps1` - Azure AI
- `scripts/test-openai-direct.ps1` - OpenAI (to be created)
- `scripts/test-anthropic.ps1` - Claude (to be created)
- `scripts/test-deepseek.ps1` - DeepSeek (to be created)
- `scripts/test-gemini.ps1` - Gemini (to be created)

---

## SECURITY NOTES

⚠️ **IMPORTANT**:
- Never commit `.env` file to git
- `.env` is already in `.gitignore`
- Rotate keys if exposed
- Use environment variables in production
- Never log API keys

---

## UPDATED ARCHITECTURE

With direct access to best models, your architecture is **significantly stronger**:

✅ **Primary Orchestration**: Claude 4.5, GPT-5 (best models)  
✅ **Reasoning Tasks**: DeepSeek V3.1 (specialized)  
✅ **NPC Dialogue**: Local Ollama (cost-effective)  
✅ **Video Generation**: Sora (cutting-edge)  
✅ **Fallback**: OpenRouter (flexibility)

This setup gives you **the best of all worlds** - premium models for orchestration, cost-effective local models for NPCs, and specialized models for reasoning/video.

---

**Next Steps**: Run `.\scripts\configure-api-keys.ps1` to set up your environment variables.

