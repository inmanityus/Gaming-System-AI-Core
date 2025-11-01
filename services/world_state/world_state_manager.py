"""
World State Manager - Dynamic world state tracking and updates.
Manages real-time world state with persistence and caching.
"""

import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class WorldStateManager:
    """
    Manages dynamic world state with real-time updates.
    Handles state persistence, caching, and synchronization.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._state_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        self._version = 1
    
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
    
    async def get_current_world_state(self) -> Dict[str, Any]:
        """
        Get current world state with caching.
        
        Returns:
            Current world state dictionary
        """
        cache_key = "world_state:current"
        
        # Check Redis cache first
        redis = await self._get_redis()
        cached = await redis.hgetall(cache_key)
        
        if cached:
            # Parse JSON values
            state = {}
            for k, v in cached.items():
                try:
                    state[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    state[k] = v
            return state
        
        # Fallback to PostgreSQL
        postgres = await self._get_postgres()
        query = """
            SELECT world_time, weather, global_events, faction_power,
                   economic_state, npc_population, territory_control, simulation_data,
                   created_at, updated_at
            FROM world_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        result = await postgres.fetch(query)
        
        if not result:
            return self._get_default_world_state()
        
        # Build world state
        world_state = {
            "world_time": result["world_time"],
            "current_weather": result["weather"] or "overcast",
            "global_events": json.loads(result["global_events"]) if isinstance(result["global_events"], str) else result["global_events"],
            "faction_power": json.loads(result["faction_power"]) if isinstance(result["faction_power"], str) else result["faction_power"],
            "economic_state": json.loads(result["economic_state"]) if isinstance(result["economic_state"], str) else result["economic_state"],
            "npc_population": json.loads(result["npc_population"]) if isinstance(result["npc_population"], str) else result["npc_population"],
            "territory_control": json.loads(result["territory_control"]) if isinstance(result["territory_control"], str) else result["territory_control"],
            "meta_data": json.loads(result["simulation_data"]) if isinstance(result["simulation_data"], str) else (result["simulation_data"] or {}),
            "version": self._version,
            "last_updated": result["updated_at"].isoformat() if result["updated_at"] else None,
        }
        
        # Cache the state
        await self._cache_world_state(cache_key, world_state)
        
        return world_state
    
    async def update_world_state(
        self,
        updates: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update world state with optimistic locking.
        
        Args:
            updates: Dictionary of state updates
            expected_version: Expected version for optimistic locking
        
        Returns:
            Updated world state
        """
        postgres = await self._get_postgres()
        
        # Get current state for version check
        current_state = await self.get_current_world_state()
        current_version = current_state.get("version", 1)
        
        if expected_version and current_version != expected_version:
            raise ValueError(f"Version mismatch: expected {expected_version}, got {current_version}")
        
        # Build update query
        update_fields = []
        params = []
        param_idx = 1
        
        if "world_time" in updates:
            update_fields.append(f"world_time = ${param_idx}")
            params.append(updates["world_time"])
            param_idx += 1
        
        if "current_weather" in updates:
            update_fields.append(f"weather = ${param_idx}")
            params.append(updates["current_weather"])
            param_idx += 1
        
        if "global_events" in updates:
            update_fields.append(f"global_events = ${param_idx}::jsonb")
            params.append(json.dumps(updates["global_events"]))
            param_idx += 1
        
        if "faction_power" in updates:
            update_fields.append(f"faction_power = ${param_idx}::jsonb")
            params.append(json.dumps(updates["faction_power"]))
            param_idx += 1
        
        if "economic_state" in updates:
            update_fields.append(f"economic_state = ${param_idx}::jsonb")
            params.append(json.dumps(updates["economic_state"]))
            param_idx += 1
        
        if "npc_population" in updates:
            update_fields.append(f"npc_population = ${param_idx}::jsonb")
            params.append(json.dumps(updates["npc_population"]))
            param_idx += 1
        
        if "territory_control" in updates:
            update_fields.append(f"territory_control = ${param_idx}::jsonb")
            params.append(json.dumps(updates["territory_control"]))
            param_idx += 1
        
        if "meta_data" in updates:
            update_fields.append(f"simulation_data = ${param_idx}::jsonb")
            params.append(json.dumps(updates["meta_data"]))
            param_idx += 1
        
        if not update_fields:
            return current_state
        
        # Always update timestamp and version
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_fields.append("version = version + 1")
        
        # For now, always update existing record (assume world_states always exists)
        query = f"""
            UPDATE world_states
            SET {', '.join(update_fields)}
            WHERE id = (
                SELECT id FROM world_states
                ORDER BY created_at DESC
                LIMIT 1
            )
            RETURNING id, world_time, weather, global_events, faction_power,
                      economic_state, npc_population, territory_control, simulation_data,
                      created_at, updated_at
        """
        
        result = await postgres.fetch(query, *params)
        
        if not result:
            raise ValueError("Failed to update world state")
        
        # Build updated state
        updated_state = {
            "id": str(result["id"]),
            "world_time": result["world_time"],
            "current_weather": result["weather"],
            "global_events": json.loads(result["global_events"]) if isinstance(result["global_events"], str) else result["global_events"],
            "faction_power": json.loads(result["faction_power"]) if isinstance(result["faction_power"], str) else result["faction_power"],
            "economic_state": json.loads(result["economic_state"]) if isinstance(result["economic_state"], str) else result["economic_state"],
            "npc_population": json.loads(result["npc_population"]) if isinstance(result["npc_population"], str) else result["npc_population"],
            "territory_control": json.loads(result["territory_control"]) if isinstance(result["territory_control"], str) else result["territory_control"],
            "meta_data": json.loads(result["simulation_data"]) if isinstance(result["simulation_data"], str) else result["simulation_data"],
            "version": current_version + 1,
            "last_updated": result["updated_at"].isoformat() if result["updated_at"] else None,
        }
        
        # Update cache
        await self._cache_world_state("world_state:current", updated_state)
        
        return updated_state
    
    async def _cache_world_state(self, cache_key: str, state: Dict[str, Any]):
        """Cache world state in Redis."""
        redis = await self._get_redis()
        
        # Prepare data for Redis hash
        cache_data = {}
        for k, v in state.items():
            if isinstance(v, (dict, list)):
                cache_data[k] = json.dumps(v)
            else:
                cache_data[k] = str(v)
        
        # Store with TTL
        await redis.hset(cache_key, mapping=cache_data)
        await redis.expire(cache_key, self._cache_ttl)
    
    def _get_default_world_state(self) -> Dict[str, Any]:
        """Get default world state when no data available."""
        return {
            "world_time": "2025-10-29T23:17:17Z",
            "current_weather": "overcast",
            "global_events": {},
            "faction_power": {},
            "economic_state": {
                "market_stability": 0.7,
                "inflation_rate": 0.02,
                "resource_availability": 0.8,
            },
            "npc_population": {},
            "territory_control": {},
            "meta_data": {
                "last_major_event": None,
                "world_age_days": 1,
                "stability_index": 0.6,
            },
            "version": 1,
            "last_updated": None,
        }
    
    async def get_world_state_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get world state history."""
        postgres = await self._get_postgres()
        
        query = """
            SELECT world_time, weather, global_events, faction_power,
                   economic_state, npc_population, territory_control, simulation_data,
                   created_at, updated_at
            FROM world_states
            ORDER BY created_at DESC
            LIMIT $1
        """
        
        results = await postgres.fetch_all(query, limit)
        
        history = []
        for result in results:
            history.append({
                "world_time": result["world_time"],
                "current_weather": result["weather"],
                "global_events": json.loads(result["global_events"]) if isinstance(result["global_events"], str) else result["global_events"],
                "faction_power": json.loads(result["faction_power"]) if isinstance(result["faction_power"], str) else result["faction_power"],
                "economic_state": json.loads(result["economic_state"]) if isinstance(result["economic_state"], str) else result["economic_state"],
                "npc_population": json.loads(result["npc_population"]) if isinstance(result["npc_population"], str) else result["npc_population"],
                "territory_control": json.loads(result["territory_control"]) if isinstance(result["territory_control"], str) else result["territory_control"],
                "meta_data": json.loads(result["simulation_data"]) if isinstance(result["simulation_data"], str) else result["simulation_data"],
                "created_at": result["created_at"].isoformat() if result["created_at"] else None,
                "updated_at": result["updated_at"].isoformat() if result["updated_at"] else None,
            })
        
        return history
    
    async def clear_cache(self):
        """Clear world state cache."""
        redis = await self._get_redis()
        await redis.delete("world_state:current")
        self._state_cache.clear()
    
    async def get_state_metrics(self) -> Dict[str, Any]:
        """Get world state metrics."""
        current_state = await self.get_current_world_state()
        
        return {
            "version": current_state.get("version", 1),
            "last_updated": current_state.get("last_updated"),
            "world_age_days": current_state.get("meta_data", {}).get("world_age_days", 1),
            "stability_index": current_state.get("meta_data", {}).get("stability_index", 0.6),
            "market_stability": current_state.get("economic_state", {}).get("market_stability", 0.7),
            "active_events": len(current_state.get("global_events", {})),
            "faction_count": len(current_state.get("faction_power", {})),
            "territory_count": len(current_state.get("territory_control", {})),
        }
