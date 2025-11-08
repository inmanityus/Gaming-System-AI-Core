"""
Database Connection Module for Story Teller service.
Provides direct PostgreSQL and Redis connections without cross-service imports.
"""

import asyncpg
import aioredis
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages PostgreSQL and Redis connections for story_teller service."""
    
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[aioredis.Redis] = None
    
    async def get_postgres_pool(self) -> asyncpg.Pool:
        """Get or create PostgreSQL connection pool."""
        if self.postgres_pool is None:
            self.postgres_pool = await asyncpg.create_pool(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5443")),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "Inn0vat1on!"),
                database=os.getenv("POSTGRES_DB", "gaming_system_ai_core"),
                min_size=2,
                max_size=20
            )
            logger.info("PostgreSQL connection pool created")
        return self.postgres_pool
    
    async def get_redis_client(self) -> aioredis.Redis:
        """Get or create Redis client."""
        if self.redis_client is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis client created")
        return self.redis_client
    
    async def close(self):
        """Close all database connections."""
        if self.postgres_pool:
            await self.postgres_pool.close()
            logger.info("PostgreSQL connection pool closed")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis client closed")


# Singleton instance
_db_connection: Optional[DatabaseConnection] = None


async def get_database_connection() -> DatabaseConnection:
    """Get singleton DatabaseConnection instance."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


async def get_postgres() -> asyncpg.Pool:
    """Convenience function to get PostgreSQL pool directly."""
    db = await get_database_connection()
    return await db.get_postgres_pool()


async def get_redis() -> aioredis.Redis:
    """Convenience function to get Redis client directly."""
    db = await get_database_connection()
    return await db.get_redis_client()

