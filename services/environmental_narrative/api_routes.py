"""
API routes for Environmental Narrative Service.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from services.environmental_narrative.narrative_service import (
    EnvironmentalNarrativeService,
    SceneType,
    StoryScene,
    SceneGenerationError,
)

router = APIRouter(prefix="/environmental-narrative", tags=["environmental-narrative"])

# Global service instance
_narrative_service: EnvironmentalNarrativeService = None


# Pydantic models for request/response validation
class GenerateSceneRequest(BaseModel):
    """Request model for scene generation."""
    scene_type: str = Field(..., description="Type of scene to generate")
    location_x: float = Field(..., ge=-100000, le=100000, description="X coordinate")
    location_y: float = Field(..., ge=-100000, le=100000, description="Y coordinate")
    location_z: float = Field(..., ge=-10000, le=10000, description="Z coordinate")
    density: Optional[int] = Field(None, ge=5, le=50, description="Optional clutter density (5-50)")
    
    @validator('scene_type')
    def validate_scene_type(cls, v):
        valid_types = [t.value for t in SceneType]
        if v.lower() not in valid_types:
            raise ValueError(f'scene_type must be one of: {valid_types}')
        return v.lower()
    
    @validator('density')
    def validate_density(cls, v):
        if v is not None and (v < 5 or v > 50):
            raise ValueError('density must be between 5 and 50')
        return v


class RecordDiscoveryRequest(BaseModel):
    """Request model for discovery recording."""
    player_id: str = Field(..., description="Player UUID")
    object_id: Optional[str] = Field(None, description="Optional object UUID")
    scene_id: Optional[str] = Field(None, description="Optional scene UUID")
    noticed: bool = Field(True, description="Whether player explicitly noticed")


class EnvironmentalChangeRequest(BaseModel):
    """Request model for environmental change recording."""
    change_type: str = Field(..., description="Type of change")
    location_x: float = Field(..., ge=-100000, le=100000)
    location_y: float = Field(..., ge=-100000, le=100000)
    location_z: float = Field(..., ge=-10000, le=10000)
    description: str = Field(..., min_length=1, max_length=1000, description="Description of change")
    player_id: Optional[str] = Field(None, description="Optional player UUID")


def get_narrative_service() -> EnvironmentalNarrativeService:
    """Get or create narrative service instance."""
    global _narrative_service
    if _narrative_service is None:
        _narrative_service = EnvironmentalNarrativeService()
    return _narrative_service


@router.post("/scenes/generate")
async def generate_scene(
    request: GenerateSceneRequest,
    service: EnvironmentalNarrativeService = Depends(get_narrative_service)
) -> Dict[str, Any]:
    """
    Generate a story scene with validated input.
    
    Args:
        request: Scene generation request with validated input
    """
    try:
        scene_type_enum = SceneType(request.scene_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scene_type: {request.scene_type}. Must be one of: {[t.value for t in SceneType]}"
        )
    
    location = (request.location_x, request.location_y, request.location_z)
    
    try:
        scene = await service.generate_story_scene(scene_type_enum, location, request.density)
        return scene.to_dict()
    except SceneGenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scenes/{scene_id}")
async def get_scene(
    scene_id: str,
    service: EnvironmentalNarrativeService = Depends(get_narrative_service)
) -> Dict[str, Any]:
    """Get a scene by ID."""
    try:
        scene_uuid = UUID(scene_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid scene_id: {scene_id}")
    
    scene = await service.get_scene(scene_uuid)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_id} not found")
    
    return scene.to_dict()


@router.post("/discoveries")
async def record_discovery(
    request: RecordDiscoveryRequest,
    service: EnvironmentalNarrativeService = Depends(get_narrative_service)
) -> Dict[str, Any]:
    """
    Record a discovery with validated input.
    
    Args:
        request: Discovery recording request
    """
    try:
        player_uuid = UUID(request.player_id)
        obj_uuid = UUID(request.object_id) if request.object_id else None
        scene_uuid = UUID(request.scene_id) if request.scene_id else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")
    
    reward = await service.record_discovery(player_uuid, obj_uuid, scene_uuid, request.noticed)
    return reward.to_dict()


@router.get("/discoveries/metrics")
async def get_discovery_metrics(
    service: EnvironmentalNarrativeService = Depends(get_narrative_service)
) -> Dict[str, Any]:
    """Get discovery metrics (99% details tracking)."""
    return service.get_discovery_metrics()


@router.post("/environmental-history")
async def record_environmental_change(
    request: EnvironmentalChangeRequest,
    service: EnvironmentalNarrativeService = Depends(get_narrative_service)
) -> Dict[str, Any]:
    """
    Record an environmental change with validated input.
    
    Args:
        request: Environmental change request
    """
    location = (request.location_x, request.location_y, request.location_z)
    player_uuid = None
    if request.player_id:
        try:
            player_uuid = UUID(request.player_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid player_id: {request.player_id}")
    
    try:
        await service.record_environmental_change(
            request.change_type,
            location,
            request.description,
            player_uuid
        )
        return {"status": "recorded"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/environmental-history")
async def get_environmental_history(
    location_x: Optional[float] = None,
    location_y: Optional[float] = None,
    location_z: Optional[float] = None,
    radius: float = Field(50.0, ge=0.0, le=1000.0, description="Search radius"),
    limit: int = Field(100, ge=1, le=1000, description="Maximum records"),
    service: EnvironmentalNarrativeService = Depends(get_narrative_service)
) -> List[Dict[str, Any]]:
    """
    Get environmental history.
    
    Args:
        location_x: Optional X coordinate (if provided, filters by radius)
        location_y: Optional Y coordinate
        location_z: Optional Z coordinate
        radius: Search radius (0-1000)
        limit: Maximum records (1-1000)
    """
    location = None
    if location_x is not None and location_y is not None and location_z is not None:
        location = (location_x, location_y, location_z)
    
    return await service.get_environmental_history(location, radius, limit)
