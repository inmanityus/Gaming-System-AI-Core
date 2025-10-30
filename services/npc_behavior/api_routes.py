"""
API Routes - FastAPI routes for NPC Behavior Service.
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .behavior_engine import BehaviorEngine
from .personality_system import PersonalitySystem
from .goal_manager import GoalManager
from .interaction_router import InteractionRouter


# Pydantic models
class InteractionIntent(BaseModel):
    type: str
    source_id: UUID
    target_id: UUID
    data: Dict[str, Any] = {}


# Router
router = APIRouter(prefix="/npc", tags=["NPC Behavior"])


# Dependencies
def get_behavior_engine() -> BehaviorEngine:
    return BehaviorEngine()


def get_personality_system() -> PersonalitySystem:
    return PersonalitySystem()


def get_goal_manager() -> GoalManager:
    return GoalManager()


def get_interaction_router() -> InteractionRouter:
    return InteractionRouter()


# Routes
@router.post("/{npc_id}/update")
async def update_npc(
    npc_id: UUID,
    engine: BehaviorEngine = Depends(get_behavior_engine),
):
    """Update NPC behavior."""
    try:
        result = await engine.update_npc(npc_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update")
async def batch_update_npcs(
    npc_ids: List[UUID],
    max_concurrent: int = 10,
    engine: BehaviorEngine = Depends(get_behavior_engine),
):
    """Batch update multiple NPCs."""
    try:
        results = await engine.batch_update_npcs(npc_ids, max_concurrent)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interaction/route")
async def route_interaction(
    intent: InteractionIntent,
    router: InteractionRouter = Depends(get_interaction_router),
):
    """Route an interaction intent."""
    try:
        result = router.route(intent.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "npc_behavior"}
