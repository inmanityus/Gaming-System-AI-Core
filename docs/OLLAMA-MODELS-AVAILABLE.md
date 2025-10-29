# Available Ollama Models Inventory
**Date**: January 29, 2025  
**Status**: ✅ Verified and Configured

---

## AVAILABLE MODELS ANALYSIS

### ✅ Tier 1 Models (Generic NPCs - Zombies, Ghouls)

**Recommended for Tier 1**:
- ✅ **phi3:mini** (2.2 GB) - ⭐ **BEST CHOICE**
  - Size: Perfect for Tier 1
  - Quality: Excellent for simple dialogue
  - Latency: 50-150ms expected
  
- ✅ **tinyllama** (637 MB) - ⭐ **ULTRA-LIGHT**
  - Size: Smallest option
  - Quality: Good for grunts, taunts
  - Latency: Fastest (30-100ms expected)
  
- ✅ **qwen2.5:3b** (1.9 GB) - ✅ **GOOD**
  - Quality: Better than TinyLlama
  - Latency: 50-120ms expected
  
- ✅ **llama3.2:3b** (2.0 GB) - ✅ **GOOD**
  - Quality: Good instruction following
  - Latency: 50-120ms expected

**Use Case**: Simple reactions, grunts, basic dialogue
**Concurrency**: 10-20 NPCs per GPU
**VRAM Usage**: 1-2 GB per instance

---

### ✅ Tier 2 Models (Elite NPCs - Vampires, Werewolves)

**Recommended for Tier 2** (with LoRA adapters):
- ✅ **llama3.1:8b** (4.9 GB) - ⭐ **BEST CHOICE**
  - Quality: Excellent for Tier 2
  - LoRA Support: Full support
  - Latency: 100-300ms expected
  
- ✅ **mistral:7b** (4.4 GB) - ⭐ **EXCELLENT**
  - Quality: Great instruction following
  - LoRA Support: Full support
  - Latency: 100-250ms expected
  
- ✅ **qwen2.5:7b** (4.7 GB) - ✅ **GOOD**
  - Quality: Good, multilingual
  - LoRA Support: Full support
  - Latency: 100-280ms expected
  
- ✅ **mistral-openorca:7b** (4.1 GB) - ✅ **ALTERNATIVE**
  - Quality: Orca-trained variant
  - Use: Alternative if standard Mistral unavailable

**Use Case**: Threats, negotiations, contextual reactions
**Concurrency**: 5-10 NPCs per GPU
**VRAM Usage**: 4-6 GB per instance (with LoRA)

---

### ✅ Tier 3 Models (Major NPCs - Nemeses, Bosses)

**Base Models** (same as Tier 2, with personalized LoRA):
- ✅ **llama3.1:8b** + Personalized LoRA - ⭐ **PRIMARY**
- ✅ **mistral:7b** + Personalized LoRA - ⭐ **ALTERNATIVE**

**Use Case**: Full conversations, personality depth
**Concurrency**: 2-5 NPCs per GPU
**VRAM Usage**: 6-8 GB per instance (with personalized LoRA)

---

### ⚠️ Specialized Models (Not for Standard NPCs)

- ✅ **deepseek-coder-v2** (8.9 GB)
  - Use: Code generation, specialized tasks
  - NOT for NPC dialogue
  
- ✅ **deepseek-r1** (5.2 GB) - ⚠️ **NOTE: NOT DeepSeek V3**
  - Use: Reasoning tasks, complex logic
  - NOT DeepSeek V3 (user cannot support V3)
  - Still useful for reasoning-heavy NPCs
  
- ✅ **qwen2.5-coder:7b** (4.7 GB)
  - Use: Code generation, specialized tasks
  - NOT for standard NPC dialogue

- ✅ **hir0rameel/qwen-claude:latest** (5.2 GB)
  - Use: Experimental, Claude-like behavior
  - Could be interesting for Tier 2/3 NPCs

---

### ❌ Large Models (Too Big for Production)

- ❌ **gemma3:27b** (17 GB) - Too large for concurrent use
- ❌ **magistral:24b** (14 GB) - Too large for concurrent use
- ❌ **llama2-uncensored:70b** (38 GB) - Far too large
- ❌ **qwen3:235b-a22b** (142 GB) - Massive, impractical

**Recommendation**: Avoid these for production NPC serving

---

### 🤔 Experimental Models

- ✅ **gpt-oss** (13 GB)
  - Use: Experimental, may be useful for Tier 3
  - Test performance before production use

---

## UPDATED MODEL ALLOCATION

### Recommended Configuration

**Tier 1 (Generic NPCs)**:
```yaml
Primary: phi3:mini (2.2 GB)
Fallback: tinyllama (637 MB) - for ultra-fast responses
Alternative: qwen2.5:3b (1.9 GB) - for better quality when needed
```

**Tier 2 (Elite NPCs)**:
```yaml
Primary: llama3.1:8b (4.9 GB) - Best overall
Secondary: mistral:7b (4.4 GB) - Excellent alternative
Fallback: qwen2.5:7b (4.7 GB) - Good quality
```

**Tier 3 (Major NPCs)**:
```yaml
Primary: llama3.1:8b + Personalized LoRA
Alternative: mistral:7b + Personalized LoRA
```

**Specialized Tasks**:
```yaml
Reasoning: deepseek-r1 (5.2 GB) - Complex logic
Coding: deepseek-coder-v2 (8.9 GB) - Code generation
Experimental: gpt-oss (13 GB) - Test for Tier 3 alternative
```

---

## DEEPSEEK NOTE

⚠️ **Important**: You have **deepseek-r1** but **NOT DeepSeek V3.1**

- **Available**: `deepseek-r1` (5.2 GB) - Reasoning model
- **NOT Available**: DeepSeek V3.1 (as specified in some docs)
- **Alternative**: Use DeepSeek V3.1 via Azure deployment or Direct API

**Recommendation**:
- Use `deepseek-r1` locally for reasoning tasks
- Use DeepSeek V3.1 via Azure/API for orchestration when needed
- Update documentation to reflect this

---

## VRAM CAPACITY ANALYSIS

**Your Hardware**: 2x RTX 5090 (32GB each) = 64GB total VRAM

**Potential Load**:
- Tier 1: 10-20 instances × 1.5GB = 15-30GB
- Tier 2: 5-10 instances × 5GB = 25-50GB
- Tier 3: 2-5 instances × 7GB = 14-35GB

**Total Capacity**: With 64GB VRAM, you can handle:
- ✅ Full Tier 1 + Tier 2 deployment on one GPU
- ✅ Tier 3 instances on second GPU
- ✅ Plenty of headroom for LoRA adapters

---

## NEXT STEPS

1. ✅ **Model inventory complete** - All models documented
2. ⏭️ **Test model performance** - Benchmark latency/quality
3. ⏭️ **Create LoRA adapters** - Train per monster type
4. ⏭️ **Update solution docs** - Remove DeepSeek V3.1 references (local)
5. ⏭️ **Configure model routing** - Set up tier-based selection

---

**Status**: ✅ Ready for implementation  
**Note**: DeepSeek V3.1 available via Azure/API, not locally

