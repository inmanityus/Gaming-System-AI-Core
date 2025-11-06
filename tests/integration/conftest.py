"""
Pytest configuration for Integration Tests.
Provides shared fixtures and setup/teardown for async tests with database connections.
"""

import pytest
import pytest_asyncio
import asyncio


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_pools_before_test():
    """Reset connection pools before each test to avoid event loop conflicts."""
    import services.state_manager.connection_pool as cp
    
    # Reset pools to ensure fresh state for each test
    if cp._postgres_pool is not None:
        try:
            if hasattr(cp._postgres_pool, '_pool') and cp._postgres_pool._pool:
                if not cp._postgres_pool._pool.is_closing():
                    await cp._postgres_pool._pool.close()
        except Exception:
            pass  # Ignore errors during cleanup
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
            pass  # Ignore errors during cleanup
    if hasattr(cp, '_redis_pool'):
        cp._redis_pool = None
    
    yield
    
    # Cleanup after test - ensure all async operations complete
    try:
        # Give any pending operations time to complete
        await asyncio.sleep(0.1)
        
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
        # This is expected when event loop closes before cleanup completes
        cp._postgres_pool = None
        if hasattr(cp, '_redis_pool'):
            cp._redis_pool = None


@pytest_asyncio.fixture(scope="function")
async def ensure_db_cleanup():
    """Ensure database operations complete before test ends."""
    yield
    
    # Wait for any pending database operations
    try:
        await asyncio.sleep(0.05)  # Small delay to let operations complete
    except RuntimeError:
        # Event loop already closed - that's okay
        pass

