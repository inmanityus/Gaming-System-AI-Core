# Unified Requirements Document
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Consolidated**: 2025-11-05 08:13:05  
**Source Files**: 14 documents  
**Consolidation Rule**: Newer files override older when requirements clash

---

## TABLE OF CONTENTS

1. [Core Vision & Game Concept](#core-vision--game-concept)
2. [Technical Architecture](#technical-architecture)
3. [AI System Requirements](#ai-system-requirements)
4. [Platform & Deployment](#platform--deployment)
5. [Monetization System](#monetization-system)
6. [User Experience Requirements](#user-experience-requirements)
7. [Content Rating & Safety](#content-rating--safety)
8. [Performance Requirements](#performance-requirements)
9. [Cost Targets](#cost-targets)
10. [Model Architecture Requirements](#model-architecture-requirements)
11. [Model Training Requirements](#model-training-requirements)
12. [Multi-Language Speech System](#multi-language-speech-system)
13. [Terrain System Requirements](#terrain-system-requirements)
14. [Weather System Requirements](#weather-system-requirements)
15. [Day/Night World Requirements](#daynight-world-requirements)
16. [Facial Expression Requirements](#facial-expression-requirements)
17. [Voice & Audio Requirements](#voice--audio-requirements)
18. [Immersive Features Requirements](#immersive-features-requirements)
19. [Story Teller Requirements](#story-teller-requirements)
20. [UE5 Tools Requirements](#ue5-tools-requirements)
21. [Peer Coding & Pairwise Testing Requirements](#peer-coding--pairwise-testing-requirements)
22. [Code Quality & Audit Requirements](#code-quality--audit-requirements)

---

## PEER CODING & PAIRWISE TESTING REQUIREMENTS

**MANDATORY - NO EXCEPTIONS**

### Core Principle
**ALL code must be peer-reviewed and ALL tests must be pairwise-validated. This is not optional.**

### Peer-Based Coding Requirements

**MANDATORY PROCESS:**
1. **Coder Model** (Primary): Writes code implementation
   - Must meet minimum model levels (Claude 4.5+, GPT-5+, Gemini 2.5 Pro+)
   - Implements requirement based on unified requirements document
   - Ensures code is real, not mock/fake/placeholder
   
2. **Reviewer Model** (Secondary): Reviews code
   - Must be different model from different provider when possible
   - Must meet minimum model levels
   - Validates:
     - Code is real and not mock/fake
     - Code is syntactically correct
     - Code is optimized while supporting requirements
     - Code meets all requirement specifications
   
3. **Coder Final Review**: Coder reviews Reviewer feedback
   - Ensures Reviewer feedback is incorporated
   - Verifies code is real and not mock/fake
   - Verifies code is syntactically correct
   - Optimizes code while supporting requirements
   - Adds code to file

**AUDIT TRAIL REQUIREMENTS:**
- Every code file MUST have audit trail document
- Audit trail must include:
  - Coder model name and version
  - Reviewer model name and version
  - Review timestamp
  - Review feedback summary
  - Changes made based on review
  - Final approval status

### Pairwise Testing Requirements

**MANDATORY PROCESS:**
1. **Tester Model** (Primary): Creates tests
   - Must meet minimum model levels
   - Writes comprehensive test suite
   - Tests cover all code paths, edge cases, error conditions
   
2. **Reviewer Model** (Secondary): Validates tests
   - Must be different model from different provider
   - Must meet minimum model levels
   - Validates:
     - Tests are real and test real code (not mocks in integration+ tests)
     - Tests properly test the code
     - Tests enforce requirements
     - Tests cover edge cases
   
3. **Tester Final Review**: Tester reviews Reviewer feedback
   - Verifies tests are correct
   - Verifies tests properly test the code
   - Adds tests to testing suite

**TEST EXECUTION REQUIREMENTS:**
1. **Tester Model**: Runs all tests
   - Runs test suite
   - Captures all results
   
2. **Reviewer Model**: Runs same tests independently
   - Runs identical test suite
   - Compares results to Tester
   - Non-matches are rejected and force test re-write
   
3. **Iteration**: Process repeats until all tests pass and results match

**AUDIT TRAIL REQUIREMENTS:**
- Every test file MUST have audit trail document
- Audit trail must include:
  - Tester model name and version
  - Reviewer model name and version
  - Test execution timestamp
  - Test results from both models
  - Result comparison
  - Final validation status

**TEST HIERARCHY REQUIREMENTS:**
- Unit Tests: Test individual functions/methods (mocked dependencies OK for unit tests only)
- Functional Tests: Test functional units (groups of functions)
- Integration Tests: Test component integration (NO mocks - real implementations)
- Subsystem Tests: Test complete subsystems
- System Tests: Test complete system functionality
- Cross-System Tests: Test interactions between systems
- E2E Tests: Test complete user journeys

### Minimum Model Levels

**MANDATORY - NO EXCEPTIONS:**
- Claude: Minimum 4.5 Sonnet, 4.1 Opus (NO Claude 3.x allowed)
- GPT: Minimum 5, 5-Pro, Codex-2 (NO GPT-4.0, GPT-4o, GPT-3.x allowed)
- Gemini: Minimum 2.5 Pro or 2.5 Flash (NO Gemini 1.5 allowed)
- DeepSeek: Minimum V3 (3.1 Terminus) (NO V2 or V1 allowed)
- Grok: Minimum 4 or 4 Fast (NO Grok 3.x allowed)
- Mistral: Minimum 3.1 Medium or Devstral (NO 1.x allowed)

**Reference**: Global-Workflows/minimum-model-levels.md

### Enforcement

**MANDATORY ENFORCEMENT:**
- ❌ NO code without peer review
- ❌ NO tests without pairwise validation
- ❌ NO older generation models
- ❌ NO skipping audit trails
- ❌ NO mock/fake code in production paths
- ❌ NO static test examples

**AUDIT TRAIL LOCATION:**
- Code audit trails: .cursor/audit/code/[filename]-audit.md
- Test audit trails: .cursor/audit/tests/[testname]-audit.md
- Consolidated audit index: .cursor/audit/index.md

---


---

## ⚠️ OPTIONAL (But Recommended)

*Source: UE5-TOOLS-REQUIREMENTS.md (2025-11-05)*

## ⚠️ OPTIONAL (But Recommended)


### ✅ 1. Session Cleanup

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### ✅ 1. Session Cleanup
- Ran cleanup protocols
- Verified current project state
- Confirmed directory structure


### ✅ 2. Gap Analysis

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### ✅ 2. Gap Analysis
- Reviewed `docs/More Requirements.md` comprehensively
- Analyzed current solution capabilities
- Identified 6 major missing features:
  1. Weather System (completely missing)
  2. Facial Expressions/Body Language (not implemented)
  3. Voice/Audio System (MetaSounds mentioned but not detailed)
  4. Enhanced Terrain Ecosystems (basic procedural exists, lacks richness)
  5. Day/Night Transition Mechanism (planned but not detailed)
  6. Immersive Features (not fully developed)


### ✅ 3. Multi-Model Collaboration

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### ✅ 3. Multi-Model Collaboration
- **Director**: Claude Sonnet 4.5 (comprehensive assessment, priorities, integration points)
- **Specialist 1**: GPT-5-Nano (technical implementation, UE5-specific recommendations)
- **Specialist 2**: Gemini 2.0 Flash (scalability, event-driven architecture)
- **Research**: Perplexity (best practices for weather systems)
- **Research**: Exa (weather, facial expressions, MetaSounds documentation)


### ✅ 4. Comprehensive Solution Architecture

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### ✅ 4. Comprehensive Solution Architecture
- Created detailed solution documents for all 6 systems
- Defined architecture, implementation approach, integration points
- Provided code examples and task breakdowns
- Established timelines: 18-24 weeks total


### ✅ 5. Task Breakdown

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### ✅ 5. Task Breakdown
- Created `docs/tasks/MORE-REQUIREMENTS-TASKS.md`
- 27 detailed tasks with acceptance criteria
- Total estimated hours: 342-460 hours
- Organized by priority and dependencies


### ✅ 6. Integration with Global Manager

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### ✅ 6. Integration with Global Manager
- Updated `GLOBAL-MANAGER.md` with new phases
- Added More Requirements tasks to build order
- Established integration points

---


## ✅ INSTALLED & WORKING

*Source: UE5-TOOLS-REQUIREMENTS.md (2025-11-05)*

## ✅ INSTALLED & WORKING

1. **Unreal Engine 5.6**
   - Location: `C:\Program Files\Epic Games\UE_5.6`
   - Status: ✅ Installed
   - UnrealBuildTool: ✅ Found

2. **Visual Studio Build Tools 2022**
   - Location: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools`
   - Status: ✅ Installed
   - MSBuild: ✅ Found

---


## 📋 CURRENT STATUS

*Source: UE5-TOOLS-REQUIREMENTS.md (2025-11-05)*

## 📋 CURRENT STATUS

**Automation Status**: ✅ **READY**

- ✅ UE5 project structure created
- ✅ C++ source files created
- ✅ Target.cs files created
- ✅ Build automation scripts ready
- ✅ Continuous build automation ready

**Build Commands**:
```powershell
# Build everything
.\scripts\build-everything.ps1

# Build UE5 only
.\scripts\build-ue5-project.ps1

# Generate VS files only
.\scripts\generate-vs-files.ps1

# Continuous build (watches for changes)
.\scripts\continuous-build-automation.ps1
```

---


## 📋 TABLE OF CONTENTS

*Source: Requirements.md (2025-11-04)*

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


## 📝 NOTES

*Source: UE5-TOOLS-REQUIREMENTS.md (2025-11-05)*

## 📝 NOTES

- **MetaSounds & Niagara**: Built-in to UE5.6, no separate plugin needed
- **Visual Studio Build Tools**: Sufficient for compilation
- **Full Visual Studio**: Recommended for development, but not required for automation
- **Build automation**: Fully functional with current setup

---

**Status**: ✅ **ALL REQUIRED TOOLS INSTALLED - AUTOMATION WORKING**


## 🚀 WHAT AUTOMATION CAN DO NOW

*Source: UE5-TOOLS-REQUIREMENTS.md (2025-11-05)*

## 🚀 WHAT AUTOMATION CAN DO NOW

1. ✅ Generate Visual Studio solution files automatically
2. ✅ Compile UE5 C++ project from command line
3. ✅ Clean intermediate files
4. ✅ Run Python backend tests
5. ✅ Monitor for changes and auto-rebuild

---


## 🚨 CRITICAL REQUIREMENTS - ALL MANDATORY

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 🚨 CRITICAL REQUIREMENTS - ALL MANDATORY


## 🚨 EXECUTIVE SUMMARY

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 🚨 EXECUTIVE SUMMARY

**Strategy**: Three-tier hybrid model architecture to replace both small models AND for-pay models while maintaining 300+ FPS gameplay and reducing scaling costs.

**Key Decision**: Large MoE models (DeepSeek-V3 671B) handle async high-level tasks (stories, narrative, worldbuilding) even though they're not fast enough for real-time gaming. This enables maximum quality for specialized roles while keeping real-time performance optimized.

---


### 1. Audio System (VA-002, VA-003, VA-004) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 1. Audio System (VA-002, VA-003, VA-004) ✅
**Documents**: 9 architecture files
- MetaSounds dynamic soundscape
- 4-tier dialogue priority
- Weather audio layering
- Zone-based ambient triggers
- Performance: 0.97ms CPU, 140MB memory


## 1. COMPREHENSIVE MODEL TYPE REQUIREMENTS

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 1. COMPREHENSIVE MODEL TYPE REQUIREMENTS

The SRL→RLVR solution MUST properly train models for EVERY specific role in the game:


## 1. CORE VISION

*Source: Requirements.md (2025-11-04)*

## 1. CORE VISION


## 1. DAY/NIGHT TRANSITION ENHANCEMENT

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## 1. DAY/NIGHT TRANSITION ENHANCEMENT


## 1. OVERVIEW

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 1. OVERVIEW


## 1. TERRAIN SYSTEM

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

## 1. TERRAIN SYSTEM


## 1. THREE-TIER MODEL ARCHITECTURE

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 1. THREE-TIER MODEL ARCHITECTURE


### 1.1 Personality Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.1 Personality Models
**Training Requirements:**
- **Emotions**: Understand and generate appropriate emotional responses
- **Expressions**: Facial expression mapping based on emotions
- **Actions**: Personality-driven action selection
- **Inherent Traits**: Core personality characteristics (aggression, intelligence, charisma, survival instincts, faction loyalty, personal goals)
- **Dynamic Adaptation**: Adjust behavior based on player interactions

**Training Data Sources:**
- Monster species lore
- Character stat definitions
- Behavioral pattern examples
- Historical interaction logs


### 1.1 Purpose

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 1.1 Purpose
Create a comprehensive multi-language speech system that enhances immersion and gameplay through:
- Creature-specific languages (vampires, werewolves, etc.)
- Made-up languages for music/soundtracks (copyright-free)
- Real languages for cultural immersion (Italian, French, Spanish)
- Language as gameplay mechanic (ancient artifacts, languages of power)
- Easy-to-use settings system
- In-game feedback collection


### 1.1 Tier Classification: Gold, Silver, Bronze

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 1.2 Facial Expression Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.2 Facial Expression Models
**Training Requirements:**
- **Emotion Mapping**: Map emotions to facial expressions
- **Body Language Integration**: Coordinate with body language systems
- **Context Awareness**: Expressions must match dialogue and actions
- **Personality Variation**: Different personalities show emotions differently

**Training Data Sources:**
- Facial expression libraries
- Emotion-action correlation data
- Personality-expression mapping
- Game-specific expression requirements


### 1.2 Key Principles

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 1.2 Key Principles
- **Immersion First**: Every scene should feel realistic and engaging
- **Multi-Sensory**: Engage as many senses as possible (audio, visual, tactile)
- **Consistency**: Languages must be authentic and consistent
- **Gameplay Integration**: Languages are not just flavor, they're mechanics
- **Accessibility**: Settings must be easy to use, not overwhelming
- **Feedback Loop**: Player feedback improves the system continuously

---


### 1.3 Building Generation Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.3 Building Generation Models
**Training Requirements:**
- **Exterior Generation**: Buildings, streets, city layouts
- **Interior Generation**: Apartments, morgues, labs
- **Architectural Styles**: Consistent with game world aesthetic
- **Day/Night Variations**: Different interiors for day vs. night worlds
- **Environmental Storytelling**: Buildings tell stories through design

**Training Data Sources:**
- Architectural style guides
- Building type specifications
- City layout patterns
- Environmental storytelling requirements


### 1.4 Animal Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.4 Animal Models
**Training Requirements:**
- **Behavior Patterns**: Natural animal behaviors (bears, mountain lions, sharks, etc.)
- **Day vs. Night**: Different animals in different worlds
- **Terrain-Specific**: Animals appropriate to geography (mountains, ocean, plains)
- **Interaction Logic**: How animals interact with player and monsters

**Training Data Sources:**
- Animal behavior databases
- Terrain-specific animal lists
- Game world context
- Interaction scenario examples


### 1.5 Plant Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.5 Plant Models
**Training Requirements:**
- **Flora Generation**: Plants appropriate to terrain and season
- **Ecosystem Integration**: Plants work within biome systems
- **Seasonal Variations**: Plants change with seasons (Fall colors, Winter bare, Spring growth, Summer full)
- **Environmental Impact**: Plants affect gameplay (cover, resources, atmosphere)

**Training Data Sources:**
- Flora databases by biome
- Seasonal variation data
- Ecosystem interaction patterns
- Game-specific plant requirements


### 1.6 Tree Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.6 Tree Models
**Training Requirements:**
- **Tree Generation**: Appropriate to terrain and season
- **Environmental Sounds**: Trees make sounds (groan in wind, etc.)
- **Visual Impact**: Trees contribute to atmosphere
- **Gameplay Elements**: Trees as cover, landmarks, resources

**Training Data Sources:**
- Tree species databases
- Seasonal variation data
- Sound effect requirements
- Gameplay integration needs


### 1.7 Sound Models

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 1.7 Sound Models
**Training Requirements:**
- **Building Sounds**: Creaks, rumbles, mechanical sounds
- **Animal Sounds**: All animal vocalizations (cats meow, etc.)
- **Environmental Sounds**: Trees groaning, wind, water
- **Vehicle Sounds**: Cars rumbling, sirens
- **Background Ambience**: Insects, distant conversations, plates clinking
- **Music Generation**: Eerie tracks, high energy, jump scare emphasis, contextual music

**Training Data Sources:**
- Sound effect libraries
- Music style guides
- Environmental sound requirements
- Game-specific audio needs

---


## 10. COST TARGETS

*Source: Requirements.md (2025-11-04)*

## 10. COST TARGETS


## 10. MIGRATION STRATEGY

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 10. MIGRATION STRATEGY


### 10.1 Phase 1: Foundation (Weeks 1-2)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 10.1 Phase 1: Foundation (Weeks 1-2)
- Stand up EKS with L4 and A10G node groups
- Deploy vLLM and TensorRT-LLM infrastructure
- Implement router/orchestrator with three-tier routing
- Baseline latency tests for all tiers


### 10.2 Phase 2: Training (Weeks 3-6)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 10.2 Phase 2: Training (Weeks 3-6)
- Train Gold tier models (3B-8B) with SRL→RLVR
- Train Silver tier models (7B-13B) with SRL→RLVR
- Set up DeepSeek-V3 Bronze tier infrastructure
- Implement MCP servers (Storyteller, Cybersecurity, Admin)


### 10.3 Phase 3: Deployment (Weeks 7-10)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 10.3 Phase 3: Deployment (Weeks 7-10)
- Deploy Gold tier for real-time NPCs
- Deploy Silver tier for interactive NPCs
- Deploy Bronze tier for async narrative generation
- Integrate with game engine (decoupled architecture)


### 10.4 Phase 4: Optimization (Weeks 11-12)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 10.4 Phase 4: Optimization (Weeks 11-12)
- Implement speculative decoding
- Optimize KV cache management
- Set up nightly distillation (Bronze → Silver → Gold)
- Performance tuning and cost optimization

---


## 11. IMPLEMENTATION PRIORITIES

*Source: Requirements.md (2025-11-04)*

## 11. IMPLEMENTATION PRIORITIES


## 11. SUCCESS CRITERIA

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 11. SUCCESS CRITERIA


### 11.1 Performance

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 11.1 Performance
- ✅ Gold tier: p95 < 16ms per token (real-time NPCs)
- ✅ Silver tier: p95 80-250ms (interactive NPCs)
- ✅ Bronze tier: Async processing, quality over speed
- ✅ Game frame rate: 300+ FPS maintained


### 11.2 Quality

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 11.2 Quality
- ✅ Output quality matches or exceeds for-pay models on specialized tasks
- ✅ Non-AI detectable output (human evaluation)
- ✅ Guardrails enforced (zero violations)
- ✅ Player satisfaction metrics maintained


### 11.3 Cost

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 11.3 Cost
- ✅ Training costs within budget ($8.6k-$32k one-time for Bronze)
- ✅ Inference costs 10-50× lower than for-pay models
- ✅ Break-even achieved within 3-6 months
- ✅ Scaling costs predictable and manageable


### 11.4 Reliability

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 11.4 Reliability
- ✅ 99.9% uptime for Gold tier
- ✅ Graceful degradation on failures
- ✅ Automatic failover to backups
- ✅ Zero game-breaking incidents

---


## 12. MANDATORY ENFORCEMENT

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 12. MANDATORY ENFORCEMENT


## 12. SUCCESS METRICS

*Source: Requirements.md (2025-11-04)*

## 12. SUCCESS METRICS


### 12.1 No Exceptions

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 12.1 No Exceptions
- ❌ NO using for-pay models for tasks Bronze tier can handle
- ❌ NO blocking operations in Gold tier
- ❌ NO large models in real-time path
- ❌ NO static training examples
- ❌ NO skipping quality control


### 12.2 All Rules Apply

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


## 13. REFERENCES

*Source: Requirements.md (2025-11-04)*

## 13. REFERENCES


## 14. SRL→RLVR TRAINING SYSTEM REQUIREMENTS

*Source: Requirements.md (2025-11-04)*

## 14. SRL→RLVR TRAINING SYSTEM REQUIREMENTS

**Status**: Production-Ready Architecture  
**Last Updated**: 2025-11-03  
**Reference**: `Global-Docs/SRL-RLVR-TRAINING-SYSTEM-COMPLETE.md`


### 14.1 Overview

*Source: Requirements.md (2025-11-04)*

### 14.1 Overview

The SRL→RLVR Training System is a comprehensive framework for training small language models using Google's Supervised Reinforcement Learning (SRL) followed by Reinforcement Learning with Verifiable Rewards (RLVR). This system enables fine-tuning models on domain-specific tasks using AI-generated expert demonstrations and outcome-based rewards.

**Key Benefits:**
- Two-Stage Training: SRL provides dense step-wise supervision, RLVR refines with outcome-based rewards
- Dynamic Example Generation: Three-model collaboration continuously generates high-quality training examples
- Model Selection: Intelligent routing selects optimal models for specific responsibilities
- Stability: KL divergence penalties prevent catastrophic forgetting
- Verification: Built-in validation ensures training quality


### 14.10 Verification and Quality Assurance

*Source: Requirements.md (2025-11-04)*

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


### 14.2 Core Components Required

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

### 14.6 Configuration Requirements

**Configuration File**: `configs/srl_rlvr_training.yaml`

**Required Sections:**
- SRL configuration (learning_rate, kl_penalty_weight, max_kl, reward_norm_method, batch_size, epochs)
- RLVR configuration (learning_rate, use_ppo, clip_epsilon, value_coef, entropy_coef, gamma, epochs)
- Collaboration configuration (cloud_llm_model, num_examples_per_request, max_regeneration_attempts, min_verification_score)
- Model selection configuration (cost_weight, performance_weight, update_frequency_days)


### 14.7 Integration Requirements

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

### 14.9 Security and Compliance

**Required Security Measures:**
- API keys stored securely (environment variables or secrets manager)
- Data privacy (PII redaction if needed)
- Model security (output validation to prevent injection attacks)
- Access control (restrict training operations to authorized users)
- Audit logging (log all training operations for compliance)


## 2. DECOUPLING STRATEGY: FRAME RATE vs LLM UPDATES

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 2. DECOUPLING STRATEGY: FRAME RATE vs LLM UPDATES


## 2. DYNAMIC TRAINING REQUIREMENTS

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 2. DYNAMIC TRAINING REQUIREMENTS


## 2. GAME CONCEPT: "THE BODY BROKER"

*Source: Requirements.md (2025-11-04)*

## 2. GAME CONCEPT: "THE BODY BROKER"


## 2. MULTI-LANGUAGE SPEECH SYSTEM REQUIREMENTS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 2. MULTI-LANGUAGE SPEECH SYSTEM REQUIREMENTS


## 2. VOICE/AUDIO SYSTEM

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## 2. VOICE/AUDIO SYSTEM


## 2. WEATHER SYSTEM

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

## 2. WEATHER SYSTEM


### 2. Weather System (WS-001, WS-002) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 2. Weather System (WS-001, WS-002) ✅
**Documents**: 2 architecture files
- WeatherManager C++ architecture
- 15 weather states
- Niagara particle systems
- Performance: 3.5ms GPU


### 2.1 Critical Architecture Pattern

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 2.1 Language Types

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 2.1 Language Types

#### 2.1.1 Creature Languages (Made-Up)
**Required Languages:**
- **Vampire Language (Volkh)**: Sibilants, fricatives, "dark" vowels, reflects hierarchy and ritual
- **Werewolf Language (Lycan)**: Guttural sounds, growling sounds, pack dynamics
- **Zombie Language**: Decayed, simplified version of common
- **Ghoul Language**: Guttural, hunger-focused
- **Lich Language**: Ancient, ritualistic, power-focused
- **Other Monster Languages**: Extensible for future creatures

**Characteristics:**
- Each language has unique phoneme inventory
- Grammar rules specific to creature culture
- Vocabulary reflects creature priorities (hunting, hierarchy, ritual, etc.)
- Consistent application across all game interactions

#### 2.1.2 Real Languages (Cultural Immersion)
**Required Languages:**
- **Italian**: For Light-side characters, cultural scenes
- **French**: For Light-side characters, cultural scenes
- **Spanish**: For raps, music, cultural scenes
- **Common**: Universal language all characters understand

**Characteristics:**
- Authentic pronunciation and grammar
- Cultural context awareness
- Regional variations (dialects) where appropriate
- Integration with cultural storytelling

#### 2.1.3 Music Languages (Made-Up, Copyright-Free)
**Purpose**: Create original music and lyrics without copyright concerns

**Requirements:**
- Phoneme-based generation for lyrics
- Melodic patterns that match creature/character themes
- No recognizable linguistic structure (to avoid copyright)
- Procedural generation for variety
- Integration with MetaSound system

**Use Cases:**
- Bar singers in scenes
- Background music with vocals
- Ritual chants
- Ambient environmental audio

#### 2.1.4 Language of Power (Gameplay Mechanic)
**Purpose**: Ancient artifacts, scrolls, magical language that affects gameplay

**Requirements:**
- Words and sentences cause in-game effects
- Deciphering mechanics (player learns language over time)
- Integration with spell/ability system
- Ancient scrolls contain power words
- Translation mechanics for discovery

**Gameplay Integration:**
- Finding artifacts unlocks language fragments
- Learning language enables new abilities
- Incorrect pronunciation causes failure
- Mastery unlocks advanced powers


### 2.1 Never Static Examples

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 2.1 Never Static Examples
**CRITICAL**: Training examples must NEVER be static.

**Requirements:**
- **Continuous Improvement**: Each training run must look for new and better ways to create examples
- **Technology Advancement**: As technology grows, training capabilities must grow
- **Problem Evolution**: Training must adapt to new problem types and scenarios
- **Innovation**: Always seek novel approaches to example generation

**Implementation:**
- Three-model collaboration continuously improves example generation methods
- Research new training techniques as they emerge
- Experiment with different example formats and structures
- Analyze training effectiveness and iterate


### 2.2 Core Language System Architecture

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 2.2 Core Language System Architecture

#### 2.2.1 Language Definition Module
**Required Components:**
- Language metadata (name, type, family, culture)
- Phoneme inventory (sounds used in language)
- Grammar rules (word order, morphology, syntax)
- Lexicon (vocabulary, root words, affixes)
- Prestige dialect (standard version)
- Seed words (initial vocabulary)
- AI model hints (generation guidance)

**Data Structure:**
```python
class LanguageDefinition:
    name: str
    language_type: Enum  # Monster, Human, Ancient, Ritual
    language_family: str
    culture: str
    phoneme_inventory: PhonemeInventory
    grammar_rules: GrammarRules
    prestige_dialect: str
    seed_words: List[str]
    level: int  # Complexity/understanding level
    ai_model_hints: str
```

#### 2.2.2 Phoneme Generator Module
**Purpose**: Generate consistent sound inventories for each language

**Requirements:**
- Base phoneme set (IPA symbols)
- Phoneme distribution (vowels, consonants, unique sounds)
- Phonotactics (sound combination rules)
- Stress patterns
- Creature-specific constraints:
  - Vampire: Sibilants (s, z, sh, zh), fricatives (f, v), dark vowels (ɔ, ʌ)
  - Werewolf: Guttural (k, g, x), growling (ʁ), avoid labials if snout-like
  - Lich: Ancient, ritualistic sounds
  - Zombie: Decayed, simplified phonemes

#### 2.2.3 Morphology/Grammar Generator Module
**Purpose**: Define grammatical rules for each language

**Requirements:**
- Word order (SVO, SOV, VSO, etc.)
- Morphological type (agglutinative, fusional, isolating)
- Grammatical categories (cases, tenses, gender, number)
- Agreement rules (subject-verb, noun-adjective)
- Creature-specific grammar:
  - Vampire: Elaborate noun cases for hierarchy
  - Werewolf: Complex verb conjugation for aggression levels
  - Lich: Ritualistic grammatical structures

#### 2.2.4 Lexicon Generator Module
**Purpose**: Create and manage vocabulary

**Requirements:**
- Root words from seed words
- Derivational morphology (prefixes, suffixes, infixes)
- Compounding (combining root words)
- Semantic domains (culture-specific vocabulary)
- Loanwords (borrowed words from other languages)
- Dynamic expansion (AI generates new words based on context)

**Semantic Focus Areas:**
- Vampire: Lineage, rituals, seduction, hierarchy
- Werewolf: Hunting, pack dynamics, territory, aggression
- Lich: Power, ritual, death, knowledge
- Zombie: Hunger, decay, basic needs

#### 2.2.5 Sentence Generator Module
**Purpose**: Construct grammatically correct sentences

**Requirements:**
- Parse tree generation from grammar rules
- Word selection from lexicon
- Morphological inflection
- Word order application
- Context-aware generation
- Emotion/tone integration

#### 2.2.6 Dialect Generator Module
**Purpose**: Create regional/social variations

**Requirements:**
- Phonological shifts (pronunciation variations)
- Lexical variation (different words for same concept)
- Grammatical simplification/complication
- Cultural influences (contact with other languages)
- Geographic distribution
- Social class variations

#### 2.2.7 Translation/Interpretation Module
**Purpose**: Translate between languages and provide context

**Requirements:**
- Translation database (all language pairs)
- Meaning storage (contextual meanings, cultural nuances)
- Translation accuracy based on player skill
- Interpretation (contextual information, hidden meanings)
- Cultural nuance detection
- Real-time translation for player understanding

**Player Learning Mechanics:**
- Partial understanding based on skill level
- Language learning through:
  - Finding artifacts/scrolls
  - Interacting with native speakers
  - Using magical artifacts
  - Reading ancient texts
- Skill progression affects translation quality

#### 2.2.8 AI Model Integration Module
**Purpose**: Integrate small-medium AI models for dynamic generation

**Model Architecture:**
- Transformer models (GPT-2, distilled versions) for generation
- RNNs/LSTMs/GRUs for sequential generation
- Fine-tuned for language generation and translation

**Training Data:**
- Seed data (hand-crafted examples)
- Real-world language corpora
- Game transcripts (collected during gameplay)
- SRL→RLVR training integration

**AI Tasks:**
- Lexicon expansion (generate new words)
- Sentence generation (contextually appropriate)
- Dialect drift (language evolution over time)
- Dynamic translation (neologisms, idioms)
- Procedural lore crafting (create ancient languages)

**Model Integration:**
- Use existing SRL→RLVR training system
- Gold tier (3B-8B) for real-time generation
- Silver tier (7B-13B) for complex dialogue
- Bronze tier (671B MoE) for expert language creation

#### 2.2.9 Language of Power Module
**Purpose**: Gameplay mechanic for magical language

**Requirements:**
- Base languages (monster or real languages)
- Magical syntax rules
- Gameplay functions (spells, abilities)
- Translation from artifacts to usable language
- Pronunciation accuracy affects power
- Mastery unlocks advanced abilities

**Example Mechanics:**
- Simple fire spell: "volkh-kru 'incendio'" (blood-words 'fire')
- Powerful necromancy: "volkh-kru 'vita' 'mortis'" (blood-words 'life' 'death')
- Incorrect pronunciation = spell failure
- Correct pronunciation = spell success with power scaling


### 2.2 Dynamic Rules Integration

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 2.2 Dynamic Rules Integration
**Requirements:**
- **Versioned Rules**: Training must use current dynamic rules version
- **Rule Updates**: When rules update, models must be re-trained with new rules
- **Rule Compliance**: All training examples must comply with current rules
- **Rule Evolution**: Training system must handle rule changes gracefully

---


### 2.2 Implementation Requirements

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 2.3 Integration Requirements

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 2.3 Integration Requirements

#### 2.3.1 Dialogue System Integration
**Required Features:**
- Text-to-Speech (TTS) for all languages
- Subtitles in player's chosen language
- Original language display option
- Keyword highlighting (in-game meaning callouts)
- Language-specific voice characteristics
- Emotion/tone integration

**TTS Requirements:**
- Modular TTS systems per language
- Customizable voice banks for creatures
- Phoneme-based synthesis for made-up languages
- Real-time generation or pre-generation
- Quality vs. performance optimization

#### 2.3.2 Audio System Integration
**Required Features:**
- Audio middleware integration (Wwise, FMOD)
- Real-time playback support
- Adaptive soundscapes
- Synchronization with lip-sync
- Layered audio (background music, dialogue, effects)
- Music language integration

**MetaSound Integration:**
- Procedural music generation
- Language-based musical patterns
- Real-time audio mixing
- Environmental audio layers

#### 2.3.3 NPC System Integration
**Required Features:**
- NPCs speak their native language to each other
- Leader NPCs use "poor common" (broken common language)
- Dynamic language switching based on context
- Language affects NPC relationships
- Understanding language unlocks dialogue options
- Partial understanding mechanics

**Example Scenarios:**
- Monster gang in the Dark: Monsters speak native language, leader speaks poor common
- Bar scene: Singer uses music language, patrons speak real languages
- Ancient artifact discovery: Player must decipher language of power

#### 2.3.4 Gameplay Integration
**Required Features:**
- Language learning as progression mechanic
- Artifact/scroll discovery unlocks language fragments
- Language mastery enables new abilities
- Language affects NPC interactions
- Translation puzzles
- Language-based quests

**Learning Progression:**
- Beginner: Basic words, simple phrases
- Intermediate: Full sentences, complex grammar
- Advanced: Nuances, idioms, cultural context
- Master: Perfect understanding, ability to speak


### 2.4 Consistency & Quality Requirements

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 2.4 Consistency & Quality Requirements

#### 2.4.1 Consistency Requirements
- Phonological rules applied consistently
- Grammar rules applied consistently
- Lexicon consistency checks
- Cross-reference validation
- Lore integration verification

#### 2.4.2 Quality Requirements
- Languages feel authentic (not random gibberish)
- Cultural context accuracy
- Pronunciation guides for players
- Translation accuracy
- Voice acting quality (if applicable)

#### 2.4.3 Performance Requirements
- Real-time generation: <200ms for simple sentences
- Pre-generation: Background processing for complex content
- Caching: Frequently used phrases cached
- Streaming: Token-by-token generation for longer content
- Resource optimization: Efficient model usage

---


## 3. DAY VS. NIGHT WORLDS

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

## 3. DAY VS. NIGHT WORLDS


### 3. DAY/NIGHT SYSTEM

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

### 3. DAY/NIGHT SYSTEM

#### More Requirements.md Asks For:
- **Same Buildings, Different Interiors**: Same city, different residents (human day, monster night), completely different interiors
- **OR Dual Realities**: Normal Earth during day, monster reality at night, forced transition
- **Transition Mechanism**: Ability to leak monsters into human world, give monster families access to steal people, human criminals reverse access, player must stop actions
- **Story Teller Integration**: Equip story teller with ability to leverage transition options
- **Material Transfer**: Transition human parts to monster world, materials for drugs from monster world

#### Current Solution Has:
- Dual-world system planned (Day/Night switching)
- Global state flag (day/night)
- World switching with fade transitions
- Context-specific gameplay systems
- Lighting/shader adjustments

#### Gap:
- ❌ Transition mechanism not detailed
- ❌ No "leaking" mechanism between worlds
- ❌ No material transfer system defined
- ❌ Story teller integration not specified
- ❌ No anti-leak gameplay mechanics (player stopping leaks)

---


### 3. Facial Expression System (FE-001 through FE-005) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 3. Facial Expression System (FE-001 through FE-005) ✅
**Documents**: 6 architecture files
- 8 primary emotions
- MetaHuman integration
- Lip-sync pipeline
- Body language animation
- Performance: 1.0ms per NPC


## 3. HOSTING & DEPLOYMENT STRATEGY

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 3. HOSTING & DEPLOYMENT STRATEGY


## 3. MODEL SELECTION SYSTEM REQUIREMENTS

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 3. MODEL SELECTION SYSTEM REQUIREMENTS


## 3. SETTINGS SYSTEM REQUIREMENTS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 3. SETTINGS SYSTEM REQUIREMENTS


## 3. TECHNICAL ARCHITECTURE

*Source: Requirements.md (2025-11-04)*

## 3. TECHNICAL ARCHITECTURE


## 3. WEATHER SYSTEM

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## 3. WEATHER SYSTEM


### 3.1 Core Settings Categories

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 3.1 Core Settings Categories

#### 3.1.1 Audio Settings
**Required Controls:**
- Master volume (0.0-1.0)
- Music volume (0.0-1.0)
- Sound effects volume (0.0-1.0)
- Voice/dialogue volume (0.0-1.0)
- Audio quality presets (Low/Medium/High)
- Language preference (for TTS/subtitles)
- Subtitle language selection
- Original language display toggle

**Advanced Options:**
- Individual language volume controls
- Audio spatialization settings
- 3D audio on/off
- Audio compression settings

#### 3.1.2 Video Settings
**Required Controls:**
- Resolution (preset or custom)
- Quality presets (Low/Medium/High/Ultra)
- Window mode (Windowed/Fullscreen/Borderless)
- VSync (On/Off)
- Frame rate limit (30/60/120/Unlimited)
- Individual effects toggles:
  - Lumen (Global Illumination)
  - Nanite (Virtualized Geometry)
  - Ray Tracing
  - Shadow quality
  - Texture quality
  - Post-processing effects

**Advanced Options:**
- Custom resolution
- Aspect ratio
- HDR settings
- Color blind modes
- Motion blur toggle

#### 3.1.3 Controls Settings
**Required Controls:**
- Mouse sensitivity (0.1-10.0)
- Mouse smoothing (On/Off)
- Invert Y-axis (On/Off)
- Key bindings (customizable per action)
- Controller support (if applicable)
- Input device selection

**Advanced Options:**
- Mouse acceleration
- Dead zone settings (controller)
- Custom key bind profiles
- Macro support (if applicable)

#### 3.1.4 Accessibility Settings
**Required Controls:**
- Screen reader support
- High contrast mode
- Text scaling (UI size)
- Color blind options
- Motion sensitivity controls
- Difficulty settings
- Subtitles (always on/off/smart)

**Advanced Options:**
- Custom color schemes
- Font size adjustments
- UI element scaling
- Input assistance


### 3.1 Dynamic Model Selection

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 3.1 Dynamic Model Selection
**CRITICAL**: Model selection must be based on responsibilities and best viable self-hosted model for that job.

**Requirements:**
- **Responsibility-Based**: Model selection determined by task requirements (personality, facial, building, etc.)
- **Best Fit**: Always select the best available model for specific tasks
- **Not Arbitrary**: Selection must be data-driven, not arbitrary or static
- **Performance-Based**: Selection based on benchmarks and testing, not assumptions


### 3.1 Training & Fine-Tuning (AWS Required)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 3.2 Cost-Benefit Analysis

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 3.2 Cost-Benefit Analysis
**Requirements:**
- **New Model Evaluation**: When new models are released, perform cost-benefit analysis
- **Replacement Criteria**: Determine if new model warrants replacement of existing
- **Training Cost**: Account for training costs in replacement decision
- **Performance Gain**: Measure actual performance improvements, not just claims
- **Swap Process**: Trained new models must be swapped in when warranted

**Analysis Criteria:**
- Performance benchmarks (relevant to task)
- Resource requirements (VRAM, compute)
- Training time and cost
- Inference latency
- Quality metrics
- Cost per inference


### 3.2 Inference Hosting (Flexible)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 3.2 Settings Interface Design

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 3.2 Settings Interface Design

#### 3.2.1 Navigation Structure
**Tab-Based Navigation:**
- Audio tab
- Video tab
- Controls tab
- Accessibility tab
- AI Assist tab (if enabled)

**Progressive Disclosure:**
- Basic settings visible by default
- Advanced options in expandable sections
- "Show Advanced" toggle
- Contextual help tooltips

#### 3.2.2 Quick Presets
**Performance Presets:**
- Low Performance (optimized for weak hardware)
- Medium Performance (balanced)
- High Performance (maximum quality)
- Auto-detect (on first launch)

**Accessibility Presets:**
- Vision Accessibility (high contrast, large text)
- Motor Accessibility (reduced input requirements)
- Cognitive Accessibility (simplified UI, clear guidance)

**Cultural Presets:**
- Language preference presets
- Regional audio settings

#### 3.2.3 Real-Time Preview
**Required Features:**
- Live preview window for visual changes
- Audio test buttons for sound adjustments
- Control sensitivity test area
- Performance impact indicators
- Before/after comparison

**Implementation:**
- Preview pane shows changes immediately
- Audio test plays sample sounds
- Mouse sensitivity test area
- FPS counter during preview

#### 3.2.4 Guided Setup
**First-Time Setup:**
- Wizard on first launch
- Interactive calibration tools
- Hardware detection
- Optimal settings suggestion
- Plain language descriptions

**Calibration Tools:**
- Mouse sensitivity calibration
- Audio level calibration
- Visual quality assessment
- Performance benchmark


### 3.3 AI-Assisted Settings (Optional)

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 3.3 AI-Assisted Settings (Optional)

#### 3.3.1 Performance Monitoring
**Purpose**: Suggest optimal settings based on performance

**Requirements:**
- Monitor FPS during gameplay
- Track input latency
- Monitor hardware utilization
- Detect performance issues
- Suggest settings adjustments

**Features:**
- Real-time FPS display (optional)
- Performance warnings
- Automatic quality adjustment
- Manual optimization suggestions

#### 3.3.2 AI Settings Optimizer
**Purpose**: Intelligently adjust settings for best experience

**Requirements:**
- Only runs when explicitly enabled
- Analyzes player behavior patterns
- Suggests settings based on:
  - Hardware capabilities
  - Performance metrics
  - Player preferences
  - Gameplay patterns

**Resource Management:**
- Minimal resource usage
- Runs in background only
- Can be disabled
- Opt-in feature

#### 3.3.3 Adaptive Settings
**Purpose**: Automatically adjust based on context

**Requirements:**
- Scene complexity detection
- Dynamic quality adjustment
- Performance-based scaling
- Battery optimization (if applicable)

**Limitations:**
- Must be opt-in
- Can be disabled
- Transparent to user
- No unexpected changes


### 3.3 Continuous Model Evaluation

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 3.3 Continuous Model Evaluation
**Requirements:**
- **Regular Reviews**: Periodically evaluate all models for improvements
- **Benchmark Updates**: Update benchmarks as game evolves
- **Task-Specific Metrics**: Different metrics for different model types
- **Automated Evaluation**: System must automatically evaluate models

---


### 3.4 Settings Persistence

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 3.4 Settings Persistence

#### 3.4.1 Storage Requirements
- Local storage (config files)
- Cloud sync (optional, per-user)
- Profile support (multiple users)
- Export/import settings
- Reset to defaults

#### 3.4.2 Integration Points
- Game engine settings system
- Audio system settings
- Video rendering settings
- Input system settings
- Accessibility system settings

---


## 4. AI SYSTEM REQUIREMENTS

*Source: Requirements.md (2025-11-04)*

## 4. AI SYSTEM REQUIREMENTS


## 4. FACIAL EXPRESSIONS

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

## 4. FACIAL EXPRESSIONS


### 4. FACIAL EXPRESSIONS / BODY LANGUAGE

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

### 4. FACIAL EXPRESSIONS / BODY LANGUAGE

#### More Requirements.md Asks For:
- **Facial Emotions**: Combine with body language to influence dialogue perception
- **Influence on Communication**: Same words with different facial expression/posture read entirely differently
- **Examples**: Hostile stance with scowl and clenched teeth vs open stance with broad smile
- **Integration**: Should work with existing Personality Models for emotion

#### Current Solution Has:
- Personality Models for emotion to determine dialogue and actions
- NPC personality system
- Behavior engine

#### Gap:
- ❌ No facial expression system
- ❌ No body language system
- ❌ No visual emotion rendering
- ❌ No integration between facial expressions and dialogue perception
- ❌ No posture/stance system

---


## 4. FEEDBACK SYSTEM REQUIREMENTS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 4. FEEDBACK SYSTEM REQUIREMENTS


## 4. MODEL SELECTION & REPLACEMENT STRATEGY

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 4. MODEL SELECTION & REPLACEMENT STRATEGY


## 4. PAID MODEL FINE-TUNING REQUIREMENTS

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 4. PAID MODEL FINE-TUNING REQUIREMENTS


### 4. Terrain Ecosystem (TE-001 through TE-004) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 4. Terrain Ecosystem (TE-001 through TE-004) ✅
**Documents**: 4 architecture files
- Biome detection & transitions
- Flora HISM pooling
- Fauna AI with flocking
- Performance: 7ms total


### 4.1 Feedback Collection Points

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 4.1 Feedback Collection Points

#### 4.1.1 Trigger Points
**Automatic Triggers:**
- Post-session summary (optional)
- After major game events
- On feature first use
- Random sampling (opt-in)

**Manual Triggers:**
- Player-initiated feedback
- Bug reporting
- Suggestion submission
- Issue reporting

#### 4.1.2 Feedback Methods

**Quick Feedback:**
- Emoji reactions (👍 👎 😊 😞)
- 1-5 star ratings
- Single-click feedback buttons
- Thumbs up/down
- Quick category selection

**Detailed Feedback:**
- Optional text input
- Screenshot/video clip attachment
- Context-aware categories
- Multi-choice questions
- Open-ended responses

#### 4.1.3 Feedback Categories
**Predefined Categories:**
- Gameplay experience
- Language system quality
- Audio/video quality
- Performance issues
- Bug reports
- Feature requests
- Accessibility concerns
- Content concerns

**Context-Aware Categories:**
- Based on current game state
- Based on recent events
- Based on player actions
- Based on system performance


### 4.1 Hierarchical LLM Architecture (4-Layer System)

*Source: Requirements.md (2025-11-04)*

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


### 4.1 Replace Small Models (3B-8B)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 4.1 Replace Small Models (3B-8B)

**Decision**: **KEEP small models for Gold tier (real-time NPCs)**

**Rationale**:
- Small models (3B-8B) are the ONLY models capable of sub-16ms inference
- Large models cannot achieve real-time performance (760ms+ latency)
- Small models properly trained with SRL→RLVR can match quality of larger models for specific tasks
- Cost is minimal: $75 training, extremely low inference cost

**Action**: Train small models MORE aggressively with SRL→RLVR to maximize quality while maintaining speed.


### 4.1 Supported Providers

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 4.1 Supported Providers
**Requirements:**
- **Gemini**: Fine-tuning support through Google Cloud
- **ChatGPT**: Fine-tuning through OpenAI API
- **Anthropic Claude**: Fine-tuning through Anthropic API (when available)
- **Other Providers**: Monitor and support new fine-tuning offerings


### 4.2 Distributed LLM System

*Source: Requirements.md (2025-11-04)*

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


### 4.2 Feedback Interface Design

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 4.2 Feedback Interface Design

#### 4.2.1 UI Requirements
- Non-intrusive design
- Easy to access but not annoying
- Quick feedback options prominent
- Detailed feedback easy to find
- Clear submission confirmation

#### 4.2.2 Integration Points
- In-game overlay (hotkey accessible)
- Pause menu integration
- Main menu integration
- Post-session summary
- Contextual popups (rare, opt-in)


### 4.2 Fine-Tuning Strategy

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 4.2 Fine-Tuning Strategy
**Requirements:**
- **Always Evaluate**: Always look for fine-tuning opportunities
- **Cost-Benefit**: Evaluate fine-tuning cost vs. prompt engineering effectiveness
- **Task-Specific**: Fine-tune for specific high-value tasks
- **Quality Improvement**: Fine-tuning must provide measurable quality improvement


### 4.2 Replace Mid-Size Models (7B-13B)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 4.2 Replace Mid-Size Models (7B-13B)

**Decision**: **EVALUATE case-by-case, likely KEEP for Silver tier**

**Rationale**:
- Mid-size models provide excellent quality/latency balance
- Training cost is still reasonable ($240)
- Can handle interactive tasks that don't need frame-rate sync
- Large models too expensive and slow for this tier

**Action**: Continue using 7B-13B for Silver tier, evaluate larger models only if quality insufficient after SRL→RLVR training.


### 4.3 Feedback Storage & Usage

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 4.3 Feedback Storage & Usage

#### 4.3.1 Storage Requirements
- Local cache for immediate use
- Cloud sync for aggregation
- Privacy-focused data handling
- Anonymization options
- Data retention policies

#### 4.3.2 Data Usage

**Training Integration:**
- Feeds into SRL→RLVR training system
- Informs AI model improvements
- Language quality feedback → Language model training
- Settings feedback → Settings optimization
- Gameplay feedback → Gameplay improvements

**Analytics:**
- Player experience reports
- Performance trend analysis
- Feature usage tracking
- Quality metrics

**Development:**
- Bug tracking
- Feature prioritization
- Quality assurance
- Player satisfaction metrics

#### 4.3.3 Privacy & Compliance
- GDPR compliance
- Data anonymization
- Opt-out options
- Clear privacy policy
- User consent requirements

---


### 4.3 Integration with Training System

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 4.3 Integration with Training System
**Requirements:**
- **SRL→RLVR**: Use SRL→RLVR approach for paid model fine-tuning where applicable
- **Data Consistency**: Use same training data quality standards
- **Validation**: Validate fine-tuned models with same rigor as self-hosted models
- **Rollback**: Support rollback of fine-tuned models if issues detected


### 4.3 Model Specifications

*Source: Requirements.md (2025-11-04)*

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


### 4.3 Replace For-Pay Models

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 4.4 Prompt Engineering Fallback

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 4.4 Prompt Engineering Fallback
**Requirements:**
- **When Fine-Tuning Unavailable**: Use prompt engineering when fine-tuning not available
- **Optimization**: Continuously optimize prompts for best results
- **Template Management**: Maintain prompt templates for different tasks
- **A/B Testing**: Test different prompt strategies

---


### 4.4 State Management

*Source: Requirements.md (2025-11-04)*

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


## 5. ENHANCED TERRAIN ECOSYSTEMS

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## 5. ENHANCED TERRAIN ECOSYSTEMS


### 5. Immersive Features (IM-001, IM-002, IM-003) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 5. Immersive Features (IM-001, IM-002, IM-003) ✅
**Documents**: 3 architecture files
- Camera post-process effects
- Environmental storytelling
- Accessibility features
- Performance: 1.8ms total


## 5. MCP SERVER INTEGRATION

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 5. MCP SERVER INTEGRATION


## 5. MODEL PERFORMANCE TRACKING REQUIREMENTS

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 5. MODEL PERFORMANCE TRACKING REQUIREMENTS


## 5. PLATFORM & DEPLOYMENT

*Source: Requirements.md (2025-11-04)*

## 5. PLATFORM & DEPLOYMENT


## 5. TECHNICAL IMPLEMENTATION REQUIREMENTS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 5. TECHNICAL IMPLEMENTATION REQUIREMENTS


## 5. VOICE & AUDIO SYSTEM

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

## 5. VOICE & AUDIO SYSTEM


### 5. VOICES / AUDIO SYSTEM

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

### 5. VOICES / AUDIO SYSTEM

#### More Requirements.md Asks For:
- **Voice Support**: Audio system with voice generation
- **Monster Voices**: Different sounds for different monsters, personality impacts voice
- **AI Voice Quality**: Ensure voices don't sound like AI models
- **Environmental Sounds**: Buildings creak, cars rumble, cats meow, creatures make sounds, trees groan in wind
- **Music System**: 
  - Eerie and barely audible
  - Loud and high energy
  - Emphasize jump scares
  - Radio music when turned on
  - NOT constantly running soundtracks
- **Background Ambiance**: Insects, vehicles, sirens, people talking (unclear words), plates/glasses clinking at restaurants
- **Realistic Soundscapes**: City always has background noise

#### Current Solution Has:
- MetaSounds mentioned in UE5 requirements (not detailed)
- Audio settings in requirements (master volume, music volume, sound effects volume, voice volume)

#### Gap:
- ❌ No voice generation system
- ❌ No monster-specific voice system
- ❌ No environmental sound system
- ❌ No music system implementation
- ❌ No background ambiance system
- ❌ No audio integration with gameplay (jump scares, radio, etc.)

---


### 5.1 Integration with Existing Systems

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 5.1 Integration with Existing Systems

#### 5.1.1 SRL→RLVR Training System Integration
**Required Integration:**
- Language generation feedback → Model training
- Translation quality feedback → Model improvement
- Player language learning data → Training examples
- Settings optimization feedback → Model training
- Feedback data → Training data generation

**Data Flow:**
- Feedback via Kinesis streams (partitioned by user_id)
- Model improvement pipeline
- Batch processing for efficiency
- Real-time training updates (nightly)

#### 5.1.2 AI Inference Service Integration
**Required Integration:**
- Language generation requests
- Translation requests
- TTS generation requests
- Settings optimization requests
- Feedback processing requests

**Model Routing:**
- Gold tier (3B-8B) for real-time language generation
- Silver tier (7B-13B) for complex dialogue
- Bronze tier (671B MoE) for expert language creation
- Cost-benefit routing for optimal selection

#### 5.1.3 Game Engine Integration
**Required Integration:**
- Unreal Engine 5 dialogue system
- MetaSound audio system
- Settings UI (UMG)
- Feedback UI (UMG)
- Save game system


### 5.1 Performance Metrics

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 5.1 Performance Metrics
**Requirements:**
- **Latency Tracking**: Track inference latency (p50, p95, p99)
- **Quality Metrics**: Track output quality (task-specific metrics)
- **Error Rates**: Track error and failure rates
- **Resource Usage**: Track VRAM, compute, memory usage
- **Cost Tracking**: Track cost per inference for paid models


### 5.1 Required MCP Servers

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 5.2 Performance Requirements

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 5.2 Performance Requirements

#### 5.2.1 Language Generation Performance
- Real-time generation: <200ms for simple sentences
- Pre-generation: Background processing for complex content
- Caching: 80%+ cache hit rate for common phrases
- Streaming: Token-by-token for longer content
- Resource usage: Efficient model utilization

#### 5.2.2 Settings System Performance
- Settings changes: <100ms application
- Preview rendering: Real-time
- Settings save/load: <50ms
- Cloud sync: Background, non-blocking

#### 5.2.3 Feedback System Performance
- Feedback submission: <200ms
- Screenshot capture: <500ms
- Data upload: Background, non-blocking
- Analytics processing: Async, batched


### 5.2 Weakness Detection

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 5.2 Weakness Detection
**Requirements:**
- **Continuous Monitoring**: Monitor all models continuously
- **Anomaly Detection**: Detect performance degradation or quality issues
- **Trend Analysis**: Identify trends indicating weakness
- **Alert System**: Alert when weakness detected
- **Prevention**: Replace models BEFORE weaknesses become game issues


### 5.3 Multi-Model Evaluation System

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 5.3 Multi-Model Evaluation System
**Requirements:**
- **Three-Model Collaboration**: Use three models to determine evaluation criteria
- **Benchmark Selection**: Models determine which benchmarks are relevant
- **Research Integration**: Research model strengths and weaknesses
- **Testing**: Test models to verify performance claims
- **Decision Making**: Models help make replacement decisions


### 5.3 Scalability Requirements

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 5.3 Scalability Requirements

#### 5.3.1 Language System Scalability
- Support for 10+ languages (extensible)
- 1000+ vocabulary words per language
- Dynamic lexicon expansion
- Efficient storage and retrieval

#### 5.3.2 Settings System Scalability
- Support for 100+ settings
- Multiple user profiles
- Cloud sync for millions of users
- Efficient storage format

#### 5.3.3 Feedback System Scalability
- Handle 1000+ feedback submissions per day
- Efficient storage and retrieval
- Real-time analytics processing
- Batch training data generation

---


### 5.4 Performance History

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 5.4 Performance History
**Requirements:**
- **Historical Tracking**: Track performance over time
- **Comparison**: Compare current vs. historical performance
- **Regression Detection**: Detect performance regressions
- **Improvement Tracking**: Track improvements from training

---


## 6. IMMERSIVE FEATURES

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

## 6. IMMERSIVE FEATURES


### 6. Integration (INT-001) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 6. Integration (INT-001) ✅
**Documents**: 1 architecture file
- GameEventBus subsystem
- 23 event types
- Cross-system integration
- Performance: 0.1ms per event


## 6. INTEGRATION REQUIREMENTS

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 6. INTEGRATION REQUIREMENTS


## 6. MONETIZATION SYSTEM

*Source: Requirements.md (2025-11-04)*

## 6. MONETIZATION SYSTEM


## 6. PERFORMANCE OPTIMIZATION REQUIREMENTS

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 6. PERFORMANCE OPTIMIZATION REQUIREMENTS


## 6. QUALITY ASSURANCE REQUIREMENTS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 6. QUALITY ASSURANCE REQUIREMENTS


### 6.1 AWS Deployment

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 6.1 AWS Deployment
**Requirements:**
- **All Training in AWS**: All model training must run in AWS (local dev computer cannot handle model inference)
- **SageMaker Integration**: Use AWS SageMaker for training
- **Step Functions**: Use AWS Step Functions for workflow orchestration
- **ECR**: Use AWS ECR for container registry
- **S3**: Use AWS S3 for data storage
- **DynamoDB**: Use AWS DynamoDB for metadata
- **CloudWatch**: Use AWS CloudWatch for monitoring


### 6.1 Free Tier (Freemium Model)

*Source: Requirements.md (2025-11-04)*

### 6.1 Free Tier (Freemium Model)

**Requirements:**
- **Upfront Free Portion**: Significant enough to demonstrate value
- **Limited Customization**: Prevents abuse, drives subscription desire
- **Conversion Focus**: Designed to make players want more
- **Quality Gate**: Free experience must be polished, not crippled demo


### 6.1 Language System QA

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 6.1 Language System QA
- Consistency checks (automated)
- Translation accuracy validation
- Pronunciation guide accuracy
- Cultural context verification
- Voice acting quality (if applicable)


### 6.1 Real-Time Path (Gold Tier) - Sub-16ms Target

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 6.2 Existing System Integration

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 6.2 Existing System Integration
**Requirements:**
- **Model Management System**: Integrate with existing model management
- **AI Inference Service**: Models must work with inference service
- **Orchestration Service**: Models must integrate with orchestration
- **State Management**: Models must integrate with game state


### 6.2 Interactive Path (Silver Tier) - 80-250ms Target

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 6.2 Interactive Path (Silver Tier) - 80-250ms Target

**Framework**: vLLM with PagedAttention  
**Quantization**: INT8, FP8, or AWQ  
**Optimizations**:
- Mixed precision inference
- Prompt caching for common patterns
- Speculative decoding optional (3B draft for 8-13B targets)
- Continuous batching with moderate batch sizes


### 6.2 Settings System QA

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 6.2 Settings System QA
- Settings persistence testing
- Cloud sync testing
- Performance impact testing
- Accessibility compliance testing
- Cross-platform compatibility (if applicable)


### 6.2 Subscription System

*Source: Requirements.md (2025-11-04)*

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

*Source: Requirements.md (2025-11-04)*

### 6.3 Ambassador/Coupon System

**Requirements:**
- **Coupon Codes**: Discount codes for subscriptions
- **Ambassador Program**: Referral tracking and rewards
- **Code Management**: Admin system for generating/managing codes
- **Tracking**: Analytics on code usage and conversion


### 6.3 Async Path (Bronze Tier) - Seconds Acceptable

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 6.3 Async Path (Bronze Tier) - Seconds Acceptable

**Optimizations**:
- Heavy batching for maximum throughput
- Tensor parallel + expert parallel for MoE models
- Spot instances for cost optimization
- Nightly distillation: Bronze traces → Silver adapters → Gold adapters

---


### 6.3 Feedback System QA

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 6.3 Feedback System QA
- Data collection accuracy
- Privacy compliance validation
- Analytics accuracy
- Training data quality validation

---


### 6.3 Testing Integration

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 6.3 Testing Integration
**Requirements:**
- **Comprehensive Testing**: Rigorous testing throughout (cutting edge, no safety net)
- **Integration Testing**: Test integration with all systems
- **Performance Testing**: Test performance under load
- **Quality Testing**: Test output quality

---


### 6.4 Cost Per User Calculations

*Source: Requirements.md (2025-11-04)*

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


## 7. COST PROJECTIONS & SCALING

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 7. COST PROJECTIONS & SCALING


## 7. DOCUMENTATION REQUIREMENTS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 7. DOCUMENTATION REQUIREMENTS


## 7. SUCCESS CRITERIA

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 7. SUCCESS CRITERIA


### 7. Testing (TEST-001) ✅

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### 7. Testing (TEST-001) ✅
**Documents**: 1 architecture file
- Integration test suite
- Performance validation
- Edge case handling
- Complete coverage strategy

---


## 7. USER EXPERIENCE REQUIREMENTS

*Source: Requirements.md (2025-11-04)*

## 7. USER EXPERIENCE REQUIREMENTS


### 7.1 Settings Page

*Source: Requirements.md (2025-11-04)*

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


### 7.1 Training Costs

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 7.1 Training Costs

| Model Tier | Size | Instance | Training Time | Cost per Run |
|------------|------|----------|---------------|--------------|
| **Gold** | 3B-8B | g6.12xlarge | 5-10 hours | $75 |
| **Silver** | 7B-13B | p4d.24xlarge | 10-20 hours | $240 |
| **Bronze** | 671B MoE | p5.48xlarge (multi-node) | 1-3 days | $8,640-$32,400 |


### 7.1 Training Success

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 7.1 Training Success
- ✅ All model types successfully trained using SRL→RLVR
- ✅ Training examples continuously improve
- ✅ Models meet performance requirements
- ✅ Models meet quality requirements


### 7.1 User Documentation

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 7.1 User Documentation
- Language learning guide
- Settings optimization guide
- Feedback submission guide
- Accessibility features guide


### 7.2 Developer Documentation

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 7.2 Developer Documentation
- Language system architecture
- Settings system API
- Feedback system API
- Integration guides
- Testing procedures

---


### 7.2 Helpful Indicators & Guidance

*Source: Requirements.md (2025-11-04)*

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


### 7.2 Inference Costs (Self-Hosted)

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 7.2 Inference Costs (Self-Hosted)

**Per 1M Tokens** (approximate, depends on quantization and sequence length):
- **Gold (3B on L4, 4-bit)**: $0.6-$1.0 per 1M tokens
- **Silver (7B-8B on L4/A10G, INT8)**: $1.4-$3.3 per 1M tokens
- **Silver (13B on A10G, INT8)**: $3.1-$6.7 per 1M tokens
- **Bronze (DeepSeek-V3)**: Highly variable, batch heavily for efficiency


### 7.2 Model Selection Success

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 7.2 Model Selection Success
- ✅ Dynamic selection based on responsibilities
- ✅ Cost-benefit analysis performed for new models
- ✅ Models replaced when warranted
- ✅ Selection not arbitrary or static


### 7.3 Comparison to For-Pay Models

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 7.3 Comparison to For-Pay Models

**For-Pay Model Costs** (per 1M tokens):
- GPT-5 Pro: ~$10-$50 per 1M tokens
- Claude 4.5 Sonnet: ~$3-$15 per 1M tokens
- Gemini 2.5 Pro: ~$1.25-$10 per 1M tokens

**Self-Hosted Savings**:
- Gold tier: **10-50× cheaper** than for-pay
- Silver tier: **3-10× cheaper** than for-pay
- Bronze tier: **Break-even after ~860K-32M tokens** (one-time training cost)


### 7.3 Paid Model Success

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 7.3 Paid Model Success
- ✅ Fine-tuning opportunities identified and evaluated
- ✅ Fine-tuned models provide quality improvements
- ✅ Prompt engineering optimized when fine-tuning unavailable


### 7.4 Performance Tracking Success

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 7.4 Performance Tracking Success
- ✅ All models continuously monitored
- ✅ Weaknesses detected before becoming issues
- ✅ Models replaced proactively
- ✅ Performance history maintained

---


### 7.4 Scaling Strategy

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


## 8. CONTENT RATING & SAFETY

*Source: Requirements.md (2025-11-04)*

## 8. CONTENT RATING & SAFETY


## 8. MANDATORY ENFORCEMENT

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

## 8. MANDATORY ENFORCEMENT


## 8. QUALITY CONTROL REQUIREMENTS

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 8. QUALITY CONTROL REQUIREMENTS


## 8. SUCCESS METRICS

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 8. SUCCESS METRICS


### 8.1 Language System Metrics

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 8.1 Language System Metrics
- Player language learning progression
- Translation accuracy (player-reported)
- Language immersion ratings
- Language-based gameplay engagement
- Music language copyright compliance (100%)


### 8.1 No Exceptions

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 8.1 No Exceptions
**CRITICAL**: There are NO exceptions to these requirements.

- ❌ NO training using old methods
- ❌ NO static examples
- ❌ NO arbitrary model selection
- ❌ NO ignoring paid model fine-tuning opportunities
- ❌ NO skipping performance tracking


### 8.1 Non-AI Detectable Output

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 8.2 All Rules Apply

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### 8.2 All Rules Apply
**CRITICAL**: All rules in `/all-rules` must be followed, including:
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

**END OF MODEL TRAINING REQUIREMENTS**


### 8.2 Guardrails Enforcement

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


### 8.2 Settings System Metrics

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 8.2 Settings System Metrics
- Settings adjustment frequency
- Performance improvement from settings
- Accessibility feature usage
- User satisfaction with settings UI
- AI-assisted settings adoption (if enabled)


### 8.3 Feedback System Metrics

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### 8.3 Feedback System Metrics
- Feedback submission rate
- Feedback quality (detailed vs. quick)
- Response time to feedback
- Training data generation from feedback
- Player satisfaction with feedback system

---


### 8.3 Quality Metrics

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

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


## 9. IMPLEMENTATION PRIORITIES

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

## 9. IMPLEMENTATION PRIORITIES


## 9. INTEGRATION WITH EXISTING SYSTEMS

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

## 9. INTEGRATION WITH EXISTING SYSTEMS


## 9. PERFORMANCE REQUIREMENTS

*Source: Requirements.md (2025-11-04)*

## 9. PERFORMANCE REQUIREMENTS


### 9.1 SRL→RLVR Training System

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 9.1 SRL→RLVR Training System

**Requirement**: ALL models MUST be trained using SRL→RLVR approach
- ✅ Three-model collaboration generates expert trajectories
- ✅ SRL stage: Step-wise supervision
- ✅ RLVR stage: Outcome-based fine-tuning
- ✅ Dynamic example generation (never static)
- ✅ Performance tracking and weakness detection


### 9.2 Model Management System

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 9.2 Model Management System

**Integration**:
- Model registry for all three tiers
- Version tracking and rollback capability
- A/B testing infrastructure
- Canary deployments


### 9.3 AI Inference Service

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 9.3 AI Inference Service

**Integration**:
- Unified API for all tiers
- Intelligent routing based on SLA requirements
- Load balancing across model instances
- Health checks and failover


### 9.4 Orchestration Service

*Source: MODEL-ARCHITECTURE-REQUIREMENTS.md (2025-11-05)*

### 9.4 Orchestration Service

**Integration**:
- Hierarchical pipeline still applies
- Bronze tier handles Layer 4 (coordination)
- Silver tier handles Layer 3 (interaction)
- Gold tier handles Layer 2 (customization)

---


### AI Integration Architecture

*Source: Requirements.md (2025-11-04)*

### AI Integration Architecture
- **Inference Servers**: Separate from game servers (DO NOT run on game servers)
- **Serving Stack**: 
  - Development: Ollama
  - Production: vLLM or TensorRT-LLM (better concurrency)
- **Model Management**: LoRA adapters on shared base models (10-50x more efficient than separate models)

---


### Break-Even Analysis

*Source: Requirements.md (2025-11-04)*

### Break-Even Analysis
- Must be profitable at target subscription price
- Account for customer acquisition costs
- Consider lifetime value vs. daily costs

---


## COMPLETE SYSTEM SUMMARY

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

## COMPLETE SYSTEM SUMMARY


### Content Moderation

*Source: Requirements.md (2025-11-04)*

### Content Moderation
- **Multi-Layer Approach**:
  1. Generation-at-source constraints (train models to avoid prohibited content)
  2. Real-time AI filtering (input + output)
  3. Human review queue for edge cases
  4. Player reporting system


### Core Gameplay Loop

*Source: Requirements.md (2025-11-04)*

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


### Core Principle

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### Core Principle
**ALL model training MUST use the SRL→RLVR training solution. NO exceptions. NO alternative training methods.**


### Cost Optimization Goals

*Source: Requirements.md (2025-11-04)*

### Cost Optimization Goals
- **77% cost reduction** via hybrid local/cloud approach (vs. cloud-only)
- **Aggressive caching**: 80%+ of content served from cache
- **Economies of scale**: Cost per user decreases with player count


### Cost Per User Per Day

*Source: Requirements.md (2025-11-04)*

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


### Critical (Core Gameplay Impact)

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

### Critical (Core Gameplay Impact)
1. **Weather System** - Affects atmosphere, gameplay, immersion
2. **Day/Night Transition Mechanism** - Core to game concept
3. **Voice/Audio System** - Essential for dialogue and immersion


### Critical Gaps Identified:

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### Critical Gaps Identified:
1. **Weather System**: 0% implemented - completely missing
2. **Audio System**: 10% implemented - MetaSounds mentioned but no details
3. **Facial Expressions**: 0% implemented - not in current solution
4. **Terrain Ecosystems**: 30% implemented - basic procedural exists, needs enhancement
5. **Day/Night**: 40% implemented - planned but needs enhancement
6. **Immersive Features**: 20% implemented - basic features exist


### Current Progress Estimate:

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### Current Progress Estimate:
- **Core Systems**: ~45% complete
- **More Requirements**: ~15% complete (basic terrain, partial day/night)
- **Overall Project**: ~35% complete

---


### Deployment Architecture

*Source: Requirements.md (2025-11-04)*

### Deployment Architecture
- **Game Servers**: CPU-bound, handle game logic
- **Inference Cluster**: GPU-bound, separate infrastructure
- **Scalability**: Horizontal scaling for inference nodes

---


## DETAILED GAP ANALYSIS

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

## DETAILED GAP ANALYSIS


### DN-001: TimeOfDayManager Core System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### DN-001: TimeOfDayManager Core System
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 8-10 hours

**Description**:
- Create TimeOfDayManager C++ singleton class
- Implement time progression logic
- Build subscriber registration system
- Create ITimeAwareInterface for time-sensitive systems
- Implement save/load functionality

**Acceptance Criteria**:
- [ ] TimeOfDayManager singleton accessible globally
- [ ] Time progresses according to TimeScale setting
- [ ] Subscribers can register/unregister dynamically
- [ ] Time state saves and loads correctly
- [ ] Events broadcast at configurable intervals

**Dependencies**: GE-001 (UE5 Project Setup)  
**Watchdog**: All compilation commands >5 seconds  
**Testing**: Unit tests for time progression, subscriber system

---


### DN-002: Visual Controllers (Sky, Light, Fog)

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### DN-002: Visual Controllers (Sky, Light, Fog)
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 10-12 hours

**Description**:
- Configure Sky Atmosphere component
- Create sun/moon rotation curves
- Build MPC_TimeOfDay Material Parameter Collection
- Implement light intensity/color interpolation
- Create volumetric fog control system

**Acceptance Criteria**:
- [ ] Sky Atmosphere responds to time changes
- [ ] Sun/moon position and intensity change smoothly
- [ ] MPC parameters update in real-time
- [ ] Volumetric fog density/color changes with time
- [ ] No visual artifacts during transitions

**Dependencies**: DN-001  
**Watchdog**: All blueprint compilation  
**Testing**: Visual validation, performance profiling

---


### DN-003: Blueprint API & Integration

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### DN-003: Blueprint API & Integration
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 8-10 hours

**Description**:
- Create Blueprint API for designer accessibility
- Build debug visualization tools
- Optimize performance (event throttling)
- Integration testing with existing systems
- Documentation and usage examples

**Acceptance Criteria**:
- [ ] Designers can control time via Blueprint
- [ ] Debug tools show time state visually
- [ ] Event broadcasting optimized (no frame spikes)
- [ ] Integrates with existing Game Engine systems
- [ ] Documentation complete with examples

**Dependencies**: DN-001, DN-002  
**Watchdog**: All testing commands  
**Testing**: Integration tests, performance validation

---


## EXECUTIVE SUMMARY

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

## EXECUTIVE SUMMARY

After reviewing `More Requirements.md` and current solution capabilities, significant gaps exist in:
1. **Weather System** - Completely missing
2. **Facial Expressions/Body Language** - Not implemented
3. **Voice/Audio System** - Not implemented (MetaSounds mentioned but not detailed)
4. **Enhanced Terrain Ecosystems** - Basic procedural exists but lacks rich ecosystem features
5. **Day/Night Transition Mechanism** - Planned but not detailed
6. **Immersive Features** - Not fully developed

---


### FE-001: Core Emotion System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### FE-001: Core Emotion System
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 16-18 hours

**Description**:
- Create ExpressionManagerComponent
- Implement emotional state blending
- Build transition interpolation system
- Create expression preset data tables
- Implement personality model interface
- Event broadcasting setup

**Acceptance Criteria**:
- [ ] Component manages emotional state
- [ ] Emotions blend smoothly
- [ ] Transitions interpolate correctly
- [ ] Expression presets load from data tables
- [ ] Personality interface works
- [ ] Events broadcast on expression changes

**Dependencies**: GE-001, (Personality Models exist)  
**Watchdog**: Expression system compilation  
**Testing**: Emotion blending tests, state validation

---


### FE-002: MetaHuman Integration

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### FE-002: MetaHuman Integration
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 20-24 hours

**Description**:
- Configure Control Rig for facial control
- Map emotional states to blend shapes
- Implement eye tracking system
- Build gaze targeting logic
- Create blink and micro-expression system
- Test across multiple MetaHuman faces

**Acceptance Criteria**:
- [ ] Control Rig controls facial features
- [ ] Blend shapes map to emotions correctly
- [ ] Eyes track targets naturally
- [ ] Gaze targeting works smoothly
- [ ] Blinking and micro-expressions occur
- [ ] Works across different MetaHuman faces

**Dependencies**: FE-001  
**Watchdog**: MetaHuman compilation  
**Testing**: Visual validation, cross-character testing

---


### FE-003: Lip-Sync & Audio Integration

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### FE-003: Lip-Sync & Audio Integration
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 12-16 hours

**Description**:
- Integrate with Audio System
- Implement phoneme extraction from dialogue
- Build jaw animation from audio analysis
- Create lip-sync data caching system
- Test synchronization accuracy
- Optimize performance

**Acceptance Criteria**:
- [ ] Lip-sync matches dialogue audio
- [ ] Phonemes extracted correctly
- [ ] Jaw animation looks natural
- [ ] Data caching improves performance
- [ ] Sync accuracy > 90%
- [ ] Performance within budget (0.3ms CPU per character)

**Dependencies**: FE-001, FE-002, VA-003  
**Watchdog**: Lip-sync testing  
**Testing**: Accuracy validation, performance profiling

---


### FE-004: Body Language System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### FE-004: Body Language System
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 16-20 hours

**Description**:
- Create body language animation blueprint
- Build gesture library (hand movements, posture)
- Implement additive animation layers
- Create personality-driven idle variations
- Build procedural hand positioning
- Test animation blending

**Acceptance Criteria**:
- [ ] Animation blueprint layers blend correctly
- [ ] Gestures trigger appropriately
- [ ] Idle variations change with personality
- [ ] Hand positioning looks natural
- [ ] No animation popping or artifacts
- [ ] Performance acceptable

**Dependencies**: FE-001  
**Watchdog**: Animation compilation  
**Testing**: Animation blending tests, visual validation

---


### FE-005: Integration & Polish

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### FE-005: Integration & Polish
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 10-12 hours

**Description**:
- Integrate with dialogue system
- Connect to personality models
- Blueprint API for designers
- Performance optimization
- Debug visualization tools
- Documentation and examples

**Acceptance Criteria**:
- [ ] Facial expressions trigger during dialogue
- [ ] Personality influences expressions
- [ ] Blueprint API functional
- [ ] Performance optimized
- [ ] Debug tools show expression state
- [ ] Documentation complete

**Dependencies**: FE-001, FE-002, FE-003, FE-004  
**Watchdog**: Integration testing  
**Testing**: Comprehensive integration tests

---


## FINDINGS

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

## FINDINGS


### Full Visual Studio 2022

*Source: UE5-TOOLS-REQUIREMENTS.md (2025-11-05)*

### Full Visual Studio 2022
**Why**: Better IntelliSense, debugging, and development experience

**How to Install**:
1. Download: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++" workload
3. Include:
   - MSVC v143 - VS 2022 C++ x64/x86 build tools
   - Windows 10/11 SDK (latest)
   - C++ CMake tools
   - IntelliSense support

**Benefit**: 
- Better code completion
- Integrated debugging
- Easier navigation

---


### Future Platform Considerations

*Source: Requirements.md (2025-11-04)*

### Future Platform Considerations
- Other platforms deferred until after successful Steam launch
- Architecture designed for eventual portability


### Game Engine

*Source: Requirements.md (2025-11-04)*

### Game Engine
- **Primary Engine**: Unreal Engine 5 (latest version)
- **Deployment**: Steam + PC Desktop only (simplifies multi-platform)
- **Rationale**: UE5 provides Lumen, Nanite, MetaSounds, PCG framework - essential for horror atmosphere


### Game Features

*Source: Requirements.md (2025-11-04)*

### Game Features
- **Horror Elements**: Jump scares, chases, tense atmosphere
- **Progression System**: Street-level → Empire builder
- **Social Mechanics**: House politics, alliances, betrayals
- **Resource Management**: Body parts, equipment, supernatural powers
- **Combat & Stealth**: Fight cops, avoid monsters, survive deals
- **Narrative Emergence**: AI-driven story based on player choices


### Game Metrics

*Source: Requirements.md (2025-11-04)*

### Game Metrics
- **Player Retention**: Day 7 retention >40%
- **Subscription Conversion**: Free-to-paid conversion >5%
- **Player Satisfaction**: Net Promoter Score >50
- **Content Quality**: Player reports of repetitive/broken content <5%

---


### Geography Considerations

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### Geography Considerations
- **Mountain Setting**: Deep forests, glens, wildfires, creatures of the deep, bears, mountain lions, magical streams, fairies, river lords, elementals, caves
- **Ocean Shore Setting**: Deep sea creatures, sharks, giant squid, hurricanes, tsunamis, fog, sea breezes, fishing adventures, pirate attacks, giant spiders
- **Plains Setting**: Rolling hills, plains, woods, roaming monsters, big cats, wolves, snakes, tornados, floods, rivers
- **Combined Settings**: Unique combinations (tropic rainforests, deserts, etc.)

**Requirement**: All player worlds must use the SAME terrain configuration initially.

---


### High Priority (Enhances Experience)

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

### High Priority (Enhances Experience)
4. **Facial Expressions/Body Language** - Affects NPC interaction quality
5. **Enhanced Terrain Ecosystems** - Rich world features


### Identified Risks:

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### Identified Risks:
1. **Performance**: Multiple systems running simultaneously
   - Mitigation: Strict performance budgets defined
   
2. **Integration Complexity**: 6 new systems integrating with existing
   - Mitigation: Event-driven architecture, clear contracts
   
3. **Timeline**: 18-24 weeks is significant
   - Mitigation: Phased approach, parallel development tracks

4. **Fake Code**: Need to verify existing implementation
   - Mitigation: `/test-comprehensive` protocol, peer review

---


### IM-001: Foundation (Camera Effects, Haptics, Settings)

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### IM-001: Foundation (Camera Effects, Haptics, Settings)
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 16-20 hours

**Description**:
- Create ImmersionManagerSubsystem
- Build post-process camera effects material
- Implement haptic feedback system
- Create accessibility settings framework
- Build settings UI panel

**Acceptance Criteria**:
- [ ] Subsystem accessible globally
- [ ] Camera effects render correctly
- [ ] Haptics trigger appropriately
- [ ] Settings framework functional
- [ ] Settings UI displays and saves

**Dependencies**: GE-001  
**Watchdog**: Immersion system testing  
**Testing**: Camera effects validation, haptics testing

---


### IM-002: Environmental Storytelling

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### IM-002: Environmental Storytelling
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 16-20 hours

**Description**:
- Create environmental detail actor system
- Build weather-reactive props library
- Implement time-based object states
- Create creature track/trail system
- Build narrative object placement tools

**Acceptance Criteria**:
- [ ] Detail actors respond to weather
- [ ] Props react appropriately
- [ ] Object states change with time
- [ ] Creature tracks render
- [ ] Placement tools work for designers

**Dependencies**: IM-001, WS-004, DN-002, TE-004  
**Watchdog**: Storytelling system testing  
**Testing**: Visual validation, tool usability

---


### IM-003: Accessibility Features

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### IM-003: Accessibility Features
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 16-20 hours

**Description**:
- Enhanced subtitle system with customization
- Color-blind shader implementations
- Alternative audio cue system
- Configurable effect intensity controls
- Performance scaling automation

**Acceptance Criteria**:
- [ ] Subtitles customizable and clear
- [ ] Color-blind modes work correctly
- [ ] Audio cues provide alternatives
- [ ] Effect intensity adjustable
- [ ] Performance scaling automatic

**Dependencies**: IM-001, VA-004  
**Watchdog**: Accessibility testing  
**Testing**: Accessibility validation, user testing

---


### Immediate (This Session):

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### Immediate (This Session):
1. ✅ Use `/test-comprehensive` to verify existing code (identify fake/mock)
2. ✅ Begin documenting actual vs planned implementation
3. ⏳ Continue building following `/all-rules`


### Immediate Actions Required

*Source: MODEL-TRAINING-REQUIREMENTS.md (2025-11-02)*

### Immediate Actions Required
1. **Audit**: Find and identify ALL existing training/fine-tuning tasks
2. **Scrap**: Any models that have been "fine-tuned" using incorrect methods must be scrapped and re-trained
3. **Switch**: ALL untrained models must use the SRL→RLVR solution
4. **Replace**: Any training tasks using old methods must be replaced with new SRL→RLVR tasks

---


### Implementation

*Source: Requirements.md (2025-11-04)*

### Implementation
- **Rating Enforcement**: Tag-based system, pre-generation validation
- **Monitoring**: Continuous quality checks, alert on degradation
- **Transparency**: Acknowledge limitations, clear communication

---


### INT-001: Central Event Bus System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### INT-001: Central Event Bus System
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 8-10 hours

**Description**:
- Create GameEventBus subsystem
- Implement event delegates for all systems
- Build subscription/unsubscription system
- Create event broadcasting infrastructure
- Documentation and examples

**Acceptance Criteria**:
- [ ] Event bus accessible globally
- [ ] All systems can publish/subscribe
- [ ] Events broadcast efficiently
- [ ] No memory leaks from subscriptions
- [ ] Documentation complete

**Dependencies**: GE-001  
**Watchdog**: Event bus testing  
**Testing**: Event propagation tests, memory profiling

---


## INTEGRATION TASKS

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## INTEGRATION TASKS


## KEY DELIVERABLES

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

## KEY DELIVERABLES

1. **`docs/GAP-ANALYSIS-MORE-REQUIREMENTS.md`**
   - Comprehensive comparison of requirements vs current state
   - Priority ranking and recommendations

2. **`docs/solutions/MORE-REQUIREMENTS-SOLUTION.md`**
   - Complete architecture for all 6 systems
   - Integration points and dependencies
   - Timeline: 18-24 weeks

3. **`docs/tasks/MORE-REQUIREMENTS-TASKS.md`**
   - 27 actionable tasks
   - Acceptance criteria for each
   - Estimated hours: 342-460

4. **Updated `docs/tasks/GLOBAL-MANAGER.md`**
   - Integrated new tasks into build order
   - Added Phase 4 & 5 for More Requirements

---


### Key Documents

*Source: Requirements.md (2025-11-04)*

### Key Documents
- **[RECOMMENDATIONS.md](./RECOMMENDATIONS.md)**: Detailed technical recommendations, feasibility assessments, architecture decisions
- **[FEASIBILITY-ASSESSMENT.md](./FEASIBILITY-ASSESSMENT.md)**: Original feasibility analysis
- **[BODY-BROKER-TECHNICAL-ASSESSMENT.md](./BODY-BROKER-TECHNICAL-ASSESSMENT.md)**: Game-specific technical assessment
- **[DISTRIBUTED-LLM-ARCHITECTURE.md](./DISTRIBUTED-LLM-ARCHITECTURE.md)**: LLM infrastructure architecture


### Key Innovation

*Source: Requirements.md (2025-11-04)*

### Key Innovation
This system combines **hierarchical LLM pipelines** with **specialized model orchestration** to create content far beyond what humans can build alone, enabling emergent gameplay and narrative experiences that are unique to each player.

---


### Long Term (Following Phases):

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### Long Term (Following Phases):
1. Complete More Requirements systems (18-24 weeks)
2. Integration testing across all systems
3. Performance optimization
4. Accessibility features
5. Polish and refinement

---


### Medium Priority (Polish)

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

### Medium Priority (Polish)
6. **Immersive Features** - Multi-sensory enhancement

---


### Milestones Completed: 19

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

### Milestones Completed: 19
**Duration**: This session  
**Architecture Documents**: 20 complete systems

---


### Model Consultations

*Source: Requirements.md (2025-11-04)*

### Model Consultations
All technical decisions validated through consultation with:
- Claude Sonnet 4.5
- GPT-5-Pro
- Gemini 2.5 Pro
- DeepSeek V3.1 Terminus
- Grok 4

---

---


### Multi-Sensory Immersion

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### Multi-Sensory Immersion
- **High-End Visualizations**: Visual quality to impact other senses
- **Audio Integration**: Great audio integration
- **Visceral Responses**: 
  - Seeing putrid trash with flies = visceral sense of stink
  - Night insect bite with welt + visuals/audio = dizziness/weakness
  - Careful: Don't go too far (no vomiting - queasy is fine)

**Requirement**: System must create immersive experiences through visual and audio cues.

---

*Full content from original "More Requirements.md" - see ../More Requirements.md for complete details*


### Music System

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### Music System
- **Mood Setting**: Eerie and barely audible, loud and high energy
- **Jump Scare Emphasis**: Music for jump scares
- **Contextual**: When radio turns on, etc.
- **Realistic**: NOT constantly running soundtracks
- **Background Noise**: City always has background (insects, vehicles, sirens, people talking, plates/glasses clinking, etc.)

**Requirement**: Sound models must be trained for all sounds, music tracks, and voice generation.

---


## NEXT STEPS

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

## NEXT STEPS

1. Collaborate with 5 top models to validate this analysis
2. Use complex-solution process to design comprehensive solutions
3. Break down into actionable tasks
4. Integrate into current solution architecture
5. Test comprehensively against requirements


## OBJECTIVES COMPLETED

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

## OBJECTIVES COMPLETED


### Optimization Strategies

*Source: Requirements.md (2025-11-04)*

### Optimization Strategies
- **Aggressive Caching**: 80%+ cache hit rate target
- **Predictive Generation**: Generate content before player arrives
- **LOD Systems**: AI LOD (simpler AI for distant NPCs)
- **Streaming**: Response streaming for dialogue

---


### Phase 1: Foundation (Months 1-3)

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### Phase 1: Foundation (Months 1-3)
- Core language definition system
- Basic creature languages (Vampire, Werewolf)
- Common language support
- Basic settings system
- Feedback collection infrastructure


### Phase 1: Foundation (Months 1-6)

*Source: Requirements.md (2025-11-04)*

### Phase 1: Foundation (Months 1-6)
- ✅ Unreal Engine 5 integration
- ✅ Basic procedural generation
- ✅ Cloud LLM integration (prove gameplay)
- ✅ Core game mechanics
- ✅ Steam deployment setup


### Phase 2: AI Integration (Months 6-12)

*Source: Requirements.md (2025-11-04)*

### Phase 2: AI Integration (Months 6-12)
- ✅ Local LLM infrastructure (Ollama)
- ✅ LoRA adapter system
- ✅ Basic hierarchical pipeline (L1-L2)
- ✅ NPC dialogue system (L3)
- ✅ 100-player test


### Phase 2: Expansion (Months 4-6)

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### Phase 2: Expansion (Months 4-6)
- Additional creature languages
- Real languages (Italian, French, Spanish)
- Language of power gameplay mechanics
- Advanced settings features
- Feedback analysis and usage


### Phase 3: Advanced Features (Months 12-24)

*Source: Requirements.md (2025-11-04)*

### Phase 3: Advanced Features (Months 12-24)
- ✅ Full hierarchical system (L1-L4)
- ✅ Monster-specific LLMs
- ✅ Orchestration layer
- ✅ Subscription/monetization
- ✅ Settings & UX polish
- ✅ 1000+ player test


### Phase 3: Enhancement (Months 7-9)

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### Phase 3: Enhancement (Months 7-9)
- Music language system
- Advanced translation features
- AI-assisted settings (if approved)
- Feedback training integration
- Quality optimization


### Phase 4: Polish (Months 10-12)

*Source: MULTI-LANGUAGE-SPEECH-SYSTEM-REQUIREMENTS.md (2025-11-05)*

### Phase 4: Polish (Months 10-12)
- Full language consistency validation
- Settings UI polish
- Feedback system refinement
- Performance optimization
- Documentation completion

---

**Document Status**: Complete and ready for implementation  
**Next Steps**: Generate solution architecture and begin Phase 1 implementation


### Phase 4: Production Scale (Months 24-36)

*Source: Requirements.md (2025-11-04)*

### Phase 4: Production Scale (Months 24-36)
- ✅ Multi-GPU cluster
- ✅ Production-grade infrastructure
- ✅ Full optimization
- ✅ Launch preparation

---


### Primary Platforms

*Source: Requirements.md (2025-11-04)*

### Primary Platforms
- **Steam**: Primary distribution platform
- **PC Desktop**: Windows 10/11 native builds
- **Rationale**: Simplifies deployment, focuses resources, avoids console certification complexity


## PRIORITY RANKING

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

## PRIORITY RANKING


## PROGRESS UPDATE

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

## PROGRESS UPDATE

**Project Completion**: ~35% overall
- Core Gaming Systems: ~45%
- More Requirements Features: ~15%
- Integration & Testing: ~20%
- Documentation: ~60%

**Next Milestone Target**: Verify existing implementation, begin foundation systems

---

**Status**: ✅ **ANALYSIS & DESIGN COMPLETE - READY FOR IMPLEMENTATION**


### Project Goal

*Source: Requirements.md (2025-11-04)*

### Project Goal
Build an AI-driven gaming core using **Unreal Engine 5** that leverages hierarchical, distributed LLM architectures to create truly dynamic game experiences where:
- Every player has a completely unique experience
- NPCs respond dynamically to player actions (not pre-written scripts)
- Content is generated procedurally with AI assistance
- The system can anticipate player reactions based on interactions
- The game adapts in real-time to player choices and behaviors


### Rating System

*Source: Requirements.md (2025-11-04)*

### Rating System
- **Target**: M (Mature) rating
- **Guardrails Required**:
  - Suicide prevention (never promote)
  - Real-world violence prevention (never encourage real killings)
  - Content filtering based on rating level
  - Age-appropriate content enforcement


### Rating Target

*Source: Requirements.md (2025-11-04)*

### Rating Target
- **ESRB**: M (Mature)
- **Content**: Violence, horror, mature themes
- **Never Allowed**: Suicide promotion, real-world killing encouragement

---


## RECOMMENDATIONS

*Source: GAP-ANALYSIS-MORE-REQUIREMENTS.md (2025-11-05)*

## RECOMMENDATIONS

1. **Build Weather System First**: Most impactful missing feature
2. **Enhance Day/Night Transition**: Core gameplay mechanic needs detail
3. **Implement Audio System**: Essential for horror atmosphere
4. **Add Facial Expressions**: Enhances NPC interactions significantly
5. **Enrich Terrain Ecosystems**: Adds world depth
6. **Polish Immersive Features**: Final layer of engagement

---


### Requirements

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### Requirements
- **Personality Models**: Already have personality models for emotions, dialogue, actions
- **Facial Emotions**: Must consider facial emotions - humans are very sensitive to facial expressions
- **Body Language Integration**: Combined with body language, heavily influences perception
- **Example**: Same sentence with hostile stance/scowl vs. open stance/smile reads completely differently

**Requirement**: Facial expression models must be trained to understand emotions, expressions, actions, inherent traits.

---


## RISKS & MITIGATION

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

## RISKS & MITIGATION


### Scalability

*Source: Requirements.md (2025-11-04)*

### Scalability
- **Concurrent Players**: Design for 1000+ concurrent players
- **NPC Generation**: 10-25 concurrent AI-driven NPCs per shard
- **Content Generation**: Predictive pre-generation to mask latency


### Seasonal Requirements

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### Seasonal Requirements
- **Four Seasons**: Fall (beautiful colors), Winter (bitter cold, white landscapes), Spring (vibrant reawakening), Summer (hot and humid)
- **Weather Events**:
  - Storms, ice, snow (driving restrictions, slick surfaces)
  - Flash floods, thunderstorms, mud puddles (Spring)
  - Windy conditions (Fall)
  - Intense heat, cloudless days (Summer)
  - Unpredictable changes (hot to cold in Spring/Fall, sunshine to thunderstorm in Summer)

---


### Short Term (Next Sessions):

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

### Short Term (Next Sessions):
1. Begin More Requirements Foundation tasks
   - INT-001: Central Event Bus System
   - DN-001: TimeOfDayManager Core
   - DN-002: Visual Controllers

2. Verify existing implementation
   - Run comprehensive tests
   - Identify and fix any fake/mock code
   - Validate what's actually built


## SUCCESS METRICS

*Source: MILESTONE-MORE-REQUIREMENTS-ANALYSIS.md (2025-11-05)*

## SUCCESS METRICS

- ✅ Gap analysis complete and validated
- ✅ Solution architecture comprehensive and production-ready
- ✅ Tasks broken down with clear acceptance criteria
- ✅ Integration points defined
- ✅ Timeline established
- ✅ Ready for implementation

---


## SUMMARY

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## SUMMARY

**Total Tasks**: 27  
**Total Estimated Hours**: 342-460 hours  
**Critical Path**: DN-001 → DN-002 → VA-001 → WS-001 → TE-001 → Integration

**Priority Order**:
1. Foundation: Day/Night, Event Bus
2. Core Systems: Audio, Weather
3. Enhancement: Facial Expressions, Terrain Ecosystems
4. Polish: Immersive Features, Accessibility

**Next Steps**:
1. Add these tasks to GLOBAL-MANAGER.md
2. Begin implementation following /all-rules
3. Test comprehensively after each milestone
4. Update progress percentage regularly


## SYSTEMS ARCHITECTURED

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

## SYSTEMS ARCHITECTURED


## TABLE OF CONTENTS

*Source: CORE-REQUIREMENTS.md (2025-11-02)*

## TABLE OF CONTENTS

1. [Core Vision](#core-vision)
2. [Game Concept](#game-concept)
3. [Technical Architecture](#technical-architecture)
4. [AI System Requirements](#ai-system-requirements)
5. [Platform & Deployment](#platform--deployment)
6. [Monetization System](#monetization-system)
7. [User Experience Requirements](#user-experience-requirements)
8. [Content Rating & Safety](#content-rating--safety)
9. [Performance Requirements](#performance-requirements)
10. [Cost Targets](#cost-targets)

---

*Full content from original Requirements.md - see ../Requirements.md for complete details*


### Target Performance

*Source: Requirements.md (2025-11-04)*

### Target Performance
- **PC (Mid-Range)**: 60fps at 1080p Medium settings
- **PC (High-End)**: 60fps at 1440p/4K High/Ultra settings
- **AI Latency**:
  - L1/L2 generation: Sub-100ms (mostly procedural)
  - L3 dialogue: First token <200ms, streaming
  - L4 coordination: 100-300ms for plan updates


## TASK ORGANIZATION

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## TASK ORGANIZATION

Tasks organized by system priority:
1. Day/Night Transition Enhancement (Foundation)
2. Voice/Audio System
3. Weather System
4. Facial Expressions/Body Language
5. Enhanced Terrain Ecosystems
6. Immersive Features

---


### TE-001: Biome System Foundation

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### TE-001: Biome System Foundation
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 16-20 hours

**Description**:
- Create BiomeDataAsset structure
- Implement biome detection and transitions
- Build biome registry system
- Create designer-friendly biome editor
- Implement save/load for biome state
- Basic integration with World Partition

**Acceptance Criteria**:
- [ ] Biome data assets load correctly
- [ ] Biome transitions detect smoothly
- [ ] Registry tracks all biomes
- [ ] Designer editor works
- [ ] Biome state persists
- [ ] World Partition integration functional

**Dependencies**: GE-001  
**Watchdog**: Biome system compilation  
**Testing**: Biome detection tests, World Partition validation

---


### TE-002: Flora Management System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### TE-002: Flora Management System
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 20-24 hours

**Description**:
- Create FloraManager with HISM pooling
- Implement chunk-based streaming logic
- Build PCG graphs for procedural distribution
- Create LOD system for flora
- Implement wind animation integration
- Build seasonal appearance changes
- Performance optimization (culling, instancing)

**Acceptance Criteria**:
- [ ] HISM components pool correctly
- [ ] Streaming loads/unloads flora smoothly
- [ ] PCG graphs generate natural distributions
- [ ] LOD reduces complexity at distance
- [ ] Wind animates foliage appropriately
- [ ] Seasonal changes apply correctly
- [ ] Performance within budget (2ms CPU, 4ms GPU)

**Dependencies**: TE-001, WS-003 (wind integration)  
**Watchdog**: Flora system testing  
**Testing**: Streaming tests, performance profiling

---


### TE-003: Fauna System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### TE-003: Fauna System
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 20-24 hours

**Description**:
- Create FaunaSpawner system
- Implement population management
- Build creature AI behavior trees
- Create flocking/herding behaviors
- Implement predator-prey interactions
- Build time-of-day activity patterns
- Weather response behaviors
- Spawn/despawn optimization

**Acceptance Criteria**:
- [ ] Creatures spawn within population limits
- [ ] Behavior trees function correctly
- [ ] Flocking/herding looks natural
- [ ] Predator-prey interactions work
- [ ] Activity patterns match time of day
- [ ] Weather affects creature behavior
- [ ] Spawn/despawn optimized

**Dependencies**: TE-001, DN-001, WS-001  
**Watchdog**: Fauna system testing  
**Testing**: AI behavior tests, performance validation

---


### TE-004: Environmental Response & Polish

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### TE-004: Environmental Response & Polish
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 16-20 hours

**Description**:
- Integrate with Weather System
- Connect to TimeOfDayManager
- Build seasonal transition system
- Implement dynamic growth mechanics
- Create audio integration for ambient life
- Build harvesting/interaction system
- Performance profiling across biomes

**Acceptance Criteria**:
- [ ] Ecosystems respond to weather
- [ ] Time affects ecosystem state
- [ ] Seasonal transitions work smoothly
- [ ] Dynamic growth calculates correctly
- [ ] Ambient audio triggers appropriately
- [ ] Harvesting/interaction functional
- [ ] Performance acceptable across all biomes

**Dependencies**: TE-001, TE-002, TE-003, WS-004, DN-002, VA-002  
**Watchdog**: Integration testing  
**Testing**: Comprehensive ecosystem integration tests

---


### Technical Metrics

*Source: Requirements.md (2025-11-04)*

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


### TEST-001: Comprehensive Integration Testing

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### TEST-001: Comprehensive Integration Testing
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 20-30 hours

**Description**:
- Create integration test suite
- Test all system interactions
- Validate event propagation
- Performance testing with all systems active
- Edge case identification and resolution

**Acceptance Criteria**:
- [ ] All integration tests pass
- [ ] Events propagate correctly
- [ ] Performance targets met
- [ ] Edge cases handled
- [ ] Test documentation complete

**Dependencies**: All system tasks complete  
**Watchdog**: Integration testing  
**Testing**: Automated test suite, manual validation

---


## TESTING TASKS

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

## TESTING TASKS


## TOTAL ARCHITECTURE

*Source: MORE-REQUIREMENTS-COMPLETE.md (2025-11-02)*

## TOTAL ARCHITECTURE

**Systems**: 7 major systems
**Architecture Documents**: 20 complete designs
**Performance Budgets**: All defined
**Blueprint APIs**: All documented
**Integration Points**: All mapped
**Test Strategies**: All planned

---

**Status**: ✅ **MORE REQUIREMENTS ARCHITECTURE 100% COMPLETE**


### VA-001: AudioManager Core & Submix Graph

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### VA-001: AudioManager Core & Submix Graph
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 16-20 hours

**Description**:
- Create AudioManager subsystem
- Implement submix graph structure
- Build MetaSound template system
- Create spatial audio component pools
- Implement dialogue priority queue

**Acceptance Criteria**:
- [ ] AudioManager accessible as subsystem
- [ ] Submix graph routes audio correctly
- [ ] MetaSound templates work in-game
- [ ] Spatial audio pools prevent allocation spikes
- [ ] Dialogue queue handles priorities correctly

**Dependencies**: GE-001, DN-001  
**Watchdog**: All audio compilation  
**Testing**: Audio routing tests, memory profiling

---


### VA-002: Ambient & Weather Audio Integration

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### VA-002: Ambient & Weather Audio Integration
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 16-20 hours

**Description**:
- Create time-of-day ambient MetaSounds
- Build weather audio layering system
- Implement zone-based ambient triggers
- Create audio occlusion system
- Build reverb/context switching

**Acceptance Criteria**:
- [ ] Ambient audio changes with time of day
- [ ] Weather audio layers correctly
- [ ] Zone transitions trigger appropriate ambience
- [ ] Occlusion blocks sound through walls
- [ ] Reverb changes based on environment context

**Dependencies**: VA-001, DN-002, (Weather System planned)  
**Watchdog**: Audio testing commands  
**Testing**: Audio integration tests, spatial validation

---


### VA-003: Voice & Dialogue System

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### VA-003: Voice & Dialogue System
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 10-12 hours

**Description**:
- Implement dialogue playback system
- Create interrupt handling logic
- Build subtitle event broadcasting
- Generate lip-sync data pipeline
- Voice concurrency management

**Acceptance Criteria**:
- [ ] Dialogue plays with correct priority
- [ ] Interrupts work smoothly
- [ ] Subtitles display and update correctly
- [ ] Lip-sync data generated for facial system
- [ ] Multiple voices can play concurrently

**Dependencies**: VA-001  
**Watchdog**: Dialogue testing  
**Testing**: Playback tests, lip-sync accuracy validation

---


### VA-004: Audio Optimization & Polish

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### VA-004: Audio Optimization & Polish
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 8-10 hours

**Description**:
- Audio pooling optimization
- Performance profiling (CPU/Memory)
- Blueprint API finalization
- Integration testing
- Documentation

**Acceptance Criteria**:
- [ ] Audio system meets performance budget (0.8ms CPU)
- [ ] Memory usage within limits (150MB)
- [ ] Blueprint API complete and documented
- [ ] All integration tests pass
- [ ] Documentation complete

**Dependencies**: VA-001, VA-002, VA-003  
**Watchdog**: Performance testing  
**Testing**: Comprehensive performance and integration tests

---


### Voice Requirements

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### Voice Requirements
- **Monster Voices**: Different sounds for different monsters
- **Personality Impact**: How personalities impact voices
- **AI Quality**: Voices must NOT sound like they came from an AI model
- **Sound Effects**: Everything makes sounds:
  - Buildings creak
  - Cars rumble
  - Animals make sounds (cats meow, etc.)
  - Trees groan in heavy winds
  - MANY other sounds


### World Transition System

*Source: ADDITIONAL-REQUIREMENTS.md (2025-11-02)*

### World Transition System
- **Same Buildings, Different Interiors**: Same city structure, completely different residents (human vs. monster)
- **Alternative**: Similar cities with reality transitions (normal Earth by day, monster reality by night)
- **Transition Mechanics**:
  - Way to transition between versions
  - Monster leaks into human world (occasional)
  - Monster families can steal people (crime syndicates/mob style)
  - Human criminals can reverse-leak
  - Player must prevent/stop these actions
  - Story teller must leverage these options

---


### WS-001: WeatherManager Core & State Machine

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### WS-001: WeatherManager Core & State Machine
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 16-20 hours

**Description**:
- Create WeatherManager C++ class
- Implement weather state machine
- Build transition interpolation system
- Create MPC_Weather with all parameters
- Implement event broadcasting
- Create weather data assets structure

**Acceptance Criteria**:
- [ ] WeatherManager manages state correctly
- [ ] Transitions interpolate smoothly
- [ ] MPC parameters update appropriately
- [ ] Events broadcast to subscribers
- [ ] Weather data assets load and apply

**Dependencies**: GE-001, DN-001  
**Watchdog**: Weather system compilation  
**Testing**: State machine tests, transition validation

---


### WS-002: Niagara Particle Systems

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### WS-002: Niagara Particle Systems
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 20-24 hours

**Description**:
- Build Niagara rain system with GPU particles
- Create snow particle system with accumulation
- Implement fog/mist volumetric system
- Build lightning strike system
- Implement particle pooling and LOD
- Optimize particle performance

**Acceptance Criteria**:
- [ ] Rain particles render and collide correctly
- [ ] Snow accumulates on surfaces
- [ ] Fog has appropriate density variation
- [ ] Lightning strikes trigger correctly
- [ ] Particle pooling prevents allocation issues
- [ ] LOD reduces particles at distance
- [ ] Performance within budget (3ms GPU)

**Dependencies**: WS-001  
**Watchdog**: Particle system testing  
**Testing**: Visual validation, performance profiling

---


### WS-003: Material Integration (Wetness, Snow, Wind)

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### WS-003: Material Integration (Wetness, Snow, Wind)
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 16-20 hours

**Description**:
- Create wetness material function
- Build snow accumulation shader
- Implement dynamic puddle system
- Create wind-driven foliage animation
- Build cloud material with volumetrics
- Test materials across asset library

**Acceptance Criteria**:
- [ ] Surfaces show wetness from rain
- [ ] Snow accumulates realistically
- [ ] Puddles form and persist
- [ ] Foliage animates with wind
- [ ] Clouds render with volumetrics
- [ ] All materials work across asset types

**Dependencies**: WS-001  
**Watchdog**: Material compilation  
**Testing**: Visual validation across materials, performance

---


### WS-004: Weather Integration & Polish

*Source: MORE-REQUIREMENTS-TASKS.md (2025-11-05)*

### WS-004: Weather Integration & Polish
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 16-20 hours

**Description**:
- Integrate with TimeOfDayManager
- Connect to Audio System
- Build seasonal weather system
- Create weather preset library
- Performance optimization pass
- Blueprint API for designers
- Testing and bug fixing
- Documentation

**Acceptance Criteria**:
- [ ] Weather responds to time of day
- [ ] Audio layers match weather intensity
- [ ] Seasons affect weather probabilities
- [ ] Weather presets work in Blueprint
- [ ] Performance targets met
- [ ] All integration tests pass
- [ ] Documentation complete

**Dependencies**: WS-001, WS-002, WS-003, DN-002, VA-002  
**Watchdog**: Integration testing  
**Testing**: Comprehensive integration and performance tests

---



