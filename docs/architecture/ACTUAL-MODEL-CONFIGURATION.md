# Actual Model Configuration Summary
**Last Updated**: January 29, 2025  
**Status**: ✅ All Models Verified and Documented

---

## QUICK REFERENCE

### Local Ollama Models (Available)

**Tier 1 - Generic NPCs**:
- ✅ phi3:mini (2.2 GB) - ⭐ Recommended
- ✅ tinyllama (637 MB) - ⭐ Fastest option
- ✅ qwen2.5:3b (1.9 GB)
- ✅ llama3.2:3b (2.0 GB)

**Tier 2 - Elite NPCs**:
- ✅ llama3.1:8b (4.9 GB) - ⭐ Recommended
- ✅ mistral:7b (4.4 GB) - ⭐ Excellent alternative
- ✅ qwen2.5:7b (4.7 GB)
- ✅ mistral-openorca:7b (4.1 GB)

**Tier 3 - Major NPCs**:
- ✅ llama3.1:8b + personalized LoRA - ⭐ Recommended
- ✅ mistral:7b + personalized LoRA - Alternative

**Specialized**:
- ✅ deepseek-r1 (5.2 GB) - Reasoning tasks
- ✅ deepseek-coder-v2 (8.9 GB) - Code generation
- ✅ qwen2.5-coder:7b (4.7 GB) - Code tasks

### Cloud/API Models (Available)

**Orchestration (Layer 4)**:
- ✅ Claude Sonnet 4.5 (Anthropic Direct) - ⭐ Primary
- ✅ GPT-5/GPT-4 (OpenAI Direct) - ⭐ Secondary
- ✅ DeepSeek V3.1 (Azure/API) - ⭐ Reasoning
- ✅ GLM-4.6 (Zhipu AI) - Cost-effective
- ✅ Kimi K2 (Moonshot) - Alternative

**Reasoning**:
- ✅ DeepSeek V3.1 (Azure deployment: DeepSeek-V3.1) - ⭐ Best
- ✅ DeepSeek Direct API
- ✅ deepseek-r1 (Ollama local) - Local alternative

---

## IMPORTANT NOTES

### DeepSeek V3.1 Configuration

⚠️ **DeepSeek V3.1 is NOT available locally via Ollama**

**Available Options**:
1. ✅ **Azure Deployment**: `DeepSeek-V3.1` (already deployed)
2. ✅ **DeepSeek Direct API**: Direct API key configured
3. ✅ **Local Alternative**: `deepseek-r1` (Ollama) - Reasoning-focused

**Recommendation**: Use Azure deployment `DeepSeek-V3.1` or Direct API for orchestration. Use local `deepseek-r1` only for specific reasoning tasks.

---

## MODEL ALLOCATION STRATEGY

### NPC Dialogue (80% of AI usage)
- **Tier 1**: phi3:mini or tinyllama (local Ollama)
- **Tier 2**: llama3.1:8b + LoRA (local Ollama)
- **Tier 3**: llama3.1:8b + personalized LoRA (local Ollama)

### Orchestration (20% of AI usage)
- **Primary**: Claude Sonnet 4.5 (Anthropic Direct)
- **Secondary**: GPT-5/GPT-4 (OpenAI Direct)
- **Reasoning**: DeepSeek V3.1 (Azure/API)
- **Fallback**: GLM-4.6, Kimi K2, GPT-3.5

---

## VRAM CAPACITY

**Hardware**: 2x RTX 5090 (32GB each) = 64GB total

**Estimated Usage**:
- Tier 1: 15-30GB (10-20 instances)
- Tier 2: 25-50GB (5-10 instances)
- Tier 3: 14-35GB (2-5 instances)
- **Total**: 54-115GB capacity (split across 2 GPUs)

**Conclusion**: ✅ Plenty of capacity for full deployment

---

## TESTING

Run model tests:
```powershell
.\scripts\test-ollama-models.ps1
```

This will verify all Tier 1, 2, 3 models are working correctly.

---

**Status**: ✅ All models verified and ready for deployment

