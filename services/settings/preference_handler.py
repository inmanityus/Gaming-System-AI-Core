"""
Preference Handler - Manages player preferences and settings per-user.
"""

import json
from typing import Any, Dict, Optional
from uuid import UUID

from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool


class PreferenceHandler:
    """
    Handles player-specific preferences and settings.
    Preferences are stored per-player and persist across sessions.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def get_preference(self, player_id: UUID, category: str, key: str, default: Any = None) -> Any:
        """
        Get a player preference value.
        
        Args:
            player_id: Player UUID
            category: Preference category (e.g., "audio", "video", "controls")
            key: Preference key
            default: Default value if not found
        
        Returns:
            Preference value or default
        """
        postgres = await self._get_postgres()
        
        query = """
            SELECT value
            FROM player_preferences
            WHERE player_id = $1 AND category = $2 AND key = $3
        """
        
        result = await postgres.fetch(query, player_id, category, key)
        
        if result:
            return json.loads(result["value"]) if isinstance(result["value"], str) else result["value"]
        
        return default
    
    async def set_preference(self, player_id: UUID, category: str, key: str, value: Any) -> bool:
        """
        Set a player preference value.
        
        Args:
            player_id: Player UUID
            category: Preference category
            key: Preference key
            value: Preference value (must be JSON-serializable)
        
        Returns:
            True if preference was saved
        """
        postgres = await self._get_postgres()
        
        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value is not JSON-serializable: {e}")
        
        query = """
            INSERT INTO player_preferences (player_id, category, key, value, updated_at)
            VALUES ($1, $2, $3, $4::jsonb, CURRENT_TIMESTAMP)
            ON CONFLICT (player_id, category, key)
            DO UPDATE SET value = $4::jsonb, updated_at = CURRENT_TIMESTAMP
        """
        
        await postgres.execute(query, player_id, category, key, json_value)
        
        return True
    
    async def get_all_preferences(self, player_id: UUID, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all preferences for a player.
        
        Args:
            player_id: Player UUID
            category: Optional category filter
        
        Returns:
            Dictionary of preferences {category: {key: value}}
        """
        postgres = await self._get_postgres()
        
        if category:
            query = """
                SELECT category, key, value
                FROM player_preferences
                WHERE player_id = $1 AND category = $2
                ORDER BY category, key
            """
            results = await postgres.fetch_all(query, player_id, category)
        else:
            query = """
                SELECT category, key, value
                FROM player_preferences
                WHERE player_id = $1
                ORDER BY category, key
            """
            results = await postgres.fetch_all(query, player_id)
        
        preferences = {}
        for row in results:
            cat = row["category"]
            key = row["key"]
            value = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
 vel
            
            if cat not in preferences:
                preferences[cat] = {}
            preferences[cat][key] = value
        
        return preferences
    
    async def delete_preference(self, player_id: UUID, category: str, key: str) -> bool:
        """
        Delete a player preference (restores to default).
        
        Args:
            player_id: Player UUID
            category: Preference category
            key: Preference key
        
        Returns:
            True if preference was deleted
        """
        postgres = await self._get_postgres()
        
        query = "DELETE FROM player_preferences WHERE player_id = $1 AND category = $2 AND key = $3"
        await postgres.execute(query, player_id, category, key)
        
        return True

