#!/usr/bin/env python3
"""
Report Cache Service
TTL-based caching for in-memory report storage with LRU eviction.

P1-1 CRITICAL FIX: Prevents unbounded memory growth in in-memory storage.
This is a temporary solution until PostgreSQL migration (P0-5) is complete.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import threading

logger = logging.getLogger(__name__)


class ReportCache:
    """
    Thread-safe LRU cache with TTL for report storage.
    
    Features:
    - TTL-based expiration (default: 24 hours)
    - LRU eviction when max size reached
    - Thread-safe operations
    - Automatic cleanup on access
    """
    
    def __init__(
        self, 
        max_size: int = 1000,
        ttl_hours: int = 24
    ):
        """
        Initialize report cache.
        
        Args:
            max_size: Maximum number of reports to store (default: 1000)
            ttl_hours: Time-to-live for cached reports in hours (default: 24)
        """
        self._cache = OrderedDict()
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
        logger.info(f"Report cache initialized: max_size={max_size}, ttl={ttl_hours}h")
    
    def add(self, report_id: str, report: Dict[str, Any]) -> None:
        """
        Add report to cache with TTL.
        
        Args:
            report_id: Unique report identifier
            report: Report data dictionary
        """
        with self._lock:
            # Cleanup expired entries first
            self._cleanup_expired()
            
            # Enforce size limit (LRU eviction)
            if len(self._cache) >= self._max_size:
                # Remove oldest entry (FIFO/LRU)
                oldest_id, oldest_data = self._cache.popitem(last=False)
                logger.info(f"Evicted oldest report from cache: {oldest_id}")
            
            # Add new entry with expiration timestamp
            self._cache[report_id] = {
                'data': report,
                'expires_at': datetime.utcnow() + self._ttl
            }
            
            # Move to end (most recently used)
            self._cache.move_to_end(report_id)
            
            logger.debug(f"Added report to cache: {report_id} (size: {len(self._cache)}/{self._max_size})")
    
    def get(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get report from cache.
        
        Args:
            report_id: Unique report identifier
            
        Returns:
            Report data dictionary if found and not expired, None otherwise
        """
        with self._lock:
            if report_id not in self._cache:
                return None
            
            entry = self._cache[report_id]
            
            # Check expiration
            if datetime.utcnow() > entry['expires_at']:
                logger.debug(f"Report expired in cache: {report_id}")
                del self._cache[report_id]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(report_id)
            
            return entry['data']
    
    def update(self, report_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing report in cache.
        
        Args:
            report_id: Unique report identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if updated, False if not found or expired
        """
        with self._lock:
            existing = self.get(report_id)
            if existing is None:
                return False
            
            # Apply updates
            existing.update(updates)
            
            # Update cache (also refreshes TTL)
            self.add(report_id, existing)
            
            logger.debug(f"Updated report in cache: {report_id}")
            return True
    
    def exists(self, report_id: str) -> bool:
        """Check if report exists in cache and is not expired."""
        return self.get(report_id) is not None
    
    def delete(self, report_id: str) -> bool:
        """
        Delete report from cache.
        
        Args:
            report_id: Unique report identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if report_id in self._cache:
                del self._cache[report_id]
                logger.debug(f"Deleted report from cache: {report_id}")
                return True
            return False
    
    def values(self) -> list:
        """
        Get all non-expired report values.
        
        Returns:
            List of report data dictionaries
        """
        with self._lock:
            # Cleanup expired first
            self._cleanup_expired()
            
            # Return copy of all report data
            return [entry['data'].copy() for entry in self._cache.values()]
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache (internal use)."""
        now = datetime.utcnow()
        expired = [
            report_id for report_id, entry in self._cache.items()
            if entry['expires_at'] < now
        ]
        
        for report_id in expired:
            del self._cache[report_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired reports from cache")
    
    def cleanup(self) -> int:
        """
        Force cleanup of expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            before_size = len(self._cache)
            self._cleanup_expired()
            after_size = len(self._cache)
            removed = before_size - after_size
            
            if removed > 0:
                logger.info(f"Cache cleanup: removed {removed} expired entries")
            
            return removed
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                'current_size': len(self._cache),
                'max_size': self._max_size,
                'utilization': len(self._cache) / self._max_size if self._max_size > 0 else 0,
                'ttl_hours': self._ttl.total_seconds() / 3600
            }
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            cleared = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared all {cleared} entries from cache")

