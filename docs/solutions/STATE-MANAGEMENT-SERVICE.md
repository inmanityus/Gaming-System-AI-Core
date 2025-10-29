# State Management Service Solution
**Service**: Game State, Semantic Memory, Event Sourcing  
**Date**: January 29, 2025

---

## SERVICE OVERVIEW

Provides centralized game state management, semantic memory for NPCs, and event sourcing for rollback capability.

---

## ARCHITECTURE

### Technology Stack
- **Hot State**: Redis (in-memory)
- **Persistent State**: PostgreSQL
- **Semantic Memory**: Pinecone/Weaviate (vector DB)
- **Events**: PostgreSQL + Event Store

### State Structure

```python
class GameState:
    entities: Dict[UUID, Entity]  # NPCs, items, locations
    world_state: WorldState  # Time, weather, factions
    player_history: List[Event]  # Actions, relationships
    narrative_state: NarrativeState  # Plot progression
```

### Redis Hot State
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def update_entity_state(entity_id, state_changes):
    key = f"entity:{entity_id}"
    redis_client.hset(key, mapping=state_changes)
    redis_client.expire(key, 3600)  # TTL

def get_entity_state(entity_id):
    key = f"entity:{entity_id}"
    return redis_client.hgetall(key)
```

### PostgreSQL Persistent State
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    type VARCHAR(50),
    data JSONB,
    updated_at TIMESTAMP
);

CREATE TABLE player_history (
    id SERIAL PRIMARY KEY,
    player_id UUID,
    action VARCHAR(100),
    context JSONB,
    timestamp TIMESTAMP
);
```

### Vector Database (Semantic Memory)
```python
import pinecone

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone.Index("npc-memories")

def store_npc_memory(npc_id, memory_text, embedding):
    index.upsert(
        vectors=[{
            'id': f"{npc_id}_{timestamp}",
            'values': embedding,
            'metadata': {
                'npc_id': npc_id,
                'text': memory_text
            }
        }]
    )

def retrieve_relevant_memories(npc_id, query_embedding, top_k=5):
    results = index.query(
        vector=query_embedding,
        filter={'npc_id': npc_id},
        top_k=top_k
    )
    return results
```

### Event Sourcing
```python
class EventStore:
    def append_event(self, event: Event):
        # Write to PostgreSQL
        self.pg.execute(
            "INSERT INTO events (stream_id, event_type, data) VALUES (%s, %s, %s)",
            (event.stream_id, event.type, event.data)
        )
    
    def get_stream_events(self, stream_id):
        events = self.pg.fetch_all(
            "SELECT * FROM events WHERE stream_id = %s ORDER BY sequence",
            (stream_id,)
        )
        return events
    
    def replay_events(self, stream_id, target_sequence=None):
        events = self.get_stream_events(stream_id)
        if target_sequence:
            events = [e for e in events if e.sequence <= target_sequence]
        return self.apply_events(events)
```

---

**Next**: See `LEARNING-SERVICE.md` for how feedback feeds into model improvement.

