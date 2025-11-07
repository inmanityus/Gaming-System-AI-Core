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
- **State**: Redis Cluster for shared state ⭐ **UPDATED**
- **Connection Pooling**: gRPC (40-100 connections), PostgreSQL (20-50) ⭐ **NEW**
- **Cost Controls**: Rate limiting, tier gating, budget monitoring ⭐ **NEW**

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

## COST CONTROLS & TIER GATING ⭐ **NEW**

### Integration with Settings/Payment Service

**Tier Checking Before Expensive LLM Calls**:
```python
from fastapi import Depends, HTTPException
from services.settings import SettingsService
from services.payment import PaymentService

class OrchestrationService:
    def __init__(self):
        self.settings_service = SettingsService()
        self.payment_service = PaymentService()
        self.rate_limiter = RateLimiter()
    
    async def generate_content(self, request: ContentRequest, user_id: str):
        # Check user tier before expensive operations
        user_tier = await self.settings_service.get_user_tier(user_id)
        
        # Check rate limits
        if not await self.rate_limiter.check_limit(user_id, user_tier):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {user_tier} tier"
            )
        
        # Layer 4 coordination only for Premium/Whale tiers
        if request.requires_coordination:
            if user_tier == "free":
                # Use cached/pre-generated content instead
                return await self.get_cached_orchestration(request)
            
            # Check cost budget
            estimated_cost = self.estimate_layer4_cost(request)
            if not await self.payment_service.can_afford(user_id, estimated_cost):
                raise HTTPException(
                    status_code=402,
                    detail="Insufficient budget for this operation"
                )
            
            # Process Layer 4 (expensive)
            orchestration = await self.layer4.coordinate(
                customized,
                interactions
            )
            
            # Track cost
            await self.payment_service.charge_user(user_id, estimated_cost)
        
        return ContentResponse(...)
```

### Rate Limiting Per Tier

```python
from datetime import datetime, timedelta
import redis

class RateLimiter:
    def __init__(self):
        self.redis = redis.Redis(host='redis-cluster')
    
    TIER_LIMITS = {
        "free": {
            "layer3_daily": 5,      # 5 Layer 3 calls/day
            "layer4_daily": 0,      # 0 Layer 4 calls/day
            "layer3_hourly": 1      # 1 Layer 3 call/hour
        },
        "premium": {
            "layer3_daily": 50,     # 50 Layer 3 calls/day
            "layer4_daily": 5,      # 5 Layer 4 calls/day
            "layer3_hourly": 10     # 10 Layer 3 calls/hour
        },
        "whale": {
            "layer3_daily": -1,     # Unlimited
            "layer4_daily": -1,     # Unlimited
            "layer3_hourly": -1     # Unlimited (with cost alerts)
        }
    }
    
    async def check_limit(self, user_id: str, tier: str, layer: int) -> bool:
        limits = self.TIER_LIMITS[tier]
        
        if layer == 3:
            daily_key = f"rate_limit:{user_id}:layer3:daily"
            hourly_key = f"rate_limit:{user_id}:layer3:hourly"
            
            daily_count = await self.redis.get(daily_key) or 0
            hourly_count = await self.redis.get(hourly_key) or 0
            
            if limits["layer3_daily"] != -1 and int(daily_count) >= limits["layer3_daily"]:
                return False
            if limits["layer3_hourly"] != -1 and int(hourly_count) >= limits["layer3_hourly"]:
                return False
            
            # Increment counters
            await self.redis.incr(daily_key)
            await self.redis.expire(daily_key, 86400)  # 24 hours
            await self.redis.incr(hourly_key)
            await self.redis.expire(hourly_key, 3600)   # 1 hour
            
        elif layer == 4:
            daily_key = f"rate_limit:{user_id}:layer4:daily"
            daily_count = await self.redis.get(daily_key) or 0
            
            if limits["layer4_daily"] != -1 and int(daily_count) >= limits["layer4_daily"]:
                return False
            
            await self.redis.incr(daily_key)
            await self.redis.expire(daily_key, 86400)
        
        return True
```

### Cost Monitoring

```python
from prometheus_client import Gauge, Counter

cost_gauge = Gauge('cost_per_request_usd', 'Cost per request', ['layer', 'model'])
request_counter = Counter('llm_requests_total', 'Total LLM requests', ['layer', 'tier'])

class CostTracker:
    MODEL_COSTS = {
        "claude-4.5": 0.003,    # $0.003 per 1K tokens
        "gpt-5": 0.005,
        "gpt-4": 0.003,
        "gemini-2.5": 0.002
    }
    
    async def track_cost(self, layer: int, model: str, tokens: int, user_id: str):
        cost_per_1k = self.MODEL_COSTS.get(model, 0.001)
        cost = (tokens / 1000) * cost_per_1k
        
        # Record metrics
        cost_gauge.labels(layer=layer, model=model).set(cost)
        
        # Track per user
        daily_cost_key = f"cost:{user_id}:daily"
        await redis_cluster.incrbyfloat(daily_cost_key, cost)
        await redis_cluster.expire(daily_cost_key, 86400)
        
        # Check budget limit (Whale tier: $100/month)
        daily_cost = float(await redis_cluster.get(daily_cost_key) or 0)
        if daily_cost > 3.33:  # $100/30 days = $3.33/day
            send_alert(f"User {user_id} exceeded daily budget: ${daily_cost:.2f}")
```

### Fallback on Rate Limit Exceeded

```python
async def get_cached_orchestration(self, request: ContentRequest):
    """Return cached/pre-generated content when rate limit hit"""
    cache_key = f"orchestration:{hash(request.seed)}"
    cached = await redis_cluster.get(cache_key)
    
    if cached:
        return ContentResponse.from_json(cached)
    
    # Use Layer 1-2 only (no expensive Layer 3-4)
    foundation = await self.layer1.generate_base(request)
    customized = await self.layer2.customize(foundation)
    
    return ContentResponse(
        foundation=foundation,
        customized=customized,
        interactions=None,
        orchestration=None
    )
```

---

## CONNECTION POOLING ⭐ **NEW**

### gRPC Connection Pool Configuration

```python
import grpc
from grpc import aio

class ConnectionPool:
    def __init__(self, service_name: str, address: str, pool_size: int = 100):
        self.service_name = service_name
        self.address = address
        self.pool = []
        
        # Create connection pool
        for _ in range(pool_size):
            channel = aio.insecure_channel(
                address,
                options=[
                    ('grpc.keepalive_time_ms', 10000),
                    ('grpc.keepalive_timeout_ms', 5000),
                    ('grpc.keepalive_permit_without_calls', True),
                    ('grpc.http2.max_frame_size', 4194304),      # 4MB
                    ('grpc.http2.max_connection_window_size', 1048576000),  # 1GB
                ]
            )
            self.pool.append(channel)
        
        self.current = 0
    
    def get_channel(self):
        """Round-robin channel selection"""
        channel = self.pool[self.current]
        self.current = (self.current + 1) % len(self.pool)
        return channel

# Usage in Orchestration Service
inference_pool = ConnectionPool(
    "ai-inference",
    "ai-inference:50051",
    pool_size=100
)

async def call_inference_service(request):
    channel = inference_pool.get_channel()
    stub = InferenceServiceStub(channel)
    return await stub.GenerateDialogue(request)
```

---

**Next**: See `STATE-MANAGEMENT-SERVICE.md` for state persistence details.

