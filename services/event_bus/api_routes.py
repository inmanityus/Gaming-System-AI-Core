"""
Event Bus API Routes - FastAPI endpoints for event bus.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .event_bus import GameEventBus, GameEvent, EventType


router = APIRouter(prefix="/events", tags=["events"])


# Global event bus instance (singleton)
_event_bus_instance: Optional[GameEventBus] = None


def get_event_bus() -> GameEventBus:
    """Get or create event bus instance."""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = GameEventBus(use_redis=True)
    return _event_bus_instance


# Pydantic models
class PublishEventRequest(BaseModel):
    event_type: str
    source: str
    data: Dict[str, Any] = {}
    player_id: Optional[str] = None
    priority: str = "normal"


class SubscribeRequest(BaseModel):
    event_type: str
    subscriber_id: Optional[str] = None


@router.post("/publish")
async def publish_event(
    request: PublishEventRequest,
    event_bus: GameEventBus = Depends(get_event_bus)
) -> Dict[str, Any]:
    """
    Publish an event to the event bus - REAL IMPLEMENTATION.
    
    Events are broadcast to all subscribers immediately.
    """
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type: {request.event_type}"
        )
    
    event = GameEvent(
        event_type=event_type,
        source=request.source,
        data=request.data,
        player_id=request.player_id,
        priority=request.priority,
    )
    
    notified_count = await event_bus.publish(event)
    
    return {
        "success": True,
        "event_id": event.event_id,
        "notified_subscribers": notified_count,
        "event": event.to_dict(),
    }


@router.get("/history/{event_type}")
async def get_history(
    event_type: str,
    limit: int = 10,
    event_bus: GameEventBus = Depends(get_event_bus)
) -> Dict[str, Any]:
    """Get event history for an event type."""
    try:
        et = EventType(event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    history = await event_bus.get_event_history(et, limit=limit)
    
    return {
        "event_type": event_type,
        "history": [event.to_dict() for event in history],
        "count": len(history),
    }


@router.get("/stats")
async def get_stats(
    event_bus: GameEventBus = Depends(get_event_bus)
) -> Dict[str, Any]:
    """Get event bus statistics."""
    stats = await event_bus.get_stats()
    return stats


@router.post("/subscribe")
async def subscribe_to_event(
    request: SubscribeRequest,
    event_bus: GameEventBus = Depends(get_event_bus)
) -> Dict[str, Any]:
    """
    Subscribe to an event type via webhook.
    
    Note: This is a webhook-based subscription. For in-process subscriptions,
    use the GameEventBus class directly.
    """
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type: {request.event_type}"
        )
    
    # For webhook subscriptions, would register webhook URL
    # For now, return subscription info
    subscription_id = await event_bus.subscribe(
        event_type=event_type,
        callback=lambda e: print(f"Webhook event: {e}"),  # Would be webhook call
        subscriber_id=request.subscriber_id
    )
    
    return {
        "success": True,
        "subscription_id": subscription_id,
        "event_type": request.event_type,
    }



