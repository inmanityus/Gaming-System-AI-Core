"""
Time Manager API Routes - FastAPI endpoints for time management.
"""

import asyncio
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .time_manager import TimeOfDayManager, TimeData


router = APIRouter(prefix="/time", tags=["time"])


# Global time manager instance (singleton)
_time_manager_instance: Optional[TimeOfDayManager] = None


def get_time_manager() -> TimeOfDayManager:
    """Get or create time manager instance."""
    global _time_manager_instance
    if _time_manager_instance is None:
        _time_manager_instance = TimeOfDayManager(time_scale=60.0, start_hour=7)
        # Auto-start time progression
        asyncio.create_task(_time_manager_instance.start())
    return _time_manager_instance


# Pydantic models
class SetTimeRequest(BaseModel):
    hour: int
    minute: int = 0
    day: int = None


class SetTimeScaleRequest(BaseModel):
    time_scale: float  # Real seconds per game hour


@router.get("/current")
async def get_current_time(
    time_manager: TimeOfDayManager = Depends(get_time_manager)
) -> Dict[str, Any]:
    """Get current game time - REAL IMPLEMENTATION."""
    current_time = time_manager.get_current_time()
    return {
        "success": True,
        "time": current_time.to_dict(),
    }


@router.post("/set")
async def set_time(
    request: SetTimeRequest,
    time_manager: TimeOfDayManager = Depends(get_time_manager)
) -> Dict[str, Any]:
    """Set game time manually - REAL IMPLEMENTATION."""
    if not (0 <= request.hour < 24):
        raise HTTPException(status_code=400, detail="Hour must be 0-23")
    if not (0 <= request.minute < 60):
        raise HTTPException(status_code=400, detail="Minute must be 0-59")
    
    time_manager.set_time(request.hour, request.minute, request.day)
    
    return {
        "success": True,
        "time": time_manager.get_current_time().to_dict(),
    }


@router.post("/scale")
async def set_time_scale(
    request: SetTimeScaleRequest,
    time_manager: TimeOfDayManager = Depends(get_time_manager)
) -> Dict[str, Any]:
    """Set time scale - REAL IMPLEMENTATION."""
    if request.time_scale <= 0:
        raise HTTPException(status_code=400, detail="Time scale must be > 0")
    
    time_manager.set_time_scale(request.time_scale)
    
    return {
        "success": True,
        "time_scale": time_manager.time_scale,
    }


@router.post("/start")
async def start_time_progression(
    time_manager: TimeOfDayManager = Depends(get_time_manager)
) -> Dict[str, Any]:
    """Start time progression - REAL IMPLEMENTATION."""
    await time_manager.start()
    return {"success": True, "message": "Time progression started"}


@router.post("/stop")
async def stop_time_progression(
    time_manager: TimeOfDayManager = Depends(get_time_manager)
) -> Dict[str, Any]:
    """Stop time progression - REAL IMPLEMENTATION."""
    await time_manager.stop()
    return {"success": True, "message": "Time progression stopped"}


@router.get("/stats")
async def get_stats(
    time_manager: TimeOfDayManager = Depends(get_time_manager)
) -> Dict[str, Any]:
    """Get time manager statistics - REAL IMPLEMENTATION."""
    stats = await time_manager.get_stats()
    return stats

