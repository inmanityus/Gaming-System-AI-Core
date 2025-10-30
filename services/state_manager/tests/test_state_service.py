"""
Integration tests for State Management Service.
Tests REAL connections to PostgreSQL and Redis.
"""

import pytest
import pytest_asyncio
from uuid import UUID, uuid4

from services.state_manager.state_operations import StateOperations, ConflictResolutionError


@pytest_asyncio.fixture
async def state_ops():
    """Create StateOperations instance for testing."""
    ops = StateOperations()
    yield ops
    # Don't close pools - let pytest handle cleanup


@pytest_asyncio.fixture
async def test_player_id(state_ops):
    """Create a test player and return player ID."""
    postgres = await state_ops._get_postgres()
    
    # Create a test player
    query = """
        INSERT INTO players (steam_id, username, tier, stats, inventory, money, reputation, level, xp)
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9)
        RETURNING id
    """
    
    import json
    result = await postgres.fetch(
        query,
        f"test_steam_{uuid4()}",
        "TestPlayer",
        "free",
        json.dumps({}),
        json.dumps([]),
        0.0,
        0,
        1,
        0.0,
    )
    
    player_id = result["id"]
    yield player_id
    
    # Cleanup: delete game states first, then player
    try:
        await postgres.execute("DELETE FROM game_states WHERE player_id = $1", player_id)
        await postgres.execute("DELETE FROM players WHERE id = $1", player_id)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_create_game_state(state_ops, test_player_id):
    """Test creating a game state."""
    player_id = test_player_id
    
    state = await state_ops.create_game_state(
        player_id=player_id,
        current_world="day",
        location="warehouse_district",
        position={"x": 100.0, "y": 200.0, "z": 50.0},
        active_quests=["quest_001"],
        session_data={"last_played": "2025-01-29"},
    )
    
    assert state is not None
    assert str(state["player_id"]) == str(player_id)
    assert state["current_world"] == "day"
    assert state["version"] == 1
    
    print("✓ Create game state test passed")


@pytest.mark.asyncio
async def test_get_game_state(state_ops, test_player_id):
    """Test retrieving a game state."""
    player_id = test_player_id
    
    # Create state
    created = await state_ops.create_game_state(
        player_id=player_id,
        current_world="night",
    )
    state_id = UUID(created["id"])
    
    # Retrieve state
    retrieved = await state_ops.get_game_state(state_id)
    
    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["current_world"] == "night"
    
    print("✓ Get game state test passed")


@pytest.mark.asyncio
async def test_cache_hit_rate(state_ops, test_player_id):
    """Test cache hit rate improves after first read."""
    player_id = test_player_id
    
    # Create state
    created = await state_ops.create_game_state(
        player_id=player_id,
        current_world="day",
    )
    state_id = UUID(created["id"])
    
    # Reset cache stats for this test
    state_ops.cache.reset_stats()
    
    # First read (cache miss)
    await state_ops.get_game_state(state_id)
    hit_rate_1 = state_ops.cache.get_hit_rate()
    
    # Second read (cache hit)
    await state_ops.get_game_state(state_id)
    hit_rate_2 = state_ops.cache.get_hit_rate()
    
    # Third read (cache hit)
    await state_ops.get_game_state(state_id)
    hit_rate_3 = state_ops.cache.get_hit_rate()
    
    # Hit rate should improve after first read
    assert hit_rate_2 > hit_rate_1
    assert hit_rate_3 >= hit_rate_2
    assert hit_rate_3 >= 50.0
    
    print(f"✓ Cache hit rate test passed (final rate: {hit_rate_3:.1f}%)")


@pytest.mark.asyncio
async def test_optimistic_locking(state_ops, test_player_id):
    """Test optimistic locking conflict resolution."""
    player_id = test_player_id
    
    # Create state
    created = await state_ops.create_game_state(
        player_id=player_id,
        current_world="day",
    )
    state_id = UUID(created["id"])
    version = created["version"]
    
    # Update with correct version (should succeed)
    updated = await state_ops.update_game_state(
        state_id=state_id,
        expected_version=version,
        current_world="night",
    )
    assert updated["current_world"] == "night"
    assert updated["version"] == version + 1
    
    # Try to update with old version (should fail)
    with pytest.raises(ConflictResolutionError):
        await state_ops.update_game_state(
            state_id=state_id,
            expected_version=version,  # Old version
            current_world="day",
        )
    
    print("✓ Optimistic locking test passed")


@pytest.mark.asyncio
async def test_get_game_state_by_player(state_ops, test_player_id):
    """Test retrieving game state by player ID."""
    player_id = test_player_id
    
    # Create active state
    created = await state_ops.create_game_state(
        player_id=player_id,
        current_world="day",
    )
    
    # Retrieve by player
    retrieved = await state_ops.get_game_state_by_player(player_id, active_only=True)
    
    assert retrieved is not None
    assert str(retrieved["player_id"]) == str(player_id)
    assert retrieved["is_active"] is True
    
    print("✓ Get game state by player test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
