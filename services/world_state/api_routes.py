"""
API Routes - FastAPI routes for World State Service.
Handles world state management, events, factions, and economy.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from world_state_manager import WorldStateManager
from event_system import EventSystem
from faction_manager import FactionManager
from economic_manager import EconomicManager


# Pydantic models
class WorldStateUpdate(BaseModel):
    world_time: Optional[str] = None
    current_weather: Optional[str] = None
    global_events: Optional[Dict[str, Any]] = None
    faction_power: Optional[Dict[str, Any]] = None
    economic_state: Optional[Dict[str, Any]] = None
    npc_population: Optional[Dict[str, Any]] = None
    territory_control: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


class EventGenerationRequest(BaseModel):
    event_type: str
    trigger: str
    intensity: float = 0.5
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FactionPowerUpdate(BaseModel):
    faction_id: str
    power_delta: float


class TerritoryControlUpdate(BaseModel):
    faction_id: str
    territory_id: str
    control_level: float


class EconomicEventRequest(BaseModel):
    event_type: str
    intensity: float = 0.5


# Router
router = APIRouter(prefix="/world", tags=["World State"])

# Dependencies
def get_world_state_manager() -> WorldStateManager:
    return WorldStateManager()


def get_event_system() -> EventSystem:
    return EventSystem()


def get_faction_manager() -> FactionManager:
    return FactionManager()


def get_economic_manager() -> EconomicManager:
    return EconomicManager()


# World State Routes
@router.get("/state/current")
async def get_current_world_state(
    world_manager: WorldStateManager = Depends(get_world_state_manager),
):
    """Get current world state."""
    try:
        state = await world_manager.get_current_world_state()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/state/update")
async def update_world_state(
    updates: WorldStateUpdate,
    world_manager: WorldStateManager = Depends(get_world_state_manager),
):
    """Update world state."""
    try:
        update_dict = updates.dict(exclude_unset=True)
        updated_state = await world_manager.update_world_state(update_dict)
        return updated_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/history")
async def get_world_state_history(
    limit: int = 10,
    world_manager: WorldStateManager = Depends(get_world_state_manager),
):
    """Get world state history."""
    try:
        history = await world_manager.get_world_state_history(limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/metrics")
async def get_world_state_metrics(
    world_manager: WorldStateManager = Depends(get_world_state_manager),
):
    """Get world state metrics."""
    try:
        metrics = await world_manager.get_state_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Event System Routes
@router.post("/events/generate")
async def generate_event(
    request: EventGenerationRequest,
    event_system: EventSystem = Depends(get_event_system),
):
    """Generate a new event."""
    try:
        event = await event_system.generate_event(
            request.event_type,
            request.trigger,
            request.intensity,
            request.description,
            request.metadata,
        )
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/active")
async def get_active_events(
    event_system: EventSystem = Depends(get_event_system),
):
    """Get all active events."""
    try:
        events = await event_system.get_active_events()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/history")
async def get_event_history(
    limit: int = 50,
    event_system: EventSystem = Depends(get_event_system),
):
    """Get event history."""
    try:
        events = await event_system.get_event_history(limit)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/statistics")
async def get_event_statistics(
    event_system: EventSystem = Depends(get_event_system),
):
    """Get event statistics."""
    try:
        stats = await event_system.get_event_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/{event_id}/complete")
async def complete_event(
    event_id: str,
    event_system: EventSystem = Depends(get_event_system),
):
    """Mark event as completed."""
    try:
        success = await event_system.complete_event(event_id)
        return {"success": success, "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Faction Management Routes
@router.get("/factions/{faction_id}/power")
async def get_faction_power(
    faction_id: str,
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Get faction power."""
    try:
        power = await faction_manager.get_faction_power(faction_id)
        return {"faction_id": faction_id, "power": power}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/factions/{faction_id}/power")
async def update_faction_power(
    faction_id: str,
    request: FactionPowerUpdate,
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Update faction power."""
    try:
        new_power = await faction_manager.update_faction_power(faction_id, request.power_delta)
        return {"faction_id": faction_id, "new_power": new_power}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/factions/{faction_id}/territory")
async def get_faction_territory(
    faction_id: str,
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Get faction territory control."""
    try:
        territories = await faction_manager.get_territory_control(faction_id)
        return {"faction_id": faction_id, "territories": territories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/factions/{faction_id}/territory")
async def update_territory_control(
    faction_id: str,
    request: TerritoryControlUpdate,
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Update territory control."""
    try:
        success = await faction_manager.update_territory_control(
            faction_id, request.territory_id, request.control_level
        )
        return {"success": success, "faction_id": faction_id, "territory_id": request.territory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/factions/{faction_id}/relationships")
async def get_faction_relationships(
    faction_id: str,
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Get faction relationships."""
    try:
        relationships = await faction_manager.get_faction_relationships(faction_id)
        return {"faction_id": faction_id, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/factions/conflicts")
async def get_faction_conflicts(
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Get active faction conflicts."""
    try:
        conflicts = await faction_manager.get_faction_conflicts()
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/factions/rankings")
async def get_faction_rankings(
    faction_manager: FactionManager = Depends(get_faction_manager),
):
    """Get faction power rankings."""
    try:
        rankings = await faction_manager.get_faction_rankings()
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Economic Management Routes
@router.get("/economy/market")
async def get_market_state(
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Get current market state."""
    try:
        market_state = await economic_manager.get_market_state()
        return market_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/economy/simulate")
async def simulate_market_dynamics(
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Simulate market dynamics."""
    try:
        results = await economic_manager.simulate_market_dynamics()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economy/resources/{resource_type}/price")
async def get_resource_price(
    resource_type: str,
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Get resource price."""
    try:
        price = await economic_manager.get_resource_price(resource_type)
        return {"resource_type": resource_type, "price": price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/economy/trade/calculate")
async def calculate_trade_value(
    resource_type: str,
    quantity: int,
    buyer_faction: Optional[str] = None,
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Calculate trade value."""
    try:
        trade_value = await economic_manager.calculate_trade_value(
            resource_type, quantity, buyer_faction
        )
        return trade_value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economy/trends")
async def get_market_trends(
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Get market trends."""
    try:
        trends = await economic_manager.get_market_trends()
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economy/indicators")
async def get_economic_indicators(
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Get economic indicators."""
    try:
        indicators = await economic_manager.get_economic_indicators()
        return indicators
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/economy/events/generate")
async def generate_economic_event(
    request: EconomicEventRequest,
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Generate economic event."""
    try:
        event = await economic_manager.generate_economic_event(
            request.event_type, request.intensity
        )
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health and Status Routes
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "world_state"}


@router.get("/status")
async def get_service_status(
    world_manager: WorldStateManager = Depends(get_world_state_manager),
    event_system: EventSystem = Depends(get_event_system),
    faction_manager: FactionManager = Depends(get_faction_manager),
    economic_manager: EconomicManager = Depends(get_economic_manager),
):
    """Get comprehensive service status."""
    try:
        # Get status from each component
        world_metrics = await world_manager.get_state_metrics()
        event_stats = await event_system.get_event_statistics()
        economic_indicators = await economic_manager.get_economic_indicators()
        
        return {
            "service": "world_state",
            "status": "healthy",
            "world_state": world_metrics,
            "events": event_stats,
            "economy": economic_indicators,
            "timestamp": "2025-10-29T23:17:17Z",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
