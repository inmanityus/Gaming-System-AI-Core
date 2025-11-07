# Model Architecture Requirements - Multi-Tier Strategy
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Date**: 2025-11-03  
**Status**: NEW REQUIREMENTS - Model Replacement & Architecture Strategy  
**Replaces**: Partial model selection requirements  
**Enforces**: ALL rules in `/all-rules`

---

## 🚨 EXECUTIVE SUMMARY

**Strategy**: Three-tier hybrid model architecture to replace both small models AND for-pay models while maintaining 300+ FPS gameplay and reducing scaling costs.

**Key Decision**: Large MoE models (DeepSeek-V3 671B) handle async high-level tasks (stories, narrative, worldbuilding) even though they're not fast enough for real-time gaming. This enables maximum quality for specialized roles while keeping real-time performance optimized.

---

## 1. THREE-TIER MODEL ARCHITECTURE

### 1.1 Tier Classification: Gold, Silver, Bronze

#### **GOLD TIER - Real-Time (Sub-16ms per Token)**
**Purpose**: Real-time NPC interactions, frame-rate synchronous gameplay  
**SLA**: p95 end-to-end < 16ms; deterministic budgets; no blocking I/O  
**Model Size**: 3B-8B parameters  
**Use Cases**:
- NPC action selection at frame rate
- Short utterance continuation (1-8 tokens)
- Quick intent classification
- Environmental "barks" and reactions
- Procedural item descriptions

**Requirements**:
- ✅ Sub-16ms inference latency per token
- ✅ No tool calls or blocking operations
- ✅ Pre-warmed KV caches
- ✅ Quantization: 4-bit AWQ or FP8
- ✅ Framework: TensorRT-LLM for maximum speed
- ✅ Speculative decoding with 1B-2B draft models

**Model Candidates**:
- Qwen2.5-3B-Instruct
- Llama-3.2-3B-Instruct
- Phi-3.5-mini (license permitting)
- Mistral-7B-Instruct (aggressively quantized)

#### **SILVER TIER - Interactive (80-250ms)**
**Purpose**: High-quality interactions that don't need frame-rate synchronization  
**SLA**: p95 80-250ms; can use tools and RAG  
**Model Size**: 7B-13B parameters  
**Use Cases**:
- Key NPC conversations (quest givers, faction leaders)
- Complex dialogue systems
- Player support and moderation
- Mission logic and coordination
- Code suggestions in development tooling

**Requirements**:
- ✅ 80-250ms inference latency acceptable
- ✅ Tool use via MCP servers allowed
- ✅ RAG retrieval from vector stores
- ✅ Quantization: INT8, FP8, or AWQ
- ✅ Framework: vLLM with PagedAttention
- ✅ Speculative decoding optional

**Model Candidates**:
- Llama-3.1-8B-Instruct
- Qwen2.5-7B-Instruct
- Mistral-Nemo-12B-Instruct
- DeepSeek-Coder-6.7B (for code-specific tasks)
- Qwen2.5-Math-7B (for reasoning tasks)

#### **BRONZE TIER - Asynchronous (Seconds Acceptable)**
**Purpose**: High-quality expert work where latency doesn't matter  
**SLA**: Seconds acceptable; async processing  
**Model Size**: Large MoE (671B total, 37B active)  
**Use Cases**:
- Storyteller: Main story arcs, branching questlines, plot generation
- Worldbuilding: Lore generation, historical texts, environmental descriptions
- Cybersecurity: Deep code analysis, security audits, threat assessment
- Admin Operations: Batched reports, data analysis, system administration
- Content Creation: Long-form narrative, documentation, creative writing

**Requirements**:
- ✅ Latency acceptable (760ms+ per token is fine)
- ✅ Highest quality outputs
- ✅ Complex multi-step reasoning
- ✅ Long context (128K+ tokens)
- ✅ Batch processing for efficiency
- ✅ Framework: Multi-node SageMaker or EKS with tensor parallel

**Model Candidates**:
- DeepSeek-V3.1-Terminus (671B MoE, 37B active) - **PRIMARY**
- Mixtral-8x22B (backup option)
- For-pay models as last-resort fallback only

---

## 2. DECOUPLING STRATEGY: FRAME RATE vs LLM UPDATES

### 2.1 Critical Architecture Pattern

**Problem**: 300+ FPS requires sub-16ms per frame, but even small models can't guarantee this consistently.

**Solution**: Decouple game frame rate from LLM update rate.

**Pattern**:
```
Game Loop (300+ FPS):
├── Physics Step (every frame)
├── Deterministic Micro-Policies (every frame) ← NPC controllers
├── Rendering (every frame)
└── LLM Intent Updates (1-2 Hz, async, non-blocking) ← LLM system
```

### 2.2 Implementation Requirements

#### NPC Controller Architecture
```python
class NPCController:
    """
    Decoupled NPC system:
    - Micro-policy runs at frame rate (deterministic)
    - LLM updates intent at lower frequency (1-2 Hz)
    - Intent cache provides smooth transitions
    """
    
    def update_frame(self, delta_time):
        # Runs every frame (300+ FPS)
        # Uses cached intent from LLM
        self.micro_policy.execute(self.cached_intent)
        
    def update_llm_intent(self):
        # Runs at 1-2 Hz (async, non-blocking)
        # Updates cached intent for micro-policy
        future_intent = asyncio.create_task(
            self.llm_service.get_intent(self.npc_context)
        )
        # Micro-policy continues using current cached intent
```

#### Intent Cache System
- **Per-NPC Intent Cache**: Stores high-level intent (aggressive, friendly, curious, etc.)
- **Dialogue Next-Token Cache**: Pre-computed next dialogue tokens
- **State Prediction Buffer**: Predicts 3-5 seconds ahead
- **Cache Refresh**: Updates asynchronously without blocking frame loop

#### Ahead-of-User Prediction
- **State Prediction Service**: Continuously predicts future game states
- **Pre-computation**: Generate responses for likely player actions
- **Response Streaming**: Stream tokens as they generate (don't wait for full response)
- **Prefetching**: Predict player's next action and pre-generate responses

---

## 3. HOSTING & DEPLOYMENT STRATEGY

### 3.1 Training & Fine-Tuning (AWS Required)

**All model training MUST run in AWS** (local dev computer cannot handle model inference).

#### Instance Requirements

**Bronze Tier (Large MoE)**:
- **Instance**: `p5.48xlarge` (8× H100 80GB) - Multi-node (3-4 nodes = 24 H100s)
- **Training Time**: 1-3 days per epoch
- **Training Cost**: $8,640-$32,400 per fine-tuning run
- **Method**: LoRA/QLoRA adapters only (not full fine-tuning)
- **Storage**: FSx for Lustre for high-throughput I/O

**Silver Tier (Mid-Size)**:
- **Instance**: `p4d.24xlarge` (8× A100 40GB) or `p5.48xlarge` (8× H100 80GB)
- **Training Time**: 10-20 hours
- **Training Cost**: $240 per fine-tuning run
- **Method**: LoRA/QLoRA with DPO/ORPO for preference alignment

**Gold Tier (Small)**:
- **Instance**: `g6.12xlarge` (NVIDIA L4) or `g5.12xlarge` (A10G)
- **Training Time**: 5-10 hours
- **Training Cost**: $75 per fine-tuning run
- **Method**: QLoRA for maximum efficiency

#### SageMaker Integration
- **Training Jobs**: SageMaker Training with ECR containers
- **Model Registry**: SageMaker Model Registry or MLflow
- **Async Inference**: SageMaker Async Inference for Bronze tier
- **Real-Time Endpoints**: SageMaker Real-Time Endpoints for Silver tier (optional)

### 3.2 Inference Hosting (Flexible)

#### Production Inference

**Gold Tier (Real-Time)**:
- **Primary**: EC2 `g6.xlarge` (L4 24GB) or EKS on EC2 with TensorRT-LLM
- **Framework**: TensorRT-LLM for maximum speed
- **Quantization**: 4-bit AWQ
- **Networking**: NLB + gRPC, colocate in same AZ as game servers
- **Scaling**: Auto-scaling with warm pools (N≥2 hot replicas per AZ)

**Silver Tier (Interactive)**:
- **Primary**: EC2 `g6.12xlarge` (L4) or `g5.12xlarge` (A10G) with vLLM
- **Framework**: vLLM with PagedAttention and continuous batching
- **Quantization**: INT8, FP8, or AWQ
- **Networking**: NLB + gRPC
- **Scaling**: Aggressive autoscaling based on demand

**Bronze Tier (Async)**:
- **Primary**: SageMaker Async Inference Endpoints or EKS job queues on `p5.48xlarge`
- **Framework**: Multi-node with tensor parallel + expert parallel
- **Processing**: Batch prompts heavily for efficiency
- **Storage**: Outputs to S3/Aurora, surfaced via caches

#### Development & Local

**Ollama Integration**:
- **Purpose**: Developer iteration, offline demos, edge deployment
- **Models**: Mirror production weights and prompts
- **Limitation**: NOT used for hard real-time production
- **Usage**: Testing, prototyping, local development

#### Self-Hosted Option

**On-Prem GPUs**:
- Deploy same Helm charts (vLLM/TensorRT-LLM) on K8s cluster
- Router can target on-prem endpoints via weighted routing
- Useful for cost control if hardware already owned

---

## 4. MODEL SELECTION & REPLACEMENT STRATEGY

### 4.1 Replace Small Models (3B-8B)

**Decision**: **KEEP small models for Gold tier (real-time NPCs)**

**Rationale**:
- Small models (3B-8B) are the ONLY models capable of sub-16ms inference
- Large models cannot achieve real-time performance (760ms+ latency)
- Small models properly trained with SRL→RLVR can match quality of larger models for specific tasks
- Cost is minimal: $75 training, extremely low inference cost

**Action**: Train small models MORE aggressively with SRL→RLVR to maximize quality while maintaining speed.

### 4.2 Replace Mid-Size Models (7B-13B)

**Decision**: **EVALUATE case-by-case, likely KEEP for Silver tier**

**Rationale**:
- Mid-size models provide excellent quality/latency balance
- Training cost is still reasonable ($240)
- Can handle interactive tasks that don't need frame-rate sync
- Large models too expensive and slow for this tier

**Action**: Continue using 7B-13B for Silver tier, evaluate larger models only if quality insufficient after SRL→RLVR training.

### 4.3 Replace For-Pay Models

**Strategy**: **Use Large MoE Models (DeepSeek-V3) for specialized roles**

**Replace For-Pay Models For**:
- ✅ **Storyteller**: DeepSeek-V3 for narrative generation (async acceptable)
- ✅ **Cybersecurity**: DeepSeek-V3 for deep analysis (async acceptable)
- ✅ **Admin Operations**: DeepSeek-V3 for batched tasks (async acceptable)
- ✅ **High-Level Planning**: DeepSeek-V3 for complex reasoning (async acceptable)

**Keep For-Pay Models As**:
- Last-resort fallback only
- Temporary bridge during migration
- Special cases where MoE models insufficient

**ROI Calculation**:
- For-pay models: $0.01-$0.001 per 1K tokens (ongoing OpEx)
- DeepSeek-V3 training: $8.6k-$32k one-time (CapEx)
- Break-even: ~860K-32M tokens (achieved quickly for storyteller/admin use)
- **Massive cost savings at scale**

### 4.4 Dynamic Model Selection

**Router/Orchestrator Requirements**:
- **Policy Engine**: Chooses model tier by persona, SLA, request size, context freshness
- **Gold Tier**: Avoids tool use, uses in-memory intent cache only
- **Silver Tier**: Can call MCP tools and RAG
- **Bronze Tier**: Runs asynchronously via job queue, returns artifacts to shared stores

**Selection Criteria**:
1. **Request Type**: Real-time vs interactive vs async
2. **Quality Requirements**: Simple vs complex reasoning needed
3. **Latency Budget**: Sub-16ms vs 80-250ms vs seconds acceptable
4. **Context Size**: Small vs medium vs very large context
5. **Cost Sensitivity**: High-volume (Gold) vs moderate (Silver) vs low-volume high-value (Bronze)

---

## 5. MCP SERVER INTEGRATION

### 5.1 Required MCP Servers

#### **Storyteller MCP**
**Purpose**: Narrative generation, worldbuilding, lore retrieval  
**Tier**: Bronze (async)  
**Capabilities**:
- RAG against "Lorebook" in OpenSearch Serverless
- Plot/quest graph store (Aurora Postgres)
- Asset catalogs and templates
- Historical context retrieval
- Narrative consistency checking

#### **Cybersecurity MCP**
**Purpose**: Security analysis, code auditing, threat detection  
**Tier**: Bronze (async), Silver (interactive analysis)  
**Capabilities**:
- Semgrep integration
- Trivy, Syft/Grype scanners
- AWS Security Hub read-only
- CloudTrail/GuardDuty readers
- Code repository analysis
- **Access Control**: Read-only by default, write operations require human approval

#### **Admin MCP**
**Purpose**: System administration, website management, operations  
**Tier**: Bronze (batched), Silver (interactive queries)  
**Capabilities**:
- Read-most AWS APIs via STS-assumed roles
- Fitness website admin tools
- System monitoring and health checks
- **Change-Making Tools**: Require MFA or Slack approval flow

#### **Game State MCP**
**Purpose**: Game world state access for NPCs and systems  
**Tier**: Gold (read-only cache), Silver (live queries)  
**Capabilities**:
- Read-only snapshots of world state
- Player/NPC attributes and stats
- Quest progress and status
- **Write Operations**: Event-queued for engine arbitration, never direct DB writes

#### **RAG/Vector Search MCP**
**Purpose**: Knowledge retrieval, semantic search  
**Tier**: Silver, Bronze  
**Capabilities**:
- Vector search in OpenSearch Serverless
- Per-persona indices
- Shared lore index
- Long-term memory summaries

#### **Utilities MCP**
**Purpose**: Common utilities for all models  
**Tier**: All tiers  
**Capabilities**:
- Vector search operations
- Key/value config store
- Time, UUID generation
- Rate limiting
- Content filtering (ProtectAI Guard open models)

### 5.2 MCP Integration Rules

**Gold Tier (Real-Time)**:
- ❌ **NEVER blocks on MCP calls**
- ✅ Uses pre-fetched data from MCP (cached in intent cache)
- ✅ Tool calls become async requests to Silver/Bronze
- ✅ Results cached and picked up on next non-urgent turn

**Silver Tier (Interactive)**:
- ✅ Can call MCP tools synchronously (80-250ms budget)
- ✅ RAG retrieval allowed
- ✅ Tool use for complex queries

**Bronze Tier (Async)**:
- ✅ Full MCP tool access
- ✅ Long-running operations allowed
- ✅ Batch operations for efficiency

---

## 6. PERFORMANCE OPTIMIZATION REQUIREMENTS

### 6.1 Real-Time Path (Gold Tier) - Sub-16ms Target

**Quantization**:
- ✅ 4-bit AWQ or FP8 for 3B-8B models
- ✅ TensorRT-LLM engines optimized per GPU type
- ✅ Sequence length buckets for different contexts

**KV Cache Management**:
- ✅ Per-NPC pinned caches in GPU memory
- ✅ LRU eviction for inactive NPCs
- ✅ Sliding window attention to cap memory
- ✅ Prefix cache for system prompts

**Speculative Decoding**:
- ✅ Draft model (1B-2B) proposes tokens
- ✅ Target model (3B-8B) verifies
- ✅ 1.5-2.2× speedups typical without quality loss

**Batching Strategies**:
- ✅ Separate real-time queues with small max batch sizes (1-4)
- ✅ Isolate from background queues with aggressive batching
- ✅ Continuous batching with micro-batches for Gold tier

**Engine Integration**:
- ✅ Zero-copy gRPC
- ✅ Pinned memory for GPU transfers
- ✅ CPU affinity and NUMA awareness
- ✅ Co-locate GPU nodes with game servers (same AZ)

**Token Control**:
- ✅ Short outputs (1-8 tokens) for NPC control
- ✅ Enforce max_new_tokens and early-exit logits
- ✅ Dynamic prompt truncation if needed

### 6.2 Interactive Path (Silver Tier) - 80-250ms Target

**Framework**: vLLM with PagedAttention  
**Quantization**: INT8, FP8, or AWQ  
**Optimizations**:
- Mixed precision inference
- Prompt caching for common patterns
- Speculative decoding optional (3B draft for 8-13B targets)
- Continuous batching with moderate batch sizes

### 6.3 Async Path (Bronze Tier) - Seconds Acceptable

**Optimizations**:
- Heavy batching for maximum throughput
- Tensor parallel + expert parallel for MoE models
- Spot instances for cost optimization
- Nightly distillation: Bronze traces → Silver adapters → Gold adapters

---

## 7. COST PROJECTIONS & SCALING

### 7.1 Training Costs

| Model Tier | Size | Instance | Training Time | Cost per Run |
|------------|------|----------|---------------|--------------|
| **Gold** | 3B-8B | g6.12xlarge | 5-10 hours | $75 |
| **Silver** | 7B-13B | p4d.24xlarge | 10-20 hours | $240 |
| **Bronze** | 671B MoE | p5.48xlarge (multi-node) | 1-3 days | $8,640-$32,400 |

### 7.2 Inference Costs (Self-Hosted)

**Per 1M Tokens** (approximate, depends on quantization and sequence length):
- **Gold (3B on L4, 4-bit)**: $0.6-$1.0 per 1M tokens
- **Silver (7B-8B on L4/A10G, INT8)**: $1.4-$3.3 per 1M tokens
- **Silver (13B on A10G, INT8)**: $3.1-$6.7 per 1M tokens
- **Bronze (DeepSeek-V3)**: Highly variable, batch heavily for efficiency

### 7.3 Comparison to For-Pay Models

**For-Pay Model Costs** (per 1M tokens):
- GPT-5 Pro: ~$10-$50 per 1M tokens
- Claude 4.5 Sonnet: ~$3-$15 per 1M tokens
- Gemini 2.5 Pro: ~$1.25-$10 per 1M tokens

**Self-Hosted Savings**:
- Gold tier: **10-50× cheaper** than for-pay
- Silver tier: **3-10× cheaper** than for-pay
- Bronze tier: **Break-even after ~860K-32M tokens** (one-time training cost)

### 7.4 Scaling Strategy

**NPC Load Example**:
- 10,000 NPCs total
- 2,000 "spotlight" NPCs at 2 Hz LLM updates = 16k tokens/sec
- With 3B model at 250 tok/s per L4 GPU → ~64 L4 GPUs needed
- Cost: ~$45/hour for 64× L4 = **$32,400/month** (24/7)
- Compare to for-pay: 10,000 NPCs × frequent updates = **millions per month**

**Mitigation Strategies**:
- Run LLM at 1-2 Hz for most NPCs (not every frame)
- Micro-policies at frame rate, LLM updates at lower frequency
- Allocate LLM budget to "spotlight" NPCs only
- Use distilled policies or cached intents for background NPCs

---

## 8. QUALITY CONTROL REQUIREMENTS

### 8.1 Non-AI Detectable Output

**Requirements**:
- ✅ Output must not sound "AI-generated"
- ✅ Natural language patterns and variations
- ✅ Personality-consistent but not robotic
- ✅ Contextually appropriate responses
- ✅ Human-like imperfections and natural flow

**Implementation**:
- SRL→RLVR training includes "naturalness" in reward function
- Post-processing to add variation
- A/B testing with human evaluators
- Continuous monitoring for "AI-sounding" patterns

### 8.2 Guardrails Enforcement

**Content Filtering**:
- ✅ ProtectAI Guard open models on request/response path
- ✅ Stricter filters for player-facing outputs
- ✅ Custom guardrails for game-specific content policies

**Safety Checks**:
- ✅ Toxicity detection
- ✅ Bias monitoring
- ✅ Inappropriate content filtering
- ✅ Privacy protection (PII redaction)

### 8.3 Quality Metrics

**Per Tier**:
- **Gold**: Intent accuracy, response time (p50/p95/p99), cache hit rate
- **Silver**: Dialogue quality, coherence, player satisfaction
- **Bronze**: Narrative quality, worldbuilding coherence, creativity scores

**Continuous Monitoring**:
- Real-time quality metrics dashboard
- Alert on quality degradation
- Automated quality testing
- Human-in-the-loop feedback collection

---

## 9. INTEGRATION WITH EXISTING SYSTEMS

### 9.1 SRL→RLVR Training System

**Requirement**: ALL models MUST be trained using SRL→RLVR approach
- ✅ Three-model collaboration generates expert trajectories
- ✅ SRL stage: Step-wise supervision
- ✅ RLVR stage: Outcome-based fine-tuning
- ✅ Dynamic example generation (never static)
- ✅ Performance tracking and weakness detection

### 9.2 Model Management System

**Integration**:
- Model registry for all three tiers
- Version tracking and rollback capability
- A/B testing infrastructure
- Canary deployments

### 9.3 AI Inference Service

**Integration**:
- Unified API for all tiers
- Intelligent routing based on SLA requirements
- Load balancing across model instances
- Health checks and failover

### 9.4 Orchestration Service

**Integration**:
- Hierarchical pipeline still applies
- Bronze tier handles Layer 4 (coordination)
- Silver tier handles Layer 3 (interaction)
- Gold tier handles Layer 2 (customization)

---

## 10. MIGRATION STRATEGY

### 10.1 Phase 1: Foundation (Weeks 1-2)
- Stand up EKS with L4 and A10G node groups
- Deploy vLLM and TensorRT-LLM infrastructure
- Implement router/orchestrator with three-tier routing
- Baseline latency tests for all tiers

### 10.2 Phase 2: Training (Weeks 3-6)
- Train Gold tier models (3B-8B) with SRL→RLVR
- Train Silver tier models (7B-13B) with SRL→RLVR
- Set up DeepSeek-V3 Bronze tier infrastructure
- Implement MCP servers (Storyteller, Cybersecurity, Admin)

### 10.3 Phase 3: Deployment (Weeks 7-10)
- Deploy Gold tier for real-time NPCs
- Deploy Silver tier for interactive NPCs
- Deploy Bronze tier for async narrative generation
- Integrate with game engine (decoupled architecture)

### 10.4 Phase 4: Optimization (Weeks 11-12)
- Implement speculative decoding
- Optimize KV cache management
- Set up nightly distillation (Bronze → Silver → Gold)
- Performance tuning and cost optimization

---

## 11. SUCCESS CRITERIA

### 11.1 Performance
- ✅ Gold tier: p95 < 16ms per token (real-time NPCs)
- ✅ Silver tier: p95 80-250ms (interactive NPCs)
- ✅ Bronze tier: Async processing, quality over speed
- ✅ Game frame rate: 300+ FPS maintained

### 11.2 Quality
- ✅ Output quality matches or exceeds for-pay models on specialized tasks
- ✅ Non-AI detectable output (human evaluation)
- ✅ Guardrails enforced (zero violations)
- ✅ Player satisfaction metrics maintained

### 11.3 Cost
- ✅ Training costs within budget ($8.6k-$32k one-time for Bronze)
- ✅ Inference costs 10-50× lower than for-pay models
- ✅ Break-even achieved within 3-6 months
- ✅ Scaling costs predictable and manageable

### 11.4 Reliability
- ✅ 99.9% uptime for Gold tier
- ✅ Graceful degradation on failures
- ✅ Automatic failover to backups
- ✅ Zero game-breaking incidents

---

## 12. MANDATORY ENFORCEMENT

### 12.1 No Exceptions
- ❌ NO using for-pay models for tasks Bronze tier can handle
- ❌ NO blocking operations in Gold tier
- ❌ NO large models in real-time path
- ❌ NO static training examples
- ❌ NO skipping quality control

### 12.2 All Rules Apply
**CRITICAL**: All rules in `/all-rules` must be followed:
- Peer-based coding for all implementation
- Pairwise testing for all tests
- Three-AI review for all solutions
- Comprehensive testing after every task
- Memory consolidation after every task
- 45-minute milestones
- Timer service running
- Work visibility in real-time
- Automatic continuation

---

**END OF MODEL ARCHITECTURE REQUIREMENTS**




