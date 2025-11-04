# AI-Driven Gaming Core - Requirements Document
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Last Updated**: January 29, 2025  
**Status**: Ready for Implementation

---

## 📋 TABLE OF CONTENTS

1. [Core Vision](#core-vision)
2. [Game Concept: "The Body Broker"](#game-concept-the-body-broker)
3. [Technical Architecture](#technical-architecture)
4. [AI System Requirements](#ai-system-requirements)
5. [Platform & Deployment](#platform--deployment)
6. [Monetization System](#monetization-system)
7. [User Experience Requirements](#user-experience-requirements)
8. [Content Rating & Safety](#content-rating--safety)
9. [Performance Requirements](#performance-requirements)
10. [Cost Targets](#cost-targets)

**For detailed technical recommendations and feasibility assessments, see:**  
📖 **[RECOMMENDATIONS.md](./RECOMMENDATIONS.md)**

---

## 1. CORE VISION

### Project Goal
Build an AI-driven gaming core using **Unreal Engine 5** that leverages hierarchical, distributed LLM architectures to create truly dynamic game experiences where:
- Every player has a completely unique experience
- NPCs respond dynamically to player actions (not pre-written scripts)
- Content is generated procedurally with AI assistance
- The system can anticipate player reactions based on interactions
- The game adapts in real-time to player choices and behaviors

### Key Innovation
This system combines **hierarchical LLM pipelines** with **specialized model orchestration** to create content far beyond what humans can build alone, enabling emergent gameplay and narrative experiences that are unique to each player.

---

## 2. GAME CONCEPT: "THE BODY BROKER"

### Core Gameplay Loop
The player is a **Body Broker** operating between two worlds:

**Day World:**
- Rob morgues and kill people (avoid cops)
- Obtain lab equipment to grow human parts
- Add ingredients for specific monster types
- Purchase supernatural powers (invisibility, super strength, speed)
- Build empire: labs, morgues, supply chain
- Progress from street-level to "King Pimp" running massive operation

**Night World:**
- Sell body parts to monsters (necessary scum, but valuable)
- Start with generic parts to lowest customers (zombies, ghouls)
- Unlock intermediates that sell for you
- Gain access to higher-level monsters (vampires, werewolves, liches)
- Enter house politics and intrigue
- Ally and double-cross monster houses
- Always hunted, always in danger

### Game Features
- **Horror Elements**: Jump scares, chases, tense atmosphere
- **Progression System**: Street-level → Empire builder
- **Social Mechanics**: House politics, alliances, betrayals
- **Resource Management**: Body parts, equipment, supernatural powers
- **Combat & Stealth**: Fight cops, avoid monsters, survive deals
- **Narrative Emergence**: AI-driven story based on player choices

### Rating Target
- **ESRB**: M (Mature)
- **Content**: Violence, horror, mature themes
- **Never Allowed**: Suicide promotion, real-world killing encouragement

---

## 3. TECHNICAL ARCHITECTURE

### Game Engine
- **Primary Engine**: Unreal Engine 5 (latest version)
- **Deployment**: Steam + PC Desktop only (simplifies multi-platform)
- **Rationale**: UE5 provides Lumen, Nanite, MetaSounds, PCG framework - essential for horror atmosphere

### AI Integration Architecture
- **Inference Servers**: Separate from game servers (DO NOT run on game servers)
- **Serving Stack**: 
  - Development: Ollama
  - Production: vLLM or TensorRT-LLM (better concurrency)
- **Model Management**: LoRA adapters on shared base models (10-50x more efficient than separate models)

---

## 4. AI SYSTEM REQUIREMENTS

### 4.1 Hierarchical LLM Architecture (4-Layer System)

**Layer 1 - Foundation (Low-Level LLMs):**
- **Generic Monster Generator**: Base stats, type, core attributes
- **Basic Terrain Generator**: Landscape primitives, biome foundation
- **Room Layout Generator**: Basic geometry, room primitives
- **Characteristics**: Fast, reusable, cacheable, deterministic seeds
- **Implementation**: Primarily procedural code; LLMs generate parameters/seeds

**Layer 2 - Customization (Mid-Level LLMs):**
- **Monster Customizer**: Takes generic monster → adds characteristics (traits, personality, backstory)
- **Terrain Enhancer**: Adds details, environmental storytelling elements
- **Room Detailer**: Adds props, hazards, narrative elements
- **Characteristics**: Runs parallel per entity; synchronized only where dependencies exist
- **Implementation**: Specialized fine-tuned models or LoRA adapters

**Layer 3 - Interaction (High-Level LLMs):**
- **One-on-One NPC Interactions**: Dialogue generation per NPC
- **Relationship Management**: Tracks player-NPC relationships, faction standing
- **Dialogue System**: Streams responses, maintains personality consistency
- **Characteristics**: Only for active NPCs; deferred/streamed for others
- **Implementation**: 7-8B models with NPC-specific LoRA adapters

**Layer 4 - Coordination (Top-Level LLMs):**
- **Battle Coordination**: Multiple monsters in combat scenarios
- **Environmental Storytelling**: Scene orchestration, narrative beats
- **Orchestration Manager**: Cloud LLMs coordinate specialized mini-LLMs
- **Story Director**: Writes ongoing story, sends instructions to specialists
- **Characteristics**: Lightweight plans; delegate heavy generation to sub-queues
- **Implementation**: Cloud LLMs (GPT-5, Claude 4.5) + local coordinators

### 4.2 Distributed LLM System

**Specialized Mini-LLMs (Local/Ollama):**
- **Exterior Generation LLM**: Buildings, streets, city layouts
- **Interior Generation LLM**: Apartments, morgues, labs
- **Monster-Specific LLMs**: One per race (vampires, werewolves, zombies, ghouls, liches)
  - Each has guides on: aggression, intelligence, charisma (classic character stats modernized with AI)
  - Autonomous decision-making: one-on-one interactions AND battles
- **Landscape LLM**: Forests, cemeteries, terrain features
- **Terrain Generator**: Natural environments
- **All operate in PARALLEL** to prevent bottlenecks

**Orchestration Layer (Cloud/Paid LLMs):**
- **Story Directors**: Write ongoing story, coordinate mini-LLMs
- **Coordination Managers**: Send instructions to specialized LLMs
- **Conflict Resolution**: Resolve inconsistencies between parallel generations
- **Validation**: Ensure coherence across all generated content

**Monster Behavior System:**
- **Character Stats (AI-Powered)**:
  - Aggression levels (affects combat behavior)
  - Intelligence (affects tactics, negotiation)
  - Charisma (affects social interactions)
  - Survival instincts
  - Faction loyalty
  - Personal goals/motivations
- **Autonomous Actions**:
  - Orchestration LLMs set up scenarios
  - Monster-specific LLMs act autonomously based on their guides
  - Can override base behavior when context requires
  - Battle coordination with multiple monsters simultaneously

### 4.3 Model Specifications

**Local Models (Ollama/vLLM):**
- **Tier 1 (Generic NPCs)**: 3-4B models (Phi-3-mini, TinyLlama) - 50-150ms latency
- **Tier 2 (Elite NPCs)**: 7-8B models (Llama-3.1-8B, Mistral-7B) + LoRA - 100-300ms latency
- **Tier 3 (Major NPCs)**: 7-8B + personalized LoRA - 200-500ms latency
- **Quantization**: 8-bit/FP8 preferred, 4-bit for VRAM constraints

**Cloud Models (Orchestration):**
- **Primary**: GPT-5-Pro, Claude Sonnet 4.5, Gemini 2.5 Pro
- **Fallback**: GPT-3.5 Turbo (10x cheaper for validation)
- **Always use latest models** - system must support model updates

### 4.4 State Management

**Requirements:**
- **Centralized Game State**: Redis/PostgreSQL with vector store
- **Entity Registry**: All NPCs, items, locations with UUIDs
- **World State**: Time, weather, factions, relationships
- **Player History**: Actions, relationships, choices tracked
- **Narrative State**: Plot progression, story beats
- **Semantic Memory**: Vector database (Pinecone/Weaviate) for NPC memories

**State Synchronization:**
- All LLMs read from shared state
- Changes written back as structured diffs
- Validation layer ensures consistency
- Event sourcing for rollback capability

---

## 5. PLATFORM & DEPLOYMENT

### Primary Platforms
- **Steam**: Primary distribution platform
- **PC Desktop**: Windows 10/11 native builds
- **Rationale**: Simplifies deployment, focuses resources, avoids console certification complexity

### Future Platform Considerations
- Other platforms deferred until after successful Steam launch
- Architecture designed for eventual portability

### Deployment Architecture
- **Game Servers**: CPU-bound, handle game logic
- **Inference Cluster**: GPU-bound, separate infrastructure
- **Scalability**: Horizontal scaling for inference nodes

---

## 6. MONETIZATION SYSTEM

### 6.1 Free Tier (Freemium Model)

**Requirements:**
- **Upfront Free Portion**: Significant enough to demonstrate value
- **Limited Customization**: Prevents abuse, drives subscription desire
- **Conversion Focus**: Designed to make players want more
- **Quality Gate**: Free experience must be polished, not crippled demo

### 6.2 Subscription System

**Payment Provider**: 
- **Primary**: Stripe (or better alternative if models recommend)
- **Requirements**: 
  - Recurring billing support
  - Coupon code system
  - Ambassador/referral tracking
  - International payment support

**Subscription Tiers** (to be determined):
- Basic subscription (access to full game)
- Premium (enhanced AI features, priority generation)
- VIP (exclusive content, early access)

### 6.3 Ambassador/Coupon System

**Requirements:**
- **Coupon Codes**: Discount codes for subscriptions
- **Ambassador Program**: Referral tracking and rewards
- **Code Management**: Admin system for generating/managing codes
- **Tracking**: Analytics on code usage and conversion

### 6.4 Cost Per User Calculations

**Target Metrics**:
- Cost per user per day to run game
- Must account for:
  - AI inference costs (local + cloud)
  - Infrastructure (servers, bandwidth)
  - Game server costs
- **Goal**: Sustainable economics at target subscription price

**Assumptions** (to be refined):
- Average 2-3 hours gameplay per day per user
- Mix of free and subscription users
- Scaling economies considered

---

## 7. USER EXPERIENCE REQUIREMENTS

### 7.1 Settings Page

**Required Controls:**
- **Audio Settings**:
  - Master volume
  - Music volume
  - Sound effects volume
  - Voice volume
  - Audio quality presets
- **Video Settings**:
  - Resolution
  - Quality presets (Low/Medium/High/Ultra)
  - Windowed/Fullscreen/Borderless
  - VSync
  - Frame rate limits
  - Individual effects toggles (Lumen, Nanite, etc.)
- **Controls**:
  - Mouse sensitivity
  - Key bindings (customizable)
  - Invert Y-axis option
- **Gameplay**:
  - Subtitles on/off
  - Difficulty settings
  - Auto-save frequency

### 7.2 Helpful Indicators & Guidance

**Philosophy**: Clear guidance without immersion-breaking

**Requirements:**
- **NO Massive Arrows**: Avoid obvious, intrusive indicators
- **Subtle Visual Cues**:
  - Gentle highlights on interactable objects
  - Glowing edges (subtle)
  - Particle effects for important locations
  - Screen-edge indicators pointing off-screen
- **Contextual Help**:
  - Helpful minion NPC that appears when complex actions needed
  - Tutorial hints that fade after completion
  - Tooltips on first interaction with new mechanics
- **Objective Tracking**:
  - Clear but unobtrusive objective list
  - Distance indicators to objectives
  - Map markers (toggleable)
- **Interaction Prompts**:
  - Context-sensitive action prompts (Press E to interact)
  - Only show when player is near and looking at object
  - Fade in/out smoothly

**Goal**: Players should never be confused about what to do next, but guidance should feel natural and integrated.

---

## 8. CONTENT RATING & SAFETY

### Rating System
- **Target**: M (Mature) rating
- **Guardrails Required**:
  - Suicide prevention (never promote)
  - Real-world violence prevention (never encourage real killings)
  - Content filtering based on rating level
  - Age-appropriate content enforcement

### Content Moderation
- **Multi-Layer Approach**:
  1. Generation-at-source constraints (train models to avoid prohibited content)
  2. Real-time AI filtering (input + output)
  3. Human review queue for edge cases
  4. Player reporting system

### Implementation
- **Rating Enforcement**: Tag-based system, pre-generation validation
- **Monitoring**: Continuous quality checks, alert on degradation
- **Transparency**: Acknowledge limitations, clear communication

---

## 9. PERFORMANCE REQUIREMENTS

### Target Performance
- **PC (Mid-Range)**: 60fps at 1080p Medium settings
- **PC (High-End)**: 60fps at 1440p/4K High/Ultra settings
- **AI Latency**:
  - L1/L2 generation: Sub-100ms (mostly procedural)
  - L3 dialogue: First token <200ms, streaming
  - L4 coordination: 100-300ms for plan updates

### Scalability
- **Concurrent Players**: Design for 1000+ concurrent players
- **NPC Generation**: 10-25 concurrent AI-driven NPCs per shard
- **Content Generation**: Predictive pre-generation to mask latency

### Optimization Strategies
- **Aggressive Caching**: 80%+ cache hit rate target
- **Predictive Generation**: Generate content before player arrives
- **LOD Systems**: AI LOD (simpler AI for distant NPCs)
- **Streaming**: Response streaming for dialogue

---

## 10. COST TARGETS

### Cost Per User Per Day
**Initial Targets** (to be refined with actual data):
- **Free Users**: $0.50-1.10/day (limited AI features)
- **Subscription Users**: $1.50-2.50/day (full AI features)
- **Premium Users**: $2.00-3.00/day (priority + enhanced features)

**Components**:
- Local LLM inference: Amortized hardware cost
- Cloud LLM API costs: Direct per-token costs
- Infrastructure: Servers, bandwidth, storage
- Game server operations

### Cost Optimization Goals
- **77% cost reduction** via hybrid local/cloud approach (vs. cloud-only)
- **Aggressive caching**: 80%+ of content served from cache
- **Economies of scale**: Cost per user decreases with player count

### Break-Even Analysis
- Must be profitable at target subscription price
- Account for customer acquisition costs
- Consider lifetime value vs. daily costs

---

## 11. IMPLEMENTATION PRIORITIES

### Phase 1: Foundation (Months 1-6)
- ✅ Unreal Engine 5 integration
- ✅ Basic procedural generation
- ✅ Cloud LLM integration (prove gameplay)
- ✅ Core game mechanics
- ✅ Steam deployment setup

### Phase 2: AI Integration (Months 6-12)
- ✅ Local LLM infrastructure (Ollama)
- ✅ LoRA adapter system
- ✅ Basic hierarchical pipeline (L1-L2)
- ✅ NPC dialogue system (L3)
- ✅ 100-player test

### Phase 3: Advanced Features (Months 12-24)
- ✅ Full hierarchical system (L1-L4)
- ✅ Monster-specific LLMs
- ✅ Orchestration layer
- ✅ Subscription/monetization
- ✅ Settings & UX polish
- ✅ 1000+ player test

### Phase 4: Production Scale (Months 24-36)
- ✅ Multi-GPU cluster
- ✅ Production-grade infrastructure
- ✅ Full optimization
- ✅ Launch preparation

---

## 12. SUCCESS METRICS

### Technical Metrics
- **AI Quality**: >85% QA approval for generated content
- **Latency**: 
  - Tier 1-2: 100-600ms ✅
  - Tier 3: 800-1500ms (250ms first token with streaming) ✅
  - Tier 4: Async 2-5s (non-blocking) ✅
- **Cache Hit Rate**: >90% for content generation (up from 80%)
- **Uptime**: 99.9% for inference services
- **Cost Per User**: $0.50-2.50/day (with rate limiting and caching)
- **P99 Latency**: <400ms (down from 3000ms with optimizations)
- **Throughput**: 10K RPS (up from 1K with connection pooling)

### Game Metrics
- **Player Retention**: Day 7 retention >40%
- **Subscription Conversion**: Free-to-paid conversion >5%
- **Player Satisfaction**: Net Promoter Score >50
- **Content Quality**: Player reports of repetitive/broken content <5%

---

## 13. REFERENCES

### Key Documents
- **[RECOMMENDATIONS.md](./RECOMMENDATIONS.md)**: Detailed technical recommendations, feasibility assessments, architecture decisions
- **[FEASIBILITY-ASSESSMENT.md](./FEASIBILITY-ASSESSMENT.md)**: Original feasibility analysis
- **[BODY-BROKER-TECHNICAL-ASSESSMENT.md](./BODY-BROKER-TECHNICAL-ASSESSMENT.md)**: Game-specific technical assessment
- **[DISTRIBUTED-LLM-ARCHITECTURE.md](./DISTRIBUTED-LLM-ARCHITECTURE.md)**: LLM infrastructure architecture

### Model Consultations
All technical decisions validated through consultation with:
- Claude Sonnet 4.5
- GPT-5-Pro
- Gemini 2.5 Pro
- DeepSeek V3.1 Terminus
- Grok 4

---

---

## 14. SRL→RLVR TRAINING SYSTEM REQUIREMENTS

**Status**: Production-Ready Architecture  
**Last Updated**: 2025-11-03  
**Reference**: `Global-Docs/SRL-RLVR-TRAINING-SYSTEM-COMPLETE.md`

### 14.1 Overview

The SRL→RLVR Training System is a comprehensive framework for training small language models using Google's Supervised Reinforcement Learning (SRL) followed by Reinforcement Learning with Verifiable Rewards (RLVR). This system enables fine-tuning models on domain-specific tasks using AI-generated expert demonstrations and outcome-based rewards.

**Key Benefits:**
- Two-Stage Training: SRL provides dense step-wise supervision, RLVR refines with outcome-based rewards
- Dynamic Example Generation: Three-model collaboration continuously generates high-quality training examples
- Model Selection: Intelligent routing selects optimal models for specific responsibilities
- Stability: KL divergence penalties prevent catastrophic forgetting
- Verification: Built-in validation ensures training quality

### 14.2 Core Components Required

#### 14.2.1 Three-Model Collaboration System

**Required Components:**
1. **Context Retriever (Model A)**:
   - Gathers domain knowledge and rules
   - Retrieves historical examples
   - Fetches relevant context from knowledge base
   - Integrates with rules engine

2. **Teacher Planner (Model B)**:
   - Generates expert step-by-step trajectories
   - Uses cloud LLMs to create training examples
   - Produces step-wise solutions with reasoning
   - Creates dense reward structures

3. **Verifier (Model C)**:
   - Validates and corrects trajectories
   - Ensures correctness, completeness, and rule compliance
   - Provides verification scores (minimum 0.7 threshold)
   - Regenerates examples that fail validation (max 3 attempts)

**Implementation Requirements:**
- Async HTTP client for cloud LLM API calls
- Collaboration orchestrator to coordinate all three models
- Trajectory format with step-wise rewards
- Validation criteria per model type

#### 14.2.2 SRL Training Pipeline

**Required Features:**
- Step-wise reward extraction from expert trajectories
- Supervised learning on expert demonstrations
- KL divergence penalty for stability (weight: 0.1, max_kl: 0.1)
- Reward normalization (z-score method)
- Batch processing (batch_size: 32)
- Multi-epoch training (5 epochs recommended)

**Technical Requirements:**
- PyTorch 2.0+ and Transformers 4.30+
- Support for LoRA adapters (PEFT 0.4.0+)
- Gradient clipping (max_norm: 1.0)
- Learning rate: 1e-5 for SRL stage
- Loss tracking and metrics collection

#### 14.2.3 RLVR Fine-Tuning Pipeline

**Required Features:**
- Outcome-based reward computation (0.0 to 1.0 scale)
- PPO (Proximal Policy Optimization) training
- Reference policy anchoring (SRL-trained model as baseline)
- Clipped objective (epsilon: 0.2)
- Value function estimation
- Entropy bonus for exploration (coefficient: 0.01)
- KL divergence penalty to maintain SRL knowledge

**Technical Requirements:**
- TRL library 0.7.0+ for RL training
- PPO trainer with configurable hyperparameters
- Learning rate: 1e-6 for RLVR stage
- Gamma (discount factor): 0.99
- Value coefficient: 0.5
- Multi-epoch fine-tuning (3 epochs recommended)

#### 14.2.4 Dynamic Model Selection System

**Required Features:**
- Responsibility mapping (model type → trainer routing)
- Cost-benefit analysis:
  - Performance benchmarks comparison
  - Cost evaluation (training and inference)
  - Inference speed assessment
  - Hardware requirements analysis
- Request routing to appropriate trainer
- Model-specific schema support
- Automatic model evaluation and selection updates (weekly/monthly)

**Model Type Support:**
- Sentiment Analysis
- Code Generation
- Content Moderation
- NPC Dialogue Generation
- World Generation
- Story Generation
- [Extensible for future model types]

#### 14.2.5 Performance Tracking System

**Required Features:**
- Training metrics monitoring:
  - Loss tracking (supervised and policy loss)
  - KL divergence monitoring (< 0.1 threshold)
  - Reward progression tracking
  - Stability checks (no spikes or crashes)
- Validation loop:
  - Periodic evaluation on held-out validation set
  - Metrics comparison to baseline
  - Early stopping on no improvement
- Weakness detection:
  - Failure mode identification
  - Performance degradation tracking
  - Continuous evaluation over time
- Model versioning and registry

### 14.3 Multi-Tier Model Architecture Strategy

#### 14.3.1 Gold Tier - Small Models (3B-8B)

**Purpose**: Real-time NPC interactions requiring sub-16ms inference

**Models**: Qwen2.5-3B, Llama-3.2-3B, Phi-3.5-mini

**Requirements:**
- Training cost: ~$75 per fine-tuning run
- Inference cost: $0.6-$1.0 per 1M tokens (self-hosted)
- Hardware: Consumer GPUs (RTX 5090, L4)
- Latency: Sub-16ms inference (ONLY models capable of this)
- Use cases: Real-time NPCs, environmental barks, procedural descriptions

**Hosting:**
- Training: AWS SageMaker g6.12xlarge (L4) or g5.12xlarge (A10G)
- Inference: EC2 g6.xlarge (L4) or EKS with TensorRT-LLM

#### 14.3.2 Silver Tier - Mid-Size Models (7B-13B)

**Purpose**: Interactive NPCs with 80-250ms latency acceptable

**Models**: Llama-3.1-8B, Qwen2.5-7B, Mistral-Nemo-12B

**Requirements:**
- Training cost: ~$240 per fine-tuning run
- Inference cost: $1.4-$6.7 per 1M tokens (self-hosted)
- Hardware: 1-2 datacenter GPUs (A100/H100)
- Latency: 80-250ms (acceptable for interactive tasks)
- Use cases: Key NPCs, complex dialogue, multi-turn conversations, player support
- MCP tools and RAG support required

**Hosting:**
- Training: AWS SageMaker p4d.24xlarge (8× A100) or p5.48xlarge (8× H100)
- Inference: EC2 g6.12xlarge (L4) or g5.12xlarge (A10G) with vLLM

#### 14.3.3 Bronze Tier - Large MoE Models (671B)

**Purpose**: Expert-level tasks where quality is paramount, latency doesn't matter

**Models**: DeepSeek-V3.1-Terminus (671B MoE, 37B active)

**Requirements:**
- Training cost: $8,640-$32,400 per fine-tuning run
- Inference cost: Variable, break-even at 860K-32M tokens (1-3 months)
- Hardware: Multi-node cluster (24+ H100s)
- Latency: 760ms per token (async acceptable)
- Use cases: Storyteller, narrative generation, cybersecurity, admin operations, worldbuilding
- Replaces for-pay models (GPT-5 Pro, Claude 4.5 Sonnet, Gemini 2.5 Pro)

**Hosting:**
- Training: AWS SageMaker p5.48xlarge multi-node (24+ H100s)
- Inference: SageMaker Async Inference or EKS job queues (p5.48xlarge)

### 14.4 Nightly Distillation Strategy

**Purpose**: Continuously reduce dependency on expensive Bronze tier

**Process:**
1. Collect Bronze tier traces (high-quality outputs)
2. Distill to Silver tier adapters (LoRA)
3. Distill Silver to Gold tier adapters (LoRA)

**Requirements:**
- Automated distillation pipeline
- Trace collection from Bronze tier outputs
- LoRA adapter generation for Silver/Gold tiers
- Quality validation after distillation
- Scheduled nightly execution

**Benefit**: Over time, Silver and Gold tiers improve without needing Bronze tier for same tasks, reducing costs while maintaining quality.

### 14.5 Training Infrastructure Requirements

#### 14.5.1 AWS SageMaker Deployment

**MANDATORY**: All AI models must run in AWS, not locally. Local dev computer cannot handle model inference.

**Training Infrastructure:**
- **Gold Tier**: g6.12xlarge (L4) or g5.12xlarge (A10G)
- **Silver Tier**: p4d.24xlarge (8× A100) or p5.48xlarge (8× H100)
- **Bronze Tier**: p5.48xlarge multi-node (24+ H100s)

**Deployment Workflow** (MANDATORY):
1. Build everything locally (compile code, run tests)
2. Test everything locally (ensure 100% pass rate)
3. Verify dev system integrity
4. Deploy to AWS (services, infrastructure, configuration)
5. Test in AWS (run ALL tests against AWS services)
6. Shutdown local models (stop all local AI model services)
7. Fix issues immediately using `/all-rules` and `/test-comprehensive`

**Scripts Required:**
- `scripts/aws-deploy-full.ps1` - Full deployment workflow
- `scripts/aws-deploy-services.ps1` - Deploy services to AWS
- `scripts/aws-test-services.ps1` - Test services in AWS
- `scripts/shutdown-local-models.ps1` - Stop local models

#### 14.5.2 Directory Structure

```
srl_rlvr_training/
├── collaboration/          # Three-model collaboration
│   ├── context_retriever.py
│   ├── teacher_planner.py
│   ├── verifier.py
│   └── orchestrator.py
├── srl/                    # SRL training
│   ├── srl_trainer.py
│   ├── reward_normalizer.py
│   └── kl_controller.py
├── rlvr/                   # RLVR training
│   ├── rlvr_trainer.py
│   ├── ppo_trainer.py
│   └── dpo_trainer.py
├── dynamic/                # Dynamic systems
│   ├── model_selector.py
│   ├── example_generator.py
│   └── rules_integration.py
├── performance/            # Performance tracking
│   ├── performance_tracker.py
│   └── weakness_detector.py
└── models/                # Model-specific trainers
    ├── base_trainer.py
    └── [model_type]_trainer.py
```

### 14.6 Configuration Requirements

**Configuration File**: `configs/srl_rlvr_training.yaml`

**Required Sections:**
- SRL configuration (learning_rate, kl_penalty_weight, max_kl, reward_norm_method, batch_size, epochs)
- RLVR configuration (learning_rate, use_ppo, clip_epsilon, value_coef, entropy_coef, gamma, epochs)
- Collaboration configuration (cloud_llm_model, num_examples_per_request, max_regeneration_attempts, min_verification_score)
- Model selection configuration (cost_weight, performance_weight, update_frequency_days)

### 14.7 Integration Requirements

#### 14.7.1 Learning Service Integration

**Required Integration Points:**
- Game event feedback collection → Model improvement
- Player interaction logging → Training data generation
- Narrative quality feedback → Storyteller model improvement
- Event quality feedback → Event generation improvement
- Player engagement metrics → Overall system improvement

**Data Flow:**
- Feedback via Kinesis streams (partitioned by user_id)
- Model improvement pipeline
- Batch processing for efficiency

#### 14.7.2 Model-Specific Implementation

**Required for Each Model Type:**
1. Model-specific schema (Pydantic models)
2. Specialized trainer class (inherits BaseTrainer)
3. Custom preprocessing methods
4. Model-specific validation logic
5. Type-specific metrics computation

**Example Model Types:**
- Sentiment Analysis: `{"text": str, "sentiment": str, "confidence": float}`
- Code Generation: `{"prompt": str, "code": str, "tests": List[str]}`
- Content Moderation: `{"content": str, "flags": List[str], "severity": str}`
- NPC Dialogue: `{"context": str, "dialogue": str, "personality": dict}`

### 14.8 Performance Benchmarks

**Expected Performance Improvements:**
- SRL Stage: 20-40% improvement over baseline
- RLVR Stage: Additional 10-20% improvement over SRL
- Combined: 30-60% improvement over untrained baseline

**Training Time (Approximate):**
- SRL: 2-5 hours for 1000 examples (depends on model size)
- RLVR: 1-3 hours for 500 examples
- Total: 3-8 hours for complete training pipeline

### 14.9 Security and Compliance

**Required Security Measures:**
- API keys stored securely (environment variables or secrets manager)
- Data privacy (PII redaction if needed)
- Model security (output validation to prevent injection attacks)
- Access control (restrict training operations to authorized users)
- Audit logging (log all training operations for compliance)

### 14.10 Verification and Quality Assurance

**During Training:**
- Training metrics monitoring (loss decreases, KL divergence < 0.1, reward increases)
- Validation loop (periodic evaluation on held-out set)
- Stability checks (no sudden spikes or crashes)

**After Training:**
- Performance testing (comprehensive test suite)
- Weakness detection (failure mode identification)
- Expert example validation (generalization beyond training set)
- Integration tests (end-to-end validation)

**Verification Components:**
- Verifier (Model C): Validates training examples before use
- Performance Tracker: Continuous monitoring of model quality
- Test Suites: Comprehensive validation for each model type
- Integration Tests: End-to-end validation

---

**Document Status**: Complete and ready for implementation  
**Next Steps**: Begin Phase 1 (Foundation) development
