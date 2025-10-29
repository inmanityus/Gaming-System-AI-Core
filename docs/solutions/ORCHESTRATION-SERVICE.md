# Orchestration Service Solution
**Service**: Hierarchical LLM Pipeline Coordination  
**Date**: January 29, 2025

---

## SERVICE OVERVIEW

Coordinates the 4-layer hierarchical LLM pipeline, manages parallel execution, resolves conflicts, and orchestrates complex scenarios (battles, environmental storytelling).

---

## ARCHITECTURE

### Technology Stack
- **Runtime**: Python, FastAPI
- **Cloud LLMs**: GPT-5-Pro, Claude Sonnet 4.5, Gemini 2.5 Pro
- **Local Coordinators**: Python async/await
- **State**: Redis for shared state

### 4-Layer Pipeline

```python
class OrchestrationService:
    def __init__(self):
        self.layer1 = FoundationLayer()  # Procedural + small LLMs
        self.layer2 = CustomizationLayer()  # Specialized local LLMs
        self.layer3 = InteractionLayer()  # NPC dialogue
        self.layer4 = CoordinationLayer()  # Cloud LLMs
        self.state_manager = StateManager()
    
    async def generate_content(self, request: ContentRequest):
        # Layer 1: Foundation
        foundation = await self.layer1.generate_base(request)
        
        # Layer 2: Customization (parallel)
        customization_tasks = [
            self.layer2.customize_monster(foundation.monster),
            self.layer2.enhance_terrain(foundation.terrain),
            self.layer2.detail_room(foundation.room)
        ]
        customized = await asyncio.gather(*customization_tasks)
        
        # Layer 3: Interactions (only for active NPCs)
        if request.activate_npcs:
            interactions = await self.layer3.generate_dialogue(
                customized.monsters, 
                request.player_context
            )
        
        # Layer 4: Coordination (if needed)
        if request.requires_coordination:
            orchestration = await self.layer4.coordinate(
                customized, 
                interactions
            )
        
        return ContentResponse(foundation, customized, interactions, orchestration)
```

### Layer 1: Foundation
```python
class FoundationLayer:
    async def generate_base(self, request):
        # Mostly procedural
        monster = generate_monster_base(
            seed=request.seed,
            type=request.monster_type
        )
        
        terrain = procedural_terrain.generate(
            biome=request.biome,
            size=request.size
        )
        
        room = procedural_room.generate(
            dimensions=request.dimensions,
            seed=request.seed
        )
        
        return FoundationOutput(monster, terrain, room)
```

### Layer 2: Customization
```python
class CustomizationLayer:
    async def customize_monster(self, base_monster):
        # Use specialized LoRA adapter
        response = await inference_service.generate(
            model="llama3.1-8b+vampire-lora",
            prompt=f"Add personality to: {base_monster}",
            stream=False
        )
        return customize_monster_from_llm(base_monster, response)
```

### Layer 3: Interaction
```python
class InteractionLayer:
    async def generate_dialogue(self, npcs, player_context):
        # Only for active NPCs (within player range)
        active_npcs = [n for n in npcs if n.is_active]
        
        dialogue_tasks = [
            self.generate_npc_dialogue(npc, player_context)
            for npc in active_npcs
        ]
        
        dialogues = await asyncio.gather(*dialogue_tasks)
        return dialogues
```

### Layer 4: Coordination
```python
class CoordinationLayer:
    async def coordinate(self, content, interactions):
        # Use cloud LLM for orchestration
        orchestration_prompt = f"""
        Coordinate this scenario:
        - Monsters: {content.monsters}
        - Player context: {interactions.player_context}
        
        Generate battle coordination plan.
        """
        
        response = await cloud_llm.generate(
            model="gpt-5-pro",
            prompt=orchestration_prompt,
            max_tokens=1024
        )
        
        plan = parse_orchestration_plan(response)
        return plan
```

---

## PARALLEL EXECUTION

### DAG-Based Execution
- Layer 1: Fully parallel (all monsters, terrain tiles)
- Layer 2: Parallel per entity (synchronize only on dependencies)
- Layer 3: Only for active NPCs (defer others)
- Layer 4: Lightweight plans (delegate heavy work)

### Conflict Resolution
```python
async def resolve_conflicts(self, layer_outputs):
    # Check for inconsistencies
    conflicts = detect_conflicts(layer_outputs)
    
    if conflicts:
        # Use cloud LLM to resolve
        resolution = await cloud_llm.resolve(
            conflicts,
            context=self.state_manager.get_context()
        )
        return apply_resolution(layer_outputs, resolution)
    
    return layer_outputs
```

---

## STATE SYNCHRONIZATION

### Shared State Manager
```python
class StateManager:
    def __init__(self):
        self.redis = Redis(host='localhost', port=6379)
        self.pg = PostgreSQL()
        self.vector_db = Pinecone()
    
    async def get_context(self, entity_id, radius=100):
        entities = self.get_entities_nearby(entity_id, radius)
        history = self.get_relevant_history(entity_id)
        world_state = self.get_world_state()
        
        return {
            "entities": entities,
            "history": history,
            "world": world_state
        }
    
    async def update_state(self, entity_id, changes):
        # Write to Redis (hot state)
        await self.redis.hset(f"entity:{entity_id}", mapping=changes)
        
        # Persist to PostgreSQL
        await self.pg.update_entity(entity_id, changes)
        
        # Update vector DB for semantic search
        await self.vector_db.upsert(
            id=entity_id,
            values=encode_semantic(changes)
        )
```

---

## BATTLE COORDINATION

### Multi-NPC Combat
```python
async def coordinate_battle(self, monsters, player):
    # Each monster acts autonomously based on their LLM
    monster_actions = await asyncio.gather(*[
        monster_llm.decide_action(
            monster,
            battle_context,
            player_state
        )
        for monster in monsters
    ])
    
    # Coordinator ensures group cohesion
    coordinator_plan = await cloud_llm.coordinate_actions(
        monster_actions,
        battle_tactics="pack_coordination"
    )
    
    return BattleExecutionPlan(monster_actions, coordinator_plan)
```

---

**Next**: See `STATE-MANAGEMENT-SERVICE.md` for state persistence details.

