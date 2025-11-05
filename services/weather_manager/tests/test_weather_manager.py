"""
Tests for Weather Manager - REAL implementations only.
"""

import pytest
import asyncio
from services.weather_manager.weather_manager import WeatherManager, WeatherState, Season


@pytest.mark.asyncio
async def test_weather_manager_initialization():
    """Test Weather Manager initialization - REAL IMPLEMENTATION."""
    print("[TEST] Creating Weather Manager...")
    manager = WeatherManager(season=Season.SPRING)
    
    assert manager is not None
    assert manager.season == Season.SPRING
    assert manager.current_weather is not None
    assert manager.current_weather.state in WeatherState
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_start_stop():
    """Test starting and stopping weather manager."""
    print("[TEST] Creating and starting Weather Manager...")
    manager = WeatherManager(season=Season.SUMMER)
    
    await manager.start()
    assert manager._running is True
    print("[RESULT] Weather Manager started")
    
    await asyncio.sleep(0.1)  # Let it run briefly
    
    await manager.stop()
    assert manager._running is False
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_set_weather():
    """Test manually setting weather."""
    print("[TEST] Creating Weather Manager...")
    manager = WeatherManager(season=Season.SPRING)
    await manager.start()
    
    initial_state = manager.current_weather.state
    
    print("[TEST] Setting weather to RAIN...")
    await manager.set_weather(WeatherState.RAIN, intensity=0.7)
    
    assert manager.current_weather.state == WeatherState.RAIN
    assert manager.current_weather.intensity == 0.7
    assert manager.current_weather.state != initial_state
    print("[RESULT] Weather set successfully")
    
    await manager.stop()
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_set_season():
    """Test changing season."""
    print("[TEST] Creating Weather Manager with SPRING...")
    manager = WeatherManager(season=Season.SPRING)
    
    assert manager.season == Season.SPRING
    initial_temp = manager.current_weather.temperature
    
    print("[TEST] Changing season to WINTER...")
    manager.set_season(Season.WINTER)
    
    assert manager.season == Season.WINTER
    assert manager.current_weather.season == Season.WINTER
    # Temperature should adjust for winter
    assert manager.current_weather.temperature < initial_temp
    print("[RESULT] Season changed successfully")
    
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_forecast():
    """Test weather forecast generation."""
    print("[TEST] Creating Weather Manager...")
    manager = WeatherManager(season=Season.SPRING)
    
    print("[TEST] Getting 24-hour forecast...")
    forecast = manager.get_forecast(hours=24)
    
    assert len(forecast) == 24
    assert all("hour" in item for item in forecast)
    assert all("state" in item for item in forecast)
    assert all("temperature" in item for item in forecast)
    print(f"[RESULT] Forecast generated: {len(forecast)} hours")
    
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_statistics():
    """Test weather statistics."""
    print("[TEST] Creating Weather Manager...")
    manager = WeatherManager(season=Season.SPRING)
    await manager.start()
    
    # Change weather a few times
    await manager.set_weather(WeatherState.RAIN)
    await asyncio.sleep(0.1)
    await manager.set_weather(WeatherState.STORM)
    
    print("[TEST] Getting statistics...")
    stats = manager.get_statistics()
    
    assert "total_changes" in stats
    assert "state_counts" in stats
    assert "current_weather" in stats
    assert "season" in stats
    assert stats["total_changes"] >= 2  # At least our manual changes
    print(f"[RESULT] Statistics: {stats['total_changes']} changes")
    
    await manager.stop()
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_event_publishing():
    """Test that weather changes publish events."""
    print("[TEST] Creating Weather Manager with Event Bus...")
    from services.event_bus.event_bus import GameEventBus, EventType
    
    event_bus = GameEventBus(use_redis=False)
    manager = WeatherManager(event_bus=event_bus, season=Season.SPRING)
    
    events_received = []
    
    async def event_handler(event):
        events_received.append(event)
        print(f"[EVENT] Received: {event.event_type.value}")
    
    await event_bus.subscribe(EventType.WEATHER_CHANGED, event_handler)
    await manager.start()
    
    print("[TEST] Changing weather to trigger event...")
    await manager.set_weather(WeatherState.RAIN)
    
    # Wait a moment for event to be published
    await asyncio.sleep(0.1)
    
    assert len(events_received) >= 1
    assert events_received[0].event_type == EventType.WEATHER_CHANGED
    assert "new_state" in events_received[0].data
    print(f"[RESULT] Event published: {events_received[0].data['new_state']}")
    
    await manager.stop()
    print("[RESULT] Test: PASSED")




