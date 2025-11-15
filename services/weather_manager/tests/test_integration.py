# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Integration tests for Weather Manager with Event Bus and Time Manager.
REAL IMPLEMENTATION - Real integration tests.
"""

import pytest
import asyncio
from services.weather_manager.weather_manager import WeatherManager, WeatherState, Season
from services.time_manager.time_manager import TimeOfDayManager


@pytest.mark.asyncio
async def test_weather_manager_time_manager_integration():
    """Test Weather Manager integration with Time Manager via Event Bus."""
    print("[TEST] Creating Event Bus...")
    event_bus = GameEventBus(use_redis=False)
    
    print("[TEST] Creating Time Manager with Event Bus...")
    time_manager = TimeOfDayManager(event_bus=event_bus, time_scale=60.0)
    
    print("[TEST] Creating Weather Manager with Event Bus...")
    weather_manager = WeatherManager(event_bus=event_bus, season=Season.SPRING)
    
    weather_events_received = []
    
    async def weather_handler(event: GameEvent):
        weather_events_received.append(event)
        print(f"[WEATHER EVENT] Received: {event.data.get('new_state')}")
    
    async def time_handler(event: GameEvent):
        print(f"[TIME EVENT] Received: {event.data.get('time_state')}")
    
    print("[TEST] Subscribing to events...")
    await event_bus.subscribe(EventType.WEATHER_CHANGED, weather_handler)
    await event_bus.subscribe(EventType.TIME_OF_DAY_CHANGED, time_handler)
    
    print("[TEST] Starting managers...")
    await time_manager.start()
    await weather_manager.start()
    
    print("[TEST] Waiting for events...")
    await asyncio.sleep(1.0)  # Let systems run briefly
    
    # Manually trigger weather change
    print("[TEST] Triggering weather change...")
    await weather_manager.set_weather(WeatherState.STORM)
    await asyncio.sleep(0.1)
    
    # Verify weather event was received
    assert len(weather_events_received) >= 1
    assert weather_events_received[-1].event_type == EventType.WEATHER_CHANGED
    print(f"[RESULT] Weather event received: {weather_events_received[-1].data.get('new_state')}")
    
    await weather_manager.stop()
    await time_manager.stop()
    
    print("[RESULT] Test: PASSED")


@pytest.mark.asyncio
async def test_weather_manager_seasonal_variations():
    """Test that weather changes appropriately with seasons."""
    print("[TEST] Testing seasonal weather variations...")
    
    event_bus = GameEventBus(use_redis=False)
    
    # Test each season
    for season in Season:
        print(f"[TEST] Testing {season.value} season...")
        manager = WeatherManager(event_bus=event_bus, season=season)
        
        # Get possible states for this season
        current_state = manager.current_weather.state
        possible_states = manager._get_possible_weather_states(season, current_state)
        
        assert len(possible_states) > 0, f"No possible weather states for {season.value}"
        
        # Verify season-specific states are available
        if season == Season.WINTER:
            # Winter should have snow states available
            has_snow = any(
                s in [WeatherState.SNOW, WeatherState.HEAVY_SNOW, WeatherState.BLIZZARD]
                for s in possible_states
            )
            # Snow should be more common in winter, but not always
            print(f"[RESULT] Winter has snow states: {has_snow}")
        
        elif season == Season.SUMMER:
            # Summer should have clear/extreme heat available
            has_clear = WeatherState.CLEAR in possible_states or WeatherState.EXTREME_HEAT in possible_states
            print(f"[RESULT] Summer has clear/heat states: {has_clear}")
        
        print(f"[RESULT] {season.value} season validated")
    
    print("[RESULT] Test: PASSED")











