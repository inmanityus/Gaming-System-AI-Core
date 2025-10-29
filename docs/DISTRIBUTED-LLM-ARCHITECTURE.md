# Distributed LLM Architecture for "The Body Broker"
**Assessment Date**: January 29, 2025  
**Models Used**: Claude Sonnet 4.5, GPT-5-Pro, Gemini 2.5 Pro  
**Architecture**: Local Ollama models (per NPC type) + Cloud LLMs (complex tasks)

---

## 🚨 EXECUTIVE SUMMARY

### **Verdict: ✅ FEASIBLE BUT REQUIRES SOPHISTICATED ARCHITECTURE**

Your distributed LLM approach is **technically superior** for a successful game and addresses the cost/scalability issues from the feasibility assessment. However, it represents a **significant engineering investment** that should be phased carefully.

**Key Finding**: Instead of one model per NPC, use **one base model per GPU with hot-swappable LoRA adapters** per NPC type. This is 10-50x more efficient than loading separate models.

---

## 1. RECOMMENDED ARCHITECTURE

### Core Strategy: LoRA Adapters on Shared Base Model

**❌ Your Original Approach (Not Recommended):**
- One full model per NPC type = 25+ models = ~125GB VRAM (impossible)

**✅ Recommended Approach:**
- **One 7-8B base model per GPU** (7-8GB VRAM)
- **Hot-swappable LoRA adapters** per NPC type (50-200MB each)
- **Total VRAM**: ~10-12GB for base + 20 adapters = manageable

### Model Sizing Strategy (Per GPT-5-Pro)

```yaml
Tier 1 - Generic Monsters (Zombies, Basic Ghouls):
  Base: Phi-3-mini (3.8B) or TinyLlama (1.1B)
  Quantization: Q4_K_M (4-bit)
  VRAM: 1.5-2GB per instance
  Latency: 50-150ms TTFT
  Use Case: Grunts, taunts, simple reactions
  Concurrency: 10-20 NPCs per GPU
  
Tier 2 - Elite Monsters (Vampires, Werewolves):
  Base: Llama-3.1-8B or Mistral-7B
  LoRA: Per-monster-type adapter (50-200MB)
  Quantization: Q4_K_M or Q8_0 (8-bit preferred)
  VRAM: 4-6GB per instance (with LoRA)
  Latency: 100-300ms TTFT
  Use Case: Threats, negotiations, contextual reactions
  Concurrency: 5-10 NPCs per GPU
  
Tier 3 - Major NPCs (Nemeses, Bosses):
  Base: Llama-3.1-8B + Custom LoRA per character
  Quantization: Q5_K_M or Q8_0 (higher quality)
  VRAM: 6-8GB per instance (with personalized LoRA)
  Latency: 200-500ms TTFT
  Use Case: Full conversations, personality depth
  Concurrency: 2-5 NPCs per GPU
  
Tier 4 - Complex Work (Story, Quests):
  Model: Cloud API (GPT-5, Claude 4.5, Gemini 2.5 Pro)
  Cost: $0.01-0.10 per request
  Latency: 1-5 seconds (async acceptable)
  Use Case: Quest generation, story arcs, world events
```

---

## 2. INFRASTRUCTURE REQUIREMENTS

### Server Architecture (Critical - Per Gemini 2.5 Pro)

**🚨 CRITICAL**: **DO NOT run inference on game servers**

**Correct Architecture:**
```
Game Servers (CPU-bound)
    ↓ (Internal network, <1ms latency)
Inference Cluster (GPU-bound)
    ├── Node 1: RTX 4090 (24GB) - Tier 1 NPCs
    ├── Node 2: RTX 4090 (24GB) - Tier 1 NPCs
    ├── Node 3: RTX 6000 Ada (48GB) - Tier 2 NPCs
    └── Node 4: A100 (80GB) - Tier 3 NPCs + Cloud fallback
```

### Hardware Specifications

#### Option A: Single Beefy Server (Small Scale)
```yaml
GPU: 4x RTX 4090 (24GB each) or 1x A100 (80GB)
CPU: 32+ cores (AMD EPYC or Intel Xeon)
RAM: 256GB DDR4
Storage: 2TB NVMe SSD

Capacity:
  Concurrent Players: 200-500
  Active NPCs: 1000+
  Requests/sec: 100-300

Cost:
  Cloud (AWS p4d.24xlarge): ~$32/hour ($23k/month)
  On-prem: $30k-50k upfront + $500/month power
```

#### Option B: Distributed Cluster (Recommended)
```yaml
Lightweight Nodes (Generic NPCs):
  GPU: RTX 4060 Ti (16GB) or RTX 3090 (24GB)
  Models: 4x TinyLlama instances (or 2x Mistral-7B)
  Players: 50-100 per node
  Cost: ~$800-1200/node
  Nodes Needed: 2-4

Mid-tier Nodes (Elite NPCs):
  GPU: RTX 4070 Ti Super (16GB) or RTX 3090 (24GB)
  Models: 2x Mistral-7B + LoRA
  Players: 30-50 per node
  Cost: ~$1200-1500/node
  Nodes Needed: 2-3

Premium Node (Bosses/Major NPCs):
  GPU: RTX 4090 (24GB) or A100 (40GB)
  Models: 3x Llama-8B + LoRA
  Players: 20-30
  Cost: ~$2000-5000/node
  Nodes Needed: 1

Total Cluster: ~$8k-15k upfront + $200-500/month power
Capacity: 200-400 players
```

---

## 3. MODEL SELECTION & QUANTIZATION

### Recommended Models (Per GPT-5-Pro)

**Best Small Models:**
- **3-4B**: Qwen2.5-3B-Instruct, Llama 3.2 3B Instruct, Phi-3-mini 3.8B Instruct
- **7-8B**: Qwen2.5-7B-Instruct, Llama 3.1 8B Instruct, Mistral 7B Instruct v0.3
- **Avoid**: 13-14B models - too slow for 20+ concurrent NPCs

### Quantization Strategy

**8-bit (AWQ) or FP8 (TensorRT-LLM) - RECOMMENDED:**
- Best speed/quality trade-off
- Near-FP16 quality
- Often **faster than 4-bit** due to lower dequant overhead
- Use for Tier 2 & 3 NPCs

**4-bit (AWQ/GPTQ):**
- Use when VRAM is bottleneck (24GB cards with many concurrent sessions)
- Can be slower on small models
- Minor quality loss on nuanced instructions
- Acceptable for Tier 1 NPCs (simple dialogue)

**Key Insight**: Use **GQA/MQA models** (Mistral, Llama 3.x, Qwen2.x) to cut KV memory 3-4x compared to traditional attention.

---

## 4. FINE-TUNING vs LORA vs PROMPT ENGINEERING

### Recommended Approach: **LoRA Adapters** (Per GPT-5-Pro & Claude 4.5)

**Why LoRA over Full Fine-Tuning:**
```yaml
Advantages:
  Storage: Base model (4GB) + LoRA (50-200MB) vs 4GB per NPC
  Training Time: Hours vs days
  Flexibility: Swap adapters at runtime
  Cost: $10-50 vs $500-5000 per fine-tune
  VRAM: Share one base, load multiple adapters
```

### Training Pipeline (Per Claude 4.5)

**Phase 1 - Data Generation (Cloud LLM):**
```
Tool: GPT-4 or Claude 4.5
Task: Generate 2000-5000 dialogue examples per monster type
Prompt: "Generate vampire dialogue with: aristocratic tone, 
         references to centuries, disdain for humans as 'cattle'"
Cost: ~$50-200 per monster type
```

**Phase 2 - LoRA Training:**
```
Base Model: Llama-3.1-8B or Mistral-7B
Framework: Axolotl, PEFT, or Unsloth
Hardware: Single A100 (40GB) or 2x RTX 4090
Time: 2-6 hours per adapter
Parameters:
  - Rank: 16-32
  - Alpha: 32-64
  - Target modules: q_proj, v_proj, o_proj
  - Learning rate: 1e-4 to 3e-4
```

**Phase 3 - Validation:**
```
Metrics:
  - Perplexity on held-out dialogue
  - Human evaluation (QA team plays dialogue trees)
  - A/B testing vs base model
Acceptance: >80% approval rate from QA
```

### When to Use Each Approach

**Prompt Engineering Only:**
- ✅ Style/persona variations
- ✅ Short-turn guardrails
- ✅ Deterministic templates
- ✅ Cost: Near-zero
- ❌ Limited robustness for complex behaviors

**LoRA Adapters (RECOMMENDED):**
- ✅ Lock in persona/style
- ✅ Domain jargon
- ✅ Consistent tone
- ✅ Cost: $10-100 per adapter
- ✅ Training: 2-6 hours per adapter

**Full Fine-Tuning:**
- Only if LoRA can't achieve quality goals
- Requires domain knowledge deeply internalized
- Cost: $500-5000 per fine-tune

---

## 5. SERVING STACK RECOMMENDATIONS

### Ollama vs vLLM vs TensorRT-LLM

**Ollama** (Your Current Setup):
- ✅ Great for **development and smaller deployments**
- ✅ Easy to use, good for prototyping
- ❌ Lags behind vLLM/TensorRT-LLM for **high concurrency**
- ❌ Limited continuous batching and scheduling
- ❌ LoRA orchestration not as mature

**vLLM or TensorRT-LLM (RECOMMENDED for Production):**
- ✅ Continuous batching and preemptive scheduling
- ✅ Prefix/prompt caching per NPC persona
- ✅ LoRA hot-load and multi-LoRA support
- ✅ Speculative decoding (1.5-2x speedup)
- ✅ Production-grade performance

**Recommendation**: Use **Ollama for development**, migrate to **vLLM or TensorRT-LLM for production**.

### Optimization Techniques

**1. Continuous Batching:**
```python
batch_config = {
    "max_batch_size": 32,
    "timeout_ms": 100,  # Wait 100ms to fill batch
    "dynamic": True     # Adaptive batch sizing
}
```

**2. Prefix Caching:**
```python
# Reuse prompt processing for similar contexts
shared_context = """
You are a vampire in The Body Broker game.
Setting: Post-apocalyptic Chicago.
Player reputation: Neutral.
"""
# All vampire dialogues share this prefix
```

**3. Speculative Decoding:**
- Use tiny 1-2B drafter model
- Large 7-8B model verifies
- Achieve 2-3x speedup

**4. Response Streaming:**
- Start playing audio/showing text before generation completes
- Improves perceived latency

---

## 6. UNREAL ENGINE INTEGRATION

### Recommended Architecture (Per Claude 4.5)

```cpp
// C++ Game Code (Unreal Engine)
class UDialogueManager : public UGameInstanceSubsystem {
public:
    // Async request to local Ollama/vLLM server
    UFUNCTION(BlueprintCallable)
    void RequestNPCDialogue(
        ANPCCharacter* NPC, 
        FString PlayerPrompt,
        FDialogueResponseDelegate Callback
    );
    
private:
    // HTTP client for inference API
    TSharedPtr<IHttpRequest> CreateInferenceRequest(
        FString ModelName,
        FString Prompt,
        FDialogueContext Context
    );
    
    // Determine routing (local vs cloud)
    bool ShouldUseCloud(ENPCType Type);
};
```

### Integration Options

**Option 1: HTTP REST API (Recommended for MVP)**
```cpp
// Pros: Simple, language-agnostic, easy debugging
// Cons: HTTP overhead, no streaming benefits

Request->SetURL("http://inference-server:11434/api/generate");
Request->SetVerb("POST");

FString JsonPayload = FString::Printf(TEXT(R"({
    "model": "vampire_dialogue",
    "prompt": "%s",
    "context": %s,
    "stream": false
})"), *PlayerPrompt, *ContextJson);
```

**Option 2: gRPC/Protobuf (Production)**
```protobuf
// High-performance binary protocol
service DialogueService {
    rpc GetNPCResponse(DialogueRequest) returns (DialogueResponse);
    rpc StreamDialogue(DialogueRequest) returns (stream DialogueChunk);
}
```

**Option 3: Direct Library Binding (Advanced)**
```cpp
// Embed llama.cpp directly in game process
// Pros: Lowest latency, no network hop
// Cons: Memory management complexity, crashes affect game
```

### Complete Integration Pattern

```cpp
void UDialogueSubsystem::GetNPCDialogue(
    FDialogueRequest& Request,
    FOnDialogueReceived Callback
) {
    // Check cache first
    FString CacheKey = Request.GetCacheKey();
    if (DialogueCache.Contains(CacheKey)) {
        Callback.ExecuteIfBound(DialogueCache[CacheKey]);
        return;
    }
    
    // Determine routing
    if (ShouldUseCloud(Request.NPCType)) {
        FallbackToCloud(Request, Callback);
    } else {
        TryLocalModel(Request, Callback);
    }
}

bool UDialogueSubsystem::ShouldUseCloud(ENPCType Type) {
    switch (Type) {
        case ENPCType::QuestGiver:
        case ENPCType::StoryNPC:
        case ENPCType::FirstTimeBoss:
            return true;
        default:
            return false;
    }
}
```

---

## 7. OPERATIONAL CONCERNS

### Model Management (Per Gemini 2.5 Pro)

**Model Registry:**
- Centralized storage (AWS S3, Google Cloud Storage, self-hosted Harbor/Nexus)
- Versioned models: `goblin_shaman-v1.2-finetuned`
- Git LFS for training scripts/data (models in registry)

**Model Orchestrator Service:**
- Tracks player locations across game server shards
- Pre-emptively loads models for NPCs in areas players are moving towards
- Keeps frequently used models in persistent cache
- Unloads LRU models to free VRAM

**Update Deployment (Blue-Green or Canary):**
- **Blue-Green**: Two identical clusters, deploy to inactive, switch traffic
- **Canary**: Deploy to small subset, monitor, then roll out

### Reliability & Fallbacks

**Critical Fallback Chain:**
```
Local Model (50-200ms, $0)
    ↓ (timeout or quality failure)
Cloud Fast Model (500ms, $0.001)
    ↓ (rate limit or downtime)
Cloud Premium Model (2s, $0.01)
    ↓ (complete failure)
Static Dialogue Pool (0ms, $0)
```

**Graceful Degradation:**
- Timeout on API call (e.g., 500ms)
- Fall back to deterministic dialogue tree
- NPC says generic response: "Hmm, let me think about that"
- Game continues without breaking

### Monitoring Requirements

**Non-Negotiable Metrics (Prometheus + Grafana):**
- GPU VRAM and utilization per server
- Inference latency (average, p95, p99)
- API error rates
- Model loading times
- Queue depth for inference requests

---

## 8. COST ANALYSIS

### Comparison: Hybrid vs Cloud-Only

**Assumptions:**
- 1000 concurrent players
- 12 hours gameplay per day
- 20 dialogues per player per hour
- 150 tokens per dialogue (prompt + response)

**Cloud-Only Approach:**
```
Daily dialogues: 1000 * 12 * 20 = 240,000/day
Cost per 1k tokens: $0.03 (GPT-4-turbo)
Monthly cost: 240,000 * 150 * $0.03 / 1000 * 30
= $32,400/month 😱
```

**Hybrid Approach (80% local, 20% cloud):**
```
Local dialogues: 240,000 * 0.8 = 192,000 (Free - amortized hardware)
Cloud dialogues: 240,000 * 0.2 = 48,000

Monthly cloud: 48,000 * 150 * $0.03 / 1000 * 30
= $6,480/month

Hardware amortization:
  Server cost: $30,000
  Lifespan: 36 months
  Monthly: $30,000 / 36 = $833/month

Total hybrid: $6,480 + $833 = $7,313/month

Savings: $25,087/month (77% reduction)
```

### Break-Even Analysis

**When Hybrid Makes Sense:**
- ✅ >10k daily active players
- ✅ Dialogue is core gameplay (not flavor)
- ✅ Cloud API costs > $10k/month
- ✅ ML engineering resources available
- ✅ 2-3 months acceptable for infrastructure

**When Cloud-Only Makes Sense:**
- ✅ <1k players (early development)
- ✅ Team size < 10 people
- ✅ Dialogue is supplementary feature
- ✅ Need to ship in <6 weeks
- ✅ Prefer opex over capex

---

## 9. PHASED IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-4) - **Cloud-Only with Caching**

```yaml
Goal: Prove the concept works
Approach: Cloud-only with aggressive caching

Infrastructure:
  - Use OpenAI/Anthropic API for all NPCs
  - Implement aggressive dialogue caching
  - Build Unreal integration layer

Success Metrics:
  - 95% of dialogues served from cache
  - <$500/month API costs
  - <2 second response time
```

### Phase 2: Hybrid Transition (Weeks 5-12) - **Add Local Models**

```yaml
Goal: Reduce costs with local models
Approach: Add Ollama for common NPCs

Infrastructure:
  - Deploy single Mistral-7B for zombie/ghoul dialogue
  - Keep cloud for bosses/quests
  - Implement quality monitoring

Success Metrics:
  - 60% dialogues from local models
  - <$200/month cloud costs
  - <500ms local response time
```

### Phase 3: Fine-Tuning (Weeks 13-20) - **LoRA Adapters**

```yaml
Goal: Improve quality with custom models
Approach: LoRA adapters per monster type

Infrastructure:
  - Generate training data with GPT-4
  - Train 5 LoRA adapters (vampire, werewolf, zombie, ghoul, lich)
  - A/B test against base models

Success Metrics:
  - 85% QA approval for fine-tuned dialogues
  - Distinct personalities per monster type
  - <300ms response time maintained
```

### Phase 4: Production Scale (Weeks 21+) - **Multi-GPU Cluster**

```yaml
Goal: Handle 1000+ concurrent players
Approach: Multi-GPU cluster with load balancing

Infrastructure:
  - 3-4 node GPU cluster
  - Load balancing with failover
  - Monitoring & auto-scaling

Success Metrics:
  - 99.9% uptime
  - <100ms p95 latency
  - <$1000/month total inference costs
```

---

## 10. CRITICAL SUCCESS FACTORS

### 1. Start with Caching
- 80% of dialogues are repetitive
- Even with 0% cache, system should work
- At 80% cache, handle 5x the load

### 2. Build Fallback Chains
```
Local Model → Cloud Fast Model → Cloud Premium → Static Dialogue
```

### 3. Monitor Quality Continuously
```python
metrics = {
    "coherence_score": 0.85,  # LLM-as-judge
    "player_skip_rate": 0.15,  # Players hitting "skip"
    "repetition_rate": 0.05,    # Same response twice
    "error_rate": 0.001         # Crashes or timeouts
}

# Alert if any metric degrades >10%
```

### 4. Embrace Async Everywhere
```cpp
// Never block the game thread
UFUNCTION(BlueprintCallable, meta = (Latent, LatentInfo = "LatentInfo"))
void GetDialogueAsync(
    FLatentActionInfo LatentInfo,
    ANPCCharacter* NPC,
    FString& OutDialogue
);
```

---

## 11. FINAL RECOMMENDATION

### For "The Body Broker":

**✅ YOUR APPROACH IS SOUND - BUT IMPLEMENT IN PHASES**

**Recommended Path:**
```yaml
Months 1-3 (Development):
  - Use GPT-4-turbo/Claude for all NPCs
  - Focus on game mechanics, not ML ops
  - Cost: <$500/month (low player count)
  - Build Unreal integration layer

Months 4-6 (Soft Launch):
  - Deploy Ollama with Mistral-7B for zombies/ghouls
  - Keep cloud for bosses and quests
  - Target: 60% local, 40% cloud
  - Cost: <$1500/month (growing players)

Months 7-12 (Scale):
  - Fine-tune LoRA adapters per monster type
  - Migrate to vLLM/TensorRT-LLM for production
  - Multi-GPU server cluster
  - Target: 85% local, 15% cloud
  - Cost: <$3000/month (1000+ players)

Year 2+ (Optimize):
  - Custom models per major NPC
  - Experiment with smaller models (3B)
  - Edge deployment experiments
  - Cost: <$2000/month (optimized)
```

### Why This Approach?

1. **Validate Product-Market Fit First**: Don't over-engineer before knowing players want the game
2. **Incremental Complexity**: Each phase adds one new capability
3. **Managed Risk**: Cloud fallback always available
4. **Cost Optimization**: Start expensive, optimize as revenue grows

---

## 12. KEY TECHNICAL DECISIONS

### Model Architecture
- ✅ **One 7-8B base model per GPU** (not multiple models)
- ✅ **LoRA adapters** for NPC specialization (not full fine-tuning)
- ✅ **Hot-swap adapters** at runtime (not model swapping)

### Serving Stack
- ✅ **Ollama for development** (easy setup)
- ✅ **vLLM or TensorRT-LLM for production** (better performance)

### Infrastructure
- ✅ **Separate inference cluster** (not on game servers)
- ✅ **Distributed cluster** (not single server)

### Quantization
- ✅ **8-bit/FP8 preferred** (best speed/quality)
- ✅ **4-bit for VRAM constraints** (24GB cards)

---

## 13. CONCLUSION

**Your distributed LLM architecture is technically superior and financially viable at scale.**

**Key Takeaways:**
1. ✅ Use LoRA adapters, not separate models per NPC
2. ✅ Separate inference servers from game servers
3. ✅ Start cloud-only, transition to hybrid gradually
4. ✅ Use vLLM/TensorRT-LLM for production (not just Ollama)
5. ✅ Target 7-8B models for best quality/latency balance
6. ✅ Build robust fallback chains (local → cloud → static)
7. ✅ Monitor quality continuously

**This approach will save 70-80% on API costs while providing better latency and customization. The investment is significant but justified for a successful game with substantial player base.**

---

**Assessment Completed**: January 29, 2025  
**Models Consulted**: Claude Sonnet 4.5, GPT-5-Pro, Gemini 2.5 Pro  
**Next Steps**: Start Phase 1 (Cloud-only MVP), build Unreal integration, validate gameplay

