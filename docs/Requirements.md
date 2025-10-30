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

**Document Status**: Complete and ready for implementation  
**Next Steps**: Begin Phase 1 (Foundation) development
