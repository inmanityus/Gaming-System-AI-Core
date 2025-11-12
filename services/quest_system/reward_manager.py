"""
Reward Manager - Quest reward calculation and distribution.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
# REFACTORING: Direct database imports replaced with on-demand connections  
# from state_manager.connection_pool import get_postgres_pool, PostgreSQLPool
import asyncpg
from typing import Any as PostgreSQLPool


class RewardManager:
    """
    Manages quest reward calculation and distribution.
    Handles reward calculation, distribution to players, and reward tracking.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def calculate_rewards(
        self,
        quest_id: UUID,
        bonus_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate rewards for quest completion.
        
        Args:
            quest_id: Quest UUID
            bonus_multiplier: Bonus multiplier for rewards
        
        Returns:
            Calculated rewards dictionary
        """
        # Get quest to access reward data
        postgres = await self._get_postgres()
        
        quest_row = await postgres.fetch(
            """
            SELECT consequences
            FROM story_nodes
            WHERE id = $1 AND node_type = 'quest'
            """,
            quest_id
        )
        
        if not quest_row:
            raise ValueError(f"Quest not found: {quest_id}")
        
        consequences = quest_row.get("consequences") or {}
        if isinstance(consequences, str):
            consequences = json.loads(consequences)
        base_rewards = consequences.get("rewards", {}) or {}
        
        # Apply bonus multiplier
        rewards = {
            "money": int(base_rewards.get("money", 0) * bonus_multiplier),
            "experience": int(base_rewards.get("experience", 0) * bonus_multiplier),
            "reputation": int(base_rewards.get("reputation", 0) * bonus_multiplier),
            "items": base_rewards.get("items", []),
        }
        
        return rewards
    
    async def distribute_rewards(
        self,
        player_id: UUID,
        rewards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Distribute rewards to player.
        
        Args:
            player_id: Player UUID
            rewards: Rewards dictionary
        
        Returns:
            Distribution result
        """
        postgres = await self._get_postgres()
        
        # Get current player data
        player = await postgres.fetch(
            """
            SELECT id, money, xp, reputation, level, inventory
            FROM players
            WHERE id = $1
            """,
            player_id
        )
        
        if not player:
            raise ValueError(f"Player not found: {player_id}")
        
        # Calculate new values
        new_money = float(player["money"]) + rewards.get("money", 0)
        new_xp = float(player["xp"]) + rewards.get("experience", 0)
        new_reputation = player["reputation"] + rewards.get("reputation", 0)
        new_level = player["level"]
        
        # Check for level up (simple: 100 XP per level)
        xp_needed = new_level * 100
        while new_xp >= xp_needed:
            new_level += 1
            new_xp -= xp_needed
            xp_needed = new_level * 100
        
        # Update inventory with items
        inventory = player.get("inventory", []) or []
        if isinstance(inventory, str):
            inventory = json.loads(inventory)
        for item in rewards.get("items", []):
            inventory.append(item)
        
        # Update player
        await postgres.execute(
            """
            UPDATE players
            SET money = $1, xp = $2, reputation = $3, level = $4, inventory = $5::jsonb
            WHERE id = $6
            """,
            new_money,
            new_xp,
            new_reputation,
            new_level,
            json.dumps(inventory),
            player_id
        )
        
        return {
            "success": True,
            "rewards_distributed": rewards,
            "new_player_state": {
                "money": new_money,
                "xp": new_xp,
                "reputation": new_reputation,
                "level": new_level,
            }
        }
    
    async def complete_quest_rewards(
        self,
        quest_id: UUID,
        player_id: UUID,
        bonus_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate and distribute quest completion rewards.
        
        Args:
            quest_id: Quest UUID
            player_id: Player UUID
            bonus_multiplier: Bonus multiplier for rewards
        
        Returns:
            Distribution result
        """
        rewards = await self.calculate_rewards(quest_id, bonus_multiplier)
        result = await self.distribute_rewards(player_id, rewards)
        
        return result

