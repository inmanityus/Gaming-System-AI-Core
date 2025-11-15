"""
Story Memory API routes.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .story_schemas import StorySnapshot, DriftMetrics, StoryDecision
from .story_state_manager import StoryStateManager
from .drift_detector import DriftDetector
from .snapshot_cache import SnapshotCache


router = APIRouter(prefix="/story", tags=["story_memory"])


class DriftCheckRequest(BaseModel):
    """Request to check for narrative drift."""
    recent_window_hours: int = 3
    check_types: list[str] = ["quest_allocation", "time_allocation", "theme_consistency"]


class DriftCheckResponse(BaseModel):
    """Response from drift check."""
    drift_detected: bool
    drift_score: Optional[float] = None
    severity: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    recommended_remediation: Optional[str] = None
    canonical_theme_reminder: Optional[str] = None


# Dependencies would be injected in the actual service
story_manager: Optional[StoryStateManager] = None
drift_detector: Optional[DriftDetector] = None
snapshot_cache: Optional[SnapshotCache] = None


def get_story_manager() -> StoryStateManager:
    """Get story manager instance."""
    if not story_manager:
        raise HTTPException(status_code=500, detail="Story manager not initialized")
    return story_manager


def get_drift_detector() -> DriftDetector:
    """Get drift detector instance."""
    if not drift_detector:
        raise HTTPException(status_code=500, detail="Drift detector not initialized")
    return drift_detector


def get_snapshot_cache() -> SnapshotCache:
    """Get snapshot cache instance."""
    if not snapshot_cache:
        raise HTTPException(status_code=500, detail="Snapshot cache not initialized")
    return snapshot_cache


@router.get("/{player_id}/snapshot", response_model=StorySnapshot)
async def get_story_snapshot(
    player_id: UUID,
    force_refresh: bool = False,
    cache: SnapshotCache = Depends(get_snapshot_cache)
):
    """
    Get complete story snapshot for a player.
    
    Used by Story Teller and Ethelred to get current narrative context.
    Optimized for < 50ms P99 latency via multi-tier caching.
    """
    try:
        snapshot = await cache.get_snapshot(player_id, force_refresh=force_refresh)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Player not found")
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get snapshot: {str(e)}")


@router.post("/{player_id}/drift-check", response_model=DriftCheckResponse)
async def check_drift(
    player_id: UUID,
    request: DriftCheckRequest,
    drift_det: DriftDetector = Depends(get_drift_detector)
):
    """
    Check for narrative drift in recent gameplay.
    
    Returns drift metrics and recommendations if drift is detected.
    """
    try:
        metrics = await drift_det.check_drift(
            player_id=player_id,
            window_hours=request.recent_window_hours,
            force=True  # Always run fresh check via API
        )
        
        if not metrics:
            return DriftCheckResponse(
                drift_detected=False,
                canonical_theme_reminder="Core loop: Kill → Harvest → Negotiate → Get Drugs → Build Empire"
            )
        
        return DriftCheckResponse(
            drift_detected=True,
            drift_score=metrics.drift_score,
            severity=metrics.severity.value,
            details={
                'quest_allocation': metrics.quest_allocation,
                'time_allocation': metrics.time_allocation,
                'theme_consistency': metrics.theme_consistency
            },
            recommended_remediation=metrics.recommended_correction,
            canonical_theme_reminder=metrics.canonical_reminder
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check drift: {str(e)}")


@router.get("/{player_id}/arc-progress")
async def get_arc_progress(
    player_id: UUID,
    arc_id: Optional[str] = None,
    story_mgr: StoryStateManager = Depends(get_story_manager)
):
    """
    Get arc progress for a player.
    
    If arc_id is provided, returns progress for that specific arc.
    Otherwise returns all arc progress.
    """
    try:
        snapshot = await story_mgr.get_story_snapshot(player_id)
        
        if arc_id:
            # Find specific arc
            for arc in snapshot.arc_progress:
                if arc.arc_id == arc_id:
                    return arc
            raise HTTPException(status_code=404, detail=f"Arc {arc_id} not found")
        else:
            # Return all arcs
            return snapshot.arc_progress
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get arc progress: {str(e)}")


@router.get("/{player_id}/relationships/{entity_id}")
async def get_relationship(
    player_id: UUID,
    entity_id: str,
    story_mgr: StoryStateManager = Depends(get_story_manager)
):
    """Get relationship status with a specific NPC or faction."""
    try:
        snapshot = await story_mgr.get_story_snapshot(player_id)
        
        for rel in snapshot.relationships:
            if rel.entity_id == entity_id:
                return rel
                
        raise HTTPException(status_code=404, detail=f"No relationship found with {entity_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationship: {str(e)}")


@router.get("/{player_id}/dark-world-standings")
async def get_dark_world_standings(
    player_id: UUID,
    story_mgr: StoryStateManager = Depends(get_story_manager)
):
    """Get standings with all Dark World families."""
    try:
        snapshot = await story_mgr.get_story_snapshot(player_id)
        return snapshot.dark_world_standings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get standings: {str(e)}")


@router.get("/{player_id}/moral-alignment")
async def get_moral_alignment(
    player_id: UUID,
    cache: SnapshotCache = Depends(get_snapshot_cache)
):
    """Get player's surgeon-butcher moral alignment."""
    try:
        snapshot = await cache.get_snapshot(player_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Player not found")
        
        score = snapshot.surgeon_butcher_score
        
        # Interpret the score
        if score <= -0.7:
            alignment = "Full Surgeon"
            description = "Methodical, clinical, preserving humanity"
        elif score <= -0.3:
            alignment = "Leaning Surgeon"
            description = "Careful harvesting with moral considerations"
        elif score >= 0.7:
            alignment = "Full Butcher"
            description = "Brutal efficiency, humanity discarded"
        elif score >= 0.3:
            alignment = "Leaning Butcher"
            description = "Pragmatic harvesting, morality secondary"
        else:
            alignment = "Balanced"
            description = "Walking the line between mercy and brutality"
        
        # Calculate moral trend
        recent_decisions = snapshot.recent_decisions[:5]
        total_weight = sum(d.moral_weight for d in recent_decisions) if recent_decisions else 0
        
        if total_weight > 0.5:
            trend = "becoming_more_butcher"
        elif total_weight < -0.5:
            trend = "becoming_more_surgeon"
        else:
            trend = "stable"
        
        return {
            "score": score,
            "alignment": alignment,
            "description": description,
            "recent_trend": trend
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get moral alignment: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats(
    cache: SnapshotCache = Depends(get_snapshot_cache)
):
    """Get snapshot cache statistics."""
    return cache.get_stats()


@router.post("/cache/warm")
async def warm_cache(
    player_ids: list[UUID],
    cache: SnapshotCache = Depends(get_snapshot_cache)
):
    """Pre-warm cache for specified players."""
    await cache.warm_cache(player_ids)
    return {"status": "Cache warming initiated", "player_count": len(player_ids)}
