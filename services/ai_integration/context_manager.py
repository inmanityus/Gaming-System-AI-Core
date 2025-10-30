"""
Context Manager - Advanced context handling for AI.
Aggregates context from multiple sources and optimizes for AI consumption.
"""

import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool


class ContextManager:
    """
    Manages context for AI requests.
    Aggregates data from multiple sources and optimizes for AI consumption.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def get_player_context(self, player_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive player context.
        
        Args:
            player_id: Player UUID
        
        Returns:
            Player context dictionary
        """
        cache_key = f"player_{player_id}"
        
        # Check cache first
        if cache_key in self._context_cache:
            cached_context = self._context_cache[cache_key]
            if self._is_cache_valid(cached_context):
                return cached_context["data"]
        
        postgres = await self._get_postgres()
        
        # Get player data
        player_query = """
            SELECT steam_id, username, tier, stats, inventory, money, reputation, 
                   level, xp, created_at, updated_at
            FROM players
            WHERE id = $1
        """
        player_result = await postgres.fetch(player_query, player_id)
        
        if not player_result:
            raise ValueError(f"Player {player_id} not found")
        
        # Get current game state
        game_state_query = """
            SELECT current_world, location, position, active_quests, session_data
            FROM game_states
            WHERE player_id = $1 AND is_active = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
        """
        game_state_result = await postgres.fetch(game_state_query, player_id)
        
        # Get recent story history
        story_query = """
            SELECT node_type, title, narrative_content, choices, created_at
            FROM story_nodes
            WHERE player_id = $1 AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 10
        """
        story_results = await postgres.fetch_all(story_query, player_id)
        
        # Build context
        context = {
            "player": {
                "id": str(player_id),
                "steam_id": player_result["steam_id"],
                "username": player_result["username"],
                "tier": player_result["tier"],
                "stats": json.loads(player_result["stats"]) if isinstance(player_result["stats"], str) else player_result["stats"],
                "inventory": json.loads(player_result["inventory"]) if isinstance(player_result["inventory"], str) else player_result["inventory"],
                "money": player_result["money"],
                "reputation": player_result["reputation"],
                "level": player_result["level"],
                "xp": player_result["xp"],
            },
            "game_state": {
                "current_world": game_state_result["current_world"] if game_state_result else "day",
                "location": game_state_result["location"] if game_state_result else "unknown",
                "position": json.loads(game_state_result["position"]) if game_state_result and game_state_result["position"] else {},
                "active_quests": json.loads(game_state_result["active_quests"]) if game_state_result and game_state_result["active_quests"] else [],
                "session_data": json.loads(game_state_result["session_data"]) if game_state_result and game_state_result["session_data"] else {},
            },
            "story_history": [
                {
                    "node_type": result["node_type"],
                    "title": result["title"],
                    "narrative_content": result["narrative_content"],
                    "choices": json.loads(result["choices"]) if isinstance(result["choices"], str) else result["choices"],
                    "created_at": result["created_at"].isoformat() if result["created_at"] else None,
                }
                for result in story_results
            ],
        }
        
        # Cache the context
        self._context_cache[cache_key] = {
            "data": context,
            "timestamp": time.time(),
        }
        
        return context
    
    async def get_world_context(self) -> Dict[str, Any]:
        """
        Get current world context.
        
        Returns:
            World context dictionary
        """
        cache_key = "world_context"
        
        # Check cache first
        if cache_key in self._context_cache:
            cached_context = self._context_cache[cache_key]
            if self._is_cache_valid(cached_context):
                return cached_context["data"]
        
        postgres = await self._get_postgres()
        
        # Get latest world state
        world_query = """
            SELECT world_time, current_weather, global_events, faction_power,
                   economic_state, npc_population, territory_control, meta_data
            FROM world_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        world_result = await postgres.fetch(world_query)
        
        if not world_result:
            return self._get_default_world_context()
        
        # Get active NPCs
        npc_query = """
            SELECT n.name, n.npc_type, n.personality_vector, n.stats, n.goal_stack,
                   n.relationships, f.name as faction_name
            FROM npcs n
            JOIN factions f ON n.faction_id = f.id
            WHERE f.name IN (
                SELECT DISTINCT jsonb_object_keys(territory_control)
                FROM world_states
                ORDER BY created_at DESC
                LIMIT 1
            )
            LIMIT 20
        """
        npc_results = await postgres.fetch_all(npc_query)
        
        # Build world context
        context = {
            "world_time": world_result["world_time"],
            "current_weather": world_result["current_weather"],
            "global_events": json.loads(world_result["global_events"]) if isinstance(world_result["global_events"], str) else world_result["global_events"],
            "faction_power": json.loads(world_result["faction_power"]) if isinstance(world_result["faction_power"], str) else world_result["faction_power"],
            "economic_state": json.loads(world_result["economic_state"]) if isinstance(world_result["economic_state"], str) else world_result["economic_state"],
            "npc_population": json.loads(world_result["npc_population"]) if isinstance(world_result["npc_population"], str) else world_result["npc_population"],
            "territory_control": json.loads(world_result["territory_control"]) if isinstance(world_result["territory_control"], str) else world_result["territory_control"],
            "active_npcs": [
                {
                    "name": result["name"],
                    "type": result["npc_type"],
                    "faction": result["faction_name"],
                    "personality": json.loads(result["personality_vector"]) if isinstance(result["personality_vector"], str) else result["personality_vector"],
                    "stats": json.loads(result["stats"]) if isinstance(result["stats"], str) else result["stats"],
                    "goals": json.loads(result["goal_stack"]) if isinstance(result["goal_stack"], str) else result["goal_stack"],
                    "relationships": json.loads(result["relationships"]) if isinstance(result["relationships"], str) else result["relationships"],
                }
                for result in npc_results
            ],
        }
        
        # Cache the context
        self._context_cache[cache_key] = {
            "data": context,
            "timestamp": time.time(),
        }
        
        return context
    
    def _get_default_world_context(self) -> Dict[str, Any]:
        """Get default world context when no data available."""
        return {
            "world_time": "2025-10-29T23:17:17Z",
            "current_weather": "overcast",
            "global_events": {},
            "faction_power": {},
            "economic_state": {},
            "npc_population": {},
            "territory_control": {},
            "active_npcs": [],
        }
    
    def _is_cache_valid(self, cached_context: Dict[str, Any]) -> bool:
        """Check if cached context is still valid."""
        import time
        return time.time() - cached_context["timestamp"] < self._cache_ttl
    
    async def get_optimized_context(
        self, 
        player_id: UUID, 
        context_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Get optimized context for AI consumption.
        
        Args:
            player_id: Player UUID
            context_type: Type of context (full, minimal, story, world)
        
        Returns:
            Optimized context dictionary
        """
        if context_type == "full":
            player_context = await self.get_player_context(player_id)
            world_context = await self.get_world_context()
            return {
                "player": player_context["player"],
                "game_state": player_context["game_state"],
                "story_history": player_context["story_history"][:5],  # Last 5 story nodes
                "world": world_context,
            }
        
        elif context_type == "minimal":
            player_context = await self.get_player_context(player_id)
            return {
                "player": {
                    "id": player_context["player"]["id"],
                    "tier": player_context["player"]["tier"],
                    "level": player_context["player"]["level"],
                    "reputation": player_context["player"]["reputation"],
                },
                "game_state": {
                    "current_world": player_context["game_state"]["current_world"],
                    "location": player_context["game_state"]["location"],
                },
            }
        
        elif context_type == "story":
            player_context = await self.get_player_context(player_id)
            return {
                "story_history": player_context["story_history"],
                "current_location": player_context["game_state"]["location"],
            }
        
        elif context_type == "world":
            return await self.get_world_context()
        
        else:
            raise ValueError(f"Unknown context type: {context_type}")
    
    def clear_cache(self, player_id: Optional[UUID] = None):
        """Clear context cache."""
        if player_id:
            cache_key = f"player_{player_id}"
            if cache_key in self._context_cache:
                del self._context_cache[cache_key]
        else:
            self._context_cache.clear()
    
    async def update_context_cache(self, player_id: UUID):
        """Update context cache for a specific player."""
        cache_key = f"player_{player_id}"
        if cache_key in self._context_cache:
            del self._context_cache[cache_key]
        await self.get_player_context(player_id)
