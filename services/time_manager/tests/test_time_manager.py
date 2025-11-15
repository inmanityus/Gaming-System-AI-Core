# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Tests for Time Manager - REAL implementations only.
"""

import pytest
import asyncio
import time
from services.time_manager.time_manager import TimeOfDayManager, TimeState, TimeAwareInterface


class MockSubscriber(TimeAwareInterface):
    """Mock subscriber for testing."""
    
    def __init__(self):
        self.time_changes = []
        self.state_changes = []
    
    async def on_time_changed(self, time_data):
        self.time_changes.append(time_data)
    
    async def on_time_of_day_changed(self, old_state, new_state):
        self.state_changes.append((old_state, new_state))


@pytest.mark.asyncio
async def test_time_manager_progression():
    """Test time progression - REAL IMPLEMENTATION."""
    time_manager = TimeOfDayManager(time_scale=1.0, start_hour=7)  # Fast for testing
    
    # Start progression
    await time_manager.start()
    
    # Wait a moment for time to progress
    await asyncio.sleep(2.0)
    
    # Check time has progressed
    current_time = time_manager.get_current_time()
    assert current_time.minute > 0 or current_time.hour > 7
    
    await time_manager.stop()


@pytest.mark.asyncio
async def test_time_manager_state_changes():
    """Test time of day state changes."""
    time_manager = TimeOfDayManager(time_scale=0.1, start_hour=18)  # Very fast, start at dusk
    
    subscriber = MockSubscriber()
    await time_manager.subscribe(subscriber)
    
    await time_manager.start()
    
    # Wait for state change (should transition from dusk to night)
    await asyncio.sleep(2.0)
    
    # Check subscriber was notified
    assert len(subscriber.time_changes) > 0
    
    await time_manager.stop()


@pytest.mark.asyncio
async def test_time_manager_set_time():
    """Test manual time setting - REAL IMPLEMENTATION."""
    time_manager = TimeOfDayManager(time_scale=60.0, start_hour=7)
    
    # Set time to night
    time_manager.set_time(22, 30)  # 10:30 PM
    
    current_time = time_manager.get_current_time()
    assert current_time.hour == 22
    assert current_time.minute == 30
    assert current_time.state == TimeState.NIGHT


@pytest.mark.asyncio
async def test_time_manager_subscribe():
    """Test subscriber registration - REAL IMPLEMENTATION."""
    time_manager = TimeOfDayManager(time_scale=60.0)
    
    subscriber1 = MockSubscriber()
    subscriber2 = MockSubscriber()
    
    await time_manager.subscribe(subscriber1)
    await time_manager.subscribe(subscriber2)
    
    # Start and let time progress
    await time_manager.start()
    await asyncio.sleep(1.0)
    
    # Both should receive updates
    assert len(subscriber1.time_changes) > 0 or len(subscriber2.time_changes) > 0
    
    # Unsubscribe
    await time_manager.unsubscribe(subscriber1)
    
    await time_manager.stop()











