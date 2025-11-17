"""
Story Snapshot Cache
====================

High-performance caching layer for story snapshots.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID

import aioredis
from loguru import logger

from .story_schemas import StorySnapshot
from .story_state_manager import StoryStateManager
from .story_config import story_config


class SnapshotCache:
    """
    Multi-tier cache for story snapshots with Redis backing.
    
    Optimized for sub-50ms P99 latency requirement.
    """
    
    def __init__(
        self,
        story_manager: StoryStateManager,
        redis_url: str = None,
        ttl_seconds: int = None,
        max_memory_cache: int = None
    ):
        self.story_manager = story_manager
        self.redis_url = redis_url or story_config.redis_url
        self.ttl = timedelta(seconds=ttl_seconds or story_config.cache_ttl_seconds)
        self.max_memory_cache = max_memory_cache or story_config.cache_max_size
        
        # In-memory L1 cache
        self._memory_cache: Dict[UUID, Tuple[StorySnapshot, datetime]] = {}
        self._cache_lock = asyncio.Lock()
        
        # Redis L2 cache
        self.redis: Optional[aioredis.Redis] = None
        
        # Metrics
        self._hit_count = 0
        self._miss_count = 0
        self._latencies: list[float] = []
    
    async def connect(self) -> None:
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        logger.info("Snapshot cache connected to Redis")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
    
    async def get_snapshot(
        self,
        player_id: UUID,
        force_refresh: bool = False
    ) -> Optional[StorySnapshot]:
        """
        Get story snapshot with multi-tier caching.
        
        Args:
            player_id: Player ID
            force_refresh: Skip cache and force DB read
            
        Returns:
            Story snapshot if found
        """
        start_time = time.time()
        
        try:
            if not force_refresh:
                # Check L1 memory cache
                snapshot = await self._get_from_memory(player_id)
                if snapshot:
                    self._record_hit(time.time() - start_time)
                    return snapshot
                
                # Check L2 Redis cache
                snapshot = await self._get_from_redis(player_id)
                if snapshot:
                    # Promote to L1
                    await self._set_in_memory(player_id, snapshot)
                    self._record_hit(time.time() - start_time)
                    return snapshot
            
            # Cache miss - fetch from DB
            self._miss_count += 1
            snapshot = await self.story_manager.get_story_snapshot(player_id)
            
            if snapshot:
                # Populate both caches
                await self._set_in_redis(player_id, snapshot)
                await self._set_in_memory(player_id, snapshot)
            
            self._record_latency(time.time() - start_time)
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting snapshot for {player_id}: {e}")
            # Fall back to direct DB read
            return await self.story_manager.get_story_snapshot(player_id)
    
    async def invalidate(self, player_id: UUID) -> None:
        """
        Invalidate cached snapshot for a player.
        
        Called when story state changes.
        """
        # Remove from L1
        async with self._cache_lock:
            self._memory_cache.pop(player_id, None)
        
        # Remove from L2
        if self.redis:
            key = self._make_redis_key(player_id)
            await self.redis.delete(key)
        
        logger.debug(f"Invalidated snapshot cache for {player_id}")
    
    async def warm_cache(self, player_ids: list[UUID]) -> None:
        """Pre-warm cache for active players."""
        logger.info(f"Warming cache for {len(player_ids)} players")
        
        # Batch fetch snapshots
        tasks = [
            self.get_snapshot(player_id, force_refresh=True)
            for player_id in player_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r and not isinstance(r, Exception))
        logger.info(f"Cache warmed: {success_count}/{len(player_ids)} snapshots loaded")
    
    async def _get_from_memory(self, player_id: UUID) -> Optional[StorySnapshot]:
        """Get snapshot from memory cache."""
        async with self._cache_lock:
            if player_id in self._memory_cache:
                snapshot, expiry = self._memory_cache[player_id]
                if expiry > datetime.utcnow():
                    return snapshot
                else:
                    # Expired
                    del self._memory_cache[player_id]
        return None
    
    async def _get_from_redis(self, player_id: UUID) -> Optional[StorySnapshot]:
        """Get snapshot from Redis cache."""
        if not self.redis:
            return None
        
        try:
            key = self._make_redis_key(player_id)
            data = await self.redis.get(key)
            
            if data:
                snapshot_dict = json.loads(data)
                return StorySnapshot(**snapshot_dict)
        
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        
        return None
    
    async def _set_in_memory(self, player_id: UUID, snapshot: StorySnapshot) -> None:
        """Store snapshot in memory cache with LRU eviction."""
        async with self._cache_lock:
            expiry = datetime.utcnow() + self.ttl
            self._memory_cache[player_id] = (snapshot, expiry)
            
            # Evict oldest if over capacity
            if len(self._memory_cache) > self.max_memory_cache:
                # Find oldest entry
                oldest_id = None
                oldest_time = datetime.utcnow()
                
                for pid, (_, exp) in self._memory_cache.items():
                    if exp < oldest_time:
                        oldest_time = exp
                        oldest_id = pid
                
                if oldest_id:
                    del self._memory_cache[oldest_id]
    
    async def _set_in_redis(self, player_id: UUID, snapshot: StorySnapshot) -> None:
        """Store snapshot in Redis cache."""
        if not self.redis:
            return
        
        try:
            key = self._make_redis_key(player_id)
            data = json.dumps(snapshot.dict())
            
            await self.redis.setex(
                key,
                int(self.ttl.total_seconds()),
                data
            )
        
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def _make_redis_key(self, player_id: UUID) -> str:
        """Generate Redis key for player snapshot."""
        return f"{story_config.snapshot_cache_prefix}{player_id}"
    
    def _record_hit(self, latency: float) -> None:
        """Record cache hit."""
        self._hit_count += 1
        self._record_latency(latency)
    
    def _record_latency(self, latency: float) -> None:
        """Record latency measurement."""
        self._latencies.append(latency)
        
        # Keep only recent measurements
        if len(self._latencies) > 10000:
            self._latencies = self._latencies[-5000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
        
        # Calculate latency percentiles
        if self._latencies:
            sorted_latencies = sorted(self._latencies)
            p50_idx = int(len(sorted_latencies) * 0.5)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            
            p50_ms = sorted_latencies[p50_idx] * 1000
            p95_ms = sorted_latencies[p95_idx] * 1000
            p99_ms = sorted_latencies[p99_idx] * 1000
        else:
            p50_ms = p95_ms = p99_ms = 0
        
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "memory_cache_size": len(self._memory_cache),
            "latency_p50_ms": round(p50_ms, 2),
            "latency_p95_ms": round(p95_ms, 2),
            "latency_p99_ms": round(p99_ms, 2),
        }

