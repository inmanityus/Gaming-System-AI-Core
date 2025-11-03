"""
Lore Database Client
====================

HTTP client for communicating with the lore database service.
Retrieves game lore, historical examples, and related information.
Extends BaseHttpClient for circuit breaker and retry logic.
"""

import logging
from typing import Dict, List, Optional, Any

from .base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class LoreDatabaseClient(BaseHttpClient):
    """
    Client for retrieving game lore from the lore database service.
    
    Handles:
    - HTTP requests to lore database
    - Retry logic with exponential backoff (inherited from BaseHttpClient)
    - Circuit breaker pattern (inherited from BaseHttpClient)
    - Error handling and fallbacks (inherited from BaseHttpClient)
    """
    
    def __init__(self, lore_db_url: str, timeout: float = 5.0):
        """
        Initialize Lore Database Client.
        
        Args:
            lore_db_url: Base URL for lore database service
            timeout: Request timeout in seconds
        """
        super().__init__(lore_db_url, timeout)
        self.lore_db_url = self.base_url  # Alias for clarity
    
    async def get_lore(
        self,
        monster_species: str,
        limit: int = 50
    ) -> List[str]:
        """
        Fetch related lore entries for a monster species.
        
        Args:
            monster_species: Species identifier
            limit: Maximum number of lore entries to return
        
        Returns:
            List of lore entry strings
        """
        logger.info(f"Fetching lore for {monster_species}")
        
        url = f"{self.lore_db_url}/api/v1/lore"
        params = {
            "species": monster_species,
            "limit": limit
        }
        
        # Use base class request method
        response = await self._make_request("GET", url, params=params, max_retries=3)
        
        if response is None:
            logger.warning("Failed to fetch lore - returning empty list")
            return []
        
        if response.status == 404:
            logger.warning(f"Lore not found for {monster_species}")
            return []
        
        if response.status == 200:
            try:
                data = await response.json()
                lore_entries = data.get("entries", [])
                logger.debug(f"Retrieved {len(lore_entries)} lore entries")
                return lore_entries
            except Exception as e:
                logger.error(f"Error parsing lore JSON: {e}")
                return []
        
        # Should not reach here
        return []
    
    async def get_historical_examples(
        self,
        monster_species: str,
        model_type: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical training examples.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            limit: Maximum number of examples to return
        
        Returns:
            List of historical example dicts
        """
        logger.info(f"Fetching historical examples for {monster_species} ({model_type})")
        
        url = f"{self.lore_db_url}/api/v1/training-examples"
        params = {
            "monster_species": monster_species,
            "model_type": model_type,
            "limit": limit
        }
        
        # Use base class request method
        response = await self._make_request("GET", url, params=params, max_retries=3)
        
        if response is None:
            logger.warning("Failed to fetch historical examples - returning empty list")
            return []
        
        if response.status == 404:
            logger.warning("No historical examples found")
            return []
        
        if response.status == 200:
            try:
                data = await response.json()
                examples = data.get("examples", [])
                logger.debug(f"Retrieved {len(examples)} historical examples")
                return examples
            except Exception as e:
                logger.error(f"Error parsing examples JSON: {e}")
                return []
        
        # Should not reach here
        return []
