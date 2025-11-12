# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
API routes for Performance Mode Service.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
    ModeManager,
    PerformanceMode,
    ModePreset,
    ModeTransitionError,
)

router = APIRouter(prefix="/performance-mode", tags=["performance-mode"])

# Global mode manager instance
_mode_manager: ModeManager = None


# Pydantic models for request/response validation
class ModeRequest(BaseModel):
    """Request model for mode switching."""
    mode: Literal["immersive", "competitive"] = Field(..., description="Target performance mode")
    force: bool = Field(False, description="Force switch even if cooldown active")


class ModeResponse(BaseModel):
    """Response model for mode status."""
    mode: str
    preset: str
    target_fps: float
    config: Dict[str, Any]


class PresetRequest(BaseModel):
    """Request model for preset switching."""
    preset: Literal["low", "medium", "high", "ultra", "competitive"] = Field(
        ..., description="Performance preset"
    )


def get_mode_manager() -> ModeManager:
    """Get or create mode manager instance."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = ModeManager()
    return _mode_manager


@router.get("/status")
async def get_status(
    manager: ModeManager = Depends(get_mode_manager)
) -> Dict[str, Any]:
    """Get current performance mode status."""
    return manager.get_status()


@router.get("/mode")
async def get_mode(
    manager: ModeManager = Depends(get_mode_manager)
) -> Dict[str, str]:
    """Get current performance mode."""
    return {
        "mode": manager.get_current_mode().value,
        "preset": manager.get_current_preset().value,
        "target_fps": manager.get_target_fps(),
    }


@router.post("/mode", response_model=ModeResponse)
async def set_mode(
    request: ModeRequest,
    manager: ModeManager = Depends(get_mode_manager)
) -> ModeResponse:
    """
    Switch performance mode.
    
    Args:
        request: Mode request with validated input
    """
    try:
        mode_enum = PerformanceMode(request.mode.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Must be 'immersive' or 'competitive'"
        )
    
    try:
        success = await manager.set_mode_async(mode_enum, force=request.force)
        if not success:
            raise HTTPException(
                status_code=429,
                detail="Mode switch blocked by cooldown. Use force=true to override."
            )
    except ModeTransitionError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mode switch failed: {str(e)}"
        )
    
    return ModeResponse(
        mode=manager.get_current_mode().value,
        preset=manager.get_current_preset().value,
        target_fps=manager.get_target_fps(),
        config=manager.get_config_dict(),
    )


@router.post("/preset")
async def set_preset(
    preset: str,
    manager: ModeManager = Depends(get_mode_manager)
) -> Dict[str, Any]:
    """
    Set performance preset.
    
    Args:
        preset: "low", "medium", "high", "ultra", or "competitive"
    """
    try:
        preset_enum = ModePreset(preset.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset: {preset}. Must be 'low', 'medium', 'high', 'ultra', or 'competitive'"
        )
    
    manager.set_preset(preset_enum)
    
    return {
        "mode": manager.get_current_mode().value,
        "preset": manager.get_current_preset().value,
        "target_fps": manager.get_target_fps(),
        "config": manager.get_config_dict(),
    }


@router.get("/config")
async def get_config(
    mode: str = None,
    manager: ModeManager = Depends(get_mode_manager)
) -> Dict[str, Any]:
    """
    Get rendering configuration.
    
    Args:
        mode: Optional mode override ("immersive" or "competitive")
    """
    mode_enum = None
    if mode:
        try:
            mode_enum = PerformanceMode(mode.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {mode}. Must be 'immersive' or 'competitive'"
            )
    
    return manager.get_config_dict(mode_enum)


@router.post("/detect-preset")
async def detect_preset(
    fps: float,
    target_fps: float = None,
    manager: ModeManager = Depends(get_mode_manager)
) -> Dict[str, Any]:
    """
    Detect appropriate preset based on hardware performance.
    
    Args:
        fps: Current FPS
        target_fps: Target FPS (defaults to current mode target)
    """
    if target_fps is None:
        target_fps = manager.get_target_fps()
    
    recommended = manager.detect_hardware_preset(fps, target_fps)
    
    return {
        "current_fps": fps,
        "target_fps": target_fps,
        "fps_ratio": fps / target_fps if target_fps > 0 else 0.0,
        "recommended_preset": recommended.value if recommended else None,
        "current_preset": manager.get_current_preset().value,
        "current_mode": manager.get_current_mode().value,
    }
