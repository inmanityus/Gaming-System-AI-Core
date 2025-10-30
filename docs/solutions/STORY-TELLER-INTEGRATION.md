# Story Teller Service Integration Guide
**Date**: January 29, 2025  
**Purpose**: Complete integration map between Story Teller and existing services

---

## INTEGRATION OVERVIEW

The Story Teller service integrates with all existing services through well-defined API contracts and event-driven messaging.

```
                    ┌──────────────────────┐
                    │  STORY TELLER        │
                    │  SERVICE             │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│Orchestration │      │AI Inference  │      │State Mgt    │
│Service       │      │Service       │      │Service      │
└──────────────┘      └──────────────┘      └──────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│Game Engine   │      │Learning      │      │Message Bus  │
│Service       │      │Service       │      │(Kafka)      │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## INTEGRATION POINTS

### 1. Story Teller ↔ Orchestration Service

**Purpose**: Use 4-layer LLM pipeline for content generation

**API Contract**:
```python
# Story Teller → Orchestration Service

class StoryTellerToOrchestration:
    async def generate_world_base(self, request: WorldGenRequest):
        """Use Layer 1 (Foundation) for base world generation"""
        return await self.orchestration_service.layer1.generate_base(
            request=WorldBaseRequest(
                seed=request.seed,
                biome="urban_city",
                size=request.city_size,
                type="world_foundation"
            )
        )
    
    async def customize_world(self, foundation: WorldBase):
        """Use Layer 2 (Customization) for world details"""
        return await self.orchestration_service.layer2.customize_world(
            foundation=foundation,
            request=WorldCustomizationRequest()
        )
    
    async def generate_npc_dialogue(self, npc_id: str, context: dict):
        """Use Layer 3 (Interaction) for NPC dialogue"""
        return await self.orchestration_service.layer3.generate_dialogue(
            npc_id=npc_id,
            player_context=context,
            world_context=await self.get_world_context()
        )
    
    async def coordinate_battle(self, battle_context: dict):
        """Use Layer 4 (Coordination) for complex scenarios"""
        return await self.orchestration_service.layer4.coordinate(
            scenario="battle",
            context=battle_context
        )

# Orchestration Service → Story Teller

class OrchestrationToStoryTeller:
    async def notify_narrative_update(self, update: NarrativeUpdate):
        """Orchestration service notifies of narrative changes"""
        await self.story_teller.receive_narrative_update(update)
```

**Message Flow**:
```
Story Teller → Orchestration Service
├─ World Generation Request → Layer 1 → Layer 2
├─ NPC Dialogue Request → Layer 3
└─ Battle Coordination → Layer 4

Orchestration Service → Story Teller
└─ Narrative State Updates → Story Teller State Manager
```

---

### 2. Story Teller ↔ AI Inference Service

**Purpose**: Access local Ollama models and cloud LLMs

**API Contract**:
```python
# Story Teller → AI Inference Service

class StoryTellerToAIInference:
    async def generate_npc_decision(self, npc_id: str, context: dict):
        """Generate NPC decision using appropriate model"""
        
        # Select model based on NPC tier
        npc_tier = await self.get_npc_tier(npc_id)
        
        if npc_tier == 1:
            model = "phi3:mini"
        elif npc_tier == 2:
            model = "llama3.1:8b+vampire-lora"  # Monster-specific
        else:  # Tier 3
            model = "llama3.1:8b+personalized-lora"
        
        return await self.ai_inference_service.generate(
            model=model,
            prompt=self.build_decision_prompt(npc_id, context),
            temperature=0.7,
            max_tokens=256
        )
    
    async def generate_narrative(self, event: WorldEvent):
        """Generate narrative text using narrative models"""
        
        # Use specialized narrative model
        return await self.ai_inference_service.generate(
            model="story-narrative",  # Fine-tuned mistral:7b
            prompt=self.build_narrative_prompt(event),
            temperature=0.9,  # High creativity
            humanize=True  # Apply AI detection bypass
        )
    
    async def generate_event(self, event_type: str, context: dict):
        """Generate unique world event"""
        
        return await self.ai_inference_service.generate(
            model="story-events",  # Fine-tuned qwen2.5:7b
            prompt=self.build_event_prompt(event_type, context),
            temperature=0.8,
            constraints=self.get_event_constraints(event_type)
        )
```

**Model Usage**:
```
Story Teller Model Allocation:
├─ NPC Decisions: phi3:mini, llama3.1:8b (with LoRAs)
├─ Narrative Generation: mistral:7b (fine-tuned copy)
├─ Event Generation: qwen2.5:7b (fine-tuned copy)
└─ World Generation: llama3.1:8b (fine-tuned copy)
```

---

### 3. Story Teller ↔ State Management Service

**Purpose**: Read/write world state, player context, NPC states

**API Contract**:
```python
# Story Teller → State Management Service

class StoryTellerToStateManagement:
    async def write_world_state(self, state_delta: WorldStateDelta):
        """Update canonical world state"""
        
        # Write to PostgreSQL (persistent)
        await self.state_service.postgres.update_world_state(state_delta)
        
        # Update Redis (hot cache)
        await self.state_service.redis.update_hot_state(state_delta)
        
        # Update Vector DB (semantic memory)
        await self.state_service.vector_db.upsert_embeddings(
            entities=state_delta.entities,
            events=state_delta.events
        )
    
    async def read_player_context(self, player_id: str) -> PlayerContext:
        """Get player context for narrative generation"""
        
        # Get from Redis (fast)
        hot_context = await self.state_service.redis.get_player_context(player_id)
        
        # Get from PostgreSQL (complete)
        persistent_context = await self.state_service.postgres.get_player_history(player_id)
        
        # Get from Vector DB (semantic)
        semantic_context = await self.state_service.vector_db.search_player_memories(player_id)
        
        return PlayerContext(
            hot=hot_context,
            persistent=persistent_context,
            semantic=semantic_context
        )
    
    async def read_world_state(self, query: WorldStateQuery) -> WorldState:
        """Query world state for simulation"""
        
        # Spatial query (NPCs near location)
        if query.type == "spatial":
            return await self.state_service.postgres.query_spatial(
                location=query.location,
                radius=query.radius
            )
        
        # Temporal query (events in time range)
        elif query.type == "temporal":
            return await self.state_service.postgres.query_temporal(
                start_time=query.start_time,
                end_time=query.end_time
            )
        
        # Faction query (faction state)
        elif query.type == "faction":
            return await self.state_service.postgres.query_faction(
                faction_id=query.faction_id
            )

# State Management Service → Story Teller

class StateManagementToStoryTeller:
    async def notify_state_change(self, change: StateChange):
        """State service notifies of external state changes"""
        await self.story_teller.receive_state_update(change)
```

**Data Flow**:
```
Story Teller → State Management
├─ World State Updates → PostgreSQL (canonical)
├─ Hot State Updates → Redis (cache)
└─ Semantic Updates → Vector DB (memory)

State Management → Story Teller
├─ Player Context → For narrative generation
├─ World State Queries → For simulation
└─ State Change Notifications → For synchronization
```

---

### 4. Story Teller ↔ Learning Service

**Purpose**: Send feedback for model improvement

**API Contract**:
```python
# Story Teller → Learning Service

class StoryTellerToLearning:
    async def send_narrative_feedback(self, feedback: NarrativeFeedback):
        """Send narrative quality feedback"""
        
        await self.learning_service.receive_feedback(
            service="story_teller",
            feedback_type="narrative_quality",
            data={
                "narrative_id": feedback.narrative_id,
                "player_rating": feedback.player_rating,
                "ai_detection_score": feedback.ai_detection_score,
                "engagement_metrics": feedback.engagement_metrics
            }
        )
    
    async def send_event_feedback(self, feedback: EventFeedback):
        """Send event quality feedback"""
        
        await self.learning_service.receive_feedback(
            service="story_teller",
            feedback_type="event_quality",
            data={
                "event_id": feedback.event_id,
                "novelty_score": feedback.novelty_score,
                "player_reaction": feedback.player_reaction
            }
        )

# Learning Service → Story Teller

class LearningToStoryTeller:
    async def notify_model_update(self, update: ModelUpdate):
        """Learning service notifies of improved models"""
        
        if update.service == "story_teller":
            await self.story_teller.update_model(
                model_name=update.model_name,
                version=update.version,
                artifact_path=update.artifact_path
            )
```

**Feedback Loop**:
```
Story Teller → Learning Service
├─ Narrative Quality Feedback → Model improvement
├─ Event Quality Feedback → Event generation improvement
└─ Player Engagement Metrics → Overall system improvement

Learning Service → Story Teller
└─ Model Updates → Deploy improved models
```

---

### 5. Story Teller ↔ Game Engine Service

**Purpose**: Publish world updates for rendering

**API Contract**:
```python
# Story Teller → Game Engine Service

class StoryTellerToGameEngine:
    async def publish_world_update(self, update: WorldUpdate):
        """Publish world state changes to game engine"""
        
        # Publish to Kafka (async)
        await self.message_bus.publish(
            topic="world.events.major",  # or "minor"
            message=update
        )
        
        # Also publish to Redis Pub/Sub (real-time)
        await self.redis.pubsub.publish(
            channel="world.updates",
            message=update
        )
    
    async def publish_quest_update(self, quest: Quest):
        """Notify game engine of quest changes"""
        
        await self.message_bus.publish(
            topic="narrative.updates",
            message={
                "type": "quest_update",
                "quest": quest
            }
        )

# Game Engine Service → Story Teller

class GameEngineToStoryTeller:
    async def send_player_action(self, action: PlayerAction):
        """Game engine sends player actions to Story Teller"""
        
        await self.message_bus.publish(
            topic="player.actions",
            message=action
        )
    
    async def send_player_location(self, location: PlayerLocation):
        """Real-time player location updates"""
        
        await self.redis.pubsub.publish(
            channel="player.location",
            message=location
        )
```

**Event Flow**:
```
Story Teller → Game Engine
├─ World Events (major) → Kafka → Game Engine rendering
├─ Narrative Updates → Kafka → Quest UI updates
└─ Real-time Updates → Redis Pub/Sub → Immediate rendering

Game Engine → Story Teller
├─ Player Actions → Kafka → World simulation impact
└─ Player Location → Redis Pub/Sub → Spatial simulation triggers
```

---

## MESSAGE BUS ARCHITECTURE

### Kafka Topics

```python
kafka_topics = {
    "world.events.major": {
        "producer": "StoryTeller",
        "consumers": ["GameEngine", "StateManagement"],
        "partition_key": "location",
        "retention": "7_days",
        "events": [
            "faction_wars",
            "boss_spawns",
            "major_npc_deaths",
            "territory_changes"
        ]
    },
    "world.events.minor": {
        "producer": "StoryTeller",
        "consumers": ["StateManagement"],
        "partition_key": "location",
        "retention": "3_days",
        "events": [
            "npc_movements",
            "ambient_events",
            "resource_changes"
        ]
    },
    "player.actions": {
        "producer": "GameEngine",
        "consumers": ["StoryTeller", "StateManagement", "LearningService"],
        "partition_key": "player_id",
        "retention": "30_days",
        "events": [
            "all_player_decisions",
            "quest_completions",
            "combat_actions"
        ]
    },
    "narrative.updates": {
        "producer": "StoryTeller",
        "consumers": ["GameEngine", "Orchestration"],
        "partition_key": "player_id",
        "retention": "7_days",
        "events": [
            "quest_state_changes",
            "story_progress",
            "narrative_beats"
        ]
    },
    "simulation.state": {
        "producer": "StoryTeller",
        "consumers": ["StateManagement", "LearningService"],
        "partition_key": "chunk_id",
        "retention": "14_days",
        "events": [
            "periodic_world_snapshots",
            "faction_state_updates",
            "economic_changes"
        ]
    }
}
```

### Redis Pub/Sub Channels

```python
redis_channels = {
    "player.location": {
        "publisher": "GameEngine",
        "subscriber": "StoryTeller",
        "purpose": "Real-time player location updates",
        "update_frequency": "5_seconds"
    },
    "npc.proximity": {
        "publisher": "StoryTeller",
        "subscriber": "GameEngine",
        "purpose": "NPC proximity triggers",
        "update_frequency": "real_time"
    },
    "emergency.events": {
        "publisher": "Any",
        "subscriber": "All",
        "purpose": "Emergency event overrides",
        "update_frequency": "on_demand"
    }
}
```

---

## INTEGRATION SEQUENCE DIAGRAM

### World Generation Flow

```
Story Teller    Orchestration    AI Inference    State Mgt    Game Engine
     │               │                │             │             │
     │──gen_world───▶│                │             │             │
     │               │──layer1───────▶│             │             │
     │               │◀──world_base───│             │             │
     │               │──layer2───────▶│             │             │
     │               │◀──world_custom │             │             │
     │◀──world───────│                │             │             │
     │               │                │             │             │
     │──write_state───────────────────▶             │             │
     │                              │             │             │
     │──publish_update───────────────────────────────────────────▶│
     │                              │             │             │
```

### Background Simulation Flow

```
Story Teller    AI Inference    State Mgt    Message Bus
     │               │             │             │
     │──get_npcs─────▶             │             │
     │◀──npc_list────│             │             │
     │               │             │             │
     │──decide(npc1)───────────────▶             │
     │◀──decision────│             │             │
     │──decide(npc2)───────────────▶             │
     │◀──decision────│             │             │
     │               │             │             │
     │──update_state───────────────▶             │
     │               │             │             │
     │──publish_event───────────────────────────▶│
     │               │             │             │
```

---

## ERROR HANDLING & FALLBACKS

```python
class IntegrationErrorHandler:
    """Handles integration failures gracefully"""
    
    async def handle_orchestration_failure(self, error: Exception):
        """Fallback when Orchestration Service unavailable"""
        
        # Use local models directly
        return await self.ai_inference_service.generate_direct(
            model="fallback_model",
            prompt=self.build_fallback_prompt()
        )
    
    async def handle_state_service_failure(self, error: Exception):
        """Fallback when State Service unavailable"""
        
        # Use local cache only
        return await self.local_cache.get_world_state()
    
    async def handle_message_bus_failure(self, error: Exception):
        """Fallback when Message Bus unavailable"""
        
        # Direct HTTP call to Game Engine
        await self.game_engine_api.post_world_update(
            update=self.pending_update
        )
```

---

**Status**: ✅ Complete integration architecture documented  
**Services Integrated**: 5 (Orchestration, AI Inference, State Management, Learning, Game Engine)  
**Message Bus**: Kafka + Redis Pub/Sub  
**Error Handling**: Fallback strategies for each integration

