"""
Social Memory & Relationship Graph System - Persistent NPC memory.

Implements REQ-NPC-003: Social Memory & Relationship Graph.

NPCs remember player interactions, track relationships, and reference past events.
"""

import json
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# REFACTORING: Direct database imports replaced with on-demand connections
# from state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool
import asyncpg
import redis.asyncio as redis
from typing import Optional, Any as PostgreSQLPool, Any as RedisPool

_logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """Sentiment types in relationships."""
    TRUST = "trust"
    FEAR = "fear"
    RESPECT = "respect"
    DISGUST = "disgust"
    AFFECTION = "affection"
    ANGER = "anger"
    NEUTRAL = "neutral"


@dataclass
class Relationship:
    """Relationship between two entities."""
    npc_id: UUID
    target_id: UUID  # Player or other NPC
    target_type: str  # "player" or "npc"
    
    # Sentiment scores (0.0 to 1.0)
    sentiments: Dict[str, float] = field(default_factory=dict)
    
    # Overall relationship score (-1.0 to 1.0)
    relationship_score: float = 0.0
    
    # Interaction history
    interaction_count: int = 0
    first_interaction_time: float = 0.0
    last_interaction_time: float = 0.0
    
    # Notable events
    notable_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "npc_id": str(self.npc_id),
            "target_id": str(self.target_id),
            "target_type": self.target_type,
            "sentiments": self.sentiments,
            "relationship_score": self.relationship_score,
            "interaction_count": self.interaction_count,
            "first_interaction_time": self.first_interaction_time,
            "last_interaction_time": self.last_interaction_time,
            "notable_events": self.notable_events,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """Create from dictionary."""
        return cls(
            npc_id=UUID(data["npc_id"]),
            target_id=UUID(data["target_id"]),
            target_type=data["target_type"],
            sentiments=data.get("sentiments", {}),
            relationship_score=data.get("relationship_score", 0.0),
            interaction_count=data.get("interaction_count", 0),
            first_interaction_time=data.get("first_interaction_time", 0.0),
            last_interaction_time=data.get("last_interaction_time", 0.0),
            notable_events=data.get("notable_events", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryEvent:
    """A memorable event in NPC memory."""
    event_id: str
    npc_id: UUID
    target_id: UUID
    event_type: str  # "dialogue", "combat", "trade", "quest", etc.
    description: str
    sentiment_impact: Dict[str, float]  # How this event affects sentiments
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0.0 (forgettable) to 1.0 (very memorable)
    context: Dict[str, Any] = field(default_factory=dict)


class SocialMemoryGraph:
    """
    Manages social memory and relationship graph for NPCs.
    
    Tracks relationships, memories, and sentiments between NPCs and players.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._relationships: Dict[Tuple[UUID, UUID], Relationship] = {}
        self._memory_events: Dict[str, MemoryEvent] = {}
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = get_state_manager_client()
        return self.redis
    
    async def get_relationship(
        self,
        npc_id: UUID,
        target_id: UUID
    ) -> Optional[Relationship]:
        """
        Get relationship between NPC and target.
        
        Args:
            npc_id: NPC UUID
            target_id: Target UUID (player or other NPC)
        
        Returns:
            Relationship object or None if not found
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        if not isinstance(target_id, UUID):
            raise TypeError(f"target_id must be UUID, got {type(target_id)}")
        
        # Check cache first
        cache_key = (npc_id, target_id)
        if cache_key in self._relationships:
            return self._relationships[cache_key]
        
        # Load from database
        try:
            postgres = await self._get_postgres()
            query = """
                SELECT npc_id, target_id, target_type, sentiments, relationship_score,
                       interaction_count, first_interaction_time, last_interaction_time,
                       notable_events, metadata
                FROM npc_relationships
                WHERE npc_id = $1 AND target_id = $2
            """
            
            result = await postgres.fetch(query, npc_id, target_id)
        except Exception as e:
            _logger.error(f"Database error getting relationship for NPC {npc_id} and target {target_id}: {e}")
            raise
        
        if result:
            relationship = Relationship.from_dict({
                "npc_id": str(result["npc_id"]),
                "target_id": str(result["target_id"]),
                "target_type": result["target_type"],
                "sentiments": json.loads(result["sentiments"]) if isinstance(result["sentiments"], str) else result["sentiments"],
                "relationship_score": result["relationship_score"],
                "interaction_count": result["interaction_count"],
                "first_interaction_time": result["first_interaction_time"],
                "last_interaction_time": result["last_interaction_time"],
                "notable_events": json.loads(result["notable_events"]) if isinstance(result["notable_events"], str) else result["notable_events"],
                "metadata": json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"],
            })
            self._relationships[cache_key] = relationship
            return relationship
        
        # Create new relationship
        relationship = Relationship(
            npc_id=npc_id,
            target_id=target_id,
            target_type="player"  # Default, could be determined from context
        )
        self._relationships[cache_key] = relationship
        return relationship
    
    async def record_interaction(
        self,
        npc_id: UUID,
        target_id: UUID,
        interaction_type: str,
        description: str,
        sentiment_impact: Optional[Dict[str, float]] = None,
        importance: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record an interaction and update relationship.
        
        Args:
            npc_id: NPC UUID
            target_id: Target UUID
            interaction_type: Type of interaction
            description: Description of interaction
            sentiment_impact: Optional sentiment changes
            importance: Importance score (0.0-1.0)
            context: Optional context dictionary
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        if not isinstance(target_id, UUID):
            raise TypeError(f"target_id must be UUID, got {type(target_id)}")
        if not isinstance(interaction_type, str) or not interaction_type.strip():
            raise ValueError(f"interaction_type must be non-empty string, got {interaction_type}")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"description must be non-empty string, got {description}")
        if not isinstance(importance, (int, float)) or not 0.0 <= float(importance) <= 1.0:
            raise ValueError(f"importance must be between 0.0 and 1.0, got {importance}")
        if sentiment_impact is not None:
            if not isinstance(sentiment_impact, dict):
                raise TypeError(f"sentiment_impact must be dict or None, got {type(sentiment_impact)}")
            for key, value in sentiment_impact.items():
                if not isinstance(value, (int, float)):
                    raise TypeError(f"sentiment_impact[{key}] must be numeric, got {type(value)}")
        
        try:
            relationship = await self.get_relationship(npc_id, target_id)
        except Exception as e:
            _logger.error(f"Error getting relationship for interaction: {e}")
            raise
        
        # Update interaction count and timestamps
        if relationship.interaction_count == 0:
            relationship.first_interaction_time = time.time()
        relationship.interaction_count += 1
        relationship.last_interaction_time = time.time()
        
        # Apply sentiment impact
        if sentiment_impact:
            for sentiment_type, impact in sentiment_impact.items():
                current_value = relationship.sentiments.get(sentiment_type, 0.0)
                # Clamp to 0.0-1.0 range
                new_value = max(0.0, min(1.0, current_value + impact))
                relationship.sentiments[sentiment_type] = new_value
        
        # Calculate relationship score from sentiments
        relationship.relationship_score = self._calculate_relationship_score(relationship.sentiments)
        
        # Create memory event if important
        if importance > 0.3:
            event = MemoryEvent(
                event_id=f"{npc_id}_{target_id}_{int(time.time())}",
                npc_id=npc_id,
                target_id=target_id,
                event_type=interaction_type,
                description=description,
                sentiment_impact=sentiment_impact or {},
                importance=importance,
                context=context or {}
            )
            relationship.notable_events.append(event.to_dict())
            self._memory_events[event.event_id] = event
        
        # Save to database
        try:
            await self._save_relationship(relationship)
        except Exception as e:
            _logger.error(f"Error saving relationship after interaction: {e}")
            raise
    
    def _calculate_relationship_score(self, sentiments: Dict[str, float]) -> float:
        """Calculate overall relationship score from sentiments."""
        # Positive sentiments increase score, negative decrease
        positive_sentiments = {
            "trust": 0.3,
            "respect": 0.2,
            "affection": 0.3,
        }
        negative_sentiments = {
            "fear": -0.2,
            "disgust": -0.3,
            "anger": -0.3,
        }
        
        score = 0.0
        for sentiment_type, weight in positive_sentiments.items():
            score += sentiments.get(sentiment_type, 0.0) * weight
        
        for sentiment_type, weight in negative_sentiments.items():
            score += sentiments.get(sentiment_type, 0.0) * weight
        
        # Clamp to -1.0 to 1.0
        return max(-1.0, min(1.0, score))
    
    async def _save_relationship(self, relationship: Relationship):
        """
        Save relationship to database.
        
        Args:
            relationship: Relationship object to save
        
        Raises:
            ValueError: If relationship is invalid
        """
        if not isinstance(relationship, Relationship):
            raise TypeError(f"relationship must be Relationship, got {type(relationship)}")
        
        try:
            postgres = await self._get_postgres()
        except Exception as e:
            _logger.error(f"Error getting postgres connection: {e}")
            raise
        
        # Check if exists
        check_query = """
            SELECT npc_id FROM npc_relationships
            WHERE npc_id = $1 AND target_id = $2
        """
        exists = await postgres.fetch(check_query, relationship.npc_id, relationship.target_id)
        
        if exists:
            # Update
            update_query = """
                UPDATE npc_relationships
                SET sentiments = $1::jsonb,
                    relationship_score = $2,
                    interaction_count = $3,
                    first_interaction_time = to_timestamp($4),
                    last_interaction_time = to_timestamp($5),
                    notable_events = $6::jsonb,
                    metadata = $7::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE npc_id = $8 AND target_id = $9
            """
            await postgres.execute(
                update_query,
                json.dumps(relationship.sentiments),
                relationship.relationship_score,
                relationship.interaction_count,
                relationship.first_interaction_time,
                relationship.last_interaction_time,
                json.dumps(relationship.notable_events),
                json.dumps(relationship.metadata),
                relationship.npc_id,
                relationship.target_id
            )
        else:
            # Insert
            insert_query = """
                INSERT INTO npc_relationships
                (npc_id, target_id, target_type, sentiments, relationship_score,
                 interaction_count, first_interaction_time, last_interaction_time,
                 notable_events, metadata, created_at, updated_at)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6, to_timestamp($7), to_timestamp($8),
                        $9::jsonb, $10::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            await postgres.execute(
                insert_query,
                relationship.npc_id,
                relationship.target_id,
                relationship.target_type,
                json.dumps(relationship.sentiments),
                relationship.relationship_score,
                relationship.interaction_count,
                relationship.first_interaction_time,
                relationship.last_interaction_time,
                json.dumps(relationship.notable_events),
                json.dumps(relationship.metadata)
            )
        
        # Update Redis cache
        try:
            redis = await self._get_redis()
            cache_key = f"npc:relationship:{relationship.npc_id}:{relationship.target_id}"
            await redis.hset(cache_key, mapping={
                "relationship_score": str(relationship.relationship_score),
                "interaction_count": str(relationship.interaction_count),
                "last_interaction": str(relationship.last_interaction_time),
            })
            await redis.expire(cache_key, 3600)  # 1 hour TTL
        except Exception as e:
            _logger.warning(f"Error updating Redis cache for relationship: {e}")
            # Don't raise - cache failures are non-critical
    
    async def get_memorable_events(
        self,
        npc_id: UUID,
        target_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[MemoryEvent]:
        """
        Get memorable events for NPC.
        
        Args:
            npc_id: NPC UUID
            target_id: Optional target UUID to filter events
            limit: Maximum number of events to return
        
        Returns:
            List of MemoryEvent objects
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        if target_id is not None and not isinstance(target_id, UUID):
            raise TypeError(f"target_id must be UUID or None, got {type(target_id)}")
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise ValueError(f"limit must be between 1 and 1000, got {limit}")
        
        try:
            relationship = await self.get_relationship(npc_id, target_id) if target_id else None
        except Exception as e:
            _logger.error(f"Error getting relationship for memorable events: {e}")
            return []
        
        if relationship:
            # Return notable events from relationship
            events = []
            for event_data in relationship.notable_events[-limit:]:
                event = MemoryEvent(
                    event_id=event_data.get("event_id", ""),
                    npc_id=UUID(event_data["npc_id"]),
                    target_id=UUID(event_data["target_id"]),
                    event_type=event_data["event_type"],
                    description=event_data["description"],
                    sentiment_impact=event_data.get("sentiment_impact", {}),
                    timestamp=event_data.get("timestamp", time.time()),
                    importance=event_data.get("importance", 0.5),
                    context=event_data.get("context", {})
                )
                events.append(event)
            return events
        
        return []
    
    async def get_dialogue_context(
        self,
        npc_id: UUID,
        target_id: UUID
    ) -> Dict[str, Any]:
        """Get dialogue context based on relationship."""
        relationship = await self.get_relationship(npc_id, target_id)
        events = await self.get_memorable_events(npc_id, target_id, limit=5)
        
        return {
            "relationship_score": relationship.relationship_score,
            "sentiments": relationship.sentiments,
            "interaction_count": relationship.interaction_count,
            "recent_events": [
                {
                    "type": event.event_type,
                    "description": event.description,
                    "timestamp": event.timestamp,
                }
                for event in events
            ],
            "first_met": relationship.first_interaction_time,
            "last_met": relationship.last_interaction_time,
        }
    
    async def get_all_relationships(self, npc_id: UUID) -> List[Relationship]:
        """
        Get all relationships for an NPC.
        
        Args:
            npc_id: NPC UUID
        
        Returns:
            List of Relationship objects
        
        Raises:
            ValueError: If npc_id is invalid
        """
        # Input validation
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        
        try:
            postgres = await self._get_postgres()
            query = """
                SELECT npc_id, target_id, target_type, sentiments, relationship_score,
                       interaction_count, first_interaction_time, last_interaction_time,
                       notable_events, metadata
                FROM npc_relationships
                WHERE npc_id = $1
                ORDER BY last_interaction_time DESC
            """
            
            results = await postgres.fetch(query, npc_id)
        except Exception as e:
            _logger.error(f"Database error getting all relationships for NPC {npc_id}: {e}")
            raise
        relationships = []
        
        for result in results:
            relationship = Relationship.from_dict({
                "npc_id": str(result["npc_id"]),
                "target_id": str(result["target_id"]),
                "target_type": result["target_type"],
                "sentiments": json.loads(result["sentiments"]) if isinstance(result["sentiments"], str) else result["sentiments"],
                "relationship_score": result["relationship_score"],
                "interaction_count": result["interaction_count"],
                "first_interaction_time": result["first_interaction_time"],
                "last_interaction_time": result["last_interaction_time"],
                "notable_events": json.loads(result["notable_events"]) if isinstance(result["notable_events"], str) else result["notable_events"],
                "metadata": json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"],
            })
            relationships.append(relationship)
            # Cache
            cache_key = (relationship.npc_id, relationship.target_id)
            self._relationships[cache_key] = relationship
        
        return relationships


# Helper function for MemoryEvent serialization
def memory_event_to_dict(event: MemoryEvent) -> Dict[str, Any]:
    """Convert MemoryEvent to dictionary."""
    return {
        "event_id": event.event_id,
        "npc_id": str(event.npc_id),
        "target_id": str(event.target_id),
        "event_type": event.event_type,
        "description": event.description,
        "sentiment_impact": event.sentiment_impact,
        "timestamp": event.timestamp,
        "importance": event.importance,
        "context": event.context,
    }

# Add to_dict method to MemoryEvent
MemoryEvent.to_dict = memory_event_to_dict

