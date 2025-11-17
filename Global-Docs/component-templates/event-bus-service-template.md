# Event Bus Service Template

**Purpose**: Reusable template for creating event-driven services  
**Last Updated**: 2025-01-29

## Service Structure

```
services/
├── {service_name}/
│   ├── __init__.py
│   ├── {service_name}.py      # Core implementation
│   ├── api_routes.py          # FastAPI endpoints
│   ├── server.py              # FastAPI server setup
│   └── tests/
│       ├── __init__.py
│       ├── test_{service_name}.py
│       └── test_integration.py
```

## Core Implementation Pattern

```python
"""
{ServiceName} - {Description}
REAL IMPLEMENTATION - No mocks, real functionality.
"""

import asyncio
from typing import Any, Dict, List, Optional
from services.event_bus.event_bus import GameEventBus, GameEvent, EventType

class {ServiceName}:
    """
    {ServiceName} - REAL IMPLEMENTATION.
    """
    
    def __init__(self, event_bus: Optional[GameEventBus] = None):
        self.event_bus = event_bus or GameEventBus(use_redis=False)
        # Initialize service state
    
    async def start(self):
        """Start the service and subscribe to relevant events."""
        # Subscribe to Event Bus
        await self.event_bus.subscribe(
            EventType.{RELEVANT_EVENT},
            self._handle_event
        )
    
    async def _handle_event(self, event: GameEvent):
        """Handle events from Event Bus."""
        # Process event
        pass
    
    async def publish_event(self, event_type: EventType, data: Dict[str, Any]):
        """Publish event to Event Bus."""
        event = GameEvent(
            event_type=event_type,
            source=self.__class__.__name__,
            data=data
        )
        await self.event_bus.publish(event)
```

## API Routes Pattern

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/{service_name}", tags=["{ServiceName}"])

class {Service}Request(BaseModel):
    # Request model
    pass

@router.get("/status")
async def get_status():
    """Get service status."""
    return {"status": "active"}

@router.post("/action")
async def perform_action(request: {Service}Request):
    """Perform service action."""
    # Implementation
    pass
```

## Test Pattern

```python
"""
Tests for {ServiceName} - REAL implementations only.
"""

import pytest
from services.{service_name}.{service_name} import {ServiceName}

@pytest.mark.asyncio
async def test_{service_name}_basic():
    """Test basic functionality."""
    service = {ServiceName}()
    # Test implementation
    assert True
```

## Integration Test Pattern

```python
@pytest.mark.asyncio
async def test_{service_name}_event_bus_integration():
    """Test integration with Event Bus."""
    from services.event_bus.event_bus import GameEventBus
    
    event_bus = GameEventBus(use_redis=False)
    service = {ServiceName}(event_bus=event_bus)
    
    events_received = []
    
    async def handler(event: GameEvent):
        events_received.append(event)
    
    await event_bus.subscribe(EventType.{EVENT}, handler)
    await service.start()
    
    # Trigger event
    # Verify event received
    assert len(events_received) == 1
```

## Notes

- Always use REAL implementations (no mocks in production code)
- Integrate with Event Bus for cross-service communication
- Show all commands and results in real-time
- Test comprehensively after each milestone
- Use lazy imports for circular dependency resolution if needed












