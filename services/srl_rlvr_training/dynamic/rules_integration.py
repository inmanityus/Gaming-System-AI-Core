"""
Rules Integration
================

Integrates dynamic rules engine with SRL→RLVR training.

Ensures training examples always use the latest versioned rules
and triggers re-training when rules are updated.
"""

import logging
import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class RulesIntegration:
    """
    Integrates dynamic rules engine with training pipeline.
    
    Ensures:
    - Training uses latest versioned rules
    - Re-training triggered on rule updates
    - Rules are versioned and tracked
    """
    
    def __init__(self, rules_engine_url: str):
        """
        Initialize Rules Integration.
        
        Args:
            rules_engine_url: URL to dynamic rules engine
        """
        self.rules_engine_url = rules_engine_url.rstrip('/')
        self.rules_version_cache: Dict[str, str] = {}
        self.rules_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize HTTP client if available
        if HTTPX_AVAILABLE:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        else:
            self.http_client = None
            logger.warning("httpx not available, rules fetching will be limited")
        
        logger.info(f"RulesIntegration initialized (engine_url: {rules_engine_url})")
    
    async def get_rules(
        self,
        monster_species: str,
        model_type: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get rules for training from rules engine.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            version: Specific rules version (None = latest)
        
        Returns:
            Dict with rules
        """
        logger.debug(f"Getting rules for {monster_species} ({model_type}), version={version}")
        
        cache_key = f"{monster_species}:{model_type}"
        
        # Return cached rules if available and version matches
        if cache_key in self.rules_cache:
            cached_rules = self.rules_cache[cache_key]
            cached_version = cached_rules.get("version")
            if version is None or cached_version == version:
                logger.debug(f"Returning cached rules (version: {cached_version})")
                return cached_rules
        
        # Fetch from rules engine
        try:
            if self.http_client:
                # Build API endpoint
                endpoint = f"{self.rules_engine_url}/api/rules"
                params = {
                    "monster_species": monster_species,
                    "model_type": model_type
                }
                if version:
                    params["version"] = version
                
                # Make async HTTP request
                response = await self.http_client.get(endpoint, params=params)
                response.raise_for_status()
                
                rules_data = response.json()
                
                # Cache rules
                self.rules_cache[cache_key] = rules_data
                if "version" in rules_data:
                    self.rules_version_cache[cache_key] = rules_data["version"]
                
                logger.info(f"Fetched rules from engine (version: {rules_data.get('version', 'unknown')})")
                return rules_data
                
            else:
                # Fallback: Use environment variables or default rules
                logger.warning("HTTP client not available, using fallback rules")
                fallback_rules = {
                    "rules": os.getenv(f"RULES_{monster_species.upper()}_{model_type.upper()}", "{}"),
                    "version": version or "fallback",
                    "monster_species": monster_species,
                    "model_type": model_type,
                    "source": "fallback"
                }
                
                # Cache fallback rules
                self.rules_cache[cache_key] = fallback_rules
                if version:
                    self.rules_version_cache[cache_key] = version
                
                return fallback_rules
                
        except Exception as e:
            logger.error(f"Error fetching rules from engine: {e}")
            # Return cached rules if available, otherwise fallback
            if cache_key in self.rules_cache:
                logger.warning("Using cached rules due to fetch error")
                return self.rules_cache[cache_key]
            
            # Last resort: return minimal rules
            return {
                "rules": {},
                "version": version or "error_fallback",
                "monster_species": monster_species,
                "model_type": model_type,
                "source": "error_fallback",
                "error": str(e)
            }
    
    async def check_rules_updated(
        self,
        monster_species: str,
        model_type: str,
        last_version: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if rules have been updated.
        
        Args:
            monster_species: Species identifier
            model_type: Type of model being trained
            last_version: Last known rules version
        
        Returns:
            (is_updated, new_version) tuple
        """
        logger.debug(f"Checking rules version for {monster_species} ({model_type}), last_version={last_version}")
        
        try:
            if self.http_client:
                # Query rules engine for latest version
                endpoint = f"{self.rules_engine_url}/api/rules/version"
                params = {
                    "monster_species": monster_species,
                    "model_type": model_type
                }
                
                response = await self.http_client.get(endpoint, params=params)
                response.raise_for_status()
                
                version_data = response.json()
                latest_version = version_data.get("version", version_data.get("latest_version"))
                
                if latest_version and latest_version != last_version:
                    logger.info(f"Rules updated: {last_version} -> {latest_version}")
                    return (True, latest_version)
                else:
                    logger.debug(f"Rules unchanged (version: {latest_version})")
                    return (False, latest_version)
                    
            else:
                # Fallback: Check cache
                cache_key = f"{monster_species}:{model_type}"
                cached_version = self.rules_version_cache.get(cache_key)
                
                if cached_version and cached_version != last_version:
                    return (True, cached_version)
                
                # Can't check without HTTP client, return False
                logger.warning("Cannot check rules version without HTTP client")
                return (False, None)
                
        except Exception as e:
            logger.error(f"Error checking rules version: {e}")
            # On error, assume no update (conservative)
            return (False, None)

