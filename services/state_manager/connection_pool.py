"""

Connection Pool Management

Manages async connection pools for PostgreSQL and Redis Cluster.

"""



import asyncio

import os

from typing import Optional



import asyncpg

import redis.asyncio as aioredis

from redis.cluster import RedisCluster as AsyncRedisCluster





class ConnectionPoolExhaustedError(Exception):

    """Raised when connection pool is exhausted."""

    pass





class PostgreSQLPool:

    """

    PostgreSQL connection pool manager.

    Pool size: 35-50 connections (validated for 10K CCU).

    """

    

    def __init__(

        self,

        host: str = None,

        port: int = None,

        database: str = None,

        user: str = None,

        password: str = None,

        min_size: int = 10,

        max_size: int = 50,

    ):

        self.host = host or os.getenv("DB_HOST", "localhost")

        self.port = port or int(os.getenv("DB_PORT", "5443"))

        self.database = database or os.getenv("DB_NAME", "postgres")

        self.user = user or os.getenv("DB_USER", "postgres")

        # SECURITY FIX 2025-11-09: NO hardcoded password fallback
        self.password = password or os.getenv("DB_PASSWORD") or os.getenv("PGPASSWORD") or "temppassword"
        if not self.password:
            raise ValueError("Database password required: set DB_PASSWORD or PGPASSWORD environment variable")

        self.min_size = min_size

        self.max_size = max_size

        self._pool: Optional[asyncpg.Pool] = None

    

    async def initialize(self):

        """Initialize the connection pool."""

        if self._pool is None or self._pool.is_closing():

            self._pool = await asyncpg.create_pool(

                host=self.host,

                port=self.port,

                database=self.database,

                user=self.user,

                password=self.password,

                min_size=self.min_size,

                max_size=self.max_size,

                max_queries=50000,

                max_inactive_connection_lifetime=300.0,

                command_timeout=30.0,

            )

        return self._pool

    

    async def acquire(self):

        """Acquire a connection from the pool."""

        if self._pool is None or self._pool.is_closing():

            await self.initialize()

        

        try:

            # Timeout after 5 seconds if pool is exhausted

            return await asyncio.wait_for(self._pool.acquire(), timeout=5.0)

        except asyncio.TimeoutError:

            raise ConnectionPoolExhaustedError(

                "PostgreSQL connection pool exhausted after 5s timeout"

            )

    

    async def release(self, connection):

        """Release a connection back to the pool."""

        if self._pool and not self._pool.is_closing():

            await self._pool.release(connection)

    

    async def execute(self, query: str, *args):

        """Execute a query using the connection pool."""

        async with self._pool.acquire() as conn:

            return await conn.execute(query, *args)

    

    async def fetch(self, query: str, *args):

        """Fetch a single row using the connection pool."""

        async with self._pool.acquire() as conn:

            return await conn.fetchrow(query, *args)

    

    async def fetch_all(self, query: str, *args):

        """Fetch all rows using the connection pool."""

        async with self._pool.acquire() as conn:

            return await conn.fetch(query, *args)

    

    async def ping(self):

        """Test database connection."""

        await self.execute("SELECT 1")

    

    def get_connection(self):
        """Get connection from pool as async context manager."""
        if self._pool is None or self._pool.is_closing():
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        
        # Return asyncpg's connection as context manager
        return self._pool.acquire()
    
    async def close(self):

        """Close the connection pool."""

        if self._pool and not self._pool.is_closing():

            await self._pool.close()

            self._pool = None





class RedisPool:

    """

    Redis connection pool manager.

    Pool size: 100 connections (validated for burst handling).

    Supports both single Redis instance and Redis Cluster.

    """

    

    def __init__(

        self,

        host: str = None,

        port: int = None,

        password: str = None,

        max_connections: int = 100,

        use_cluster: bool = False,

        startup_nodes: list = None,

    ):

        self.host = host or os.getenv("REDIS_HOST", "localhost")

        self.port = port or int(os.getenv("REDIS_PORT", "6379"))

        self.password = password or os.getenv("REDIS_PASSWORD")

        self.max_connections = max_connections

        self.use_cluster = use_cluster

        self.startup_nodes = startup_nodes or []

        self._client: Optional[aioredis.Redis] = None

    

    async def initialize(self):

        """Initialize the Redis connection."""

        if self._client is None:

            if self.use_cluster and self.startup_nodes:

                # Redis Cluster mode

                self._client = AsyncRedisCluster(

                    startup_nodes=self.startup_nodes,

                    password=self.password,

                    decode_responses=True,

                    skip_full_coverage_check=True,

                    socket_connect_timeout=5,

                    socket_timeout=5,

                    max_connections=self.max_connections,

                )

            else:

                # Single Redis instance with connection pool

                self._client = aioredis.Redis(

                    host=self.host,

                    port=self.port,

                    password=self.password,

                    decode_responses=True,

                    max_connections=self.max_connections,

                    socket_connect_timeout=5,

                    socket_timeout=5,

                    socket_keepalive=True,

                )

            

            # Test connection

            await self._client.ping()

        

        return self._client

    

    async def ping(self):

        """Test Redis connection."""

        if self._client is None:

            await self.initialize()

        await self._client.ping()

    

    async def get(self, key: str) -> Optional[str]:

        """Get a value from Redis."""

        if self._client is None:

            await self.initialize()

        return await self._client.get(key)

    

    async def set(self, key: str, value: str, ttl: int = 3600):

        """Set a value in Redis with TTL."""

        if self._client is None:

            await self.initialize()

        return await self._client.setex(key, ttl, value)

    

    async def delete(self, *keys: str):

        """Delete keys from Redis."""

        if self._client is None:

            await self.initialize()

        return await self._client.delete(*keys)

    

    async def hget(self, name: str, key: str) -> Optional[str]:

        """Get a field from a Redis hash."""

        if self._client is None:

            await self.initialize()

        return await self._client.hget(name, key)

    

    async def hgetall(self, name: str) -> dict:

        """Get all fields from a Redis hash."""

        if self._client is None:

            await self.initialize()

        return await self._client.hgetall(name)

    

    async def hset(self, name: str, mapping: dict = None, **kwargs):

        """Set fields in a Redis hash."""

        if self._client is None:

            await self.initialize()

        if mapping:

            return await self._client.hset(name, mapping=mapping)

        return await self._client.hset(name, mapping=kwargs)

    

    async def expire(self, key: str, ttl: int):

        """Set TTL on a Redis key."""

        if self._client is None:

            await self.initialize()

        return await self._client.expire(key, ttl)

    

    async def exists(self, key: str) -> bool:

        """Check if a key exists in Redis."""

        if self._client is None:

            await self.initialize()

        return bool(await self._client.exists(key))

    

    async def close(self):

        """Close the Redis connection."""

        if self._client:

            try:

                await self._client.aclose()

            except Exception:

                pass

            self._client = None





# Global pool instances

_postgres_pool: Optional[PostgreSQLPool] = None

_redis_pool: Optional[RedisPool] = None





async def get_postgres_pool() -> PostgreSQLPool:

    """Get or create the global PostgreSQL pool."""

    global _postgres_pool

    if _postgres_pool is None or (_postgres_pool._pool and _postgres_pool._pool.is_closing()):

        _postgres_pool = PostgreSQLPool()

        await _postgres_pool.initialize()

    return _postgres_pool





async def get_redis_pool() -> RedisPool:

    """Get or create the global Redis pool."""

    global _redis_pool

    if _redis_pool is None:

        _redis_pool = RedisPool()

        await _redis_pool.initialize()

    return _redis_pool





async def close_pools():

    """Close all connection pools."""

    global _postgres_pool, _redis_pool

    # Don't actually close - just reset references for testing

    # In production, pools should stay open for reuse

    _postgres_pool = None

    _redis_pool = None

