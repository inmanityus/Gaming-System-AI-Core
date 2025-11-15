# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Integration Tests for Event Bus + Time Manager
REAL implementations only - shows commands and results in real-time.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from services.time_manager.time_manager import TimeOfDayManager, TimeState


@pytest.mark.asyncio
async def test_event_bus_time_manager_integration():
    """Test Event Bus integration with TimeOfDayManager - REAL IMPLEMENTATION."""
    print("[TEST] Creating Event Bus...")
    event_bus = GameEventBus(use_redis=False)
    
    print("[TEST] Creating TimeOfDayManager with Event Bus...")
    time_manager = TimeOfDayManager(
        time_scale=0.1,  # Very fast for testing
        event_bus=event_bus,
        start_hour=18  # Start at dusk (will transition to night)
    )
    
    print("[TEST] Subscribing to time change events...")
    events_received = []
    
    async def handle_event(event: GameEvent):
        events_received.append(event)
        print(f"[EVENT] Received: {event.event_type.value} - State: {event.data.get('new_state')}")
    
    await event_bus.subscribe(EventType.TIME_OF_DAY_CHANGED, handle_event)
    
    print("[TEST] Starting time progression...")
    await time_manager.start()
    
    print("[TEST] Waiting for state change (dusk -> night)...")
    await asyncio.sleep(3.0)  # Wait for time to progress
    
    print("[TEST] Stopping time progression...")
    await time_manager.stop()
    
    print(f"[RESULT] Events received: {len(events_received)}")
    print(f"[RESULT] Time Manager stats: {await time_manager.get_stats()}")
    print(f"[RESULT] Event Bus stats: {await event_bus.get_stats()}")
    
    # Verify events were published
    assert len(events_received) > 0, "No events received from Time Manager"
    
    # Verify event contains correct data
    time_change_events = [e for e in events_received if e.event_type == EventType.TIME_OF_DAY_CHANGED]
    assert len(time_change_events) > 0, "No time change events received"
    
    print("[RESULT] Integration test: PASSED")
    return True











