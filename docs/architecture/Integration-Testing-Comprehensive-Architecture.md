# Comprehensive Integration Testing Architecture
**Date**: 2025-01-29  
**Task**: TEST-001 - Comprehensive Integration Testing  
**Status**: Design Complete

---

## OVERVIEW

Complete integration testing strategy for all game systems, covering inter-system interactions, event propagation, performance validation, and edge case handling.

---

## INTEGRATION TEST SUITE STRUCTURE

### Test Organization

```
tests/
├── integration/
│   ├── test_audio_weather_integration.py
│   ├── test_audio_facial_integration.py
│   ├── test_weather_terrain_integration.py
│   ├── test_facial_audio_integration.py
│   ├── test_terrain_fauna_integration.py
│   ├── test_time_weather_integration.py
│   └── test_complete_system_integration.py
├── performance/
│   ├── test_audio_performance.py
│   ├── test_weather_performance.py
│   ├── test_facial_performance.py
│   ├── test_terrain_performance.py
│   └── test_complete_system_performance.py
├── edge_cases/
│   ├── test_state_transitions.py
│   ├── test_concurrent_events.py
│   ├── test_error_recovery.py
│   └── test_memory_leaks.py
└── stress/
    ├── test_high_load.py
    ├── test_memory_stress.py
    └── test_event_storm.py
```

---

## INTER-SYSTEM INTEGRATION TESTS

### Audio-Weather Integration

```python
async def test_audio_weather_integration():
    """Test AudioManager responds to WeatherManager events."""
    # Setup
    event_bus = GameEventBus(use_redis=False)
    weather_manager = WeatherManager(event_bus=event_bus)
    audio_manager = AudioManager(event_bus=event_bus)
    
    # Subscribe audio to weather
    await audio_manager.subscribe_to_weather_changes()
    
    # Change weather
    await weather_manager.set_weather(WeatherState.HEAVY_RAIN)
    
    # Verify audio response
    assert audio_manager.current_weather_music == "rain_music"
    assert audio_manager.ambient_volume == 0.7  # Reduced in rain
    
    # Cleanup
    await event_bus.shutdown()
```

### Weather-Terrain Integration

```python
async def test_weather_terrain_integration():
    """Test FloraManager responds to weather changes."""
    # Setup
    event_bus = GameEventBus(use_redis=False)
    weather_manager = WeatherManager(event_bus=event_bus)
    flora_manager = FloraManager(event_bus=event_bus)
    
    # Subscribe flora to weather
    await flora_manager.subscribe_to_weather_changes()
    
    # Change weather
    await weather_manager.set_weather(WeatherState.HEAVY_RAIN)
    
    # Verify flora response
    assert flora_manager.wind_strength > 0.5
    assert all(tree.wind_animation_intensity > 0.3 for tree in flora_manager.trees)
    
    # Cleanup
    await event_bus.shutdown()
```

### Facial-Audio Integration

```python
async def test_facial_audio_integration():
    """Test ExpressionManager triggers during dialogue."""
    # Setup
    event_bus = GameEventBus(use_redis=False)
    audio_manager = AudioManager(event_bus=event_bus)
    expression_manager = ExpressionManager(event_bus=event_bus)
    
    # Start dialogue
    await audio_manager.play_dialogue("npc_001", "Hello!")
    
    # Verify expression triggers
    expressions = expression_manager.get_active_expressions("npc_001")
    assert len(expressions) > 0
    assert any(expr.emotion == "happy" for expr in expressions)
    
    # Cleanup
    await event_bus.shutdown()
```

---

## EVENT PROPAGATION TESTS

### Cross-System Event Flow

```python
async def test_time_propagation_cascade():
    """Test time events cascade through all systems."""
    event_bus = GameEventBus(use_redis=False)
    
    # Setup all systems
    time_manager = TimeOfDayManager(event_bus=event_bus)
    weather_manager = WeatherManager(event_bus=event_bus)
    flora_manager = FloraManager(event_bus=event_bus)
    fauna_manager = FaunaSpawner(event_bus=event_bus)
    
    # Track events
    events_received = []
    
    async def track_event(event: GameEvent):
        events_received.append(event.event_type)
    
    await event_bus.subscribe(EventType.TIME_OF_DAY_CHANGED, track_event)
    await event_bus.subscribe(EventType.WEATHER_CHANGED, track_event)
    await event_bus.subscribe(EventType.FLORA_SPAWNED, track_event)
    
    # Trigger time change
    await time_manager.set_time(20, 0)  # 8PM
    
    # Verify cascade
    await asyncio.sleep(0.5)  # Allow propagation
    
    assert EventType.TIME_OF_DAY_CHANGED in events_received
    assert EventType.WEATHER_CHANGED in events_received  # Weather responds to time
    assert EventType.FLORA_SPAWNED in events_received  # Flora responds to weather
    
    # Cleanup
    await event_bus.shutdown()
```

---

## PERFORMANCE TESTS

### Complete System Budget

```python
async def test_complete_system_performance():
    """Test all systems within performance budgets."""
    # Setup all systems
    event_bus = GameEventBus(use_redis=False)
    audio_manager = AudioManager(event_bus=event_bus)
    weather_manager = WeatherManager(event_bus=event_bus)
    flora_manager = FloraManager(event_bus=event_bus)
    fauna_manager = FaunaSpawner(event_bus=event_bus)
    expression_manager = ExpressionManager(event_bus=event_bus)
    
    # Measure frame time
    start_time = time.time()
    
    # Simulate one frame
    await audio_manager.update(0.016)  # 60 FPS
    await weather_manager.update(0.016)
    await flora_manager.update(0.016)
    await fauna_manager.update(0.016)
    await expression_manager.update(0.016)
    
    frame_time = time.time() - start_time
    
    # Verify within budget (total 16.67ms for 60 FPS)
    assert frame_time < 0.016, f"Frame time {frame_time*1000:.2f}ms exceeds 16.67ms"
    
    # Verify individual budgets
    assert audio_manager.cpu_time < 0.001
    assert weather_manager.cpu_time < 0.004
    assert flora_manager.cpu_time < 0.002
    assert fauna_manager.cpu_time < 0.003
    assert expression_manager.cpu_time < 0.001
```

### Load Stress Test

```python
async def test_high_load_stress():
    """Test system behavior under high load."""
    event_bus = GameEventBus(use_redis=False)
    
    # Spawn maximum systems
    flora_managers = [FloraManager(event_bus=event_bus) for _ in range(10)]
    fauna_spawners = [FaunaSpawner(event_bus=event_bus) for _ in range(5)]
    expression_managers = [ExpressionManager(event_bus=event_bus) for _ in range(20)]
    
    # Simulate 60 seconds at 60 FPS
    for frame in range(3600):
        for flora in flora_managers:
            await flora.update(0.016)
        
        for fauna in fauna_spawners:
            await fauna.update(0.016)
        
        for expr in expression_managers:
            await expr.update(0.016)
        
        # Verify no memory leaks
        if frame % 600 == 0:  # Every 10 seconds
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            assert memory_usage < 2000, f"Memory leak detected: {memory_usage}MB"
    
    # Cleanup
    await event_bus.shutdown()
```

---

## EDGE CASE TESTS

### State Transition Conflicts

```python
async def test_concurrent_state_transitions():
    """Test system handles concurrent state changes gracefully."""
    event_bus = GameEventBus(use_redis=False)
    
    weather_manager = WeatherManager(event_bus=event_bus)
    time_manager = TimeOfDayManager(event_bus=event_bus)
    
    # Trigger concurrent transitions
    task1 = weather_manager.set_weather(WeatherState.THUNDERSTORM)
    task2 = time_manager.set_time(21, 0)
    task3 = weather_manager.set_weather(WeatherState.CLEAR)
    
    # All should complete without errors
    await asyncio.gather(task1, task2, task3)
    
    # Verify final state is valid
    assert weather_manager.get_current_weather() in [WeatherState.THUNDERSTORM, WeatherState.CLEAR]
    
    # Cleanup
    await event_bus.shutdown()
```

### Memory Leak Detection

```python
async def test_subscription_memory_leaks():
    """Verify event subscriptions don't leak memory."""
    event_bus = GameEventBus(use_redis=False)
    
    initial_memory = psutil.Process().memory_info().rss
    
    # Create and destroy many subscriptions
    for i in range(1000):
        sub_id = await event_bus.subscribe(EventType.WEATHER_CHANGED, dummy_handler)
        await event_bus.unsubscribe(EventType.WEATHER_CHANGED, sub_id)
    
    # Force GC
    import gc
    gc.collect()
    
    final_memory = psutil.Process().memory_info().rss
    memory_growth = (final_memory - initial_memory) / 1024 / 1024
    
    # Should be minimal growth (< 50MB)
    assert memory_growth < 50, f"Memory leak: {memory_growth}MB growth"
    
    # Cleanup
    await event_bus.shutdown()
```

---

## VALIDATION CRITERIA

### Integration Success

1. **Event Propagation**: All events reach intended subscribers
2. **State Consistency**: All systems maintain valid state
3. **Performance Budgets**: All systems within limits
4. **Memory Stability**: No leaks over extended operation
5. **Error Recovery**: Systems handle failures gracefully

### Test Coverage

- **Unit Tests**: 80%+ coverage per system
- **Integration Tests**: All system pairs tested
- **Performance Tests**: All budgets validated
- **Edge Cases**: 100+ scenarios
- **Stress Tests**: System limits identified

---

## TEST EXECUTION FRAMEWORK

### Automated Test Runner

```bash
#!/bin/bash
# Run all integration tests

echo "Running Integration Tests..."
python -m pytest tests/integration/ -v --tb=short

echo "Running Performance Tests..."
python -m pytest tests/performance/ -v --benchmark-only

echo "Running Edge Case Tests..."
python -m pytest tests/edge_cases/ -v

echo "Running Stress Tests..."
python -m pytest tests/stress/ -v --timeout=300

echo "All tests complete!"
```

---

## REPORTING

### Test Report Format

```markdown
## Integration Test Report

**Date**: 2025-01-29
**Total Tests**: 150
**Passed**: 148
**Failed**: 2
**Skipped**: 0

### Failed Tests
1. `test_time_weather_integration` - Weather not responding to time
2. `test_stress_event_storm` - Memory exhaustion after 100k events

### Performance Results
- Audio System: 0.8ms (budget: 0.97ms) ✅
- Weather System: 3.2ms (budget: 3.5ms) ✅
- Flora System: 1.9ms (budget: 2.0ms) ✅
- Fauna System: 2.8ms (budget: 3.0ms) ✅
- Expression System: 0.9ms (budget: 1.0ms) ✅

### Recommendations
1. Fix weather-time integration bug
2. Add event rate limiting for stress protection
```

---

**Status**: ✅ **COMPREHENSIVE INTEGRATION TESTING ARCHITECTURE COMPLETE**



