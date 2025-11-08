"""
Spatial Manager - Territory control and spatial relationships.
Manages territory ownership, borders, and spatial conflicts.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database_connection import get_postgres, get_redis
import asyncpg
import aioredis


class SpatialManager:
    """
    Manages spatial relationships and territory control.
    Handles territory ownership, borders, and conflicts.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._territory_cache: Dict[str, Dict[str, Any]] = {}
        self._border_cache: Dict[str, List[str]] = {}
        self._cache_ttl = 600  # 10 minutes
    
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
    
    async def update_territory_control(self, world_state_id: str) -> Dict[str, Any]:
        """
        Update territory control based on faction power and NPC presence.
        
        Args:
            world_state_id: World state UUID
        
        Returns:
            Territory update results
        """
        # Load all factions and their territories
        factions = await self._load_faction_territories(world_state_id)
        
        # Calculate territory control strength for each faction
        control_strength = await self._calculate_control_strength(world_state_id, factions)
        
        # Determine territory ownership changes
        ownership_changes = await self._process_territory_changes(world_state_id, factions, control_strength)
        
        # Update territory borders
        border_changes = await self._update_borders(world_state_id, ownership_changes)
        
        # Generate spatial events (conflicts, expansions, etc.)
        events = await self._generate_spatial_events(world_state_id, ownership_changes, border_changes)
        
        return {
            "world_state_id": world_state_id,
            "ownership_changes": ownership_changes,
            "border_changes": border_changes,
            "events": events,
            "timestamp": time.time()
        }
    
    async def _load_faction_territories(self, world_state_id: str) -> List[Dict[str, Any]]:
        """Load all faction territories."""
        postgres = await self._get_postgres()
        
        # Note: factions table doesn't have world_state_id column
        # For simulation, get all factions (world_state filtering would require meta_data lookup)
        factions = await postgres.fetch_all(
            """
            SELECT id, name, power_level, territory, relationships, meta_data
            FROM factions
            LIMIT 50
            """
        )
        
        # Filter by world_state_id from meta_data if available
        filtered_factions = []
        for faction in factions:
            meta = faction.get("meta_data", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            if isinstance(meta, dict) and meta.get("world_state_id") == world_state_id:
                filtered_factions.append(faction)
            # If no world_state_id in meta_data, include all factions for simulation
        
        factions = filtered_factions if filtered_factions else list(factions)
        
        result = []
        for faction in factions:
            # Already filtered by world_state_id above
            territory = faction.get("territory")
            if isinstance(territory, str):
                try:
                    territory = json.loads(territory)
                except json.JSONDecodeError:
                    territory = []
            elif territory is None:
                territory = []
            
            result.append({
                "id": str(faction["id"]),
                "name": faction["name"],
                "power_level": faction.get("power_level", 0.0),
                "territory": territory if isinstance(territory, list) else [],
                "faction_type": faction.get("faction_type", "unknown")
            })
        
        return result
    
    async def _calculate_control_strength(self, world_state_id: str, factions: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate control strength for each faction in each territory."""
        postgres = await self._get_postgres()
        
        control_strength = {}
        
        # Get all territories from factions
        all_territories = set()
        for faction in factions:
            territory = faction["territory"]
            # Handle both list and dict formats
            if isinstance(territory, dict):
                territory = list(territory.keys()) if territory else []
            elif isinstance(territory, str):
                import json
                territory = json.loads(territory) if territory else []
            if isinstance(territory, list):
                # Normalize territory IDs to be hashable
                normalized = []
                for t in territory:
                    if isinstance(t, dict):
                        normalized.append(t.get("id", str(t)))
                    elif isinstance(t, (str, int)):
                        normalized.append(t)
                    else:
                        normalized.append(str(t))
                all_territories.update(normalized)
        
        # For each territory, calculate control strength for each faction
        for territory_id in all_territories:
            control_strength[territory_id] = {}
            
            for faction in factions:
                # Base strength from faction power level
                base_strength = faction["power_level"]
                
                # Count NPCs in this territory from this faction
                npc_count = await postgres.fetch(
                    """
                    SELECT COUNT(*) as count
                    FROM npcs
                    WHERE world_state_id = $1 
                      AND faction_id = $2
                      AND current_location = $3
                    """,
                    world_state_id,
                    faction["id"],
                    territory_id
                )
                
                npc_count_val = npc_count.get("count", 0) if isinstance(npc_count, dict) else 0
                
                # NPC presence adds to control strength
                npc_strength = min(npc_count_val * 0.01, 0.3)  # Max 0.3 from NPCs
                
                # Territory ownership bonus (if faction already owns territory)
                # Handle territory format (list, dict, or str)
                faction_territory = faction["territory"]
                if isinstance(faction_territory, dict):
                    faction_territory = list(faction_territory.keys()) if faction_territory else []
                elif isinstance(faction_territory, str):
                    import json
                    faction_territory = json.loads(faction_territory) if faction_territory else []
                # Normalize for comparison
                if isinstance(faction_territory, list):
                    normalized_territory = [str(t) if not isinstance(t, (str, int)) else t for t in faction_territory]
                    ownership_bonus = 0.2 if str(territory_id) in [str(t) for t in normalized_territory] else 0.0
                else:
                    ownership_bonus = 0.0
                
                # Total control strength
                total_strength = base_strength + npc_strength + ownership_bonus
                control_strength[territory_id][faction["id"]] = total_strength
        
        return control_strength
    
    async def _process_territory_changes(self, world_state_id: str, factions: List[Dict[str, Any]], control_strength: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Process territory ownership changes based on control strength."""
        changes = []
        
        # For each territory, determine if ownership should change
        for territory_id, faction_strengths in control_strength.items():
            if not faction_strengths:
                continue
            
            # Find faction with highest control strength
            strongest_faction_id = max(faction_strengths.items(), key=lambda x: x[1])[0]
            strongest_strength = faction_strengths[strongest_faction_id]
            
            # Find current owner
            current_owner = None
            for faction in factions:
                faction_territory = faction["territory"]
                # Handle territory format (list, dict, or str)
                if isinstance(faction_territory, dict):
                    faction_territory = list(faction_territory.keys()) if faction_territory else []
                elif isinstance(faction_territory, str):
                    import json
                    faction_territory = json.loads(faction_territory) if faction_territory else []
                if isinstance(faction_territory, list):
                    normalized_territory = [str(t) if not isinstance(t, (str, int)) else t for t in faction_territory]
                    if str(territory_id) in [str(t) for t in normalized_territory]:
                        current_owner = faction["id"]
                        break
            
            # Determine if ownership should change
            # Need at least 0.1 strength difference to change ownership
            if current_owner and current_owner != strongest_faction_id:
                current_strength = faction_strengths.get(current_owner, 0.0)
                if strongest_strength > current_strength + 0.1:
                    # Ownership change
                    changes.append({
                        "type": "ownership_change",
                        "territory_id": territory_id,
                        "old_owner": current_owner,
                        "new_owner": strongest_faction_id,
                        "strength_diff": strongest_strength - current_strength
                    })
            elif not current_owner and strongest_strength > 0.3:
                # New territory claimed
                changes.append({
                    "type": "territory_claimed",
                    "territory_id": territory_id,
                    "new_owner": strongest_faction_id,
                    "strength": strongest_strength
                })
        
        # Apply changes to database
        for change in changes:
            await self._apply_territory_change(world_state_id, change)
        
        return changes
    
    async def _apply_territory_change(self, world_state_id: str, change: Dict[str, Any]):
        """Apply territory ownership change to database."""
        postgres = await self._get_postgres()
        territory_id = change["territory_id"]
        
        if change["type"] == "ownership_change":
            # Remove territory from old owner
            old_owner = change["old_owner"]
            old_faction = await postgres.fetch(
                "SELECT territory FROM factions WHERE id = $1",
                old_owner
            )
            
            if old_faction:
                territory = old_faction.get("territory")
                if isinstance(territory, str):
                    territory = json.loads(territory)
                elif territory is None:
                    territory = []
                
                if territory_id in territory:
                    territory.remove(territory_id)
                
                await postgres.execute(
                    "UPDATE factions SET territory = $1::jsonb, updated_at = NOW() WHERE id = $2",
                    json.dumps(territory),
                    old_owner
                )
            
            # Add territory to new owner
            new_owner = change["new_owner"]
            new_faction = await postgres.fetch(
                "SELECT territory FROM factions WHERE id = $1",
                new_owner
            )
            
            if new_faction:
                territory = new_faction.get("territory")
                if isinstance(territory, str):
                    territory = json.loads(territory)
                elif territory is None:
                    territory = []
                
                if territory_id not in territory:
                    territory.append(territory_id)
                
                await postgres.execute(
                    "UPDATE factions SET territory = $1::jsonb, updated_at = NOW() WHERE id = $2",
                    json.dumps(territory),
                    new_owner
                )
        
        elif change["type"] == "territory_claimed":
            # Add territory to new owner
            new_owner = change["new_owner"]
            new_faction = await postgres.fetch(
                "SELECT territory FROM factions WHERE id = $1",
                new_owner
            )
            
            if new_faction:
                territory = new_faction.get("territory")
                if isinstance(territory, str):
                    territory = json.loads(territory)
                elif territory is None:
                    territory = []
                
                if territory_id not in territory:
                    territory.append(territory_id)
                
                await postgres.execute(
                    "UPDATE factions SET territory = $1::jsonb, updated_at = NOW() WHERE id = $2",
                    json.dumps(territory),
                    new_owner
                )
    
    async def _update_borders(self, world_state_id: str, ownership_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update territory borders based on ownership changes."""
        postgres = await self._get_postgres()
        
        # Get all faction territories
        factions = await postgres.fetch_all(
            # Note: factions table doesn't have world_state_id column
            "SELECT id, territory, meta_data FROM factions LIMIT 50"
        )
        
        border_changes = []
        
        # Calculate borders (territories adjacent to different owners)
        for faction in factions:
            # Filter by world_state_id if stored in meta_data
            meta = faction.get("meta_data", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            if isinstance(meta, dict) and meta.get("world_state_id") != world_state_id:
                continue  # Skip factions not in this world_state
            
            faction_id = str(faction["id"])
            territory = faction.get("territory")
            if isinstance(territory, str):
                territory = json.loads(territory)
            elif territory is None:
                territory = []
            
            # Find adjacent territories (simplified - in production, use spatial index)
            adjacent_territories = await self._find_adjacent_territories(territory, world_state_id)
            
            # Check if any adjacent territories belong to other factions
            for adj_territory in adjacent_territories:
                owner = await self._get_territory_owner(world_state_id, adj_territory)
                if owner and owner != faction_id:
                    border_changes.append({
                        "type": "border_conflict",
                        "territory1": adj_territory,
                        "faction1": owner,
                        "territory2": territory[0] if territory else None,
                        "faction2": faction_id
                    })
        
        return border_changes
    
    async def _find_adjacent_territories(self, territory_list: List[str], world_state_id: str) -> List[str]:
        """Find territories adjacent to given territories."""
        # Simplified implementation - in production, use spatial index/graph
        # For now, return empty list (would need spatial data structure)
        return []
    
    async def _get_territory_owner(self, world_state_id: str, territory_id: str) -> Optional[str]:
        """Get current owner of a territory."""
        postgres = await self._get_postgres()
        
        factions = await postgres.fetch_all(
            # Note: factions table doesn't have world_state_id column
            "SELECT id, territory, meta_data FROM factions LIMIT 50"
        )
        
        for faction in factions:
            territory = faction.get("territory")
            if isinstance(territory, str):
                territory = json.loads(territory)
            elif territory is None:
                territory = []
            
            if territory_id in territory:
                return str(faction["id"])
        
        return None
    
    async def _generate_spatial_events(self, world_state_id: str, ownership_changes: List[Dict[str, Any]], border_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate spatial events based on territory changes."""
        events = []
        
        # Ownership change events
        for change in ownership_changes:
            if change["type"] == "ownership_change":
                events.append({
                    "type": "territory_conquered",
                    "description": f"Territory {change['territory_id']} conquered by faction {change['new_owner']}",
                    "territory_id": change["territory_id"],
                    "old_owner": change["old_owner"],
                    "new_owner": change["new_owner"]
                })
            elif change["type"] == "territory_claimed":
                events.append({
                    "type": "territory_claimed",
                    "description": f"Territory {change['territory_id']} claimed by faction {change['new_owner']}",
                    "territory_id": change["territory_id"],
                    "new_owner": change["new_owner"]
                })
        
        # Border conflict events
        for border in border_changes:
            if border["type"] == "border_conflict":
                events.append({
                    "type": "border_tension",
                    "description": f"Border tension between {border['faction1']} and {border['faction2']}",
                    "faction1": border["faction1"],
                    "faction2": border["faction2"]
                })
        
        return events
    
    async def get_territory_ownership(self, world_state_id: str) -> Dict[str, str]:
        """Get current territory ownership map."""
        factions = await self._load_faction_territories(world_state_id)
        
        ownership = {}
        for faction in factions:
            territory = faction["territory"]
            # Handle both list and dict formats
            if isinstance(territory, dict):
                territory = list(territory.keys()) if territory else []
            elif isinstance(territory, str):
                import json
                territory = json.loads(territory) if territory else []
            if isinstance(territory, list):
                for territory_id in territory:
                    # Ensure territory_id is hashable (extract ID if it's a dict)
                    if isinstance(territory_id, dict):
                        territory_id = territory_id.get("id", str(territory_id))
                    elif not isinstance(territory_id, (str, int)):
                        territory_id = str(territory_id)
                    ownership[territory_id] = faction["id"]
        
        return ownership

