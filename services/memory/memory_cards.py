"""
Memory Cards Helper - Convenience Methods
Coder: Claude Sonnet 4.5

Helper class for managing relationship and quest state cards.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

from .gpu_cache_manager import RelationshipCard, QuestStateCard

logger = logging.getLogger(__name__)


class MemoryCards:
    """Helper for managing NPC memory cards."""
    
    def create_relationship_card(
        self,
        npc_id: str,
        player_id: str
    ) -> RelationshipCard:
        """Create new relationship card."""
        return RelationshipCard(
            npc_id=npc_id,
            player_id=player_id,
            last_updated=datetime.now()
        )
    
    def update_trust(
        self,
        card: RelationshipCard,
        delta: float,
        reason: str
    ) -> None:
        """Update trust score."""
        card.trust_score = max(-100.0, min(100.0, card.trust_score + delta))
        card.last_updated = datetime.now()
        logger.debug(f"Trust updated for {card.npc_id}: {delta:+.1f} ({reason})")
    
    def update_affinity(
        self,
        card: RelationshipCard,
        delta: float,
        reason: str
    ) -> None:
        """Update affinity score."""
        card.affinity_score = max(-100.0, min(100.0, card.affinity_score + delta))
        card.last_updated = datetime.now()
    
    def add_promise(self, card: RelationshipCard, promise: str) -> None:
        """Add promise."""
        card.promises_made.append(promise)
        card.last_updated = datetime.now()
    
    def mark_promise_kept(
        self,
        card: RelationshipCard,
        promise: str,
        trust_bonus: float = 10.0
    ) -> None:
        """Mark promise kept."""
        if promise in card.promises_made:
            card.promises_made.remove(promise)
            card.promises_kept.append(promise)
            self.update_trust(card, trust_bonus, f"Kept: {promise}")
    
    def serialize_relationship_card(
        self,
        card: RelationshipCard
    ) -> Dict[str, Any]:
        """Serialize relationship card."""
        return card.to_dict()
    
    def estimate_card_size_kb(self, card: Any) -> float:
        """Estimate card size (should be ≤2 KB)."""
        if isinstance(card, RelationshipCard):
            data = card.to_dict()
        elif isinstance(card, QuestStateCard):
            data = card.to_dict()
        else:
            return 0.0
        
        size_bytes = len(json.dumps(data).encode('utf-8'))
        size_kb = size_bytes / 1024
        
        if size_kb > 2.0:
            logger.warning(f"Card exceeds 2 KB: {size_kb:.2f} KB")
        
        return size_kb

