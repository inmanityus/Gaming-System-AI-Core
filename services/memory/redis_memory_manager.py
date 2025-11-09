"""
Redis Memory Manager - Level 2 Memory (Sub-ms Latency)
Coder: Claude Sonnet 4.5
Peer Review Lessons Applied

30-day rolling window storage:
- Session summaries (300-600 chars)
- Salient memories
- Relationship cards
- Quest state cards
- Emotional trajectory

Redis patterns from peer review:
- Atomic operations (SETEX, ZADD)
- Per-NPC keys (npc:<id>:type)
- TTL on all keys
- Batch operations where possible
"""

import json
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


@dataclass
class SessionSummary:
    """Session summary (300-600 chars)."""
    session_id: str
    npc_id: str
    player_id: str
    start_time: datetime
    end_time: datetime
    summary_text: str
    emotional_tone: str
    key_topics: List[str]
    important_decisions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'npc_id': self.npc_id,
            'player_id': self.player_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'summary_text': self.summary_text,
            'emotional_tone': self.emotional_tone,
            'key_topics': self.key_topics,
            'important_decisions': self.important_decisions
        }


@dataclass
class SalientMemory:
    """Salient memory atom."""
    memory_id: str
    npc_id: str
    player_id: str
    memory_type: str
    description: str
    emotional_impact: float
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'memory_id': self.memory_id,
            'npc_id': self.npc_id,
            'player_id': self.player_id,
            'memory_type': self.memory_type,
            'description': self.description,
            'emotional_impact': self.emotional_impact,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class RedisMemoryManager:
    """
    Level 2: Redis (sub-ms, 30-day window).
    
    Key structure:
    - npc:<npc_id>:sessions - List
    - npc:<npc_id>:salient - List
    - npc:<npc_id>:relationship - String (JSON)
    - npc:<npc_id>:quest - String (JSON)
    - npc:<npc_id>:emotional - Sorted Set
    """
    
    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 1,
        ttl_days: int = 30
    ):
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db
        self.ttl_seconds = ttl_days * 24 * 3600
        
        self.redis_client: Optional[Any] = None
        self._init_gate = asyncio.Event()
        
        logger.info(f"RedisMemoryManager initialized: ttl={ttl_days} days")
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if not aioredis:
            raise RuntimeError("redis.asyncio not available")
        
        try:
            redis_url = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
            self.redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await self.redis_client.ping()
            self._init_gate.set()
            logger.info("✅ Redis memory manager connected")
        except Exception as e:
            logger.error(f"Redis init failed: {e}")
            raise
    
    async def add_session_summary(
        self,
        npc_id: str,
        summary: SessionSummary
    ) -> None:
        """Add session summary."""
        await self._init_gate.wait()
        
        key = f"npc:{npc_id}:sessions"
        value = json.dumps(summary.to_dict())
        
        await self.redis_client.rpush(key, value)
        await self.redis_client.expire(key, self.ttl_seconds)
    
    async def set_relationship_card(
        self,
        npc_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Store relationship card."""
        await self._init_gate.wait()
        
        key = f"npc:{npc_id}:relationship"
        await self.redis_client.setex(key, self.ttl_seconds, json.dumps(data))
    
    async def get_relationship_card(
        self,
        npc_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get relationship card."""
        await self._init_gate.wait()
        
        key = f"npc:{npc_id}:relationship"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()

