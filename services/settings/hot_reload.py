"""
Hot Reload - Live configuration updates without service restart.
"""

import asyncio
from datetime import datetime
from typing import Callable, Dict, Optional

# REFACTORING: Direct database imports replaced with on-demand connections
import asyncpg
import redis.asyncio as redis
from typing import Any as PostgreSQLPool, Any as RedisPool


class HotReloadManager:
    """
    Manages hot-reload of configuration without service restart.
    Uses polling to detect changes and invalidates cache.
    """
    
    def __init__(self, poll_interval: int = 5):
        """
        Initialize hot reload manager.
        
        Args:
            poll_interval: Polling interval in seconds (default: 5)
        """
        self.poll_interval = poll_interval
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._last_check: Dict[str, datetime] = {}
        self._callbacks: Dict[str, list] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = await get_redis_pool()
        return self.redis
    
    def register_callback(self, resource_type: str, callback: Callable):
        """
        Register a callback to be called when configuration changes.
        
        Args:
            resource_type: Type of resource (e.g., "settings", "feature_flags")
            callback: Callback function to call on change
        """
        if resource_type not in self._callbacks:
            self._callbacks[resource_type] = []
        self._callbacks[resource_type].append(callback)
    
    async def _check_changes(self):
        """Check for configuration changes and trigger reload."""
        postgres = await self._get_postgres()
        
        # Check settings table
        query = """
            SELECT MAX(updated_at) as last_update
            FROM settings
        """
        result = await postgres.fetch(query)
        if result and result["last_update"]:
            last_update = result["last_update"]
            key = "settings"
            if key not in self._last_check or last_update > self._last_check[key]:
                if key in self._last_check:
                    # Change detected - invalidate cache and trigger callbacks
                    redis = await self._get_redis()
                    await redis.delete("setting:*")  # Pattern delete
                    
                    for callback in self._callbacks.get(key, []):
                        try:
                            await callback() if asyncio.iscoroutinefunction(callback) else callback()
                        except Exception as e:
                            print(f"Error in hot-reload callback: {e}")
                
                self._last_check[key] = last_update
        
        # Check feature_flags table
        query = """
            SELECT MAX(updated_at) as last_update
            FROM feature_flags
        """
        result = await postgres.fetch(query)
        if result and result["last_update"]:
            last_update = result["last_update"]
            key = "feature_flags"
            if key not in self._last_check or last_update > self._last_check[key]:
                if key in self._last_check:
                    redis = await self._get_redis()
                    await redis.delete("feature_flag:*")
                    
                    for callback in self._callbacks.get(key, []):
                        try:
                            await callback() if asyncio.iscoroutinefunction(callback) else callback()
                        except Exception as e:
                            print(f"Error in hot-reload callback: {e}")
                
                self._last_check[key] = last_update
    
    async def start(self):
        """Start the hot-reload polling loop."""
        if self._running:
            return
        
        self._running = True
        
        async def poll_loop():
            while self._running:
                try:
                    await self._check_changes()
                except Exception as e:
                    print(f"Error in hot-reload check: {e}")
                
                await asyncio.sleep(self.poll_interval)
        
        self._task = asyncio.create_task(poll_loop())
    
    async def stop(self):
        """Stop the hot-reload polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

