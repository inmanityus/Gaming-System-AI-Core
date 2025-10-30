"""
Integration tests for NPC Behavior Service.
"""

import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.npc_behavior.behavior_engine import BehaviorEngine
from services.npc_behavior.personality_system import PersonalitySystem
from services.npc_behavior.goal_manager import GoalManager
from services.npc_behavior.interaction_router import InteractionRouter


@pytest_asyncio.fixture(scope="module")
async def behavior_engine():
    """Behavior engine fixture."""
    engine = BehaviorEngine()
    yield engine


@pytest_asyncio.fixture(scope="module")
async def test_npc_id():
    """Test NPC ID fixture."""
    from services.state_manager.connection_pool import get_postgres_pool
    
    postgres = await get_postgres_pool()
    npc_id = uuid4()
    faction_id = uuid4()
    world_state_id = uuid4()
    
    # Create test world state first (required by npcs table)
    await postgres.execute(
        """
        INSERT INTO world_states (id, world_time, day_phase, faction_power, global_events, economic_state, npc_population, territory_control, simulation_data)
        VALUES ($1, CURRENT_TIMESTAMP, 'day', '{}'::jsonb, '[]'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb)
        """,
        world_state_id
    )
    
    # Create test faction
    await postgres.execute(
        """
        INSERT INTO factions (id, name, faction_type, description, power_level, territory, relationships, hierarchy, goals, meta_data)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb)
        """,
        faction_id,
        f"Test Faction {faction_id}",
        "neutral",
        "Test faction",
        50,
        '[]',
        '{}',
        '{}',
        '[]',
        '{}'
    )
    
    # Create test NPC
    await postgres.execute(
        """
        INSERT INTO npcs (id, world_state_id, faction_id, name, npc_type, personality_vector, stats, goal_stack, relationships, meta_data)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb)
        """,
        npc_id,
        world_state_id,
        faction_id,
        "Test NPC",
        "civilian",
        '{"aggression": 0.3, "social": 0.7, "curiosity": 0.5}',
        '{"level": 1, "health": 100}',
        '[{"type": "explore", "priority": 0.6}]',
        '{}',
        '{}'
    )
    
    yield npc_id
    
    # Cleanup
    try:
        await postgres.execute("DELETE FROM npcs WHERE id = $1", npc_id)
        await postgres.execute("DELETE FROM factions WHERE id = $1", faction_id)
        await postgres.execute("DELETE FROM world_states WHERE id = $1", world_state_id)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_behavior_engine_initialization(behavior_engine):
    """Test behavior engine initialization."""
    assert behavior_engine is not None
    assert behavior_engine.postgres is None  # Not initialized yet


@pytest.mark.asyncio
async def test_behavior_engine_update_npc(behavior_engine, test_npc_id):
    """Test updating NPC behavior."""
    result = await behavior_engine.update_npc(test_npc_id)
    
    assert isinstance(result, dict)
    assert result["npc_id"] == str(test_npc_id)
    assert "decision" in result
    assert "actions" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_personality_system_score_action():
    """Test personality system action scoring."""
    system = PersonalitySystem()
    
    personality = {"aggression": 0.8, "social": 0.3}
    score = system.score_action(personality, "combat", {})
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_goal_manager_plan():
    """Test goal manager planning."""
    manager = GoalManager()
    
    personality = {"aggression": 0.8, "social": 0.7}
    goals = manager.plan(uuid4(), personality, {})
    
    assert isinstance(goals, list)
    assert len(goals) > 0


@pytest.mark.asyncio
async def test_interaction_router_route():
    """Test interaction router."""
    router = InteractionRouter()
    
    intent = {
        "type": "social",
        "source_id": uuid4(),
        "target_id": uuid4(),
    }
    
    result = router.route(intent)
    
    assert isinstance(result, dict)
    assert result["success"] is True
    assert result["type"] == "social"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
