# Event-Driven Architecture Patterns

**Date**: 2025-01-29  
**Project**: Gaming System AI Core  
**System**: Event Bus + Time Manager Integration

## Problem Solved

**Challenge**: Multiple game systems need to react to time changes (Weather, Audio, NPCs, Lighting) without creating tight coupling.

**Solution**: Central Event Bus with publish-subscribe pattern.

## Architecture Pattern

```
TimeOfDayManager (Publisher)
    ↓ publishes events
Event Bus (Broker)
    ↓ distributes events
Weather System (Subscriber)
Audio System (Subscriber)
NPC System (Subscriber)
Lighting System (Subscriber)
```

## Key Components

### 1. GameEventBus
- **Responsibility**: Central event distribution
- **Features**: 
  - Redis Pub/Sub for cross-service
  - In-memory fallback for single-service
  - Event history tracking
  - Statistics collection

### 2. TimeOfDayManager
- **Responsibility**: Game time progression
- **Features**:
  - Configurable time scale
  - State transitions (Dawn/Day/Dusk/Night)
  - Event publishing on changes
  - Subscriber management

## Implementation Details

### Event Types
- `TIME_OF_DAY_CHANGED`: When time state changes (Day → Night)
- `TIME_CHANGED`: On every time update (hour/minute change)
- `WEATHER_CHANGED`: Weather state changes
- `NPC_EVENT`: NPC-related events

### Data Structures
```python
@dataclass
class TimeData:
    hour: int
    minute: int
    day: int
    state: TimeState
    total_minutes: int
    time_string: str  # Computed property
```

## Benefits

1. **Decoupling**: Systems don't know about each other
2. **Scalability**: Easy to add new subscribers
3. **Debugging**: Event history enables replay
4. **Testing**: Can test in isolation with mock Event Bus
5. **Flexibility**: Subscribers can filter events

## Testing Approach

- Unit tests for each component
- Integration tests for event flow
- Real-time test visibility (show all commands/results)
- 100% test coverage required

## Anti-Patterns Avoided

1. ❌ Direct service imports creating tight coupling
2. ❌ Synchronous event handling blocking operations
3. ❌ Mock implementations in production code
4. ❌ Hidden errors in test execution

## Reusable Patterns

1. **Event Bus Service Template**: Can be reused for any event-driven system
2. **Lazy Import Pattern**: For circular dependency resolution
3. **Integration Test Pattern**: For cross-service validation
4. **Real-Time Visibility Pattern**: For command/test result display

## Lessons Learned

1. **Property Decorators**: Use `@property` for computed attributes
2. **Circular Dependencies**: Resolve with lazy imports inside methods/properties
3. **Event History**: Invaluable for debugging complex interactions
4. **Real-Time Visibility**: Critical for trust and debugging












