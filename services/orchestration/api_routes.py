"""
API routes for Orchestration Service.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from services.orchestration.orchestration_service import OrchestrationService
from services.orchestration.models import ContentRequest, ContentResponse
from services.orchestration.server import get_orchestration_service

router = APIRouter(prefix="/api/v1", tags=["orchestration"])


@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentRequest,
    user_id: Optional[str] = None,
    service: OrchestrationService = Depends(get_orchestration_service)
):
    """Generate content using 4-layer pipeline."""
    return await service.generate_content(request, user_id=user_id)


@router.post("/coordinate-battle")
async def coordinate_battle(
    monsters: list,
    player: dict,
    service: OrchestrationService = Depends(get_orchestration_service)
):
    """Coordinate battle with multiple NPCs."""
    return await service.coordinate_battle(monsters, player)

