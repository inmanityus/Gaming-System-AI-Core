"""
API Dependencies for Gaming System AI Core
Handles database connections, Redis clients, and other shared resources
"""
import os
import asyncpg
import redis.asyncio as redis
from typing import Optional
import json
import structlog

logger = structlog.get_logger(__name__)

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None
_redis_client: Optional[redis.Redis] = None


async def get_db_connection_pool() -> asyncpg.Pool:
    """
    Get or create the database connection pool.
    Uses environment variables for configuration.
    """
    global _db_pool
    
    if _db_pool is None:
        # Get credentials from environment or Secrets Manager
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', '5432'))
        db_name = os.getenv('DB_NAME', 'gaming_system_ai_core')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Create connection pool
        _db_pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            min_size=10,
            max_size=20,
            command_timeout=10,
            max_inactive_connection_lifetime=60,
        )
        logger.info("Database connection pool created", 
                   host=db_host, 
                   port=db_port, 
                   database=db_name)
    
    return _db_pool


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client for caching and session management.
    """
    global _redis_client
    
    if _redis_client is None:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            max_connections=50
        )
        logger.info("Redis client created",
                   host=redis_host,
                   port=redis_port,
                   db=redis_db)
    
    return _redis_client


async def close_connections():
    """
    Close all connection pools and clients.
    Called during application shutdown.
    """
    global _db_pool, _redis_client
    
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("Database connection pool closed")
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


class DatabaseTransaction:
    """
    Context manager for database transactions
    """
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.conn: Optional[asyncpg.Connection] = None
        self.tr: Optional[asyncpg.Transaction] = None
    
    async def __aenter__(self):
        self.conn = await self.pool.acquire()
        self.tr = self.conn.transaction()
        await self.tr.start()
        return self.conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self.tr.commit()
            else:
                await self.tr.rollback()
        finally:
            await self.pool.release(self.conn)
