"""
Faction Manager - Faction power and territory control.
Manages faction relationships, power calculations, and territory control.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class FactionManager:
    """
    Manages faction power, territory control, and relationships.
    Handles power calculations, territory mapping, and conflict resolution.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._power_cache: Dict[str, float] = {}
        self._territory_cache: Dict[str, List[str]] = {}
        self._cache_ttl = 300  # 5 minutes
    
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
    
    async def get_faction_power(self, faction_id: str) -> float:
        """
        Get faction power with caching.
        
        Args:
            faction_id: Faction identifier
        
        Returns:
            Faction power value (0.0 to 1.0)
        """
        cache_key = f"faction_power:{faction_id}"
        
        # Check cache first
        if faction_id in self._power_cache:
            return self._power_cache[faction_id]
        
        # Check Redis cache
        redis = await self._get_redis()
        cached_power = await redis.get(cache_key)
        
        if cached_power:
            power = float(cached_power)
            self._power_cache[faction_id] = power
            return power
        
        # Calculate power from database
        power = await self._calculate_faction_power(faction_id)
        
        # Cache the result
        self._power_cache[faction_id] = power
        await redis.set(cache_key, str(power), ttl=self._cache_ttl)
        
        return power
    
    async def _calculate_faction_power(self, faction_id: str) -> float:
        """Calculate faction power based on multiple factors."""
        postgres = await self._get_postgres()
        
        # Get faction data
        faction_query = """
            SELECT name, description, faction_type, power_level, territory, relationships, hierarchy, goals, meta_data
            FROM factions
            WHERE id = $1
        """
        
        faction_result = await postgres.fetch(faction_query, faction_id)
        
        if not faction_result:
            return 0.0
        
        # Get NPC count for this faction
        npc_query = """
            SELECT COUNT(*) as npc_count, AVG(CAST(stats->>'level' as INTEGER)) as avg_level
            FROM npcs
            WHERE faction_id = $1
        """
        
        npc_result = await postgres.fetch(npc_query, faction_id)
        
        # Calculate power based on multiple factors
        base_power = faction_result["power_level"] or 0.0
        npc_count = npc_result["npc_count"] or 0
        avg_level = float(npc_result["avg_level"]) if npc_result["avg_level"] else 1.0
        
        # Territory influence
        territory = json.loads(faction_result["territory"]) if isinstance(faction_result["territory"], str) else faction_result["territory"]
        territory_power = len(territory) * 0.1  # 0.1 per territory
        
        # Relationship influence
        relationships = json.loads(faction_result["relationships"]) if isinstance(faction_result["relationships"], str) else faction_result["relationships"]
        relationship_power = sum(relationships.values()) * 0.05  # 0.05 per relationship point
        
        # NPC influence
        npc_power = (npc_count * avg_level) * 0.02  # 0.02 per NPC level
        
        # Calculate total power (normalized to 0.0-1.0)
        # Note: base_power is 0-100, territory_power/relationship_power/npc_power are also on 0-1 scale
        # We need to normalize base_power from 0-100 to 0-1, then add the 0-1 scaled values
        # But since we're dividing everything by 10, we're treating base_power as if it's 0-10, not 0-100
        # The formula should be: (base_power / 100) + (territory_power + relationship_power + npc_power)
        # Let's use the simpler approach: keep base_power as-is and just divide by 100
        total_power = min(1.0, base_power / 100.0 + territory_power + relationship_power + npc_power)
        
        return min(1.0, total_power)
    
    async def update_faction_power(self, faction_id: str, power_delta: float) -> float:
        """
        Update faction power by a delta amount.
        
        Args:
            faction_id: Faction identifier
            power_delta: Power change amount (-1.0 to 1.0)
        
        Returns:
            New faction power value
        """
        postgres = await self._get_postgres()
        
        # Get current power level
        current_query = "SELECT power_level FROM factions WHERE id = $1"
        current_result = await postgres.fetch(current_query, faction_id)
        
        if not current_result:
            raise ValueError(f"Faction {faction_id} not found")
        
        current_power = current_result["power_level"] or 0.0
        new_power = max(0.0, min(100.0, current_power + (power_delta * 100.0)))  # Scale to 0-100 range
        
        # Update faction power level
        update_query = """
            UPDATE factions
            SET power_level = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await postgres.execute(update_query, new_power, faction_id)
        
        # Clear cache
        self._power_cache.pop(faction_id, None)
        redis = await self._get_redis()
        await redis.delete(f"faction_power:{faction_id}")
        
        return new_power / 100.0  # Return normalized value
    
    async def get_territory_control(self, faction_id: str) -> List[str]:
        """
        Get territories controlled by a faction.
        
        Args:
            faction_id: Faction identifier
        
        Returns:
            List of territory identifiers
        """
        cache_key = f"faction_territory:{faction_id}"
        
        # Check cache first
        if faction_id in self._territory_cache:
            return self._territory_cache[faction_id]
        
        # Check Redis cache
        redis = await self._get_redis()
        cached_territories = await redis.get(cache_key)
        
        if cached_territories:
            territories = json.loads(cached_territories)
            self._territory_cache[faction_id] = territories
            return territories
        
        # Get territories from database
        postgres = await self._get_postgres()
        
        query = "SELECT territory FROM factions WHERE id = $1"
        result = await postgres.fetch(query, faction_id)
        
        if not result:
            return []
        
        territory_data = json.loads(result["territory"]) if isinstance(result["territory"], str) else result["territory"]
        territories = list(territory_data.keys()) if territory_data else []
        
        # Cache the result
        self._territory_cache[faction_id] = territories
        await redis.set(cache_key, json.dumps(territories), ttl=self._cache_ttl)
        
        return territories
    
    async def update_territory_control(
        self, 
        faction_id: str, 
        territory_id: str, 
        control_level: float
    ) -> bool:
        """
        Update territory control for a faction.
        
        Args:
            faction_id: Faction identifier
            territory_id: Territory identifier
            control_level: Control level (0.0 to 1.0)
        
        Returns:
            True if update successful
        """
        postgres = await self._get_postgres()
        
        # Get current territory data
        query = "SELECT territory FROM factions WHERE id = $1"
        result = await postgres.fetch(query, faction_id)
        
        if not result:
            return False
        
        territory_data = json.loads(result["territory"]) if isinstance(result["territory"], str) else result["territory"]
        territory_data = territory_data or {}
        
        # Update territory control
        territory_data[territory_id] = control_level
        
        # Update database
        update_query = """
            UPDATE factions
            SET territory = $1::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await postgres.execute(update_query, json.dumps(territory_data), faction_id)
        
        # Clear cache
        self._territory_cache.pop(faction_id, None)
        redis = await self._get_redis()
        await redis.delete(f"faction_territory:{faction_id}")
        
        return True
    
    async def get_faction_relationships(self, faction_id: str) -> Dict[str, float]:
        """
        Get faction relationships.
        
        Args:
            faction_id: Faction identifier
        
        Returns:
            Dictionary of faction relationships
        """
        postgres = await self._get_postgres()
        
        query = "SELECT relationships FROM factions WHERE id = $1"
        result = await postgres.fetch(query, faction_id)
        
        if not result:
            return {}
        
        relationships = json.loads(result["relationships"]) if isinstance(result["relationships"], str) else result["relationships"]
        return relationships or {}
    
    async def update_faction_relationship(
        self, 
        faction_id: str, 
        target_faction_id: str, 
        relationship_delta: float
    ) -> bool:
        """
        Update relationship between two factions.
        
        Args:
            faction_id: Source faction identifier
            target_faction_id: Target faction identifier
            relationship_delta: Relationship change (-1.0 to 1.0)
        
        Returns:
            True if update successful
        """
        postgres = await self._get_postgres()
        
        # Get current relationships
        query = "SELECT relationships FROM factions WHERE id = $1"
        result = await postgres.fetch(query, faction_id)
        
        if not result:
            return False
        
        relationships = json.loads(result["relationships"]) if isinstance(result["relationships"], str) else result["relationships"]
        relationships = relationships or {}
        
        # Update relationship
        current_relationship = relationships.get(target_faction_id, 0.0)
        new_relationship = max(-1.0, min(1.0, current_relationship + relationship_delta))
        relationships[target_faction_id] = new_relationship
        
        # Update database
        update_query = """
            UPDATE factions
            SET relationships = $1::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await postgres.execute(update_query, json.dumps(relationships), faction_id)
        
        return True
    
    async def get_faction_conflicts(self) -> List[Dict[str, Any]]:
        """Get active faction conflicts."""
        postgres = await self._get_postgres()
        
        # Get all factions with their relationships
        query = """
            SELECT id, name, relationships
            FROM factions
            WHERE relationships IS NOT NULL
        """
        
        results = await postgres.fetch_all(query)
        
        conflicts = []
        for result in results:
            faction_id = result["id"]
            faction_name = result["name"]
            relationships = json.loads(result["relationships"]) if isinstance(result["relationships"], str) else result["relationships"]
            
            if relationships:
                for target_faction_id, relationship in relationships.items():
                    if relationship < -0.5:  # Hostile relationship
                        # Get target faction name
                        target_query = "SELECT name FROM factions WHERE id = $1"
                        target_result = await postgres.fetch(target_query, target_faction_id)
                        target_name = target_result["name"] if target_result else "Unknown"
                        
                        conflicts.append({
                            "faction1_id": faction_id,
                            "faction1_name": faction_name,
                            "faction2_id": target_faction_id,
                            "faction2_name": target_name,
                            "relationship": relationship,
                            "severity": abs(relationship),
                        })
        
        return conflicts
    
    async def resolve_conflict(
        self, 
        faction1_id: str, 
        faction2_id: str, 
        resolution_type: str = "negotiation"
    ) -> Dict[str, Any]:
        """
        Resolve a conflict between two factions.
        
        Args:
            faction1_id: First faction identifier
            faction2_id: Second faction identifier
            resolution_type: Type of resolution (negotiation, war, alliance)
        
        Returns:
            Resolution result
        """
        # Get current relationship
        relationships1 = await self.get_faction_relationships(faction1_id)
        current_relationship = relationships1.get(faction2_id, 0.0)
        
        # Calculate resolution based on type
        if resolution_type == "negotiation":
            relationship_change = 0.2  # Improve relationship
        elif resolution_type == "war":
            relationship_change = -0.3  # Worsen relationship
        elif resolution_type == "alliance":
            relationship_change = 0.5  # Significantly improve relationship
        else:
            relationship_change = 0.0
        
        # Update relationship
        await self.update_faction_relationship(faction1_id, faction2_id, relationship_change)
        await self.update_faction_relationship(faction2_id, faction1_id, relationship_change)
        
        return {
            "resolution_type": resolution_type,
            "relationship_change": relationship_change,
            "new_relationship": current_relationship + relationship_change,
            "success": True,
        }
    
    async def get_faction_rankings(self) -> List[Dict[str, Any]]:
        """Get faction power rankings."""
        postgres = await self._get_postgres()
        
        query = """
            SELECT id, name, power_level, territory, relationships
            FROM factions
            ORDER BY power_level DESC
        """
        
        results = await postgres.fetch_all(query)
        
        rankings = []
        for i, result in enumerate(results, 1):
            territory_data = json.loads(result["territory"]) if isinstance(result["territory"], str) else result["territory"]
            relationships = json.loads(result["relationships"]) if isinstance(result["relationships"], str) else result["relationships"]
            
            rankings.append({
                "rank": i,
                "faction_id": result["id"],
                "name": result["name"],
                "power_level": result["power_level"],
                "territory_count": len(territory_data) if territory_data else 0,
                "relationship_count": len(relationships) if relationships else 0,
                "normalized_power": (result["power_level"] or 0) / 10.0,
            })
        
        return rankings
    
    async def clear_cache(self):
        """Clear faction cache."""
        self._power_cache.clear()
        self._territory_cache.clear()
        
        redis = await self._get_redis()
        # Clear all faction-related cache keys
        keys = await redis.keys("faction_*")
        if keys:
            await redis.delete(*keys)
