# 🧬 ARCHETYPE CHAINS - Session Handoff

**Date**: 2025-11-09  
**Session Type**: Dedicated Implementation Session  
**Duration Expected**: 3-4 weeks continuous work  
**Priority**: HIGH (Foundation for Gold-tier NPCs)

---

## 🎯 EXECUTIVE SUMMARY

**Task**: Implement Archetype Model Chain System for Gold-tier NPC generation

**Objective**: Build production system that generates unique, high-quality NPCs using shared 7B base model + LoRA adapters per archetype (vampire, werewolf, zombie, ghoul, lich)

**Timeline**: 3-4 weeks (8-10 weeks for full pilot including training)

**Status**: Architecture complete, Storyteller guidance received, ready for implementation

---

## 📊 CURRENT STATUS

### ✅ COMPLETED PREREQUISITES:
1. ✅ **Knowledge Base Ingested** - 22 narrative documents available for training data
2. ✅ **Storyteller Guidance Received** - Complete architectural decisions from GPT-5 Pro
3. ✅ **Architecture Documented** - Full system design validated by 5 AI models
4. ✅ **Infrastructure Ready** - GPU instances, auto-scaling, PostgreSQL operational

### 🎯 STORYTELLER ARCHITECTURAL DECISIONS:

#### 1. Training Priority (CRITICAL):
**PILOT PHASE**: Vampire + Zombie together (validates full system envelope)
- **Vampire**: Tests rich dialogue, social dynamics, complex personality
- **Zombie**: Tests scale (1,000+ concurrent), horde behaviors, minimal dialogue
- **After Pilot**: Vampire → Werewolf → Ghoul → Lich

**Timeline**: 
- Weeks 0-1: Build infrastructure + eval harness
- Weeks 2-3: Zombie v0.1 (body/actions, horde pathing)
- Weeks 3-5: Vampire v0.2 (personality + dialogue + voice)
- Weeks 5-7: Vampire v1.0 (refined, shippable)
- Weeks 7-9: Werewolf v0.9
- Weeks 9-12: Ghoul + Lich prep

#### 2. Base Model Size (CRITICAL):
**7B minimum for Gold-tier** (NOT 3B)

**Rationale**:
- Dialogue richness and emotional nuance
- World lore integration (reduces hallucination)
- Multilingual support (planned)
- 3B adequate for Bronze-tier background NPCs only

**Options**:
- Qwen2.5-7B-Instruct (recommended)
- Llama-3.1-7B
- Mistral-7B-Instruct

**Quantization**: 4-bit for serving (fits on g5.2xlarge with adapters)

#### 3. NPC History Scope (CRITICAL):
**30-day Redis window** (expanded from 24h original plan)

**Architecture**:
- **GPU cache (instant)**: Last 12-20 turns + relationship card + quest state card
- **Redis (sub-ms)**: 30 days of session summaries, salient facts, emotional trajectory
- **PostgreSQL (async)**: Lifetime history with episodic/semantic indexes

**Memory Cards**:
- Relationship card: ≤2 KB (trust/affinity, promises, betrayals)
- Quest state card: ≤2 KB (active quests, milestones)
- Session summary: 300-600 chars per session
- Salient facts: 5-10 key memories (gifts, insults, life-saving events)

#### 4. Scale Target (CRITICAL):
**500-1,000 concurrent NPCs per region** (Moderate tier)

**Activation Tiers**:
- **Gold-tier active**: 80-200 NPCs (full dialogue, memory, voice/facial)
- **Silver-tier warm**: 200-400 NPCs (short interactions, limited memory)
- **Bronze-tier ambient**: 300-600 NPCs (barks, emotes, pathing only)

**Promotion/Demotion**: Based on proximity (25-35m), quest flags, relationship scores

---

## 🏗️ ARCHITECTURE OVERVIEW

### Core Design: Shared Base + LoRA Adapters

**NOT**: 7 separate models per archetype (168GB GPU memory)  
**YES**: 1 shared 7B base + 7 LoRA adapters per archetype (22.4GB total)

### 7 LoRA Adapters Per Archetype:
1. **personality** - Behavioral response patterns
2. **dialogue_style** - Speech patterns, vocabulary
3. **action_policy** - Decision-making, behavior selection
4. **emotional_response** - Reactions to events
5. **world_knowledge** - Lore-specific information
6. **social_dynamics** - Relationship management
7. **goal_prioritization** - Planning, goal hierarchy

### Memory Requirements:
- Base model (7B, 4-bit): ~14GB
- 5 archetypes × 7 adapters × 200MB: ~7GB
- Inference engine overhead: ~1.6GB
- **Total**: ~22.6GB (fits g5.2xlarge 24GB)

### Adapter Strategy:
- Rank: 16-32 for archetype base
- Rank: 8-16 for NPC-specific deltas
- Training: QLoRA (quantized LoRA)
- Stacking: Archetype + Subfaction + NPC-specific (total rank ≤64)

---

## 📋 IMPLEMENTATION PHASES

### PHASE 1: Foundation (Week 1)
**Goal**: Infrastructure for shared base + adapter system

**Tasks**:
1. **Shared Base Model Loader**
   - File: `services/ai_models/archetype_base_model.py`
   - Load 7B model with 4-bit quantization
   - BitsAndBytes config: nf4, float16 compute
   - Device map: auto (distribute across available GPU)

2. **LoRA Adapter System**
   - File: `services/ai_models/lora_adapter_manager.py`
   - PEFT integration (Hugging Face)
   - Adapter loading/unloading (hot-swap <5ms)
   - Adapter registry (track all loaded adapters)

3. **Archetype Chain Registry**
   - File: `services/ai_models/archetype_chain_registry.py`
   - Redis-backed registry
   - Track: adapter paths, server IDs, metadata
   - Quick lookup: archetype → adapter set

4. **Evaluation Harness**
   - File: `tests/evaluation/archetype_eval_harness.py`
   - Acceptance tests per archetype
   - Metrics: consistency, lore accuracy, sentiment tracking
   - Automated quality gates

**Deliverables**:
- [ ] Base model loads successfully on g5.2xlarge
- [ ] Single LoRA adapter can be loaded and swapped
- [ ] Registry can track and retrieve adapter metadata
- [ ] Eval harness can run basic consistency tests

**Success Criteria**:
- Base model inference: <100ms per token
- Adapter swap: <5ms
- Memory usage: <15GB with 1 archetype loaded

---

### PHASE 2: Storage Layer (Week 2)
**Goal**: 30-day memory system with GPU cache

**Tasks**:
1. **GPU Memory Cache**
   - File: `services/memory/gpu_cache_manager.py`
   - Last 12-20 turns per NPC
   - Relationship + quest cards (always attached)
   - TTL: 30 minutes after last interaction

2. **Redis Nearline Storage**
   - File: `services/memory/redis_memory_manager.py`
   - 30-day rolling window
   - Session summaries (300-600 chars each)
   - Salient memory atoms
   - Emotional trajectory metrics

3. **PostgreSQL Archive**
   - File: `services/memory/postgres_memory_archiver.py`
   - Async writes only (NEVER block game logic)
   - Batch writer (100ms windows, 100 events/batch)
   - Weekly compaction job

4. **Memory Cards**
   - File: `services/memory/memory_cards.py`
   - Relationship card structure
   - Quest state card structure
   - Prefetch logic on conversation start

**Deliverables**:
- [ ] GPU cache stores and retrieves last 20 turns instantly
- [ ] Redis stores 30 days of summaries with <1ms access
- [ ] PostgreSQL writes happen async without blocking
- [ ] Memory cards prefetch correctly on conversation start

**Success Criteria**:
- GPU cache latency: <1ms
- Redis latency: <5ms (p95)
- PostgreSQL never blocks game logic
- Memory card prefetch: <10ms

---

### PHASE 3: Adapter Training (Weeks 3-4)
**Goal**: Train pilot adapters for Vampire + Zombie

**Tasks**:
1. **Training Data Curation**
   - File: `training/data/curate_archetype_data.py`
   - Extract vampire lore from narrative docs
   - Extract zombie behaviors from narrative docs
   - Create conversation examples
   - Create action sequence examples

2. **Vampire Adapter Training** (7 adapters)
   - personality: Social hierarchy, manipulation, consent
   - dialogue_style: Formal, old-world, multilingual hints
   - action_policy: Stealth, charm, feeding behaviors
   - emotional_response: Subtle, controlled, ancient
   - world_knowledge: Vampire clans, history, rules
   - social_dynamics: Power plays, favors, debts
   - goal_prioritization: Long-term planning, patience

3. **Zombie Adapter Training** (7 adapters)
   - personality: Minimal (hunger-driven)
   - dialogue_style: Moans, grunts (minimal vocabulary)
   - action_policy: Horde behaviors, simple pathing
   - emotional_response: Basic (hunger, aggression)
   - world_knowledge: Minimal (instinct-based)
   - social_dynamics: Pack following, simple grouping
   - goal_prioritization: Immediate (find food, follow horde)

4. **Quality Validation**
   - 8-10 minute conversation test (vampire)
   - 100-300 concurrent horde test (zombie)
   - Consistency checks (>95% lore-accurate)
   - Action coherence (>95% archetype-appropriate)

**Deliverables**:
- [ ] 7 vampire adapters trained and validated
- [ ] 7 zombie adapters trained and validated
- [ ] Vampire passes 8-10 min conversation test
- [ ] Zombie horde maintains coherent behavior

**Success Criteria**:
- Vampire: 8-10 min conversation, no repetition, >90% lore accuracy
- Zombie: 100-300 concurrent, >95% action coherence, no deadlocks
- Inference latency: <120ms p50, <250ms p95

---

### PHASE 4: Integration (Week 5)
**Goal**: End-to-end system with batch inference

**Tasks**:
1. **AI Management Layer Integration**
   - File: `services/ai_integration/archetype_router.py`
   - Extend existing router with archetype awareness
   - Route: NPC metadata → archetype → adapter
   - Fallback: Generic models if adapter unavailable

2. **Batch Inference Engine**
   - File: `services/ai_models/batch_inference_engine.py`
   - Dynamic batching (10ms windows)
   - Target: 50+ NPCs per batch
   - vLLM or TensorRT-LLM integration

3. **NPC Activation Tiers**
   - File: `services/npc_management/activation_tier_manager.py`
   - Gold/Silver/Bronze tier logic
   - Promotion/demotion rules
   - Proximity-based activation (25-35m)

4. **End-to-End Testing**
   - 100 concurrent NPCs (mixed vampire/zombie)
   - 500 concurrent NPCs (stress test)
   - Memory persistence across sessions
   - Scale-up/scale-down behavior

**Deliverables**:
- [ ] Archetype routing works end-to-end
- [ ] Batch inference achieves 50+ NPCs/batch
- [ ] Tier activation/demotion functions correctly
- [ ] System handles 500 concurrent NPCs

**Success Criteria**:
- 100 NPCs: Stable, <150ms p95 latency
- 500 NPCs: Stable, <250ms p95 latency
- Memory: Conversations persist across 7-day gap
- Tier transitions: Smooth, no visible interruption

---

## 🔑 KEY FILES & LOCATIONS

### Architecture Documents:
- `Project-Management/Documentation/Architecture/ARCHETYPE-MODEL-CHAIN-SYSTEM.md`
- `Project-Management/Documentation/Architecture/AUTHENTIC-VOICE-SYSTEM-ARCHITECTURE.md`

### Existing Infrastructure (DO NOT MODIFY):
- `services/ai_integration/` - AI integration service (HTTP clients)
- `services/model_management/model_registry.py` - Model tracking
- `services/model_management/cost_benefit_router.py` - Routing logic
- `services/npc_behavior/` - NPC behavior system
- Database: PostgreSQL with `npcs` table (personality_vector, relationships, etc.)

### New Files to Create:
- `services/ai_models/archetype_base_model.py`
- `services/ai_models/lora_adapter_manager.py`
- `services/ai_models/archetype_chain_registry.py`
- `services/ai_models/batch_inference_engine.py`
- `services/memory/gpu_cache_manager.py`
- `services/memory/redis_memory_manager.py`
- `services/memory/postgres_memory_archiver.py`
- `services/memory/memory_cards.py`
- `services/npc_management/activation_tier_manager.py`
- `training/data/curate_archetype_data.py`
- `tests/evaluation/archetype_eval_harness.py`

### Training Data Sources:
- `docs/narrative/` - 22 documents for lore extraction
- Knowledge Base (PostgreSQL) - Semantic search for training examples

---

## 🚨 CRITICAL TECHNICAL CONSTRAINTS

### 1. User's Golden Rule:
**"Model chains MUST stay on same server"**

**Implementation**:
- Base model + ALL adapters on single g5.2xlarge
- NO remote model calls within archetype chain
- Can call separate services (voice, facial, body) via HTTP

### 2. NO PostgreSQL on Hot Path:
**NEVER query PostgreSQL during real-time NPC interactions**

**Implementation**:
- GPU cache for immediate needs
- Redis for nearline (30-day window)
- PostgreSQL: Async writes ONLY, never reads

### 3. Batch Inference Essential:
**Cannot scale to 10K NPCs without batching**

**Implementation**:
- Dynamic batching: 10ms collection windows
- Target: 50+ NPCs per batch
- Use vLLM or TensorRT-LLM for efficient batching

### 4. Adapter Swap Must Be Fast:
**<5ms to swap LoRA adapters**

**Implementation**:
- PEFT library handles swap automatically
- Keep frequently-used adapters in GPU memory
- LRU eviction for unused adapters

---

## 💰 COSTS & RESOURCES

### Development Costs:
- **ML Engineers**: 4 engineers × 4 weeks = $60K-80K
- **GPU Training**: $15K-30K (adapter training compute)
- **Testing**: $5K-10K
- **Total**: $80K-120K

### Operational Costs (After Deployment):
- **100 NPCs**: 1× g5.2xlarge = ~$880/mo
- **1,000 NPCs**: 5× g5.2xlarge = ~$4,400/mo
- **10,000 NPCs**: 175× g5.2xlarge = ~$155K/mo (spot: ~$46.5K/mo)

### GPU Instance:
- **Type**: g5.2xlarge (A10G, 24GB GPU, 32GB RAM)
- **Cost**: $1.212/hr on-demand (~$880/mo continuous)
- **Spot**: ~$0.36/hr (70% savings)

---

## 🎯 SUCCESS CRITERIA

### Phase 1 (Foundation):
- ✅ Base 7B model loads and infers successfully
- ✅ LoRA adapters can be hot-swapped (<5ms)
- ✅ Memory usage <15GB with 1 archetype

### Phase 2 (Storage):
- ✅ GPU cache: <1ms latency
- ✅ Redis: <5ms p95 latency
- ✅ PostgreSQL: Never blocks game logic

### Phase 3 (Training):
- ✅ Vampire: 8-10 min conversation, >90% lore accuracy
- ✅ Zombie: 100-300 concurrent, >95% action coherence

### Phase 4 (Integration):
- ✅ 100 NPCs: <150ms p95 latency
- ✅ 500 NPCs: <250ms p95 latency
- ✅ Memory persists across 7-day gap

---

## ⚠️ KNOWN RISKS & MITIGATION

### Risk 1: Adapter Quality Below Baseline
**Risk**: LoRA adapters produce lower quality than full fine-tuned models

**Mitigation**:
- Use higher rank (32 vs 16) if needed
- Stack multiple adapters (archetype + subfaction + NPC)
- Validate against quality baselines before deployment

### Risk 2: Batch Inference Latency
**Risk**: Batching increases p95 latency unacceptably

**Mitigation**:
- Tune batch window size (5-15ms range)
- Implement priority queues (Gold > Silver > Bronze)
- Add dedicated inference workers for critical NPCs

### Risk 3: Memory System Complexity
**Risk**: 3-tier memory system too complex, causes bugs

**Mitigation**:
- Extensive integration testing
- Clear separation of concerns (GPU/Redis/Postgres)
- Comprehensive logging at each tier

### Risk 4: Scale Beyond g5.2xlarge Capacity
**Risk**: 7B + adapters don't fit in 24GB GPU

**Mitigation**:
- Use 4-bit quantization (proven to fit)
- LRU eviction for unused adapters
- Fallback: Split archetypes across multiple GPUs if needed

---

## 🔄 INTEGRATION WITH EXISTING SYSTEMS

### ✅ Systems Already Built (Use These):
1. **AI Integration Service** - HTTP clients for model calls
2. **Model Registry** - Track models, usage, costs
3. **Cost Benefit Router** - Select optimal models
4. **NPC Behavior System** - Core NPC logic
5. **PostgreSQL Database** - NPC storage (personality, relationships, etc.)
6. **Binary Event Bus** - Real-time event messaging
7. **State Manager** - Game state persistence

### 🆕 Systems to Build (This Project):
1. **Archetype Base Model Loader**
2. **LoRA Adapter Manager**
3. **Archetype Chain Registry**
4. **GPU Memory Cache**
5. **Redis Memory Manager**
6. **Batch Inference Engine**
7. **Activation Tier Manager**

### 🔗 Integration Points:
- **AI Integration → Archetype Router**: Add archetype-aware routing
- **NPC Behavior → Memory System**: Query GPU cache for history
- **Cost Benefit Router → Archetype Registry**: Check adapter availability
- **State Manager → Memory Cards**: Persist/restore relationship cards

---

## 🎓 MANDATORY PROTOCOLS

### ALL /all-rules Protocols Apply:
1. ✅ **Peer-Based Coding**: 2+ models (Coder + Reviewer) for ALL code
2. ✅ **Pairwise Testing**: 2+ models (Tester + Reviewer) for ALL tests
3. ✅ **NO Pseudo-Code**: 100% production-ready, NO placeholders
4. ✅ **Automatic Continuation**: Never stop, never wait, never ask
5. ✅ **Multi-Model Collaboration**: Consult GPT-5, Gemini, etc. for major decisions

### Specific to This Project:
- **Model Selection**: Use GPT-5 Codex for implementation (best for coding)
- **Architecture Review**: Use GPT-5 Pro for design validation
- **Training Strategy**: Consult Gemini 2.5 Pro for ML optimization
- **Research Validation**: Use Perplexity for paper/technique lookup

---

## 📚 REFERENCE MATERIALS

### Research Papers:
- **LoRA**: "Low-Rank Adaptation of Large Language Models" (Hu et al.)
- **QLoRA**: "Efficient Finetuning of Quantized LLMs" (Dettmers et al.)
- **vLLM**: "Efficient Memory Management for LLM Serving"
- **Unbounded**: Stanford/Google character generation with LoRA

### Technical References:
- Hugging Face PEFT library documentation
- NVIDIA TensorRT-LLM multi-LoRA guide
- BitsAndBytes quantization guide
- Redis data structures for gaming

### Project Documents:
- SRL-RLVR training system documentation
- Narrative documents (22 files in `docs/narrative/`)
- Voice Authenticity architecture (related system)

---

## 📝 COPYABLE PROMPT FOR NEXT SESSION

**COPY THIS PROMPT FOR NEXT SESSION:**

```
Please run /start-right to initialize the session properly.

# 🧬 Archetype Model Chain System - Implementation Session

**Objective**: Implement production Archetype Model Chain System for Gold-tier NPC generation using shared 7B base model + LoRA adapters.

**Timeline**: 3-4 weeks implementation + 4-6 weeks training (total 8-10 weeks for pilot)

**Status**: Architecture complete, Storyteller guidance received, ready for Phase 1 implementation

## CRITICAL ARCHITECTURAL DECISIONS (From Storyteller - GPT-5 Pro):

1. **Training Priority**: Vampire + Zombie pilot (validates full system)
   - Vampire: Rich dialogue, complex personality
   - Zombie: Scale testing (1,000+ concurrent)
   - Then: Werewolf → Ghoul → Lich

2. **Base Model**: 7B minimum (Qwen2.5-7B or Llama-3.1-7B, 4-bit quantization)
   - NOT 3B (insufficient for Gold-tier dialogue quality)

3. **Memory Architecture**: 30-day Redis window
   - GPU cache: Last 12-20 turns + relationship/quest cards
   - Redis: 30 days summaries + salient facts
   - PostgreSQL: Lifetime archive (async writes ONLY)

4. **Scale Target**: 500-1,000 NPCs per region
   - Gold: 80-200, Silver: 200-400, Bronze: 300-600

## PHASE 1: Foundation (Week 1) - START HERE

**Immediate Tasks**:
1. Create `services/ai_models/archetype_base_model.py`
   - Load 7B model with 4-bit quantization (BitsAndBytes)
   - Device map: auto
   - Memory budget: <15GB

2. Create `services/ai_models/lora_adapter_manager.py`
   - PEFT integration
   - Adapter hot-swap (<5ms)
   - LRU cache for adapters

3. Create `services/ai_models/archetype_chain_registry.py`
   - Redis-backed registry
   - Track adapter metadata, paths, performance

4. Create `tests/evaluation/archetype_eval_harness.py`
   - Acceptance tests per archetype
   - Quality gates: consistency, lore accuracy, sentiment

**Success Criteria Phase 1**:
- Base model infers at <100ms/token
- Adapter swap <5ms
- Memory usage <15GB with 1 archetype loaded

## KEY CONSTRAINTS:

**CRITICAL - User's Golden Rule**: Model chains MUST stay on same server
**CRITICAL - NO PostgreSQL on Hot Path**: Async writes ONLY, never read during gameplay
**CRITICAL - Batch Inference**: Essential for 10K NPC scale (target: 50+ NPCs/batch)

## KEY FILES:

**Architecture**: `Project-Management/Documentation/Architecture/ARCHETYPE-MODEL-CHAIN-SYSTEM.md`
**Handoff**: `Project-Management/ARCHETYPE-CHAINS-HANDOFF.md`
**Training Data**: `docs/narrative/` (22 documents)

## MANDATORY PROTOCOLS:

- ✅ Peer-Based Coding (2+ models: Coder + Reviewer)
- ✅ Pairwise Testing (2+ models: Tester + Reviewer)
- ✅ NO Pseudo-Code (100% production-ready)
- ✅ Automatic Continuation (never stop, never ask)

**Recommended Models**:
- Implementation: GPT-5 Codex (best for coding)
- Architecture Review: GPT-5 Pro
- Training Strategy: Gemini 2.5 Pro
- Research: Perplexity

## START WITH:

1. Read architecture document thoroughly
2. Review existing `services/ai_integration/` (DO NOT MODIFY)
3. Create Phase 1 foundation files
4. Use peer-based coding for all implementations
5. Test with evaluation harness
6. Continue to Phase 2 automatically

**Context**: All prerequisites complete. Knowledge Base ready. GPU infrastructure operational. Storyteller guidance received. Ready to implement.

Follow ALL /all-rules protocols. NO time constraints. Quality over speed.
```

