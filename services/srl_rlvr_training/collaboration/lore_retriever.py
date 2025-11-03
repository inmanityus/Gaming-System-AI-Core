"""
Lore Retriever (Model A)
========================

Retrieves and synthesizes knowledge from:
- Game lore databases
- Dynamic rules engine
- Historical game data
- External knowledge sources (when applicable)

Role: Gathers all relevant context for generating expert trajectories.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .rules_engine_client import RulesEngineClient
from .lore_database_client import LoreDatabaseClient

logger = logging.getLogger(__name__)


@dataclass
class LoreContext:
    """Structured lore context for training example generation."""
    monster_species: Optional[str] = None
    game_rules: Dict[str, Any] = None
    historical_examples: List[Dict[str, Any]] = None
    related_lore: List[str] = None
    
    def __post_init__(self):
        if self.game_rules is None:
            self.game_rules = {}
        if self.historical_examples is None:
            self.historical_examples = []
        if self.related_lore is None:
            self.related_lore = []


class LoreRetriever:
    """
    Retrieves and synthesizes game lore and rules for training example generation.
    
    This is Model A in the three-model collaboration system.
    """
    
    def __init__(self, rules_engine_url: str, lore_db_url: str):
        """
        Initialize Lore Retriever.
        
        Args:
            rules_engine_url: URL to dynamic rules engine service
            lore_db_url: URL to lore database service
        """
        self.rules_engine_client = RulesEngineClient(rules_engine_url)
        self.lore_db_client = LoreDatabaseClient(lore_db_url)
        logger.info("LoreRetriever initialized")
    
    async def close(self) -> None:
        """
        Close all client connections.
        
        Uses asyncio.gather to ensure both clients are closed even if one fails.
        """
        logger.info("Closing all client sessions")
        results = await asyncio.gather(
            self.rules_engine_client.close(),
            self.lore_db_client.close(),
            return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error during client cleanup: {result}")
    
    async def retrieve_lore(self, monster_species: str, model_type: str) -> LoreContext:
        """
        Retrieve all relevant lore for a given monster species and model type.
        
        Args:
            monster_species: Species identifier (e.g., "Vampire", "Werewolf")
            model_type: Type of model being trained (e.g., "personality", "facial")
        
        Returns:
            LoreContext: Structured context containing all relevant lore
        """
        logger.info(f"Retrieving lore for {monster_species} ({model_type})")
        
        # Fetch all data concurrently for optimal performance
        rules_task = self.rules_engine_client.get_rules(monster_species, model_type)
        historical_task = self.lore_db_client.get_historical_examples(monster_species, model_type)
        lore_task = self.lore_db_client.get_lore(monster_species)
        
        # Wait for all requests to complete concurrently
        rules, historical_examples, related_lore = await asyncio.gather(
            rules_task,
            historical_task,
            lore_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(rules, Exception):
            logger.error(f"Error fetching rules: {rules}")
            rules = {}
        if isinstance(historical_examples, Exception):
            logger.error(f"Error fetching historical examples: {historical_examples}")
            historical_examples = []
        if isinstance(related_lore, Exception):
            logger.error(f"Error fetching lore: {related_lore}")
            related_lore = []
        
        context = LoreContext(
            monster_species=monster_species,
            game_rules=rules if isinstance(rules, dict) else {},
            historical_examples=historical_examples if isinstance(historical_examples, list) else [],
            related_lore=related_lore if isinstance(related_lore, list) else []
        )
        
        logger.info(f"Retrieved lore context: {len(context.game_rules)} rules, "
                   f"{len(context.historical_examples)} examples, "
                   f"{len(context.related_lore)} lore entries")
        
        return context

