# Story Teller Service Solution
**Service**: Continuous World Simulation & Narrative Generation  
**Date**: January 29, 2025  
**Status**: ⭐ **NEW** - Complete Architecture Design

---

## SERVICE OVERVIEW

The Story Teller is the master narrative system that:
1. **Creates the base world** (city, buildings, dungeons, sewers)
2. **Populates initial NPCs** (human and monster, all priority levels)
3. **Runs continuous background simulation** (world continues when player offline/elsewhere)
4. **Manages player narrative** (quests, progression, immersion)
5. **Ensures AI detection bypass** (deep learning filter + fine-tuning)
6. **Maintains novelty** (never boring, unique storylines, unpredictable events)
7. **Balances player power** (wins at intervals, challenges require work, bosses replaceable)

**Key Innovation**: Separate specialized service that integrates with existing 4-layer LLM system while running autonomous world simulation.

---

## ARCHITECTURE

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                  STORY TELLER CORE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ World Sim    │  │ Narrative    │  │ Event        │     │
│  │ Engine       │──│ Weaver       │──│ Generator    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│              EXISTING 4-LAYER LLM SYSTEM                     │
│  Foundation → Customization → Interaction → Coordination    │
└─────────────────────────────────────────────────────────────┘
```

### Service Boundaries

**Story Teller Responsibilities:**
- World generation (base city, buildings, dungeons)
- NPC population and initialization
- Background simulation (NPC-NPC interactions, faction dynamics)
- Narrative generation (quests, story arcs, consequences)
- Novelty enforcement (anti-repetition system)
- AI detection bypass (human-likeness pipeline)

**Integration with Existing Services:**
- **Orchestration Service**: Uses 4-layer pipeline for content generation
- **AI Inference Service**: Leverages local Ollama models + cloud LLMs
- **State Management Service**: Writes world state, reads player context
- **Learning Service**: Receives feedback to improve narrative quality
- **Game Engine Service**: Publishes world updates for rendering

---

## COMPONENT ARCHITECTURE

### Component 1: World Simulation Engine (WSE)

**Purpose**: Continuous background world state management

**Architecture Pattern**: Event-Sourcing + Actor Model

```python
class WorldSimulationEngine:
    """Runs world simulation independently of player presence"""
    
    def __init__(self):
        self.temporal_manager = TemporalOrchestrator()
        self.faction_simulator = FactionDynamicsSimulator()
        self.npc_behavior_system = NPCBehaviorSystem()
        self.economic_simulator = EconomicModel()
        self.spatial_manager = SpatialTerritoryManager()
        self.causal_chain = CausalEventChain()
```

**Model Selection**:

**Primary Models** (Background Simulation):
- **World State Predictor**: Fine-tuned `qwen2.5:7b` (local)
  - Handles multi-agent reasoning
  - Fast inference for bulk NPCs
  - Fine-tuned on urban dynamics, sociology, game theory
  
- **Faction Coordinator**: Fine-tuned `llama3.1:8b` (local)
  - Complex faction relationships
  - Long context for tracking power dynamics
  - LoRA adapter: "faction-warfare"
  
- **NPC Decision Maker**: `phi3:mini` + LoRA adapters (local)
  - Fast individual decisions
  - Monster-type-specific LoRAs
  - 10-20 concurrent NPCs per GPU

**Integration with 4-Layer System**:
```python
async def generate_base_world(self, request: WorldGenRequest):
    """Use Layer 1 (Foundation) for base generation"""
    foundation = await self.orchestration_service.layer1.generate_base(
        request=WorldBaseRequest(
            seed=request.seed,
            biome="urban_city",
            size=request.city_size
        )
    )
    
    # Use Layer 2 (Customization) for details
    customized = await self.orchestration_service.layer2.customize_world(
        foundation=foundation,
        request=request
    )
    
    return customized
```

**State Management**:
```python
# PostgreSQL: Canonical world state
class WorldStateSchema:
    """Persistent world state"""
    factions: Dict[str, Faction]  # Power, resources, territories
    npcs: Dict[str, NPC]  # Status, relationships, goals
    locations: Dict[str, Location]  # Control, resources, threats
    events: List[WorldEvent]  # Historical timeline
    
# Redis: Hot state cache
class HotWorldCache:
    """Active simulation state"""
    active_events: Dict[str, Event]  # Current hour simulation
    player_proximity: Dict[str, List[str]]  # NPCs near players
    conflict_queue: List[Conflict]  # Pending resolution
    
# Vector DB: Historical patterns
class HistoricalMemory:
    """Semantic search for patterns"""
    faction_behaviors: VectorStore  # Past behaviors
    npc_personality_embeddings: VectorStore
    event_outcome_clusters: VectorStore
```

---

### Component 2: Narrative Weaver (NW)

**Purpose**: Transforms simulation events into compelling, human-like narratives

**Key Challenge**: MUST pass AI detection - never feel AI-generated

**Architecture**:
```python
class NarrativeWeaver:
    """Generates human-like narratives from simulation events"""
    
    def __init__(self):
        self.story_arc_generator = StoryArcGenerator()
        self.quest_synthesizer = QuestSynthesizer()
        self.consequence_mapper = ConsequenceMapper()
        self.pacing_controller = PacingController()
        self.novelty_filter = NoveltyEnforcer()
        self.ai_detection_bypass = HumanLikenessSystem()  # ⭐ Critical
```

**Model Selection**:

**Primary Models** (Narrative Generation):
- **Quest Generator**: Fine-tuned `mistral:7b` + "quest-generation" LoRA (local)
  - Side quests, ambient narratives
  - Fine-tuned on 50k unique story permutations
  - Dataset: Cyberpunk, noir, body horror fiction
  
- **Story Arc Generator**: `gpt-5-pro` (cloud) + Fine-tuned `llama3.1:8b` (local)
  - Major quest lines and boss narratives
  - Cloud for quality, local for speed/scale
  - Fallback chain: GPT-5 → Llama (local)
  
- **Narrative Validator**: `claude-sonnet-4.5` (cloud)
  - Coherence checking
  - Plot hole detection
  - Character consistency validation

**AI Detection Bypass Pipeline**:
```python
class HumanLikenessSystem:
    """Multi-stage humanization pipeline"""
    
    async def humanize_narrative(self, ai_text: str, context: dict) -> str:
        """Transform AI text to human-like narrative"""
        
        # Stage 1: Stylistic variation
        styled = await self.stylistic_variator.apply(
            ai_text,
            styles=['hard_boiled', 'stream_of_consciousness', 'unreliable_narrator'],
            weights=self.random_weight_vector()
        )
        
        # Stage 2: Imperfection injection
        imperfect = await self.imperfection_filter.apply(
            styled,
            techniques=[
                'sentence_fragment_insertion',  # "Gone. Just like that."
                'colloquial_substitution',  # "ain't", "gonna"
                'emotional_voice_leak',  # Author opinion bleeds through
                'subtext_implication',  # Show don't tell
                'varied_punctuation'  # Em-dashes, ellipses
            ]
        )
        
        # Stage 3: Perplexity & burstiness adjustment
        naturalized = await self.texture_optimizer.adjust(
            imperfect,
            target_perplexity_range=(40, 120),  # Human-like variance
            burstiness_coefficient=0.7  # Mix short/long sentences
        )
        
        # Stage 4: AI detection evasion
        detection_score = await self.ai_detector.score(naturalized)
        if detection_score > 0.3:  # Threshold
            naturalized = await self.adversarial_rewriter.rewrite(
                naturalized,
                target_score=0.2
            )
        
        return naturalized
```

**Deep Learning Filter Architecture**:
```python
class AIDetectionFilter:
    """Custom model to detect and filter AI-generated text"""
    
    def __init__(self):
        self.detector = self.load_detector_model()
    
    async def score(self, text: str) -> float:
        """Score: 0.0 = human, 1.0 = AI"""
        
        # Pipeline:
        # 1. BERT embeddings
        embeddings = self.bert_encoder(text)
        
        # 2. Custom CNN layer
        features = self.cnn_layer(embeddings)
        
        # 3. Attention mechanism
        attention = self.attention_mechanism(features)
        
        # 4. Perplexity analyzer
        perplexity = self.compute_perplexity(text)
        
        # 5. Burstiness detector
        burstiness = self.compute_burstiness(text)
        
        # 6. Final score
        score = self.final_classifier(
            attention,
            perplexity,
            burstiness
        )
        
        return score
    
    # Training:
    # - 100k human-written cyberpunk/noir passages
    # - 50k player-written game narratives
    # - 25k imperfect/emotional human text samples
    # - Adversarial training against GPTZero, Originality.ai
```

**Fine-Tuning Strategy**:
```python
# Fine-Tuning Configuration
fine_tuning_config = {
    "base_model": "mistral:7b",  # Or llama3.1:8b
    "training_data": {
        "human_writing": "50k horror/dark fiction passages",
        "player_content": "25k quest descriptions",
        "imperfect_text": "15k intentionally flawed samples",
        "emotional_biased": "10k subjective writing samples"
    },
    "training_objectives": [
        "next_token_prediction",  # Standard
        "perplexity_matching",  # Target: human range
        "adversarial_loss"  # Fool AI detector
    ],
    "lora_config": {
        "rank": 64,
        "alpha": 128,
        "dropout": 0.1,
        "target_modules": ["q_proj", "v_proj", "output_proj"]
    }
}
```

---

### Component 3: Event Generator (EG)

**Purpose**: Creates unpredictable, contextual events (never boring!)

**Architecture**:
```python
class EventGenerator:
    """Generates novel, unpredictable world events"""
    
    def __init__(self):
        self.random_seed_mixer = QuantumRandomGenerator()  # True randomness
        self.context_analyzer = WorldContextAnalyzer()
        self.constraint_solver = WorldLogicConstraintSolver()
        self.novelty_scorer = NoveltyEnforcer()
        self.escalation_manager = DramaPacingManager()
```

**Model Selection**:
- **Event Template Generator**: Fine-tuned `qwen2.5:7b` + "event-generation" LoRA
- **Novelty Validator**: `phi3:mini` (fast uniqueness checks)
- **Escalation Controller**: Rule-based + occasional LLM for complex scenarios

**Event Pool Architecture**:
```python
# Event Templates (10,000+)
event_templates = {
    "combat": {
        "gang_war": {
            "parameters": 200+ variables,
            "constraints": ["cannot_co_occur_with:peace_treaty"],
            "rarity": "common"
        },
        "monster_hunt": {
            "parameters": 150+ variables,
            "constraints": ["requires:faction_conflict"],
            "rarity": "uncommon"
        }
    },
    "social": {
        "betrayal": {
            "parameters": 180+ variables,
            "constraints": ["requires:alliance"],
            "rarity": "rare"
        }
    },
    "horror": {
        "body_modification": {
            "parameters": 120+ variables,
            "constraints": ["requires:lab_access"],
            "rarity": "legendary"
        }
    }
}

# Live Event Instantiation
async def generate_unique_event(event_type: str):
    """Never repeats exactly"""
    template = self.event_templates[event_type]
    world_state = await self.get_world_state()
    random_seed = self.qrng.generate()  # Quantum randomness
    player_history = await self.get_player_context()
    
    # Generate unique instance
    event = EventInstance(
        template=template,
        world_state=world_state,
        seed=random_seed,
        player_history=player_history
    )
    
    # Validate novelty
    if not await self.novelty_scorer.is_novel(event):
        return await self.generate_unique_event(event_type)  # Retry
    
    return event
```

---

## CONTINUOUS BACKGROUND SIMULATION

### Temporal Orchestration

```python
class TemporalOrchestrator:
    """Manages multi-speed simulation based on player presence"""
    
    SIMULATION_MODES = {
        'player_online': {
            'tick_rate': '1 game_hour per 5 real_seconds',
            'detail_level': 'high',
            'npc_radius': 500  # meters around player
        },
        'player_offline': {
            'tick_rate': '1 game_day per 10 real_minutes',
            'detail_level': 'macro',
            'full_world_sim': True
        },
        'player_elsewhere': {
            'tick_rate': '1 game_hour per 30 real_seconds',
            'detail_level': 'medium',
            'npc_radius': 'active_zones_only'
        }
    }
    
    async def simulate_time_period(self, duration: timedelta):
        """Run simulation forward"""
        
        # Parallel simulation of subsystems
        results = await asyncio.gather(
            self.faction_simulator.tick(duration),
            self.npc_manager.update_all(duration),
            self.economic_model.advance(duration),
            self.event_generator.spawn_events(duration)
        )
        
        # Resolve conflicts and causal chains
        world_delta = await self.conflict_resolver.resolve(results)
        
        # Update canonical state
        await self.state_manager.apply_delta(world_delta)
        
        # Generate narratives from significant changes
        if world_delta.significance > THRESHOLD:
            narrative = await self.narrative_weaver.weave(world_delta)
            await self.publish_narrative_update(narrative)
```

### NPC Independence System

```python
class NPCAgent:
    """Autonomous NPC with goals and memory"""
    
    def __init__(self, npc_id: str, npc_type: str):
        self.personality = PersonalityVector()  # 50-dim embedding
        self.goals = GoalStack()  # Hierarchical objectives
        self.memory = EpisodicMemory()  # Past interactions
        self.relationships = RelationshipGraph()
        self.resources = ResourceInventory()
        
        # Model selection based on NPC tier
        if npc_type == "generic":  # Tier 1
            self.decision_model = "phi3:mini"
        elif npc_type == "elite":  # Tier 2
            self.decision_model = "llama3.1:8b+vampire-lora"
        else:  # Tier 3 (boss)
            self.decision_model = "llama3.1:8b+personalized-lora"
        
    async def make_decision(self, world_state: WorldState):
        """LLM-powered decision making"""
        
        # Build context
        context = {
            'current_goals': self.goals.peek(),
            'recent_memories': self.memory.recall(limit=10),
            'nearby_npcs': world_state.get_nearby(self.location),
            'faction_status': self.relationships.faction_standing(),
            'available_actions': self.get_possible_actions(world_state)
        }
        
        # Personality-influenced prompt
        prompt = self.personality.shape_prompt(
            template="npc_decision",
            context=context
        )
        
        # Generate decision using AI Inference Service
        decision = await self.ai_inference_service.generate(
            model=self.decision_model,
            prompt=prompt,
            temperature=self.personality.impulsiveness,
            constraints=context['available_actions']
        )
        
        # Update memory and execute
        self.memory.store(decision)
        return await self.execute_action(decision)
```

**NPC Interaction Matrix**:
```
3 Types of NPC Interactions:
├─ Player-Independent (80% of interactions)
│   • Gang members patrol territories
│   • Rivals clash over resources
│   • Monsters hunt prey
│   • Merchants trade goods
│
├─ Player-Triggered (15%)
│   • Reputation-based reactions
│   • Quest givers spawn opportunities
│   • Enemies seek revenge
│
└─ Player-Collaborative (5%)
    • Active quest participation
    • Direct dialogue (handled by Layer 3)
    • Combat assistance
```

---

## PLAYER NARRATIVE MANAGEMENT

### Dynamic Difficulty Adjustment

```python
class DifficultyOrchestrator:
    """Manages player power curve - wins at intervals, challenges require work"""
    
    async def calculate_optimal_challenge(self, player: Player):
        """Ensure player wins at intervals but works for it"""
        
        power_level = self.player_power_model.predict(player)
        recent_wins = player.history.count_wins(last_n_hours=5)
        recent_losses = player.history.count_losses(last_n_hours=5)
        time_since_victory = player.history.time_since_major_win()
        
        # Victory scheduling algorithm
        if time_since_victory > timedelta(hours=3):
            # Schedule achievable win
            challenge_level = power_level * 0.85
            guarantee_success = True
        elif recent_losses >= 2:
            # Mercy challenge
            challenge_level = power_level * 0.70
            guarantee_success = False
        elif recent_wins >= 3:
            # Ramp up difficulty
            challenge_level = power_level * 1.3
            guarantee_success = False
        else:
            # Normal difficulty curve
            challenge_level = power_level * random.uniform(0.9, 1.15)
            guarantee_success = False
        
        # Generate challenge using Orchestration Service
        challenge = await self.orchestration_service.generate_content(
            request=ContentRequest(
                type="quest",
                difficulty_level=challenge_level,
                player_context=player,
                guaranteed_win=guarantee_success
            )
        )
        
        return challenge
```

### Boss Replacement System

```python
class BossEcosystem:
    """Ensures bosses are always replaceable - player never truly 'wins everything'"""
    
    async def handle_boss_death(self, boss: NPC, killer: Player):
        """Generate power vacuum and succession"""
        
        # Immediate narrative impact
        narrative = await self.narrative_weaver.weave_boss_death(boss, killer)
        
        # Simulate power vacuum
        faction = boss.faction
        rivals = self.get_rival_npcs(faction, boss.tier)
        
        # Multiple succession paths
        succession_scenarios = [
            {
                'type': 'internal_coup',
                'candidates': faction.members_by_ambition(),
                'probability': 0.4
            },
            {
                'type': 'external_takeover',
                'candidates': self.rival_factions_nearby(faction),
                'probability': 0.3
            },
            {
                'type': 'chaos_fragmentation',
                'result': 'split_faction',
                'probability': 0.2
            },
            {
                'type': 'player_opportunity',
                'quest': self.generate_power_grab_quest(faction),
                'probability': 0.1
            }
        ]
        
        # Select and execute succession
        outcome = weighted_random_choice(succession_scenarios)
        new_boss = await self.execute_succession(outcome)
        
        # Ensure new boss is unique (using Novelty Enforcer)
        new_boss.personality = await self.generate_unique_personality(
            different_from=boss.personality
        )
        new_boss.tactics = await self.generate_novel_tactics(
            avoid=boss.tactics
        )
        
        # Long-term: plant seeds for future bosses
        await self.seed_future_threats(faction, num_seeds=3)
```

---

## NOVELTY ENFORCEMENT (Never Boring)

### Uniqueness Guarantees

```python
class NoveltyEnforcer:
    """Prevents repetitive content"""
    
    def __init__(self):
        self.event_history = VectorStore('chromadb')  # Semantic similarity
        self.quest_fingerprints = BloomFilter(capacity=1_000_000)
        self.narrative_clusters = ClusteringModel()
    
    async def ensure_novel_quest(self, context: QuestContext):
        """Generate quest that hasn't been seen before"""
        
        max_attempts = 5
        for attempt in range(max_attempts):
            # Generate candidate quest
            quest = await self.quest_generator.generate(context)
            
            # Create fingerprint
            fingerprint = self.fingerprint_quest(quest)
            
            # Check uniqueness (bloom filter - fast)
            if fingerprint not in self.quest_fingerprints:
                # Additional semantic check (vector similarity)
                embedding = await self.embed_quest(quest)
                similar_quests = await self.event_history.similarity_search(
                    embedding,
                    threshold=0.85
                )
                
                if len(similar_quests) == 0:
                    # Truly novel quest found
                    self.quest_fingerprints.add(fingerprint)
                    await self.event_history.add(embedding, quest)
                    return quest
            
            # Increase novelty pressure
            context.novelty_requirement *= 1.5
        
        # Fallback: combine multiple quest templates
        return await self.hybrid_quest_generator.generate(context)
    
    def fingerprint_quest(self, quest: Quest) -> str:
        """Create stable quest identifier"""
        key_elements = [
            quest.objective_type,
            quest.target_entity,
            quest.location_archetype,
            quest.reward_category,
            sorted(quest.required_player_actions)
        ]
        return hash(str(key_elements))
```

### Unpredictability Injection

```python
class ChaosEngine:
    """Introduces controlled randomness - unpredictable events"""
    
    async def inject_wildcard_event(self):
        """Random events that break patterns"""
        
        wildcard_types = [
            {
                'type': 'dimensional_bleed',
                'desc': 'Reality glitch spawns impossible geometry',
                'frequency': 'rare'
            },
            {
                'type': 'npc_spontaneous_evolution',
                'desc': 'Random NPC gains sudden power/obsession',
                'frequency': 'uncommon'
            },
            {
                'type': 'faction_merger',
                'desc': 'Two rival gangs suddenly unite',
                'frequency': 'rare'
            },
            {
                'type': 'resource_inversion',
                'desc': 'Valuable resources become toxic, trash becomes gold',
                'frequency': 'very_rare'
            }
        ]
        
        # Quantum-seeded selection (true randomness)
        chosen = await self.qrng.select(wildcard_types)
        
        # Generate event with no historical precedent
        event = await self.event_generator.generate_wildcard(
            event_type=chosen,
            constraints={'must_be_novel': True}
        )
        
        return event
```

---

## INTEGRATION WITH EXISTING SERVICES

### API Contracts

```python
class StoryTellerInterface:
    """Integration points with existing services"""
    
    # FROM Story Teller TO Existing Services
    
    async def request_world_generation(self, request: WorldGenRequest):
        """Use Orchestration Service Layer 1 & 2"""
        return await self.orchestration_service.generate_content(
            request=ContentRequest(
                layer_1=True,  # Foundation
                layer_2=True,  # Customization
                type="world_base"
            )
        )
    
    async def request_npc_dialogue(self, npc_id: str, context: dict):
        """Use Orchestration Service Layer 3"""
        return await self.orchestration_service.layer3.generate_dialogue(
            npc_id=npc_id,
            context=context
        )
    
    async def request_battle_coordination(self, battle_context: dict):
        """Use Orchestration Service Layer 4"""
        return await self.orchestration_service.layer4.coordinate(
            scenario="battle",
            context=battle_context
        )
    
    async def publish_world_event(self, event: WorldEvent):
        """Notify Game Engine Service of world changes"""
        await self.message_bus.publish(
            topic="world.events",
            message=event
        )
    
    async def write_world_state(self, state_delta: WorldStateDelta):
        """Update State Management Service"""
        await self.state_service.update_world_state(state_delta)
    
    # FROM Existing Services TO Story Teller
    
    async def receive_player_action(self, action: PlayerAction):
        """Update simulation based on player choices"""
        await self.world_simulation.apply_player_action(action)
    
    async def receive_feedback(self, feedback: NarrativeFeedback):
        """Send to Learning Service"""
        await self.learning_service.receive_feedback(feedback)
```

### Message Bus Architecture

```python
# Kafka Topics for Event-Driven Architecture
kafka_topics = {
    "world.events.major": {
        "publisher": "StoryTeller",
        "subscribers": ["GameEngine", "StateManagement"],
        "events": ["faction_wars", "boss_spawns", "major_npc_deaths"]
    },
    "world.events.minor": {
        "publisher": "StoryTeller",
        "subscribers": ["StateManagement"],
        "events": ["npc_movements", "ambient_events"]
    },
    "player.actions": {
        "publisher": "GameEngine",
        "subscribers": ["StoryTeller", "StateManagement"],
        "events": ["all_player_decisions"]
    },
    "narrative.updates": {
        "publisher": "StoryTeller",
        "subscribers": ["GameEngine", "Orchestration"],
        "events": ["quest_state_changes", "story_progress"]
    },
    "simulation.state": {
        "publisher": "StoryTeller",
        "subscribers": ["StateManagement", "LearningService"],
        "events": ["periodic_world_snapshots"]
    }
}

# Redis Pub/Sub for Real-Time Updates
redis_channels = {
    "player.location": {
        "publisher": "GameEngine",
        "subscribers": ["StoryTeller"],
        "purpose": "Real-time player location updates"
    },
    "npc.proximity": {
        "publisher": "StoryTeller",
        "subscribers": ["GameEngine"],
        "purpose": "NPC proximity triggers"
    },
    "emergency.events": {
        "publisher": "Any",
        "subscribers": ["All"],
        "purpose": "Emergency event overrides"
    }
}
```

---

## MODEL ALLOCATION STRATEGY

### Copying and Fine-Tuning Models

**Strategy**: Copy base Ollama models and fine-tune separately

```bash
# Example: Copy llama3.1:8b for different fine-tunes
ollama create story-teller-world-gen --file Modelfile.world-gen
ollama create story-teller-quest-gen --file Modelfile.quest-gen
ollama create story-teller-narrative --file Modelfile.narrative

# Each has same base but different fine-tuning/LoRA adapters
```

**Model Allocation**:

**World Generation Models**:
- Base: `llama3.1:8b` (copy → `story-world-gen`)
- Fine-tune: Urban dynamics, city layouts, building generation
- LoRA: "city-generation", "dungeon-layout", "sewer-system"

**Narrative Models**:
- Base: `mistral:7b` (copy → `story-narrative`)
- Fine-tune: Horror/cyberpunk fiction, human writing patterns
- LoRA: "quest-generation", "story-arcs", "human-likeness"

**NPC Decision Models** (reuse existing):
- Tier 1: `phi3:mini` (already available)
- Tier 2: `llama3.1:8b` + monster-specific LoRAs (already available)
- Tier 3: `llama3.1:8b` + personalized LoRAs (already available)

**Event Generation Models**:
- Base: `qwen2.5:7b` (copy → `story-events`)
- Fine-tune: Event templates, causality chains
- LoRA: "combat-events", "social-events", "horror-events"

---

## PERFORMANCE OPTIMIZATION

### Spatial Partitioning

```python
class PerformanceOptimizer:
    """Ensures system scales to thousands of NPCs"""
    
    CHUNK_SIZE = 1000  # meters
    
    async def optimize_simulation(self):
        """Only simulate what matters"""
        
        # Partition world into chunks
        active_chunks = self.spatial_index.get_active_chunks(
            player_positions=self.get_all_player_positions(),
            radius=2000  # 2km around each player
        )
        
        # Three-tier simulation
        for chunk in self.world.all_chunks():
            if chunk in active_chunks:
                # High detail: Full NPC AI
                await self.simulate_chunk(chunk, detail='high')
            elif chunk.has_major_faction_activity():
                # Medium detail: Simplified AI
                await self.simulate_chunk(chunk, detail='medium')
            else:
                # Low detail: Statistical model only
                await self.simulate_chunk_statistical(chunk)
```

---

## SUCCESS METRICS

```python
class StoryTellerMetrics:
    """KPIs for Story Teller system"""
    
    TARGETS = {
        # Novelty
        'quest_uniqueness': 0.95,  # 95% of quests feel unique
        'narrative_repetition': 0.05,  # <5% repeated story beats
        
        # AI Detection
        'ai_detection_rate': 0.15,  # <15% flagged as AI
        'human_likeness_score': 0.80,  # >80% perceived as human
        
        # Player Engagement
        'session_length': 120,  # 2+ hour average sessions
        'quest_completion_rate': 0.70,  # 70% finish quests
        'player_surprise': 0.60,  # 60% report unexpected events
        
        # Performance
        'simulation_latency': 100,  # <100ms per tick
        'npc_decision_time': 50,  # <50ms per NPC decision
        'world_update_rate': 10,  # 10 updates/second
        
        # Balance
        'win_rate': 0.65,  # Players win 65% of challenges
        'challenge_satisfaction': 0.75,  # 75% feel appropriately challenged
        'power_progression': 'linear',  # Smooth growth curve
    }
```

---

## IMPLEMENTATION ROADMAP

```
Phase 1 (Weeks 1-4): Foundation
├─ Set up Story Teller service infrastructure
├─ Copy and configure Ollama models
├─ Implement basic World Simulation Engine
├─ Create PostgreSQL schema for world state
└─ Build Kafka message bus integration

Phase 2 (Weeks 5-8): NPC Systems
├─ Develop NPC Agent architecture
├─ Fine-tune models on behavioral data
├─ Implement faction simulation
├─ Create spatial partitioning system
└─ Build NPC-NPC interaction system

Phase 3 (Weeks 9-12): Narrative Engine
├─ Build Narrative Weaver
├─ Fine-tune on cyberpunk/horror corpus
├─ Implement AI detection bypass pipeline
├─ Create novelty enforcement system
└─ Integrate with deep learning filter

Phase 4 (Weeks 13-16): Integration
├─ Connect Story Teller to 4-layer system
├─ Implement dynamic difficulty adjustment
├─ Build boss replacement system
├─ Create comprehensive testing framework
└─ Performance optimization

Phase 5 (Weeks 17-20): Optimization & Polish
├─ Adversarial training against AI detectors
├─ Load testing with 10k+ concurrent NPCs
├─ Player feedback integration
└─ Launch beta with limited player base
```

---

**Status**: ✅ Complete architecture designed  
**Integration**: ✅ Fully integrated with existing 4-layer system  
**Models**: ✅ Uses available Ollama models (can copy and fine-tune)  
**AI Detection**: ✅ Comprehensive bypass strategy implemented  
**Novelty**: ✅ Anti-repetition system ensures unique narratives

