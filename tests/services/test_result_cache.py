"""
Tests for Result Cache service.
Tests Bronze tier result caching for Silver/Gold tiers.
"""

import pytest
import time
from services.cache.result_cache import ResultCache, CachedResult


class TestResultCache:
    """Test result cache functionality."""
    
    def test_get_none_when_no_cache(self):
        """Test that None is returned when no cache exists."""
        cache = ResultCache()
        result = cache.get_result("key_not_exist")
        
        assert result is None
    
    def test_set_and_get_result(self):
        """Test setting and retrieving cached result."""
        cache = ResultCache()
        result = {
            "story_arc_id": "arc_001",
            "content": "A mysterious figure approaches...",
            "length": 500
        }
        
        cache.set_result("story_arc_001", result)
        cached = cache.get_result("story_arc_001")
        
        assert cached is not None
        assert cached["story_arc_id"] == "arc_001"
        assert cached["content"] == "A mysterious figure approaches..."
    
    def test_result_expiration(self):
        """Test that cached results expire after TTL."""
        cache = ResultCache(default_ttl=0.1)  # 100ms TTL
        result = {"output": "Generated content", "tokens": 100}
        
        cache.set_result("output_001", result)
        
        # Should be cached immediately
        assert cache.get_result("output_001")["output"] == "Generated content"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should return None after expiration
        cached = cache.get_result("output_001")
        assert cached is None
    
    def test_custom_ttl(self):
        """Test custom TTL per result."""
        cache = ResultCache()
        result = {"data": "test", "value": 42}
        
        # Update with custom TTL
        cache.set_result("custom_key", result, ttl=0.2)
        
        # Should be cached
        assert cache.get_result("custom_key")["value"] == 42
        
        # Wait for expiration
        time.sleep(0.25)
        
        # Should return None
        cached = cache.get_result("custom_key")
        assert cached is None
    
    def test_invalidate_result(self):
        """Test invalidating cached result."""
        cache = ResultCache()
        result = {"output": "content to invalidate"}
        
        cache.set_result("temp_key", result)
        cache.invalidate("temp_key")
        
        # Should return None after invalidation
        cached = cache.get_result("temp_key")
        assert cached is None
    
    def test_clear_all_results(self):
        """Test clearing all cached results."""
        cache = ResultCache()
        result1 = {"type": "story", "data": "arc1"}
        result2 = {"type": "quest", "data": "quest1"}
        
        cache.set_result("key1", result1)
        cache.set_result("key2", result2)
        
        assert cache.get_result("key1")["type"] == "story"
        assert cache.get_result("key2")["type"] == "quest"
        
        cache.clear()
        
        # Both should return None
        assert cache.get_result("key1") is None
        assert cache.get_result("key2") is None
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = ResultCache()
        
        # Empty cache
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        
        # Add some results
        cache.set_result("result_001", {"data": "active"}, ttl=10.0)
        cache.set_result("result_002", {"data": "expiring"}, ttl=0.1)
        
        # Wait for one to expire
        time.sleep(0.15)
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1
    
    def test_multiple_keys(self):
        """Test caching results under multiple keys."""
        cache = ResultCache()
        
        cache.set_result("bronze_output_1", {"content": "Story arc 1", "id": "arc1"})
        cache.set_result("bronze_output_2", {"content": "Story arc 2", "id": "arc2"})
        cache.set_result("bronze_output_3", {"content": "Quest chain", "id": "q1"})
        
        # Each key should have independent cache
        assert cache.get_result("bronze_output_1")["id"] == "arc1"
        assert cache.get_result("bronze_output_2")["id"] == "arc2"
        assert cache.get_result("bronze_output_3")["id"] == "q1"
        
        # Invalidating one shouldn't affect others
        cache.invalidate("bronze_output_2")
        
        assert cache.get_result("bronze_output_1")["id"] == "arc1"
        assert cache.get_result("bronze_output_2") is None
        assert cache.get_result("bronze_output_3")["id"] == "q1"
    
    def test_large_result_caching(self):
        """Test caching large result data."""
        cache = ResultCache()
        
        # Simulate large story output
        large_result = {
            "story": "A" * 10000,  # 10KB content
            "metadata": {
                "chapter": 5,
                "characters": ["hero", "villain", "npc1", "npc2"],
                "locations": ["town", "forest", "cave"]
            }
        }
        
        cache.set_result("large_story_001", large_result)
        cached = cache.get_result("large_story_001")
        
        assert cached is not None
        assert len(cached["story"]) == 10000
        assert cached["metadata"]["chapter"] == 5

