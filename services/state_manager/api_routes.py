"""
API Routes - RESTful endpoints for State Management Service.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from schemas.validation import GameStateCreate, GameStateResponse, GameStateUpdate
from .state_operations import ConflictResolutionError, StateOperations

router = APIRouter(prefix="/api/v1/state", tags=["state"])
state_ops = StateOperations()


class GameStateCreateRequest(GameStateCreate):
    """Request schema for creating game state."""
    pass


class GameStateUpdateRequest(GameStateUpdate):
    """Request schema for updating game state."""
    pass


class ConflictErrorResponse(BaseModel):
    """Error response for conflict errors."""
    error: str
    detail: str
    state_id: str
    expected_version: Optional[int] = None


@router.post("/game-states", response_model=GameStateResponse, status_code=status.HTTP_201_CREATED)
async def create_game_state(request: GameStateCreateRequest):
    """
    Create a new game state.
    
    Returns:
        Created game state with 201 status code
    """
    try:
        state = await state_ops.create_game_state(
            player_id=request.player_id,
            current_world=request.current_world,
            location=request.location,
            position=request.position,
            active_quests=request.active_quests,
            session_data=request.session_data,
        )
        return state
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create game state: {str(e)}"
        )


@router.get("/game-states/{state_id}", response_model=GameStateResponse)
async def get_game_state(state_id: UUID):
    """
    Get game state by ID.
    
    Args:
        state_id: Game state UUID
    
    Returns:
        Game state or 404 if not found
    """
    state = await state_ops.get_game_state(state_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game state {state_id} not found"
        )
    return state


@router.get("/game-states/player/{player_id}", response_model=GameStateResponse)
async def get_game_state_by_player(player_id: UUID, active_only: bool = True):
    """
    Get active game state for a player.
    
    Args:
        player_id: Player UUID
        active_only: If True, only return active game states
    
    Returns:
        Game state or 404 if not found
    """
    state = await state_ops.get_game_state_by_player(player_id, active_only=active_only)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No game state found for player {player_id}"
        )
    return state


@router.put("/game-states/{state_id}", response_model=GameStateResponse)
async def update_game_state(state_id: UUID, request: GameStateUpdateRequest, expected_version: int):
    """
    Update game state with optimistic locking.
    
    Args:
        state_id: Game state UUID
        request: Update request body
        expected_version: Expected version number for optimistic locking
    
    Returns:
        Updated game state
    
    Raises:
        409 Conflict: If version mismatch (optimistic locking conflict)
    """
    try:
        state = await state_ops.update_game_state(
            state_id=state_id,
            expected_version=expected_version,
            current_world=request.current_world,
            location=request.location,
            position=request.position,
            active_quests=request.active_quests,
            session_data=request.session_data,
            is_active=request.is_active,
        )
        return state
    except ConflictResolutionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update game state: {str(e)}"
        )


@router.delete("/game-states/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game_state(state_id: UUID):
    """
    Delete game state (soft delete).
    
    Args:
        state_id: Game state UUID
    
    Returns:
        204 No Content on success
    """
    try:
        await state_ops.delete_game_state(state_id)
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete game state: {str(e)}"
        )


@router.get("/cache/hit-rate")
async def get_cache_hit_rate():
    """
    Get current cache hit rate statistics.
    
    Returns:
        Cache hit rate percentage and stats
    """
    hit_rate = state_ops.cache.get_hit_rate()
    tracker = state_ops.cache.hit_rate_tracker
    
    return {
        "hit_rate_percent": hit_rate,
        "hits": tracker.hits,
        "misses": tracker.misses,
        "total_requests": tracker.total_requests,
    }


@router.post("/cache/reset-stats")
async def reset_cache_stats():
    """
    Reset cache hit/miss statistics.
    
    Returns:
        Confirmation message
    """
    state_ops.cache.reset_stats()
    return {"message": "Cache statistics reset"}

