"""
Story Branching - Manages dynamic story paths and branching logic.
"""

import json
import random
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from database_connection import get_postgres
import asyncpg


class StoryBranch:
    """Represents a story branch with conditions and outcomes."""
    
    def __init__(
        self,
        branch_id: str,
        from_node_id: UUID,
        to_node_id: UUID,
        conditions: Dict[str, Any],
        weight: float = 1.0,
        is_active: bool = True,
    ):
        self.branch_id = branch_id
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        self.conditions = conditions
        self.weight = weight
        self.is_active = is_active
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "branch_id": self.branch_id,
            "from_node_id": str(self.from_node_id),
            "to_node_id": str(self.to_node_id),
            "conditions": self.conditions,
            "weight": self.weight,
            "is_active": self.is_active,
        }


class StoryBranching:
    """
    Manages dynamic story branching and path selection.
    Handles conditional story progression based on player state.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self._branch_cache: Dict[UUID, List[StoryBranch]] = {}
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def create_branch(
        self,
        from_node_id: UUID,
        to_node_id: UUID,
        conditions: Dict[str, Any],
        weight: float = 1.0,
    ) -> StoryBranch:
        """
        Create a new story branch.
        
        Args:
            from_node_id: Source story node UUID
            to_node_id: Target story node UUID
            conditions: Conditions for this branch to be available
            weight: Weight for random selection (higher = more likely)
        
        Returns:
            Created story branch
        """
        postgres = await self._get_postgres()
        
        branch_id = f"branch_{from_node_id}_{to_node_id}"
        
        query = """
            INSERT INTO story_branches
            (branch_id, from_node_id, to_node_id, conditions, weight, is_active)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            ON CONFLICT (branch_id)
            DO UPDATE SET conditions = $4::jsonb, weight = $5, is_active = $6, updated_at = CURRENT_TIMESTAMP
            RETURNING branch_id, from_node_id, to_node_id, conditions, weight, is_active
        """
        
        result = await postgres.fetch(
            query,
            branch_id,
            from_node_id,
            to_node_id,
            json.dumps(conditions),
            weight,
            True,
        )
        
        branch = StoryBranch(
            branch_id=result["branch_id"],
            from_node_id=result["from_node_id"],
            to_node_id=result["to_node_id"],
            conditions=json.loads(result["conditions"]) if isinstance(result["conditions"], str) else result["conditions"],
            weight=result["weight"],
            is_active=result["is_active"],
        )
        
        # Clear cache for this node
        if from_node_id in self._branch_cache:
            del self._branch_cache[from_node_id]
        
        return branch
    
    async def get_available_branches(
        self, 
        player_id: UUID, 
        from_node_id: UUID
    ) -> List[StoryBranch]:
        """
        Get all available branches from a story node for a player.
        
        Args:
            player_id: Player UUID
            from_node_id: Source story node UUID
        
        Returns:
            List of available story branches
        """
        # Check cache first
        if from_node_id in self._branch_cache:
            cached_branches = self._branch_cache[from_node_id]
            # Filter by player conditions
            available = []
            for branch in cached_branches:
                if await self._evaluate_branch_conditions(player_id, branch):
                    available.append(branch)
            return available
        
        postgres = await self._get_postgres()
        
        query = """
            SELECT branch_id, from_node_id, to_node_id, conditions, weight, is_active
            FROM story_branches
            WHERE from_node_id = $1 AND is_active = TRUE
        """
        
        results = await postgres.fetch_all(query, from_node_id)
        
        branches = []
        for result in results:
            branch = StoryBranch(
                branch_id=result["branch_id"],
                from_node_id=result["from_node_id"],
                to_node_id=result["to_node_id"],
                conditions=json.loads(result["conditions"]) if isinstance(result["conditions"], str) else result["conditions"],
                weight=result["weight"],
                is_active=result["is_active"],
            )
            
            # Check if branch conditions are met
            if await self._evaluate_branch_conditions(player_id, branch):
                branches.append(branch)
        
        # Cache the results
        self._branch_cache[from_node_id] = branches
        
        return branches
    
    async def _evaluate_branch_conditions(
        self, 
        player_id: UUID, 
        branch: StoryBranch
    ) -> bool:
        """Evaluate if branch conditions are met for a player."""
        if not branch.conditions:
            return True
        
        postgres = await self._get_postgres()
        
        # Check level condition
        if "min_level" in branch.conditions:
            level_query = "SELECT level FROM players WHERE id = $1"
            level_result = await postgres.fetch(level_query, player_id)
            if not level_result or level_result["level"] < branch.conditions["min_level"]:
                return False
        
        # Check reputation condition
        if "min_reputation" in branch.conditions:
            rep_query = "SELECT reputation FROM players WHERE id = $1"
            rep_result = await postgres.fetch(rep_query, player_id)
            if not rep_result or rep_result["reputation"] < branch.conditions["min_reputation"]:
                return False
        
        # Check money condition
        if "min_money" in branch.conditions:
            money_query = "SELECT money FROM players WHERE id = $1"
            money_result = await postgres.fetch(money_query, player_id)
            if not money_result or money_result["money"] < branch.conditions["min_money"]:
                return False
        
        # Check story progress condition
        if "required_story_nodes" in branch.conditions:
            story_query = """
                SELECT COUNT(*) as count
                FROM story_nodes
                WHERE player_id = $1 AND id = ANY($2) AND status = 'completed'
            """
            story_result = await postgres.fetch(
                story_query, 
                player_id, 
                branch.conditions["required_story_nodes"]
            )
            if not story_result or story_result["count"] < len(branch.conditions["required_story_nodes"]):
                return False
        
        # Check relationship conditions
        if "required_relationships" in branch.conditions:
            rel_query = "SELECT relationships FROM players WHERE id = $1"
            rel_result = await postgres.fetch(rel_query, player_id)
            if not rel_result:
                return False
            
            relationships = json.loads(rel_result["relationships"]) if isinstance(rel_result["relationships"], str) else rel_result["relationships"]
            
            for npc, min_value in branch.conditions["required_relationships"].items():
                if relationships.get(npc, 0) < min_value:
                    return False
        
        # Check item conditions
        if "required_items" in branch.conditions:
            inv_query = "SELECT inventory FROM players WHERE id = $1"
            inv_result = await postgres.fetch(inv_query, player_id)
            if not inv_result:
                return False
            
            inventory = json.loads(inv_result["inventory"]) if isinstance(inv_result["inventory"], str) else inv_result["inventory"]
            
            for item, min_count in branch.conditions["required_items"].items():
                if inventory.get(item, 0) < min_count:
                    return False
        
        # Check world state conditions
        if "world_conditions" in branch.conditions:
            world_query = """
                SELECT global_events, faction_power, economic_state
                FROM world_states
                ORDER BY created_at DESC
                LIMIT 1
            """
            world_result = await postgres.fetch(world_query)
            if not world_result:
                return False
            
            world_state = {
                "global_events": json.loads(world_result["global_events"]) if isinstance(world_result["global_events"], str) else world_result["global_events"],
                "faction_power": json.loads(world_result["faction_power"]) if isinstance(world_result["faction_power"], str) else world_result["faction_power"],
                "economic_state": json.loads(world_result["economic_state"]) if isinstance(world_result["economic_state"], str) else world_result["economic_state"],
            }
            
            for condition, value in branch.conditions["world_conditions"].items():
                if not self._evaluate_world_condition(world_state, condition, value):
                    return False
        
        return True
    
    def _evaluate_world_condition(
        self, 
        world_state: Dict[str, Any], 
        condition: str, 
        expected_value: Any
    ) -> bool:
        """Evaluate a world state condition."""
        # Simple condition evaluation
        # This could be expanded for more complex conditions
        
        if condition.startswith("global_events."):
            event_key = condition.split(".", 1)[1]
            return world_state.get("global_events", {}).get(event_key) == expected_value
        
        elif condition.startswith("faction_power."):
            faction_key = condition.split(".", 1)[1]
            return world_state.get("faction_power", {}).get(faction_key) == expected_value
        
        elif condition.startswith("economic_state."):
            econ_key = condition.split(".", 1)[1]
            return world_state.get("economic_state", {}).get(econ_key) == expected_value
        
        return False
    
    async def select_next_node(
        self, 
        player_id: UUID, 
        from_node_id: UUID
    ) -> Optional[UUID]:
        """
        Select the next story node based on available branches.
        
        Args:
            player_id: Player UUID
            from_node_id: Source story node UUID
        
        Returns:
            Next story node UUID or None if no branches available
        """
        available_branches = await self.get_available_branches(player_id, from_node_id)
        
        if not available_branches:
            return None
        
        # Weighted random selection
        total_weight = sum(branch.weight for branch in available_branches)
        if total_weight == 0:
            return available_branches[0].to_node_id
        
        import random
        random_value = random.uniform(0, float(total_weight))
        current_weight = 0
        
        for branch in available_branches:
            current_weight += float(branch.weight)
            if random_value <= current_weight:
                return branch.to_node_id
        
        # Fallback to last branch
        return available_branches[-1].to_node_id
    
    async def get_story_path(
        self, 
        player_id: UUID, 
        start_node_id: UUID, 
        max_depth: int = 10
    ) -> List[UUID]:
        """
        Get a complete story path from a starting node.
        
        Args:
            player_id: Player UUID
            start_node_id: Starting story node UUID
            max_depth: Maximum path depth
        
        Returns:
            List of story node UUIDs in path order
        """
        path = [start_node_id]
        current_node = start_node_id
        depth = 0
        
        while depth < max_depth:
            next_node = await self.select_next_node(player_id, current_node)
            if not next_node:
                break
            
            path.append(next_node)
            current_node = next_node
            depth += 1
        
        return path
    
    async def deactivate_branch(self, branch_id: str) -> bool:
        """
        Deactivate a story branch.
        
        Args:
            branch_id: Branch ID to deactivate
        
        Returns:
            True if branch was deactivated
        """
        postgres = await self._get_postgres()
        
        query = """
            UPDATE story_branches
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE branch_id = $1
        """
        
        result = await postgres.execute(query, branch_id)
        
        # Clear relevant cache entries
        self._branch_cache.clear()
        
        return result is not None
