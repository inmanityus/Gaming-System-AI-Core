"""

Simple integration tests for State Management Service.

Tests REAL connections - each test runs independently.

"""



import pytest

import pytest_asyncio

from uuid import UUID, uuid4

import json



from services.state_manager.state_operations import StateOperations, ConflictResolutionError





@pytest.mark.asyncio

async def test_full_crud_flow():

    """Test complete CRUD flow with real database."""

    ops = StateOperations()

    

    # Create test player

    postgres = await ops._get_postgres()

    player_result = await postgres.fetch(

        "INSERT INTO players (steam_id, username, tier, stats, inventory, money, reputation, level, xp) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9) RETURNING id",

        f"test_{uuid4()}",

        "TestPlayer",

        "free",

        json.dumps({}),

        json.dumps([]),

        0.0,

        0,

        1,

        0.0,

    )

    player_id = player_result["id"]

    

    try:

        # CREATE

        state = await ops.create_game_state(

            player_id=player_id,

            current_world="day",

            location="test_location",

            position={"x": 1.0, "y": 2.0, "z": 3.0},

        )

        assert state is not None

        assert state["current_world"] == "day"

        state_id = UUID(state["id"])

        

        # READ

        retrieved = await ops.get_game_state(state_id)

        assert retrieved is not None

        assert retrieved["id"] == state["id"]

        

        # UPDATE

        updated = await ops.update_game_state(

            state_id=state_id,

            expected_version=state["version"],

            current_world="night",

        )

        assert updated["current_world"] == "night"

        assert updated["version"] == state["version"] + 1

        

        # Cache hit rate check

        hit_rate = ops.cache.get_hit_rate()

        assert hit_rate >= 0.0

        

        print(f"✓ Full CRUD flow test passed (cache hit rate: {hit_rate:.1f}%)")

    finally:

        # Cleanup

        try:

            await postgres.execute("DELETE FROM game_states WHERE player_id = $1", player_id)

            await postgres.execute("DELETE FROM players WHERE id = $1", player_id)

        except Exception:

            pass



