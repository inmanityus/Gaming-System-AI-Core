"""
Guardrails Policy Cache
=======================

Maintains in-memory cache of session content policies for fast lookup
during model inference and content generation.
"""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID

import aioredis
from loguru import logger

from services.settings.content_schemas import SessionContentPolicySnapshot


class PolicyCache:
    """
    LRU cache for session content policies with Redis fallback.
    
    Optimized for microsecond-latency lookups during inference.
    """
    
    def __init__(
        self,
        redis_url: str,
        max_size: int = 10000,
        ttl_seconds: int = 3600,
    ):
        self.redis_url = redis_url
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        
        # LRU cache: session_id -> (policy, expiry)
        self._cache: OrderedDict[UUID, Tuple[SessionContentPolicySnapshot, datetime]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._redis: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis for fallback storage."""
        self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        logger.info("PolicyCache connected to Redis")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    async def get_policy(
        self, 
        session_id: UUID,
        policy_version: Optional[int] = None,
    ) -> Optional[SessionContentPolicySnapshot]:
        """
        Get policy for session, checking memory cache first.
        
        Args:
            session_id: Session to look up
            policy_version: Specific version (optional)
            
        Returns:
            Policy snapshot if found and not expired
        """
        # Check memory cache first
        async with self._lock:
            cache_key = session_id
            if cache_key in self._cache:
                policy, expiry = self._cache[cache_key]
                if expiry > datetime.utcnow():
                    # Move to end (most recently used)
                    self._cache.move_to_end(cache_key)
                    
                    # Version check if specified
                    if policy_version is not None and policy.policy_version != policy_version:
                        logger.debug(f"Version mismatch for {session_id}: wanted {policy_version}, have {policy.policy_version}")
                        return None
                    
                    return policy
                else:
                    # Expired, remove from cache
                    del self._cache[cache_key]
        
        # Not in memory, check Redis
        if self._redis:
            redis_key = f"guardrails:policy:{session_id}"
            data = await self._redis.get(redis_key)
            if data:
                try:
                    policy_dict = json.loads(data)
                    policy = SessionContentPolicySnapshot(**policy_dict)
                    
                    # Version check
                    if policy_version is not None and policy.policy_version != policy_version:
                        return None
                    
                    # Add to memory cache
                    await self._set_in_memory(session_id, policy)
                    return policy
                    
                except Exception as e:
                    logger.error(f"Failed to deserialize policy from Redis: {e}")
        
        return None
    
    async def set_policy(
        self,
        session_id: UUID,
        policy: SessionContentPolicySnapshot,
    ) -> None:
        """
        Store policy in cache.
        
        Args:
            session_id: Session ID
            policy: Policy snapshot to cache
        """
        # Store in Redis first for persistence
        if self._redis:
            redis_key = f"guardrails:policy:{session_id}"
            data = json.dumps(policy.dict())
            await self._redis.setex(
                redis_key,
                int(self.ttl.total_seconds()),
                data
            )
        
        # Then update memory cache
        await self._set_in_memory(session_id, policy)
        
        logger.debug(f"Cached policy for session {session_id} (v{policy.policy_version})")
    
    async def _set_in_memory(
        self,
        session_id: UUID,
        policy: SessionContentPolicySnapshot,
    ) -> None:
        """Update memory cache with LRU eviction."""
        async with self._lock:
            cache_key = session_id
            expiry = datetime.utcnow() + self.ttl
            
            # If already exists, update and move to end
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                self._cache[cache_key] = (policy, expiry)
            else:
                # Add new entry
                self._cache[cache_key] = (policy, expiry)
                
                # Evict oldest if over capacity
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
    
    async def invalidate(self, session_id: UUID) -> None:
        """Remove policy from all caches."""
        # Remove from memory
        async with self._lock:
            self._cache.pop(session_id, None)
        
        # Remove from Redis
        if self._redis:
            redis_key = f"guardrails:policy:{session_id}"
            await self._redis.delete(redis_key)
        
        logger.debug(f"Invalidated policy for session {session_id}")
    
    async def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        async with self._lock:
            total = len(self._cache)
            
            # Count expired entries
            now = datetime.utcnow()
            expired = sum(1 for _, (_, expiry) in self._cache.items() if expiry <= now)
            
            return {
                "total_entries": total,
                "active_entries": total - expired,
                "expired_entries": expired,
                "max_size": self.max_size,
            }

