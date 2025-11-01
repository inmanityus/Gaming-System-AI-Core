"""
Tests for Event Bus - REAL implementations only.
"""

import pytest
import asyncio
from services.event_bus.event_bus import GameEventBus, GameEvent, EventType


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    """Test basic publish/subscribe functionality - REAL IMPLEMENTATION."""
    bus = GameEventBus(use_redis=False)  # Use in-memory for testing
    
    events_received = []
    
    async def event_handler(event: GameEvent):
        events_received.append(event)
    
    # Subscribe to event type
    await bus.subscribe(EventType.TIME_OF_DAY_CHANGED, event_handler)
    
    # Publish event
    event = GameEvent(
        event_type=EventType.TIME_OF_DAY_CHANGED,
        source="test_service",
        data={"time": "night", "hour": 22}
    )
    
    notified = await bus.publish(event)
    
    # Verify
    assert notified == 1
    assert len(events_received) == 1
    assert events_received[0].event_type == EventType.TIME_OF_DAY_CHANGED
    assert events_received[0].data["time"] == "night"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    """Test multiple subscribers receive events."""
    bus = GameEventBus(use_redis=False)
    
    handler1_events = []
    handler2_events = []
    
    async def handler1(event: GameEvent):
        handler1_events.append(event)
    
    async def handler2(event: GameEvent):
        handler2_events.append(event)
    
    await bus.subscribe(EventType.WEATHER_CHANGED, handler1)
    await bus.subscribe(EventType.WEATHER_CHANGED, handler2)
    
    event = GameEvent(
        event_type=EventType.WEATHER_CHANGED,
        source="weather_service",
        data={"weather": "rain", "intensity": 0.7}
    )
    
    notified = await bus.publish(event)
    
    assert notified == 2
    assert len(handler1_events) == 1
    assert len(handler2_events) == 1


@pytest.mark.asyncio
async def test_event_bus_history():
    """Test event history storage."""
    bus = GameEventBus(use_redis=False)
    
    event = GameEvent(
        event_type=EventType.PLAYER_STATE_CHANGED,
        source="state_service",
        data={"player_id": "test-123"}
    )
    
    await bus.publish(event)
    
    history = await bus.get_event_history(EventType.PLAYER_STATE_CHANGED, limit=10)
    
    assert len(history) == 1
    assert history[0].event_id == event.event_id


@pytest.mark.asyncio
async def test_event_bus_stats():
    """Test statistics tracking."""
    bus = GameEventBus(use_redis=False)
    
    async def handler(event: GameEvent):
        pass
    
    await bus.subscribe(EventType.WORLD_STATE_UPDATED, handler)
    
    event = GameEvent(
        event_type=EventType.WORLD_STATE_UPDATED,
        source="world_service",
        data={}
    )
    
    await bus.publish(event)
    
    stats = await bus.get_stats()
    
    assert stats["events_published"] == 1
    assert stats["events_delivered"] == 1
    assert stats["subscriptions"] == 1

