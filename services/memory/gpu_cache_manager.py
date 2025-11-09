"""
GPU Cache Manager - Level 1 Memory (Instant Access)
Coder: Claude Sonnet 4.5
Applying lessons from peer review

Stores in-memory (Python dict) for instant access:
- Last 12-20 conversation turns per NPC
- Relationship cards (trust/affinity, promises, betrayals)
- Quest state cards (active quests, milestones)
- TTL: 30 minutes after last interaction

Lessons Applied:
- asyncio.Event gate for initialization
- Minimal lock scope
- TTL-based expiry
- LRU eviction
- Proper async patterns
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single conversation turn."""
    npc_id: str
    turn_number: int
    player_input: str
    npc_response: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipCard:
    """Relationship card (≤2 KB per Storyteller guidance)."""
    npc_id: str
    player_id: str
    trust_score: float = 0.0
    affinity_score: float = 0.0
    promises_made: List[str] = field(default_factory=list)
    promises_kept: List[str] = field(default_factory=list)
    promises_broken: List[str] = field(default_factory=list)
    betrayals: List[Dict[str, Any]] = field(default_factory=list)
    gifts_given: List[Dict[str, Any]] = field(default_factory=list)
    insults: List[str] = field(default_factory=list)
    life_saving_events: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize."""
        return {
            'npc_id': self.npc_id,
            'player_id': self.player_id,
            'trust_score': self.trust_score,
            'affinity_score': self.affinity_score,
            'promises_made': self.promises_made,
            'promises_kept': self.promises_kept,
            'promises_broken': self.promises_broken,
            'betrayals': self.betrayals,
            'gifts_given': self.gifts_given,
            'insults': self.insults,
            'life_saving_events': self.life_saving_events,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


@dataclass
class QuestStateCard:
    """Quest state card (≤2 KB per Storyteller guidance)."""
    npc_id: str
    player_id: str
    active_quests: List[Dict[str, Any]] = field(default_factory=list)
    completed_milestones: List[str] = field(default_factory=list)
    quest_flags: Dict[str, bool] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize."""
        return {
            'npc_id': self.npc_id,
            'player_id': self.player_id,
            'active_quests': self.active_quests,
            'completed_milestones': self.completed_milestones,
            'quest_flags': self.quest_flags,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


@dataclass
class NPCCacheEntry:
    """Complete cache entry for one NPC."""
    npc_id: str
    conversation_turns: List[ConversationTurn]
    relationship_card: Optional[RelationshipCard]
    quest_state_card: Optional[QuestStateCard]
    last_accessed: datetime
    expires_at: datetime
    created_at: datetime
    
    def is_expired(self) -> bool:
        """Check if entry expired."""
        return datetime.now() > self.expires_at


class GPUCacheManager:
    """
    Level 1 Memory: GPU Cache (instant access).
    
    Peer review lessons applied:
    - Init gate for safe concurrent access
    - TTL-based expiry  
    - Minimal lock scope
    - OrderedDict for true LRU
    """
    
    def __init__(
        self,
        max_turns: int = 20,
        ttl_minutes: int = 30,
        max_npcs: int = 500
    ):
        """
        Initialize GPU cache.
        
        Args:
            max_turns: Max turns per NPC (default: 20)
            ttl_minutes: TTL after last access (default: 30)
            max_npcs: Max NPCs to cache (default: 500)
        """
        self.max_turns = max_turns
        self.ttl_minutes = ttl_minutes
        self.max_npcs = max_npcs
        
        # OrderedDict for true LRU
        self._cache: OrderedDict[str, NPCCacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._init_gate = asyncio.Event()
        
        # Background task
        self._eviction_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            f"GPUCacheManager initialized: max_turns={max_turns}, "
            f"ttl={ttl_minutes}min, max_npcs={max_npcs}"
        )
    
    async def start(self) -> None:
        """Start cache and background eviction."""
        self._running = True
        self._init_gate.set()
        self._eviction_task = asyncio.create_task(self._eviction_loop())
        logger.info("GPU cache started")
    
    async def stop(self) -> None:
        """Stop background eviction."""
        self._running = False
        if self._eviction_task:
            self._eviction_task.cancel()
            try:
                await self._eviction_task
            except asyncio.CancelledError:
                pass
        logger.info("GPU cache stopped")
    
    async def _eviction_loop(self) -> None:
        """Background eviction every 60 seconds."""
        while self._running:
            try:
                await asyncio.sleep(60)
                await self._evict_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Eviction loop error: {e}")
    
    async def _evict_expired(self) -> None:
        """Evict expired entries."""
        now = datetime.now()
        expired = []
        
        async with self._lock:
            for npc_id, entry in list(self._cache.items()):
                if entry.is_expired():
                    expired.append(npc_id)
            
            for npc_id in expired:
                del self._cache[npc_id]
        
        if expired:
            logger.info(f"Evicted {len(expired)} expired NPCs")
    
    async def add_turn(
        self,
        npc_id: str,
        player_input: str,
        npc_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add conversation turn."""
        await self._init_gate.wait()
        
        now = datetime.now()
        expires_at = now + timedelta(minutes=self.ttl_minutes)
        
        async with self._lock:
            # Get or create entry
            if npc_id not in self._cache:
                if len(self._cache) >= self.max_npcs:
                    # Evict LRU
                    self._cache.popitem(last=False)
                
                self._cache[npc_id] = NPCCacheEntry(
                    npc_id=npc_id,
                    conversation_turns=[],
                    relationship_card=None,
                    quest_state_card=None,
                    last_accessed=now,
                    expires_at=expires_at,
                    created_at=now
                )
            
            entry = self._cache[npc_id]
            
            # Add turn
            turn = ConversationTurn(
                npc_id=npc_id,
                turn_number=len(entry.conversation_turns) + 1,
                player_input=player_input,
                npc_response=npc_response,
                timestamp=now,
                metadata=metadata or {}
            )
            
            entry.conversation_turns.append(turn)
            
            # Keep only last max_turns
            if len(entry.conversation_turns) > self.max_turns:
                entry.conversation_turns = entry.conversation_turns[-self.max_turns:]
            
            # Update timestamps
            entry.last_accessed = now
            entry.expires_at = expires_at
            
            # Move to end (LRU)
            self._cache.move_to_end(npc_id)
    
    async def get_conversation_history(
        self,
        npc_id: str,
        max_turns: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get conversation history."""
        await self._init_gate.wait()
        
        async with self._lock:
            entry = self._cache.get(npc_id)
            if not entry or entry.is_expired():
                return []
            
            # Update access time
            entry.last_accessed = datetime.now()
            entry.expires_at = datetime.now() + timedelta(minutes=self.ttl_minutes)
            self._cache.move_to_end(npc_id)
            
            turns = entry.conversation_turns
            if max_turns:
                turns = turns[-max_turns:]
            
            return turns
    
    async def set_relationship_card(
        self,
        npc_id: str,
        relationship_card: RelationshipCard
    ) -> None:
        """Set relationship card."""
        await self._init_gate.wait()
        
        now = datetime.now()
        expires_at = now + timedelta(minutes=self.ttl_minutes)
        
        async with self._lock:
            if npc_id not in self._cache:
                if len(self._cache) >= self.max_npcs:
                    self._cache.popitem(last=False)
                
                self._cache[npc_id] = NPCCacheEntry(
                    npc_id=npc_id,
                    conversation_turns=[],
                    relationship_card=None,
                    quest_state_card=None,
                    last_accessed=now,
                    expires_at=expires_at,
                    created_at=now
                )
            
            entry = self._cache[npc_id]
            relationship_card.last_updated = now
            entry.relationship_card = relationship_card
            entry.last_accessed = now
            entry.expires_at = expires_at
            self._cache.move_to_end(npc_id)
    
    async def get_relationship_card(
        self,
        npc_id: str
    ) -> Optional[RelationshipCard]:
        """Get relationship card."""
        await self._init_gate.wait()
        
        async with self._lock:
            entry = self._cache.get(npc_id)
            if not entry or entry.is_expired():
                return None
            
            entry.last_accessed = datetime.now()
            entry.expires_at = datetime.now() + timedelta(minutes=self.ttl_minutes)
            self._cache.move_to_end(npc_id)
            
            return entry.relationship_card
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_turns = sum(len(e.conversation_turns) for e in self._cache.values())
            with_rel = sum(1 for e in self._cache.values() if e.relationship_card)
            with_quest = sum(1 for e in self._cache.values() if e.quest_state_card)
            
            return {
                'total_npcs_cached': len(self._cache),
                'max_npcs': self.max_npcs,
                'total_turns_cached': total_turns,
                'npcs_with_relationship_card': with_rel,
                'npcs_with_quest_card': with_quest,
                'ttl_minutes': self.ttl_minutes
            }

