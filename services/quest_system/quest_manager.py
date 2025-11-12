"""
Quest Manager - Quest lifecycle management and CRUD operations.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# REFACTORING: Direct database imports replaced with on-demand connections
# from state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool
import asyncpg
import redis.asyncio as redis
from typing import Optional, Any as PostgreSQLPool, Any as RedisPool


class QuestManager:
    """
    Manages quest lifecycle and CRUD operations.
    Handles quest creation, updates, completion, and status management.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = get_state_manager_client()
        return self.redis
    
    async def create_quest(self, quest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new quest in the database.
        
        Args:
            quest_data: Quest data dictionary
        
        Returns:
            Created quest data
        """
        postgres = await self._get_postgres()
        redis = await self._get_redis()
        
        quest_id = UUID(quest_data["quest_id"])
        player_id = UUID(quest_data["player_id"])
        
        # Store quest as story_node with node_type='quest'
        import json as json_lib
        quest_row = await postgres.fetch(
            """
            INSERT INTO story_nodes (
                id, player_id, node_type, title, description,
                narrative_content, choices, status, prerequisites,
                consequences, meta_data
            ) VALUES (
                $1, $2, 'quest', $3, $4, $5, $6::jsonb, $7, $8::jsonb, $9::jsonb, $10::jsonb
            )
            RETURNING *
            """,
            quest_id,
            player_id,
            quest_data["title"],
            quest_data["description"],
            quest_data.get("description", ""),
            json_lib.dumps(quest_data.get("objectives", [])),
            quest_data.get("status", "active"),
            json_lib.dumps(quest_data.get("prerequisites", [])),
            json_lib.dumps({
                "rewards": quest_data.get("rewards", {}),
                "objectives": quest_data.get("objectives", []),
                "quest_giver_npc_id": quest_data.get("quest_giver_npc_id"),
                "world_state_id": quest_data.get("world_state_id"),
            }),
            json_lib.dumps(quest_data.get("meta_data", {})),
        )
        
        # Cache quest in Redis
        cache_key = f"quest:{quest_id}"
        quest_dict = self._row_to_dict(quest_row)
        await redis.set(
            cache_key,
            json.dumps(quest_dict),
            ttl=3600  # 1 hour TTL
        )
        
        # Update player's active quests in game_states
        await self._update_active_quests(player_id, quest_id, "add")
        
        return self._row_to_dict(quest_row)
    
    async def get_quest(self, quest_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get quest by ID.
        
        Args:
            quest_id: Quest UUID
        
        Returns:
            Quest data or None
        """
        redis = await self._get_redis()
        postgres = await self._get_postgres()
        
        # Try cache first
        cache_key = f"quest:{quest_id}"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Query database
        quest_row = await postgres.fetch(
            """
            SELECT * FROM story_nodes
            WHERE id = $1 AND node_type = 'quest'
            """,
            quest_id
        )
        
        if quest_row:
            quest_data = self._row_to_dict(quest_row)
            # Cache result
            await redis.set(cache_key, json.dumps(quest_data), ttl=3600)
            return quest_data
        
        return None
    
    async def get_player_quests(self, player_id: UUID, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all quests for a player.
        
        Args:
            player_id: Player UUID
            status: Optional status filter
        
        Returns:
            List of quests
        """
        postgres = await self._get_postgres()
        
        query = """
            SELECT * FROM story_nodes
            WHERE player_id = $1 AND node_type = 'quest'
        """
        params = [player_id]
        
        if status:
            query += " AND status = $2"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        rows = await postgres.fetch_all(query, *params)
        
        return [self._row_to_dict(row) for row in rows]
    
    async def update_quest_status(self, quest_id: UUID, status: str) -> Dict[str, Any]:
        """
        Update quest status.
        
        Args:
            quest_id: Quest UUID
            status: New status (active, in_progress, completed, failed)
        
        Returns:
            Updated quest data
        """
        postgres = await self._get_postgres()
        redis = await self._get_redis()
        
        quest_row = await postgres.fetch(
            """
            UPDATE story_nodes
            SET status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2 AND node_type = 'quest'
            RETURNING *
            """,
            status,
            quest_id
        )
        
        if quest_row:
            quest_data = self._row_to_dict(quest_row)
            # Update cache
            cache_key = f"quest:{quest_id}"
            await redis.set(cache_key, json.dumps(quest_data), ttl=3600)
            
            # Update active quests if completed or failed
            if status in ["completed", "failed"]:
                await self._update_active_quests(UUID(quest_data["player_id"]), quest_id, "remove")
            
            return quest_data
        
        raise ValueError(f"Quest not found: {quest_id}")
    
    async def update_quest_objectives(
        self,
        quest_id: UUID,
        objectives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update quest objectives.
        
        Args:
            quest_id: Quest UUID
            objectives: Updated objectives list
        
        Returns:
            Updated quest data
        """
        postgres = await self._get_postgres()
        redis = await self._get_redis()
        
        # Get current quest first to verify it exists
        existing_quest = await postgres.fetch(
            """
            SELECT * FROM story_nodes
            WHERE id = $1 AND node_type = 'quest'
            """,
            quest_id
        )
        
        if not existing_quest:
            raise ValueError(f"Quest not found: {quest_id}")
        
        # Update choices (objectives stored in choices JSONB)
        updated_row = await postgres.fetch(
            """
            UPDATE story_nodes
            SET choices = $1::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2 AND node_type = 'quest'
            RETURNING *
            """,
            json.dumps(objectives),
            quest_id
        )
        
        quest_data = self._row_to_dict(updated_row)
        
        # Update cache
        cache_key = f"quest:{quest_id}"
        await redis.set(cache_key, json.dumps(quest_data), ttl=3600)
        
        return quest_data
    
    async def delete_quest(self, quest_id: UUID) -> bool:
        """
        Delete a quest.
        
        Args:
            quest_id: Quest UUID
        
        Returns:
            True if deleted, False otherwise
        """
        postgres = await self._get_postgres()
        redis = await self._get_redis()
        
        # Get quest to find player_id
        quest = await self.get_quest(quest_id)
        if not quest:
            return False
        
        player_id = UUID(quest["player_id"])
        
        # Delete from database
        await postgres.execute(
            """
            DELETE FROM story_nodes
            WHERE id = $1 AND node_type = 'quest'
            """,
            quest_id
        )
        
        # Remove from cache
        cache_key = f"quest:{quest_id}"
        await redis.delete(cache_key)
        
        # Update active quests
        await self._update_active_quests(player_id, quest_id, "remove")
        
        return True
    
    async def _update_active_quests(self, player_id: UUID, quest_id: UUID, operation: str):
        """Update active quests in game_states."""
        postgres = await self._get_postgres()
        
        # Get current game state
        game_state = await postgres.fetch(
            """
            SELECT id, active_quests
            FROM game_states
            WHERE player_id = $1 AND is_active = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            player_id
        )
        
        if not game_state:
            # Create game state if it doesn't exist
            await postgres.execute(
                """
                INSERT INTO game_states (player_id, active_quests)
                VALUES ($1, $2::jsonb)
                ON CONFLICT DO NOTHING
                """,
                player_id,
                json.dumps([str(quest_id)] if operation == "add" else [])
            )
        else:
            active_quests = game_state.get("active_quests") or []
            if isinstance(active_quests, str):
                active_quests = json.loads(active_quests)
            
            if operation == "add":
                if str(quest_id) not in active_quests:
                    active_quests.append(str(quest_id))
            elif operation == "remove":
                active_quests = [q for q in active_quests if q != str(quest_id)]
            
            await postgres.execute(
                """
                UPDATE game_states
                SET active_quests = $1::jsonb
                WHERE id = $2
                """,
                json.dumps(active_quests),
                game_state["id"]
            )
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        if row is None:
            return None
        
        # Parse JSONB fields if they're strings
        consequences = row.get("consequences", {}) or {}
        if isinstance(consequences, str):
            consequences = json.loads(consequences)
        
        choices = row.get("choices", []) or []
        if isinstance(choices, str):
            choices = json.loads(choices)
        
        prerequisites = row.get("prerequisites", []) or []
        if isinstance(prerequisites, str):
            prerequisites = json.loads(prerequisites)
        
        meta_data = row.get("meta_data", {}) or {}
        if isinstance(meta_data, str):
            meta_data = json.loads(meta_data)
        
        # Extract quest-specific data from consequences
        quest_giver_npc_id = None
        world_state_id = None
        rewards = {}
        if isinstance(consequences, dict):
            quest_giver_npc_id = consequences.get("quest_giver_npc_id")
            world_state_id = consequences.get("world_state_id")
            rewards = consequences.get("rewards", {})
        
        quest_type = "side"
        if isinstance(meta_data, dict):
            quest_type = meta_data.get("quest_type", "side")
        
        return {
            "quest_id": str(row["id"]),
            "player_id": str(row["player_id"]),
            "quest_type": quest_type,
            "title": row["title"],
            "description": row["description"],
            "objectives": choices,
            "rewards": rewards,
            "status": row["status"],
            "prerequisites": prerequisites,
            "quest_giver_npc_id": quest_giver_npc_id,
            "world_state_id": world_state_id,
            "meta_data": meta_data,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }

