"""
HTTP Client for State Manager Service
Replaces direct imports from services.state_manager
"""

import aiohttp
from typing import Dict, Any, List, Optional
from uuid import UUID


class StateManagerHTTPClient:
    """HTTP client for state-manager service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "http://state-manager:8000"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_game_state(
        self,
        entity_id: str,
        state_type: str,
        state_data: dict,
        api_key: str = None
    ) -> Dict[str, Any]:
        """Create a new game state."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/state/game-states"
        headers = {"x-api-key": api_key} if api_key else {}
        
        payload = {
            "entity_id": entity_id,
            "state_type": state_type,
            "state_data": state_data
        }
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_game_state(self, state_id: UUID) -> Dict[str, Any]:
        """Get game state by ID."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/state/game-states/{state_id}"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    
    async def update_game_state(
        self,
        state_id: UUID,
        state_data: dict,
        version: Optional[int] = None,
        api_key: str = None
    ) -> Dict[str, Any]:
        """Update game state."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/state/game-states/{state_id}"
        headers = {"x-api-key": api_key} if api_key else {}
        
        payload = {
            "state_data": state_data,
            "version": version
        }
        
        async with self.session.put(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/health"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()


# Global singleton instance
_client_instance: Optional[StateManagerHTTPClient] = None


def get_state_manager_client(base_url: str = None) -> StateManagerHTTPClient:
    """Get or create StateManagerHTTPClient singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = StateManagerHTTPClient(base_url)
    return _client_instance

