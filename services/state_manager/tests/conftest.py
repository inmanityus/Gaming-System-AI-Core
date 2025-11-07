"""
Pytest configuration for State Management Service tests.
Provides shared fixtures and setup/teardown.
"""

import pytest
import pytest_asyncio
import asyncio


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_pool_before_test():
    """Reset connection pool before each test to avoid event loop conflicts."""
    import services.state_manager.connection_pool as cp
    # Reset pools to ensure fresh state for each test
    if cp._postgres_pool is not None:
        try:
            if hasattr(cp._postgres_pool, '_pool') and cp._postgres_pool._pool:
                if not cp._postgres_pool._pool.is_closing():
                    await cp._postgres_pool._pool.close()
        except Exception:
            pass  # Ignore errors
    cp._postgres_pool = None
    
    # Also reset Redis pool
    if hasattr(cp, '_redis_pool') and cp._redis_pool is not None:
        try:
            if hasattr(cp._redis_pool, '_client') and cp._redis_pool._client:
                if hasattr(cp._redis_pool._client, 'aclose'):
                    await cp._redis_pool._client.aclose()
                elif hasattr(cp._redis_pool._client, 'close'):
                    await cp._redis_pool._client.close()
        except Exception:
            pass  # Ignore errors
    if hasattr(cp, '_redis_pool'):
        cp._redis_pool = None
    
    yield
    
    # Cleanup after test
    try:
        loop = asyncio.get_running_loop()
        if cp._postgres_pool and hasattr(cp._postgres_pool, '_pool') and cp._postgres_pool._pool:
            if not cp._postgres_pool._pool.is_closing():
                await cp._postgres_pool._pool.close()
        cp._postgres_pool = None
        if hasattr(cp, '_redis_pool') and cp._redis_pool:
            if hasattr(cp._redis_pool, '_client') and cp._redis_pool._client:
                if hasattr(cp._redis_pool._client, 'aclose'):
                    await cp._redis_pool._client.aclose()
                elif hasattr(cp._redis_pool._client, 'close'):
                    await cp._redis_pool._client.close()
        if hasattr(cp, '_redis_pool'):
            cp._redis_pool = None
    except (RuntimeError, Exception):
        # Event loop closed or other error - just reset the references
        cp._postgres_pool = None
        if hasattr(cp, '_redis_pool'):
            cp._redis_pool = None






