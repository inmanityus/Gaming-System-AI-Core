"""
State Manager HTTP Client - Replaces cross-service database imports.
Provides HTTP-based access to state management service functionality.
"""

import asyncio
import aiohttp
import os
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StateManagerClient:
    """HTTP client for state-manager service."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "STATE_MANAGER_URL",
            "http://state-manager:8080"
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30.0)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_cache(self, key: str) -> Optional[str]:
        """
        Get value from Redis cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/cache/{key}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("value")
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Failed to get cache: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    async def set_cache(self, key: str, value: str, ttl_seconds: int = 3600) -> bool:
        """
        Set value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        
        Returns:
            True if cached successfully
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/cache"
            
            payload = {
                "key": key,
                "value": value,
                "ttl_seconds": ttl_seconds
            }
            
            async with session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    return True
                else:
                    logger.error(f"Failed to set cache: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete_cache(self, key: str) -> bool:
        """
        Delete value from Redis cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted successfully
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/cache/{key}"
            
            async with session.delete(url) as response:
                if response.status in (200, 204):
                    return True
                else:
                    logger.error(f"Failed to delete cache: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    async def exists_cache(self, key: str) -> bool:
        """
        Check if key exists in Redis cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/cache/{key}/exists"
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("exists", False)
                else:
                    return False
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False


# Singleton instance
_client_instance: Optional[StateManagerClient] = None


def get_state_manager_client() -> StateManagerClient:
    """Get singleton StateManagerClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = StateManagerClient()
    return _client_instance

