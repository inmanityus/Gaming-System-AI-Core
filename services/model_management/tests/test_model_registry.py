"""
Tests for Model Registry.
Tests use real PostgreSQL connections - NO MOCKS.
"""

import pytest
import pytest_asyncio
import asyncio
from uuid import uuid4
from services.model_management.model_registry import ModelRegistry
from services.state_manager.connection_pool import PostgreSQLPool


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
    
    yield
    
    # Cleanup after test
    try:
        loop = asyncio.get_running_loop()
        if cp._postgres_pool and hasattr(cp._postgres_pool, '_pool') and cp._postgres_pool._pool:
            if not cp._postgres_pool._pool.is_closing():
                await cp._postgres_pool._pool.close()
        cp._postgres_pool = None
    except (RuntimeError, Exception):
        # Event loop closed or other error - just reset the references
        cp._postgres_pool = None


@pytest_asyncio.fixture
async def db_pool():
    """Create PostgreSQLPool instance."""
    pool = PostgreSQLPool()
    await pool.initialize()
    yield pool
    if pool._pool and not pool._pool.is_closing():
        await pool._pool.close()


@pytest_asyncio.fixture
async def registry(db_pool):
    """Create ModelRegistry instance with database pool."""
    registry = ModelRegistry(db_pool=db_pool)
    yield registry


@pytest.mark.asyncio
async def test_register_model(registry, db_pool):
    """Test model registration."""
    # Use unique name with timestamp to avoid collisions
    import time
    model_name = f"test-model-{int(time.time())}"
    
    model_id = await registry.register_model(
        model_name=model_name,
        model_type="self_hosted",
        provider="huggingface",
        use_case="npc_dialogue",
        version="1.0.0",
        model_path="/path/to/model"
    )
    
    assert model_id is not None
    
    # Get model
    model = await registry.get_model(model_id)
    assert model is not None
    assert model["model_name"] == model_name
    assert model["use_case"] == "npc_dialogue"
    
    # Cleanup
    async with db_pool.get_connection() as conn:
        await conn.execute("DELETE FROM models WHERE model_id = $1", model_id)


@pytest.mark.asyncio
async def test_update_model_status(registry, db_pool):
    """Test model status update."""
    import time
    model_name = f"test-model-2-{int(time.time())}"
    
    model_id = await registry.register_model(
        model_name=model_name,
        model_type="self_hosted",
        provider="huggingface",
        use_case="story_generation",
        version="1.0.0"
    )
    
    await registry.update_model_status(model_id, "current")
    
    model = await registry.get_model(model_id)
    assert model is not None
    assert model["status"] == "current"
    
    # Cleanup
    async with db_pool.get_connection() as conn:
        await conn.execute("DELETE FROM models WHERE model_id = $1", model_id)


@pytest.mark.asyncio
async def test_get_current_model(registry, db_pool):
    """Test getting current model for use case."""
    import time
    model_name = f"current-model-{int(time.time())}"
    
    model_id = await registry.register_model(
        model_name=model_name,
        model_type="self_hosted",
        provider="huggingface",
        use_case="faction_decision",
        version="1.0.0"
    )
    
    await registry.update_model_status(model_id, "current")
    
    current = await registry.get_current_model("faction_decision")
    assert current is not None
    assert current["model_id"] == str(model_id)
    
    # Cleanup
    async with db_pool.get_connection() as conn:
        await conn.execute("DELETE FROM models WHERE model_id = $1", model_id)


@pytest.mark.asyncio
async def test_get_all_candidate_models(registry, db_pool):
    """Test getting all candidate models."""
    import time
    suffix = int(time.time())
    
    # Register multiple candidate models
    model_id_1 = await registry.register_model(
        model_name=f"candidate-1-{suffix}",
        model_type="self_hosted",
        provider="huggingface",
        use_case="npc_dialogue",
        version="1.0.0"
    )
    model_id_2 = await registry.register_model(
        model_name=f"candidate-2-{suffix}",
        model_type="self_hosted",
        provider="ollama",
        use_case="npc_dialogue",
        version="2.0.0"
    )
    
    candidates = await registry.get_candidate_models("npc_dialogue")
    # Should return at least our test candidates
    candidate_names = [c["model_name"] for c in candidates]
    assert f"candidate-1-{suffix}" in candidate_names or f"candidate-2-{suffix}" in candidate_names
    
    # Cleanup
    async with db_pool.get_connection() as conn:
        await conn.execute("DELETE FROM models WHERE model_id IN ($1, $2)", model_id_1, model_id_2)

