"""
Result Cache - Caches Bronze tier results for Silver/Gold use.
Stores async results from Bronze tier for quick retrieval.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CachedResult:
    """Cached result data."""
    result: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    ttl: float = 3600.0  # 1 hour default TTL
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl


class ResultCache:
    """Result cache for Bronze tier outputs."""
    
    def __init__(self, default_ttl: float = 3600.0):
        """
        Initialize result cache.
        
        Args:
            default_ttl: Default TTL in seconds
        """
        self.cache: Dict[str, CachedResult] = {}
        self.default_ttl = default_ttl
    
    def get_result(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            key: Cache key
        
        Returns:
            Cached result or None
        """
        cached = self.cache.get(key)
        if cached and not cached.is_expired():
            return cached.result
        return None
    
    def set_result(self, key: str, result: Dict[str, Any], ttl: Optional[float] = None):
        """
        Store result in cache.
        
        Args:
            key: Cache key
            result: Result data
            ttl: TTL in seconds (optional)
        """
        cached = CachedResult(
            result=result,
            ttl=ttl or self.default_ttl
        )
        self.cache[key] = cached
    
    def invalidate(self, key: str):
        """
        Invalidate cached result.
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cached results."""
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

