"""
Tests for Intent Cache service.
Tests NPC intent caching for Gold tier.
"""

import pytest
import time
from services.cache.intent_cache import IntentCache, CachedIntent


class TestIntentCache:
    """Test intent cache functionality."""
    
    def test_get_default_intent(self):
        """Test that default intent is returned when no cache exists."""
        cache = IntentCache()
        intent = cache.get_intent("npc_001")
        
        assert intent["action"] == "idle"
        assert intent["aggressive"] == 0.0
        assert intent["friendly"] == 0.5
    
    def test_update_and_get_intent(self):
        """Test updating and retrieving cached intent."""
        cache = IntentCache()
        new_intent = {
            "action": "attack",
            "aggressive": 0.9,
            "friendly": 0.1,
            "curious": 0.2
        }
        
        cache.update_intent("npc_001", new_intent)
        cached = cache.get_intent("npc_001")
        
        assert cached["action"] == "attack"
        assert cached["aggressive"] == 0.9
    
    def test_intent_expiration(self):
        """Test that cached intents expire after TTL."""
        cache = IntentCache(default_ttl=0.1)  # 100ms TTL
        intent = {"action": "move", "aggressive": 0.5}
        
        cache.update_intent("npc_001", intent)
        
        # Should be cached immediately
        assert cache.get_intent("npc_001")["action"] == "move"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should return default after expiration
        cached = cache.get_intent("npc_001")
        assert cached["action"] == "idle"
    
    def test_custom_ttl(self):
        """Test custom TTL per intent."""
        cache = IntentCache()
        intent = {"action": "follow", "aggressive": 0.3}
        
        # Update with custom TTL
        cache.update_intent("npc_001", intent, ttl=0.2)
        
        # Should be cached
        assert cache.get_intent("npc_001")["action"] == "follow"
        
        # Wait for expiration
        time.sleep(0.25)
        
        # Should return default
        cached = cache.get_intent("npc_001")
        assert cached["action"] == "idle"
    
    def test_invalidate_intent(self):
        """Test invalidating cached intent."""
        cache = IntentCache()
        intent = {"action": "retreat", "aggressive": 0.1}
        
        cache.update_intent("npc_001", intent)
        cache.invalidate("npc_001")
        
        # Should return default after invalidation
        cached = cache.get_intent("npc_001")
        assert cached["action"] == "idle"
    
    def test_clear_all_intents(self):
        """Test clearing all cached intents."""
        cache = IntentCache()
        intent1 = {"action": "patrol", "aggressive": 0.4}
        intent2 = {"action": "guard", "aggressive": 0.8}
        
        cache.update_intent("npc_001", intent1)
        cache.update_intent("npc_002", intent2)
        
        assert cache.get_intent("npc_001")["action"] == "patrol"
        assert cache.get_intent("npc_002")["action"] == "guard"
        
        cache.clear()
        
        # Both should return default
        assert cache.get_intent("npc_001")["action"] == "idle"
        assert cache.get_intent("npc_002")["action"] == "idle"
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = IntentCache()
        
        # Empty cache
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        
        # Add some intents
        cache.update_intent("npc_001", {"action": "move"}, ttl=10.0)
        cache.update_intent("npc_002", {"action": "idle"}, ttl=0.1)
        
        # Wait for one to expire
        time.sleep(0.15)
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1
    
    def test_multiple_npcs(self):
        """Test caching intents for multiple NPCs."""
        cache = IntentCache()
        
        cache.update_intent("npc_001", {"action": "attack", "aggressive": 0.9})
        cache.update_intent("npc_002", {"action": "defend", "aggressive": 0.5})
        cache.update_intent("npc_003", {"action": "flee", "aggressive": 0.1})
        
        # Each NPC should have independent cache
        assert cache.get_intent("npc_001")["action"] == "attack"
        assert cache.get_intent("npc_002")["action"] == "defend"
        assert cache.get_intent("npc_003")["action"] == "flee"
        
        # Invalidating one shouldn't affect others
        cache.invalidate("npc_002")
        
        assert cache.get_intent("npc_001")["action"] == "attack"
        assert cache.get_intent("npc_002")["action"] == "idle"  # default
        assert cache.get_intent("npc_003")["action"] == "flee"

