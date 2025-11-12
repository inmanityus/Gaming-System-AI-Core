"""
Configuration Manager - CRUD operations for game configuration.
Manages settings with hot-reload capabilities.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, ValidationError

# REFACTORING: Direct database imports replaced with on-demand connections
import asyncpg
from typing import Any as PostgreSQLPool


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigManager:
    """
    Manages game configuration with hot-reload support.
    Stores settings in PostgreSQL with Redis caching.
    """
    
    def __init__(self, default_settings_path: str = "config/default_settings.json"):
        """
        Initialize configuration manager.
        
        Args:
            default_settings_path: Path to default settings JSON file
        """
        self.default_settings_path = Path(default_settings_path)
        self.default_settings: Dict[str, Any] = {}
        self.postgres: Optional[PostgreSQLPool] = None
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default settings from JSON file."""
        if self.default_settings_path.exists():
            with open(self.default_settings_path, 'r', encoding='utf-8') as f:
                self.default_settings = json.load(f)
        else:
            # Minimal defaults if file doesn't exist
            self.default_settings = {
                "game": {"max_players": 10000, "world_tick_rate": 60},
                "difficulty": {"default_difficulty": "normal"},
                "features": {"beta_features_enabled": False}
            }
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration setting value.
        
        Args:
            category: Settings category (e.g., "game", "ui", "audio")
            key: Setting key within category
            default: Default value if not found
        
        Returns:
            Setting value or default
        """
        postgres = await self._get_postgres()
        
        query = """
            SELECT value
            FROM settings
            WHERE category = $1 AND key = $2
            ORDER BY updated_at DESC
            LIMIT 1
        """
        
        result = await postgres.fetch(query, category, key)
        
        if result:
            return json.loads(result["value"]) if isinstance(result["value"], str) else result["value"]
        
        # Fallback to defaults
        if default is not None:
            return default
        
        return self.default_settings.get(category, {}).get(key, None)
    
    async def set_setting(self, category: str, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set a configuration setting value.
        
        Args:
            category: Settings category
            key: Setting key
            value: Setting value (must be JSON-serializable)
            validate: Whether to validate the value
        
        Returns:
            True if setting was saved successfully
        """
        postgres = await self._get_postgres()
        
        # Validate value can be serialized
        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ConfigValidationError(f"Value is not JSON-serializable: {e}")
        
        # Upsert setting
        query = """
            INSERT INTO settings (category, key, value, updated_at)
            VALUES ($1, $2, $3::jsonb, CURRENT_TIMESTAMP)
            ON CONFLICT (category, key)
            DO UPDATE SET value = $3::jsonb, updated_at = CURRENT_TIMESTAMP
        """
        
        await postgres.execute(query, category, key, json_value)
        
        # Invalidate cache for hot-reload (requires state-manager HTTP client)
        # TODO: Use state-manager HTTP client for cache invalidation
        # redis = await get_redis_pool()
        cache_key = f"setting:{category}:{key}"
        await redis.delete(cache_key)
        
        return True
    
    async def get_all_settings(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all settings, optionally filtered by category.
        
        Args:
            category: Optional category filter
        
        Returns:
            Dictionary of settings {category: {key: value}}
        """
        postgres = await self._get_postgres()
        
        if category:
            query = """
                SELECT category, key, value
                FROM settings
                WHERE category = $1
                ORDER BY category, key
            """
            results = await postgres.fetch_all(query, category)
        else:
            query = """
                SELECT category, key, value
                FROM settings
                ORDER BY category, key
            """
            results = await postgres.fetch_all(query)
        
        settings = {}
        for row in results:
            cat = row["category"]
            key = row["key"]
            value = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
            
            if cat not in settings:
                settings[cat] = {}
            settings[cat][key] = value
        
        return settings
    
    async def delete_setting(self, category: str, key: str) -> bool:
        """
        Delete a setting (restores to default).
        
        Args:
            category: Settings category
            key: Setting key
        
        Returns:
            True if setting was deleted
        """
        postgres = await self._get_postgres()
        
        query = "DELETE FROM settings WHERE category = $1 AND key = $2"
        result = await postgres.execute(query, category, key)
        
        # Invalidate cache (requires state-manager HTTP client)
        # TODO: Use state-manager HTTP client for cache invalidation
        # redis = await get_redis_pool()
        # await redis.delete(f"setting:{category}:{key}")
        
        return True

