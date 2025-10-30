"""
Integration tests for Quest System Service.
Tests use real PostgreSQL and Redis connections.
"""

import pytest
import pytest_asyncio
import json
import asyncio
from uuid import UUID, uuid4
from typing import Dict, Any

from services.quest_system.quest_generator import QuestGenerationEngine
from services.quest_system.quest_manager import QuestManager
from services.quest_system.objective_manager import ObjectiveManager
from services.quest_system.reward_manager import RewardManager
from services.state_manager.connection_pool import get_postgres_pool


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
    # Cleanup after test - but skip if event loop is already closed
    try:
        import asyncio
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


@pytest_asyncio.fixture(scope="function")
async def test_player_id():
    """Create a test player for quests."""
    postgres = await get_postgres_pool()
    
    player_id = uuid4()
    try:
        await postgres.execute(
            """
            INSERT INTO players (id, steam_id, username, tier, money, xp, reputation, level)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            player_id,
            f"steam_{player_id}",
            "test_player",
            "free",
            1000.0,
            0.0,
            0,
            1
        )
        
        yield player_id
    finally:
        # Cleanup with exception handling to prevent event loop issues
        try:
            await postgres.execute("DELETE FROM players WHERE id = $1", player_id)
        except (Exception, RuntimeError, asyncio.CancelledError):
            pass  # Ignore cleanup errors if event loop is closing


@pytest_asyncio.fixture(scope="function")
async def test_world_state_id():
    """Create a test world state for quests."""
    from services.state_manager.connection_pool import get_postgres_pool
    postgres = await get_postgres_pool()
    
    world_state_id = uuid4()
    try:
        await postgres.execute(
            """
            INSERT INTO world_states (id, day_phase, faction_power, global_events)
            VALUES ($1, $2, $3::jsonb, $4::jsonb)
            """,
            world_state_id,
            "day",
            json.dumps({}),
            json.dumps([])
        )
        
        yield world_state_id
    finally:
        # Cleanup with exception handling to prevent event loop issues
        try:
            # Small delay to ensure previous operations complete
            await asyncio.sleep(0.05)
            await postgres.execute("DELETE FROM world_states WHERE id = $1", world_state_id)
        except (Exception, RuntimeError, asyncio.CancelledError):
            pass  # Ignore cleanup errors if event loop is closing


@pytest.mark.asyncio
async def test_quest_generator_initialization():
    """Test quest generator initialization."""
    generator = QuestGenerationEngine()
    assert generator is not None
    assert generator.postgres is None
    assert generator.redis is None
    assert generator.llm_client is None


@pytest.mark.asyncio
async def test_quest_generator_generate_quest(test_player_id, test_world_state_id):
    """Test quest generation."""
    generator = QuestGenerationEngine()
    
    quest = await generator.generate_quest(
        player_id=test_player_id,
        quest_type="side",
        world_state_id=test_world_state_id
    )
    
    assert quest is not None
    assert "quest_id" in quest
    assert "title" in quest
    assert "description" in quest
    assert "objectives" in quest
    assert "rewards" in quest
    assert quest["player_id"] == str(test_player_id)


@pytest.mark.asyncio
async def test_quest_manager_create_quest(test_player_id):
    """Test quest creation."""
    manager = QuestManager()
    
    quest_data = {
        "quest_id": str(uuid4()),
        "player_id": str(test_player_id),
        "title": "Test Quest",
        "description": "A test quest",
        "objectives": [
            {"id": "obj1", "description": "Test objective", "type": "collect", "target": "item", "count": 1}
        ],
        "rewards": {"money": 100, "experience": 50, "reputation": 10, "items": []},
        "status": "active",
    }
    
    quest = await manager.create_quest(quest_data)
    
    assert quest is not None
    assert quest["quest_id"] == quest_data["quest_id"]
    assert quest["title"] == "Test Quest"
    
    # Cleanup
    try:
        await manager.delete_quest(UUID(quest_data["quest_id"]))
    except (Exception, RuntimeError):
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_quest_manager_get_quest(test_player_id):
    """Test getting a quest."""
    manager = QuestManager()
    
    quest_data = {
        "quest_id": str(uuid4()),
        "player_id": str(test_player_id),
        "title": "Test Quest 2",
        "description": "Another test quest",
        "objectives": [],
        "rewards": {},
        "status": "active",
    }
    
    created_quest = await manager.create_quest(quest_data)
    quest_id = UUID(created_quest["quest_id"])
    
    retrieved_quest = await manager.get_quest(quest_id)
    
    assert retrieved_quest is not None
    assert retrieved_quest["quest_id"] == created_quest["quest_id"]
    assert retrieved_quest["title"] == "Test Quest 2"
    
    # Cleanup
    try:
        await manager.delete_quest(quest_id)
    except (Exception, RuntimeError):
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_quest_manager_get_player_quests(test_player_id):
    """Test getting player quests."""
    manager = QuestManager()
    
    quest_data = {
        "quest_id": str(uuid4()),
        "player_id": str(test_player_id),
        "title": "Test Quest 3",
        "description": "Yet another test quest",
        "objectives": [],
        "rewards": {},
        "status": "active",
    }
    
    created_quest = await manager.create_quest(quest_data)
    quest_id = UUID(created_quest["quest_id"])
    
    player_quests = await manager.get_player_quests(test_player_id)
    
    assert len(player_quests) > 0
    assert any(q["quest_id"] == str(quest_id) for q in player_quests)
    
    # Cleanup
    try:
        await manager.delete_quest(quest_id)
    except (Exception, RuntimeError):
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_objective_manager_get_objectives(test_player_id):
    """Test getting quest objectives."""
    manager = QuestManager()
    objective_manager = ObjectiveManager()
    
    quest_data = {
        "quest_id": str(uuid4()),
        "player_id": str(test_player_id),
        "title": "Test Quest 4",
        "description": "Quest with objectives",
        "objectives": [
            {"id": "obj1", "description": "Objective 1", "type": "collect", "target": "item", "count": 1},
            {"id": "obj2", "description": "Objective 2", "type": "kill", "target": "npc", "count": 1},
        ],
        "rewards": {},
        "status": "active",
    }
    
    created_quest = await manager.create_quest(quest_data)
    quest_id = UUID(created_quest["quest_id"])
    
    objectives = await objective_manager.get_objectives(quest_id)
    
    assert len(objectives) == 2
    assert objectives[0]["id"] == "obj1"
    assert objectives[1]["id"] == "obj2"
    
    # Cleanup
    try:
        await manager.delete_quest(quest_id)
    except (Exception, RuntimeError):
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_reward_manager_calculate_rewards(test_player_id):
    """Test reward calculation."""
    manager = QuestManager()
    reward_manager = RewardManager()
    
    quest_data = {
        "quest_id": str(uuid4()),
        "player_id": str(test_player_id),
        "title": "Test Quest 5",
        "description": "Quest with rewards",
        "objectives": [],
        "rewards": {"money": 200, "experience": 100, "reputation": 20, "items": []},
        "status": "active",
    }
    
    created_quest = await manager.create_quest(quest_data)
    quest_id = UUID(created_quest["quest_id"])
    
    rewards = await reward_manager.calculate_rewards(quest_id)
    
    assert rewards["money"] == 200
    assert rewards["experience"] == 100
    assert rewards["reputation"] == 20
    
    # Test with bonus multiplier
    bonus_rewards = await reward_manager.calculate_rewards(quest_id, bonus_multiplier=1.5)
    
    assert bonus_rewards["money"] == 300
    assert bonus_rewards["experience"] == 150
    assert bonus_rewards["reputation"] == 30
    
    # Cleanup
    try:
        await manager.delete_quest(quest_id)
    except (Exception, RuntimeError):
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_reward_manager_distribute_rewards(test_player_id):
    """Test reward distribution."""
    manager = QuestManager()
    reward_manager = RewardManager()
    
    quest_data = {
        "quest_id": str(uuid4()),
        "player_id": str(test_player_id),
        "title": "Test Quest 6",
        "description": "Quest with reward distribution",
        "objectives": [],
        "rewards": {"money": 500, "experience": 200, "reputation": 50, "items": []},
        "status": "active",
    }
    
    created_quest = await manager.create_quest(quest_data)
    quest_id = UUID(created_quest["quest_id"])
    
    # Get initial player state  
    from services.state_manager.connection_pool import get_postgres_pool
    postgres = await get_postgres_pool()
    initial_player = await postgres.fetch(
        "SELECT money, xp, reputation, level FROM players WHERE id = $1",
        test_player_id
    )
    
    initial_money = float(initial_player["money"]) if initial_player else 0.0
    initial_xp = float(initial_player["xp"]) if initial_player else 0.0
    initial_reputation = initial_player["reputation"] if initial_player else 0
    
    # Distribute rewards
    result = await reward_manager.distribute_rewards(test_player_id, {
        "money": 500,
        "experience": 200,
        "reputation": 50,
        "items": []
    })
    
    assert result["success"] is True
    assert result["new_player_state"]["money"] == initial_money + 500
    # XP may be reduced due to level-up (100 XP per level)
    # Starting level 1 (0 XP) + 200 XP = level 2 with 100 XP remaining
    initial_level = initial_player["level"] if initial_player else 1
    total_xp = initial_xp + 200
    # Calculate expected XP after potential level-ups
    current_level = initial_level
    remaining_xp = total_xp
    while remaining_xp >= current_level * 100:
        remaining_xp -= current_level * 100
        current_level += 1
    assert result["new_player_state"]["xp"] == remaining_xp
    assert result["new_player_state"]["reputation"] == initial_reputation + 50
    
    # Cleanup
    try:
        await manager.delete_quest(quest_id)
    except Exception:
        pass  # Ignore cleanup errors

