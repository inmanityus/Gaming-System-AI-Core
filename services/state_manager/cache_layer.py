"""
Redis Cache Layer
Implements caching strategy for game state with >80% hit rate target.
"""

import json
from typing import Any, Dict, Optional
from uuid import UUID

from .connection_pool import get_redis_pool, RedisPool


class CacheHitRateTracker:
    """Tracks cache hit/miss rates for monitoring."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    @property
    def total_requests(self) -> int:
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        total = self.total_requests
        if total == 0:
            return 0.0
        return (self.hits / total) * 100.0
    
    def reset(self):
        self.hits = 0
        self.misses = 0


class CacheLayer:
    """
    Redis caching layer for game state.
    Implements read-through and write-through caching strategies.
    """
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache layer.
        
        Args:
            ttl: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self.redis: Optional[RedisPool] = None
        self.hit_rate_tracker = CacheHitRateTracker()
        self._key_prefix = "state:"
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = await get_redis_pool()
        return self.redis
    
    def _make_key(self, entity_type: str, entity_id: UUID) -> str:
        """Generate cache key for entity."""
        return f"{self._key_prefix}{entity_type}:{str(entity_id)}"
    
    async def get(self, entity_type: str, entity_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get entity state from cache.
        
        Args:
            entity_type: Type of entity (e.g., "game_state", "player")
            entity_id: UUID of the entity
        
        Returns:
            Entity state dict if found, None otherwise
        """
        redis = await self._get_redis()
        key = self._make_key(entity_type, entity_id)
        
        # Try to get from Redis hash
        cached_data = await redis.hgetall(key)
        
        if cached_data:
            self.hit_rate_tracker.record_hit()
            # Parse JSON values if needed
            parsed = {}
            for k, v in cached_data.items():
                try:
                    parsed[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    parsed[k] = v
            return parsed
        
        self.hit_rate_tracker.record_miss()
        return None
    
    async def set(self, entity_type: str, entity_id: UUID, state: Dict[str, Any]):
        """
        Set entity state in cache (write-through).
        
        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity
            state: State data to cache
        """
        redis = await self._get_redis()
        key = self._make_key(entity_type, entity_id)
        
        # Convert dict values to JSON strings for Redis hash
        serialized = {}
        for k, v in state.items():
            if isinstance(v, (dict, list)):
                serialized[k] = json.dumps(v)
            else:
                serialized[k] = str(v)
        
        # Store in Redis hash with TTL
        await redis.hset(key, mapping=serialized)
        await redis.expire(key, self.ttl)
    
    async def delete(self, entity_type: str, entity_id: UUID):
        """
        Delete entity state from cache.
        
        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity
        """
        redis = await self._get_redis()
        key = self._make_key(entity_type, entity_id)
        await redis.delete(key)
    
    def get_hit_rate(self) -> float:
        """Get current cache hit rate percentage."""
        return self.hit_rate_tracker.hit_rate
    
    def reset_stats(self):
        """Reset hit/miss statistics."""
        self.hit_rate_tracker.reset()
