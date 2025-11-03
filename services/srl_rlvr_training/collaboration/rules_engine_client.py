"""
Rules Engine Client
==================

HTTP client for communicating with the dynamic rules engine service.
Extends BaseHttpClient for circuit breaker and retry logic.
"""

import logging
import asyncio
from typing import Dict, Optional, Any

from .base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class RulesEngineClient(BaseHttpClient):
    """
    Client for retrieving dynamic rules from the rules engine service.
    
    Handles:
    - HTTP requests to rules engine
    - Retry logic with exponential backoff (inherited from BaseHttpClient)
    - Circuit breaker pattern (inherited from BaseHttpClient)
    - Error handling and fallbacks (inherited from BaseHttpClient)
    """
    
    def __init__(self, rules_engine_url: str, timeout: float = 5.0):
        """
        Initialize Rules Engine Client.
        
        Args:
            rules_engine_url: Base URL for rules engine service
            timeout: Request timeout in seconds
        """
        super().__init__(rules_engine_url, timeout)
        self.rules_engine_url = self.base_url  # Alias for clarity
    
    async def get_rules(
        self,
        monster_species: str,
        model_type: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch rules from rules engine.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            version: Specific rules version (None = latest)
        
        Returns:
            Dict with rules data
        """
        logger.info(f"Fetching rules for {monster_species} ({model_type})")
        
        # Build request URL
        url = f"{self.rules_engine_url}/api/v1/rules"
        params = {
            "monster_species": monster_species,
            "model_type": model_type
        }
        if version:
            params["version"] = version
        
        # Use base class request method
        response = await self._make_request("GET", url, params=params, max_retries=3)
        
        if response is None:
            logger.warning("Failed to fetch rules - returning empty dict")
            return {}
        
        if response.status == 404:
            logger.warning(f"Rules not found for {monster_species}/{model_type}")
            return {}
        
        if response.status == 200:
            try:
                rules = await response.json()
                logger.debug(f"Retrieved {len(rules.get('rules', {}))} rules")
                return rules
            except Exception as e:
                logger.error(f"Error parsing rules JSON: {e}")
                return {}
        
        # Should not reach here (handled by _make_request)
        return {}

