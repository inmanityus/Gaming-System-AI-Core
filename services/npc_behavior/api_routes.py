"""
API Routes - FastAPI routes for NPC Behavior Service.
"""

import os
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from behavior_engine import BehaviorEngine
from personality_system import PersonalitySystem
from goal_manager import GoalManager
from interaction_router import InteractionRouter
from services.ai_integration.llm_client import LLMClient

# SECURITY: Admin API Keys for NPC operations
NPC_ADMIN_KEYS = set(os.getenv('NPC_ADMIN_KEYS', '').split(',')) if os.getenv('NPC_ADMIN_KEYS') else set()

async def verify_npc_admin(x_api_key: str = Header(None)):
    """SECURITY: Verify admin API key for NPC behavior operations."""
    if not NPC_ADMIN_KEYS:
        raise HTTPException(503, "NPC admin ops disabled: NPC_ADMIN_KEYS not configured")
    if not x_api_key or x_api_key not in NPC_ADMIN_KEYS:
        raise HTTPException(401, "Unauthorized: NPC admin access required")
    return True


# Pydantic models
class InteractionIntent(BaseModel):
    type: str
    source_id: UUID
    target_id: UUID
    data: Dict[str, Any] = {}


# Router
router = APIRouter(prefix="/npc", tags=["NPC Behavior"])


# Dependencies
_llm_client: LLMClient = None
_behavior_engine: BehaviorEngine = None

def get_llm_client() -> LLMClient:
    """Get or create LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

def get_behavior_engine() -> BehaviorEngine:
    """Get or create behavior engine with proxy architecture."""
    global _behavior_engine
    if _behavior_engine is None:
        llm_client = get_llm_client()
        _behavior_engine = BehaviorEngine(llm_client=llm_client)
    return _behavior_engine


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
    frame_time_ms: float = 3.33,
    game_state: Dict[str, Any] = None,
    engine: BehaviorEngine = Depends(get_behavior_engine),
    _admin: bool = Depends(verify_npc_admin)
):
    """Update NPC behavior using Behavioral Proxy architecture. REQUIRES ADMIN API KEY (prevents griefing)."""
    try:
        result = await engine.update_npc(npc_id, frame_time_ms, game_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update")
async def batch_update_npcs(
    npc_ids: List[UUID],
    max_concurrent: int = 10,
    engine: BehaviorEngine = Depends(get_behavior_engine),
    _admin: bool = Depends(verify_npc_admin)
):
    """Batch update multiple NPCs. REQUIRES ADMIN API KEY (prevents griefing)."""
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


@router.get("/proxy/performance")
async def get_proxy_performance(engine: BehaviorEngine = Depends(get_behavior_engine)):
    """Get Behavioral Proxy performance statistics."""
    try:
        stats = engine.proxy_manager.get_performance_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
