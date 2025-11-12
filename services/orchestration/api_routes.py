# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
API routes for Orchestration Service.
"""

import os
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Any, Dict

# Import shared models
from .models_schemas import ContentRequest, ContentResponse

# Import orchestration service
from .orchestration_service import OrchestrationService

# Placeholder function
def get_orchestration_service():
    return OrchestrationService()

router = APIRouter(prefix="/api/v1", tags=["orchestration"])

# SECURITY: Admin API Keys for orchestration operations
ORCHESTRATION_ADMIN_KEYS = set(os.getenv('ORCHESTRATION_ADMIN_KEYS', '').split(',')) if os.getenv('ORCHESTRATION_ADMIN_KEYS') else set()

async def verify_orchestration_admin(x_api_key: str = Header(None)):
    """SECURITY: Verify admin API key for orchestration operations."""
    if not ORCHESTRATION_ADMIN_KEYS:
        raise HTTPException(503, "Orchestration admin ops disabled: ORCHESTRATION_ADMIN_KEYS not configured")
    if not x_api_key or x_api_key not in ORCHESTRATION_ADMIN_KEYS:
        raise HTTPException(401, "Unauthorized: Orchestration admin access required")
    return True


@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentRequest,
    user_id: Optional[str] = None,
    service: OrchestrationService = Depends(get_orchestration_service),
    _admin: bool = Depends(verify_orchestration_admin)
):
    """Generate content using 4-layer pipeline. REQUIRES ADMIN API KEY (prevents DOS/cost attacks)."""
    return await service.generate_content(request, user_id=user_id)


@router.post("/coordinate-battle")
async def coordinate_battle(
    monsters: list,
    player: dict,
    service: OrchestrationService = Depends(get_orchestration_service),
    _admin: bool = Depends(verify_orchestration_admin)
):
    """Coordinate battle with multiple NPCs. REQUIRES ADMIN API KEY."""
    return await service.coordinate_battle(monsters, player)

