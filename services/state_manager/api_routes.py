"""
API Routes - RESTful endpoints for State Management Service.
"""

import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Header, Depends
from pydantic import BaseModel, Field

from .state_operations import ConflictResolutionError, StateOperations

# Pydantic models for game state
class GameStateCreate(BaseModel):
    """Schema for creating game state."""
    entity_id: str
    state_type: str
    state_data: dict

class GameStateUpdate(BaseModel):
    """Schema for updating game state."""
    state_data: dict
    version: Optional[int] = None

class GameStateResponse(BaseModel):
    """Schema for game state response."""
    id: UUID
    entity_id: str
    state_type: str
    state_data: dict
    version: int

router = APIRouter(prefix="/api/v1/state", tags=["state"])
state_ops = StateOperations()

# SECURITY: Admin API Keys for game state operations
STATE_ADMIN_KEYS = set(os.getenv('STATE_ADMIN_KEYS', '').split(',')) if os.getenv('STATE_ADMIN_KEYS') else set()

async def verify_state_admin(x_api_key: str = Header(None)):
    """
    SECURITY: Verify admin API key for game state operations.
    
    Required for: state CRUD operations (prevents cheating and data corruption).
    Without auth, players can modify ANY game state, enabling infinite cheating.
    """
    if not STATE_ADMIN_KEYS:
        raise HTTPException(
            status_code=503,
            detail="State operations disabled: STATE_ADMIN_KEYS not configured"
        )
    if not x_api_key or x_api_key not in STATE_ADMIN_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized: State admin access required")
    return True


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
async def create_game_state(
    request: GameStateCreateRequest,
    _admin: bool = Depends(verify_state_admin)  # SECURITY: Admin only
):
    """
    Create a new game state. REQUIRES ADMIN API KEY (prevents cheating).
    
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
async def update_game_state(
    state_id: UUID, 
    request: GameStateUpdateRequest, 
    expected_version: int,
    _admin: bool = Depends(verify_state_admin)  # SECURITY: Admin only - CHEATING PREVENTION
):
    """
    Update game state with optimistic locking. REQUIRES ADMIN API KEY (prevents cheating).
    
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
async def delete_game_state(
    state_id: UUID,
    _admin: bool = Depends(verify_state_admin)  # SECURITY: Admin only
):
    """
    Delete game state (soft delete). REQUIRES ADMIN API KEY (prevents data corruption).
    
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

