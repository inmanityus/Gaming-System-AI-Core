"""
Quest System Service - API Routes.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from .quest_generator import QuestGenerationEngine
from .quest_manager import QuestManager
from .objective_manager import ObjectiveManager
from .reward_manager import RewardManager


router = APIRouter(prefix="/quests", tags=["quests"])


# Pydantic models for request/response
class QuestGenerationRequest(BaseModel):
    player_id: str
    quest_type: str = "side"
    context: Optional[Dict[str, Any]] = None
    quest_giver_npc_id: Optional[str] = None
    world_state_id: Optional[str] = None


class QuestCreateRequest(BaseModel):
    quest_data: Dict[str, Any]


class ObjectiveUpdateRequest(BaseModel):
    objective_id: str
    progress: int
    completed: bool = False


class ObjectiveCompleteRequest(BaseModel):
    objective_id: str


class RewardCompleteRequest(BaseModel):
    quest_id: str
    bonus_multiplier: float = 1.0


# Dependency injection
def get_quest_generator() -> QuestGenerationEngine:
    """Get quest generator instance."""
    return QuestGenerationEngine()


def get_quest_manager() -> QuestManager:
    """Get quest manager instance."""
    return QuestManager()


def get_objective_manager() -> ObjectiveManager:
    """Get objective manager instance."""
    return ObjectiveManager()


def get_reward_manager() -> RewardManager:
    """Get reward manager instance."""
    return RewardManager()


@router.post("/generate", response_model=Dict[str, Any])
async def generate_quest(
    request: QuestGenerationRequest,
    generator: QuestGenerationEngine = Depends(get_quest_generator)
) -> Dict[str, Any]:
    """
    Generate a new quest using AI.
    """
    try:
        quest = await generator.generate_quest(
            player_id=UUID(request.player_id),
            quest_type=request.quest_type,
            context=request.context,
            quest_giver_npc_id=UUID(request.quest_giver_npc_id) if request.quest_giver_npc_id else None,
            world_state_id=UUID(request.world_state_id) if request.world_state_id else None,
        )
        return quest
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quest: {str(e)}"
        )


@router.post("/create", response_model=Dict[str, Any])
async def create_quest(
    request: QuestCreateRequest,
    manager: QuestManager = Depends(get_quest_manager)
) -> Dict[str, Any]:
    """
    Create a quest in the database.
    """
    try:
        quest = await manager.create_quest(request.quest_data)
        return quest
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quest: {str(e)}"
        )


@router.get("/{quest_id}", response_model=Dict[str, Any])
async def get_quest(
    quest_id: str,
    manager: QuestManager = Depends(get_quest_manager)
) -> Dict[str, Any]:
    """
    Get a quest by ID.
    """
    try:
        quest = await manager.get_quest(UUID(quest_id))
        if not quest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quest not found: {quest_id}"
            )
        return quest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quest: {str(e)}"
        )


@router.get("/player/{player_id}", response_model=List[Dict[str, Any]])
async def get_player_quests(
    player_id: str,
    status: Optional[str] = None,
    manager: QuestManager = Depends(get_quest_manager)
) -> List[Dict[str, Any]]:
    """
    Get all quests for a player.
    """
    try:
        quests = await manager.get_player_quests(UUID(player_id), status)
        return quests
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player quests: {str(e)}"
        )


@router.put("/{quest_id}/status", response_model=Dict[str, Any])
async def update_quest_status(
    quest_id: str,
    status: str,
    manager: QuestManager = Depends(get_quest_manager)
) -> Dict[str, Any]:
    """
    Update quest status.
    """
    try:
        if status not in ["active", "in_progress", "completed", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
        quest = await manager.update_quest_status(UUID(quest_id), status)
        return quest
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update quest status: {str(e)}"
        )


@router.delete("/{quest_id}")
async def delete_quest(
    quest_id: str,
    manager: QuestManager = Depends(get_quest_manager)
) -> Dict[str, Any]:
    """
    Delete a quest.
    """
    try:
        deleted = await manager.delete_quest(UUID(quest_id))
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quest not found: {quest_id}"
            )
        return {"success": True, "message": f"Quest {quest_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete quest: {str(e)}"
        )


@router.get("/{quest_id}/objectives", response_model=List[Dict[str, Any]])
async def get_quest_objectives(
    quest_id: str,
    objective_manager: ObjectiveManager = Depends(get_objective_manager)
) -> List[Dict[str, Any]]:
    """
    Get all objectives for a quest.
    """
    try:
        objectives = await objective_manager.get_objectives(UUID(quest_id))
        return objectives
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get objectives: {str(e)}"
        )


@router.put("/{quest_id}/objectives/{objective_id}", response_model=Dict[str, Any])
async def update_objective_progress(
    quest_id: str,
    objective_id: str,
    request: ObjectiveUpdateRequest,
    objective_manager: ObjectiveManager = Depends(get_objective_manager)
) -> Dict[str, Any]:
    """
    Update objective progress.
    """
    try:
        quest = await objective_manager.update_objective_progress(
            UUID(quest_id),
            objective_id,
            request.progress,
            request.completed
        )
        return quest
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update objective: {str(e)}"
        )


@router.post("/{quest_id}/objectives/{objective_id}/complete", response_model=Dict[str, Any])
async def complete_objective(
    quest_id: str,
    objective_id: str,
    objective_manager: ObjectiveManager = Depends(get_objective_manager)
) -> Dict[str, Any]:
    """
    Mark an objective as completed.
    """
    try:
        quest = await objective_manager.complete_objective(UUID(quest_id), objective_id)
        return quest
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete objective: {str(e)}"
        )


@router.post("/{quest_id}/rewards/complete", response_model=Dict[str, Any])
async def complete_quest_rewards(
    quest_id: str,
    request: RewardCompleteRequest,
    reward_manager: RewardManager = Depends(get_reward_manager),
    quest_manager: QuestManager = Depends(get_quest_manager)
) -> Dict[str, Any]:
    """
    Calculate and distribute quest completion rewards.
    """
    try:
        # Get quest to find player_id
        quest = await quest_manager.get_quest(UUID(quest_id))
        if not quest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quest not found: {quest_id}"
            )
        
        player_id = UUID(quest["player_id"])
        
        # Distribute rewards
        result = await reward_manager.complete_quest_rewards(
            UUID(quest_id),
            player_id,
            request.bonus_multiplier
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to distribute rewards: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    """
    return {
        "service": "quest_system",
        "status": "healthy",
        "version": "0.1.0"
    }

