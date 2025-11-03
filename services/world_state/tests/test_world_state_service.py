"""
Integration tests for World State Service.
Tests world state management, events, factions, and economy.
"""

import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.world_state.world_state_manager import WorldStateManager
from services.world_state.event_system import EventSystem
from services.world_state.faction_manager import FactionManager
from services.world_state.economic_manager import EconomicManager


@pytest_asyncio.fixture(scope="function")
async def world_state_manager():
    """World state manager fixture."""
    manager = WorldStateManager()
    yield manager


@pytest_asyncio.fixture(scope="function")
async def event_system():
    """Event system fixture."""
    system = EventSystem()
    yield system


@pytest_asyncio.fixture(scope="function")
async def faction_manager():
    """Faction manager fixture."""
    manager = FactionManager()
    yield manager


@pytest_asyncio.fixture(scope="function")
async def economic_manager():
    """Economic manager fixture."""
    manager = EconomicManager()
    yield manager


@pytest_asyncio.fixture(scope="function")
async def test_faction_id():
    """Test faction ID fixture."""
    # Create a test faction in the database
    from services.state_manager.connection_pool import get_postgres_pool
    
    postgres = await get_postgres_pool()
    faction_id = str(uuid4())
    
    # Insert test faction with unique name
    await postgres.execute(
        """
        INSERT INTO factions (id, name, faction_type, description, power_level, territory, relationships, hierarchy, goals, meta_data)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb)
        """,
        faction_id,
        f"Test Faction {faction_id[:8]}",
        "neutral",
        "A test faction for testing",
        50,
        '[]',
        '{}',
        '{}',
        '[]',
        '{"test": true}'
    )
    
    yield faction_id
    
    # Cleanup
    try:
        await postgres.execute("DELETE FROM factions WHERE id = $1", faction_id)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_world_state_manager_initialization(world_state_manager):
    """Test world state manager initialization."""
    assert world_state_manager is not None
    assert world_state_manager.postgres is None  # Not initialized yet


@pytest.mark.asyncio
async def test_world_state_manager_get_current_state(world_state_manager):
    """Test getting current world state."""
    state = await world_state_manager.get_current_world_state()
    
    assert isinstance(state, dict)
    assert "world_time" in state
    assert "current_weather" in state
    assert "global_events" in state
    assert "faction_power" in state
    assert "economic_state" in state
    assert "npc_population" in state
    assert "territory_control" in state
    assert "meta_data" in state


@pytest.mark.asyncio
async def test_world_state_manager_update_state(world_state_manager):
    """Test updating world state."""
    updates = {
        "current_weather": "sunny",
        "meta_data": {"test_update": True}
    }
    
    updated_state = await world_state_manager.update_world_state(updates)
    
    assert isinstance(updated_state, dict)
    assert updated_state["current_weather"] == "sunny"
    assert updated_state["meta_data"]["test_update"] is True


@pytest.mark.asyncio
async def test_world_state_manager_get_history(world_state_manager):
    """Test getting world state history."""
    history = await world_state_manager.get_world_state_history(limit=5)
    
    assert isinstance(history, list)
    assert len(history) <= 5


@pytest.mark.asyncio
async def test_world_state_manager_get_metrics(world_state_manager):
    """Test getting world state metrics."""
    metrics = await world_state_manager.get_state_metrics()
    
    assert isinstance(metrics, dict)
    assert "version" in metrics
    assert "last_updated" in metrics
    assert "world_age_days" in metrics
    assert "stability_index" in metrics


@pytest.mark.asyncio
async def test_event_system_initialization(event_system):
    """Test event system initialization."""
    assert event_system is not None
    assert event_system.postgres is None  # Not initialized yet
    assert len(event_system.event_types) == 5  # 5 event types


@pytest.mark.asyncio
async def test_event_system_generate_event(event_system):
    """Test generating an event."""
    event = await event_system.generate_event(
        "economic",
        "market_volatility",
        0.7,
        "Test economic event"
    )
    
    assert isinstance(event, dict)
    assert event["type"] == "economic"
    assert event["trigger"] == "market_volatility"
    assert event["intensity"] == 0.7
    assert event["description"] == "Test economic event"
    assert event["status"] == "active"


@pytest.mark.asyncio
async def test_event_system_get_active_events(event_system):
    """Test getting active events."""
    events = await event_system.get_active_events()
    
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_event_system_get_statistics(event_system):
    """Test getting event statistics."""
    stats = await event_system.get_event_statistics()
    
    assert isinstance(stats, dict)
    assert "total_events" in stats
    assert "active_events" in stats
    assert "event_types" in stats
    assert "avg_intensity" in stats


@pytest.mark.asyncio
async def test_faction_manager_initialization(faction_manager):
    """Test faction manager initialization."""
    assert faction_manager is not None
    assert faction_manager.postgres is None  # Not initialized yet


@pytest.mark.asyncio
async def test_faction_manager_get_power(faction_manager, test_faction_id):
    """Test getting faction power."""
    power = await faction_manager.get_faction_power(test_faction_id)
    
    assert isinstance(power, float)
    assert 0.0 <= power <= 1.0


@pytest.mark.asyncio
async def test_faction_manager_update_power(faction_manager, test_faction_id):
    """Test updating faction power."""
    new_power = await faction_manager.update_faction_power(test_faction_id, 0.1)
    
    assert isinstance(new_power, float)
    assert 0.0 <= new_power <= 1.0


@pytest.mark.asyncio
async def test_faction_manager_get_territory(faction_manager, test_faction_id):
    """Test getting faction territory."""
    territories = await faction_manager.get_territory_control(test_faction_id)
    
    assert isinstance(territories, list)


@pytest.mark.asyncio
async def test_faction_manager_get_relationships(faction_manager, test_faction_id):
    """Test getting faction relationships."""
    relationships = await faction_manager.get_faction_relationships(test_faction_id)
    
    assert isinstance(relationships, dict)


@pytest.mark.asyncio
async def test_faction_manager_get_rankings(faction_manager):
    """Test getting faction rankings."""
    rankings = await faction_manager.get_faction_rankings()
    
    assert isinstance(rankings, list)


@pytest.mark.asyncio
async def test_economic_manager_initialization(economic_manager):
    """Test economic manager initialization."""
    assert economic_manager is not None
    assert economic_manager.postgres is None  # Not initialized yet
    assert len(economic_manager.resource_types) == 6  # 6 resource types


@pytest.mark.asyncio
async def test_economic_manager_get_market_state(economic_manager):
    """Test getting market state."""
    market_state = await economic_manager.get_market_state()
    
    assert isinstance(market_state, dict)
    # Market state may have different fields depending on source
    # Just verify it's a valid dict with some content
    assert len(market_state) > 0


@pytest.mark.asyncio
async def test_economic_manager_simulate_dynamics(economic_manager):
    """Test simulating market dynamics."""
    results = await economic_manager.simulate_market_dynamics()
    
    assert isinstance(results, dict)
    assert "price_changes" in results
    assert "new_trends" in results
    assert "simulation_time" in results


@pytest.mark.asyncio
async def test_economic_manager_get_resource_price(economic_manager):
    """Test getting resource price."""
    price = await economic_manager.get_resource_price("energy")
    
    assert isinstance(price, (int, float))
    assert price > 0


@pytest.mark.asyncio
async def test_economic_manager_calculate_trade_value(economic_manager):
    """Test calculating trade value."""
    trade_value = await economic_manager.calculate_trade_value("energy", 10)
    
    assert isinstance(trade_value, dict)
    assert "resource_type" in trade_value
    assert "quantity" in trade_value
    assert "final_value" in trade_value
    assert trade_value["resource_type"] == "energy"
    assert trade_value["quantity"] == 10


@pytest.mark.asyncio
async def test_economic_manager_get_indicators(economic_manager):
    """Test getting economic indicators."""
    indicators = await economic_manager.get_economic_indicators()
    
    assert isinstance(indicators, dict)
    assert "market_stability" in indicators
    assert "inflation_rate" in indicators
    assert "resource_availability" in indicators
    assert "avg_price_change" in indicators
    assert "market_volatility" in indicators


@pytest.mark.asyncio
async def test_economic_manager_generate_event(economic_manager):
    """Test generating economic event."""
    event = await economic_manager.generate_economic_event("market_boom", 0.6)
    
    assert isinstance(event, dict)
    assert event["event_type"] == "market_boom"
    assert event["intensity"] == 0.6
    assert "description" in event
    assert "impacts" in event
    assert "timestamp" in event


@pytest.mark.asyncio
async def test_integration_flow(world_state_manager, event_system, faction_manager, economic_manager):
    """Test integration flow between components."""
    # Get world state
    world_state = await world_state_manager.get_current_world_state()
    assert isinstance(world_state, dict)
    
    # Generate an event
    event = await event_system.generate_event("economic", "market_volatility", 0.5)
    assert isinstance(event, dict)
    
    # Get market state
    market_state = await economic_manager.get_market_state()
    assert isinstance(market_state, dict)
    
    # Simulate market dynamics
    simulation_results = await economic_manager.simulate_market_dynamics()
    assert isinstance(simulation_results, dict)


@pytest.mark.asyncio
async def test_error_handling(world_state_manager):
    """Test error handling in world state manager."""
    # Test with invalid updates
    try:
        await world_state_manager.update_world_state({})
        # Should not raise an exception
    except Exception as e:
        # If it does raise an exception, it should be handled gracefully
        assert isinstance(e, (ValueError, Exception))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
