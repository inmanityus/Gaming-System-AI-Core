# Cache Invalidation Strategy
**Date**: January 29, 2025  
**Critical**: High Priority - Blocks Production Launch

---

## OVERVIEW

Complete cache invalidation strategy for multi-tier caching system (L1: UE5 Client, L2: Redis Edge, L3: Distributed Cloud/Semantic).

---

## CACHE TTL MATRIX

### By Content Type

| Content Type | L1 TTL | L2 TTL | L3 TTL | Invalidation Trigger |
|--------------|--------|--------|--------|---------------------|
| **Static Content** (Lore, World Facts) | 24hr | 24hr | 7 days | Only on game updates |
| **NPC Dialogue Templates** | 1hr | 4hr | 24hr | When NPC personality updated |
| **Dynamic NPC Dialogue** | 5min | 30min | 2hr | When player-NPC relationship changes |
| **Real-Time Content** (Market Prices) | 30s | 5min | 15min | Every market update (5s intervals) |
| **Monster Generation** | 15min | 1hr | 6hr | When monster behavior evolves |
| **Terrain/Room Generation** | 1hr | 6hr | 24hr | Only on world regeneration |
| **Orchestration Plans** | N/A | 10min | 1hr | When story state changes globally |

---

## INVALIDATION PATTERNS

### Pattern 1: Relationship-Based Invalidation

```python
class CacheInvalidator:
    def __init__(self):
        self.redis = redis_cluster
        self.pg = postgres_pool
    
    async def invalidate_npc_dialogue(self, npc_id: str, player_id: str):
        """Invalidate when player-NPC relationship changes"""
        # Invalidate L1 (client cache)
        # Client receives invalidation via WebSocket message
        await websocket.send_to_client(player_id, {
            "type": "cache_invalidate",
            "keys": [f"dialogue:{npc_id}"]
        })
        
        # Invalidate L2 (Redis)
        keys = [
            f"L2:dialogue:{npc_id}:{player_id}",
            f"L2:dialogue:{npc_id}:*"  # All dialogues for this NPC
        ]
        for key in keys:
            await self.redis.delete(key)
        
        # Invalidate L3 (semantic cache) - partial
        # Only invalidate exact matches, keep similar content
        await self.invalidate_semantic_cache(
            query="dialogue with {npc_id}",
            similarity_threshold=0.95
        )
```

### Pattern 2: Version-Based Invalidation

```python
# All cached items include version metadata
class CachedResponse:
    content: Any
    version: int
    cache_key: str
    expires_at: datetime
    invalidation_keys: List[str]  # Keys to invalidate together

# When story state changes globally
async def invalidate_global_story_state(self, story_version: int):
    """Invalidate all content tied to story version"""
    # Find all cache entries with version < story_version
    invalid_keys = await self.redis.keys(f"*:version:{story_version}*")
    
    for key in invalid_keys:
        cached = await self.get_cache_entry(key)
        if cached.version < story_version:
            await self.redis.delete(key)
            
            # Cascade to related keys
            for related_key in cached.invalidation_keys:
                await self.invalidate_cache(related_key)
```

### Pattern 3: Time-Based Invalidation (TTL)

```python
# Set TTL when caching
async def cache_with_ttl(self, key: str, value: Any, ttl_seconds: int):
    await self.redis.setex(
        key,
        ttl_seconds,
        json.dumps(value)
    )
    
    # For L1 cache, send TTL to client
    await websocket.send_to_client(player_id, {
        "type": "cache_ttl",
        "key": key,
        "ttl_seconds": ttl_seconds
    })
```

### Pattern 4: Event-Driven Invalidation

```python
# Subscribe to invalidation events
class CacheInvalidationSubscriber:
    async def on_story_state_change(self, event: StoryStateChangeEvent):
        """Invalidate when story state changes"""
        affected_npcs = event.affected_npcs
        for npc_id in affected_npcs:
            await self.invalidate_npc_dialogue(npc_id, event.player_id)
    
    async def on_moderation_update(self, event: ModerationUpdateEvent):
        """Invalidate when moderation blacklist updates"""
        # Invalidate all cached responses that might contain blacklisted terms
        await self.invalidate_by_content_hash(event.blacklist_hashes)
    
    async def on_model_update(self, event: ModelUpdateEvent):
        """Invalidate when model version updates"""
        await self.invalidate_by_model_version(
            model_name=event.model_name,
            old_version=event.old_version
        )
```

---

## CACHE CONSISTENCY MODEL

### Consistency Guarantees

**L1 (Client Cache) - Weak Consistency**:
- May be stale for up to TTL duration
- Invalidated via WebSocket push when server detects change
- Client should verify with server on critical operations

**L2 (Redis Edge) - Eventual Consistency**:
- Invalidation propagated within 5 seconds
- Read-your-writes: Same client sees updates immediately
- Other clients see updates after propagation

**L3 (Semantic Cache) - Weak Consistency**:
- Updates propagated within 1 hour
- Used for rare queries, not time-sensitive

### Invalidation Cascade

```python
async def invalidate_cache_cascade(self, key: str, content_type: str):
    """Cascade invalidation across all tiers"""
    
    # 1. Invalidate L3 (semantic) - async, low priority
    asyncio.create_task(self.invalidate_l3_semantic(key))
    
    # 2. Invalidate L2 (Redis) - immediate
    await self.redis.delete(key)
    # Invalidate related keys (pattern matching)
    related_keys = await self.redis.keys(f"{key}*")
    await self.redis.delete(*related_keys)
    
    # 3. Invalidate L1 (client) - push notification
    players_affected = await self.get_players_with_cache_key(key)
    for player_id in players_affected:
        await websocket.send_to_client(player_id, {
            "type": "cache_invalidate",
            "key": key
        })
```

---

## SPECIFIC INVALIDATION SCENARIOS

### Scenario 1: NPC Personality Evolution

```python
async def update_npc_personality(self, npc_id: str, new_personality: dict):
    """When NPC personality evolves from player interaction"""
    # Update in database
    await self.pg.update_npc_personality(npc_id, new_personality)
    
    # Invalidate all cached dialogues for this NPC
    await self.invalidate_cache_cascade(
        key=f"dialogue:{npc_id}",
        content_type="npc_dialogue"
    )
    
    # Invalidate orchestration plans involving this NPC
    await self.invalidate_orchestration_plans(npc_id=npc_id)
```

### Scenario 2: Moderation Blacklist Update

```python
async def update_moderation_blacklist(self, new_terms: List[str]):
    """When moderation blacklist is updated"""
    # Compute content hashes for blacklisted terms
    blacklist_hashes = [hash_term(term) for term in new_terms]
    
    # Invalidate cached responses containing these terms
    await self.invalidate_by_content_hash(blacklist_hashes)
    
    # Mark for re-moderation in background
    await self.queue_re_moderation(blacklist_hashes)
```

### Scenario 3: Global Story State Change

```python
async def update_story_state(self, story_state: StoryState):
    """When story state changes globally (quest completion, faction change)"""
    # Invalidate orchestration plans
    await self.invalidate_cache_cascade(
        key="orchestration:*",
        content_type="orchestration"
    )
    
    # Invalidate NPC dialogues that reference story state
    affected_npcs = story_state.affected_npcs
    for npc_id in affected_npcs:
        await self.invalidate_npc_dialogue(npc_id, None)  # All players
```

---

## CACHE VERSION HEADERS

### Version Tracking

```python
# Include version in cache responses
class CacheResponse:
    content: Any
    version: int
    cache_control: str  # "max-age=300, must-revalidate"
    etag: str  # Content hash for validation

# Client requests with version
GET /api/v1/dialogue?npc_id=123&cache_version=5

# Server compares versions
if client_version < server_version:
    return CacheResponse(
        content=new_content,
        version=server_version,
        cache_control="max-age=300"
    )
else:
    return HTTP 304 Not Modified
```

---

## MONITORING & ALERTING

### Cache Health Metrics

```python
from prometheus_client import Gauge, Counter

cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate', ['tier'])
cache_invalidation_count = Counter('cache_invalidations_total', 'Total invalidations', ['reason'])
stale_cache_served = Counter('stale_cache_served_total', 'Stale cache hits', ['tier'])

async def monitor_cache_health(self):
    """Monitor cache effectiveness"""
    l1_hit_rate = await self.get_cache_hit_rate("L1")
    l2_hit_rate = await self.get_cache_hit_rate("L2")
    l3_hit_rate = await self.get_cache_hit_rate("L3")
    
    cache_hit_rate.labels(tier="L1").set(l1_hit_rate)
    cache_hit_rate.labels(tier="L2").set(l2_hit_rate)
    cache_hit_rate.labels(tier="L3").set(l3_hit_rate)
    
    # Alert if hit rate drops below 80%
    if l2_hit_rate < 0.80:
        send_alert("L2 cache hit rate below 80%", severity="warning")
```

---

**Status**: Complete cache invalidation strategy documented

