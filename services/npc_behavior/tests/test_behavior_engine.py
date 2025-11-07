"""
Tests for Behavior Engine - Integration tests.

Tests integration with BehavioralProxy and CognitiveLayer.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, MagicMock

from services.npc_behavior.behavior_engine import BehaviorEngine
from services.npc_behavior.behavioral_proxy import ProxyManager, ProxyActionType
from services.ai_integration.llm_client import LLMClient


@pytest_asyncio.fixture
async def behavior_engine():
    """Create a BehaviorEngine instance with mocked databases."""
    engine = BehaviorEngine()
    
    # Mock postgres
    mock_postgres = AsyncMock()
    mock_postgres.fetch = AsyncMock(return_value={
        "id": uuid4(),
        "name": "Test NPC",
        "npc_type": "commoner",
        "personality_vector": '{"extraversion": 0.5}',
        "stats": '{"health": 100}',
        "goal_stack": '[]',
        "relationships": '{}',
        "meta_data": '{}',
    })
    mock_postgres.execute = AsyncMock()
    engine.postgres = mock_postgres
    
    # Mock redis
    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()
    engine.redis = mock_redis
    
    return engine


@pytest.mark.asyncio
async def test_update_npc(behavior_engine):
    """Test updating an NPC."""
    npc_id = uuid4()
    
    result = await behavior_engine.update_npc(
        npc_id=npc_id,
        frame_time_ms=3.33,
        game_state={"enemies": [], "obstacles": [], "interactables": [], "social_areas": []}
    )
    
    assert result["npc_id"] == str(npc_id)
    assert "decision" in result
    assert "actions" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_update_npc_validation(behavior_engine):
    """Test input validation in update_npc."""
    # Invalid npc_id
    with pytest.raises(TypeError):
        await behavior_engine.update_npc("not-uuid")
    
    # Invalid frame_time_ms
    with pytest.raises(ValueError):
        await behavior_engine.update_npc(uuid4(), frame_time_ms=-1.0)
    
    # Invalid game_state
    with pytest.raises(TypeError):
        await behavior_engine.update_npc(uuid4(), game_state="not-dict")


@pytest.mark.asyncio
async def test_update_npc_not_found(behavior_engine):
    """Test updating NPC that doesn't exist."""
    npc_id = uuid4()
    
    # Mock no NPC found
    behavior_engine.postgres.fetch.return_value = None
    
    with pytest.raises(ValueError, match="not found"):
        await behavior_engine.update_npc(npc_id)


@pytest.mark.asyncio
async def test_batch_update_npcs(behavior_engine):
    """Test batch updating multiple NPCs."""
    npc_ids = [uuid4() for _ in range(5)]
    
    results = await behavior_engine.batch_update_npcs(npc_ids, max_concurrent=3)
    
    assert results["total"] == 5
    assert len(results["successful"]) + len(results["failed"]) == 5


@pytest.mark.asyncio
async def test_batch_update_validation(behavior_engine):
    """Test input validation in batch_update_npcs."""
    # Invalid npc_ids
    with pytest.raises(TypeError):
        await behavior_engine.batch_update_npcs("not-list")
    
    # Invalid max_concurrent
    with pytest.raises(ValueError):
        await behavior_engine.batch_update_npcs([uuid4()], max_concurrent=0)


@pytest.mark.asyncio
async def test_queue_npc_update(behavior_engine):
    """Test queueing NPC for update."""
    npc_id = uuid4()
    
    await behavior_engine.queue_npc_update(npc_id)
    
    # Verify queue contains NPC
    assert npc_id in behavior_engine._update_queue


@pytest.mark.asyncio
async def test_queue_npc_update_validation(behavior_engine):
    """Test input validation in queue_npc_update."""
    # Invalid npc_id
    with pytest.raises(TypeError):
        await behavior_engine.queue_npc_update("not-uuid")


@pytest.mark.asyncio
async def test_get_game_state_for_proxy(behavior_engine):
    """Test getting game state for proxy."""
    npc_id = uuid4()
    
    game_state = await behavior_engine._get_game_state_for_proxy(npc_id)
    
    assert isinstance(game_state, dict)
    assert "enemies" in game_state
    assert "obstacles" in game_state
    assert "interactables" in game_state
    assert "social_areas" in game_state


@pytest.mark.asyncio
async def test_get_npc_context(behavior_engine):
    """Test getting NPC context."""
    npc_id = uuid4()
    
    # Mock faction query
    behavior_engine.postgres.fetch = AsyncMock(side_effect=[
        {"faction_id": uuid4()},  # NPC query
        None,  # World state query
        {"name": "Test Faction", "power_level": 50},  # Faction query
    ])
    
    context = await behavior_engine._get_npc_context(npc_id)
    
    assert isinstance(context, dict)
    assert "world_state" in context
    assert "faction_info" in context
    assert "nearby_npcs" in context


@pytest.mark.asyncio
async def test_get_npc_context_validation(behavior_engine):
    """Test input validation in _get_npc_context."""
    # Invalid npc_id
    with pytest.raises(TypeError):
        await behavior_engine._get_npc_context("not-uuid")


@pytest.mark.asyncio
async def test_update_npc_state(behavior_engine):
    """Test updating NPC state."""
    npc_id = uuid4()
    decision = {"action_type": "move", "target": "location_1"}
    actions = [{"type": "move", "target": "location_1"}]
    
    # Mock meta query
    behavior_engine.postgres.fetch = AsyncMock(return_value={
        "meta_data": '{"existing": "data"}'
    })
    
    await behavior_engine._update_npc_state(npc_id, decision, actions)
    
    # Verify update was called
    assert behavior_engine.postgres.execute.called
    assert behavior_engine.redis.hset.called


@pytest.mark.asyncio
async def test_update_npc_state_validation(behavior_engine):
    """Test input validation in _update_npc_state."""
    # Invalid npc_id
    with pytest.raises(TypeError):
        await behavior_engine._update_npc_state("not-uuid", {}, [])
    
    # Invalid decision
    with pytest.raises(TypeError):
        await behavior_engine._update_npc_state(uuid4(), "not-dict", [])
    
    # Invalid actions
    with pytest.raises(TypeError):
        await behavior_engine._update_npc_state(uuid4(), {}, "not-list")


@pytest.mark.asyncio
async def test_behavior_engine_with_cognitive_layer():
    """Test behavior engine with cognitive layer enabled."""
    mock_llm = Mock(spec=LLMClient)
    engine = BehaviorEngine(llm_client=mock_llm)
    
    assert engine.cognitive_layer is not None
    assert engine.cognitive_layer._running is True


@pytest.mark.asyncio
async def test_behavior_engine_without_cognitive_layer():
    """Test behavior engine without cognitive layer."""
    engine = BehaviorEngine(llm_client=None)
    
    assert engine.cognitive_layer is None
    assert engine.proxy_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



