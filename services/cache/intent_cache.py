"""
Intent Cache - Caches NPC intents for Gold tier.
Provides smooth transitions between cached and updated intents.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CachedIntent:
    """Cached intent data."""
    intent: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    ttl: float = 1.0  # 1 second default TTL
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl


class IntentCache:
    """Intent cache for Gold tier NPCs."""
    
    def __init__(self, default_ttl: float = 1.0):
        """
        Initialize intent cache.
        
        Args:
            default_ttl: Default TTL in seconds
        """
        self.cache: Dict[str, CachedIntent] = {}
        self.default_ttl = default_ttl
        self.default_intent = {
            "action": "idle",
            "aggressive": 0.0,
            "friendly": 0.5,
            "curious": 0.3
        }
    
    def get_intent(self, npc_id: str) -> Dict[str, Any]:
        """
        Get cached intent or return default.
        
        Args:
            npc_id: NPC identifier
        
        Returns:
            Cached intent or default intent
        """
        cached = self.cache.get(npc_id)
        if cached and not cached.is_expired():
            return cached.intent
        return self.default_intent
    
    def update_intent(self, npc_id: str, intent: Dict[str, Any], ttl: Optional[float] = None):
        """
        Update cached intent.
        
        Args:
            npc_id: NPC identifier
            intent: Intent data
            ttl: TTL in seconds (optional)
        """
        cached = CachedIntent(
            intent=intent,
            ttl=ttl or self.default_ttl
        )
        self.cache[npc_id] = cached
    
    def invalidate(self, npc_id: str):
        """
        Invalidate cached intent.
        
        Args:
            npc_id: NPC identifier
        """
        if npc_id in self.cache:
            del self.cache[npc_id]
    
    def clear(self):
        """Clear all cached intents."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache stats
        """
        total_entries = len(self.cache)
        expired_entries = sum(1 for cached in self.cache.values() if cached.is_expired())
        active_entries = total_entries - expired_entries
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries
        }

