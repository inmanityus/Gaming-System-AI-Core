"""
Data models for Orchestration Service.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from uuid import UUID


class ContentRequest(BaseModel):
    """Request for content generation."""
    seed: Optional[int] = None
    monster_type: Optional[str] = None
    biome: Optional[str] = None
    size: Optional[int] = None
    dimensions: Optional[Dict[str, int]] = None
    activate_npcs: bool = False
    requires_coordination: bool = False
    player_context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class FoundationOutput(BaseModel):
    """Output from Layer 1: Foundation."""
    monster: Optional[Dict[str, Any]] = None
    terrain: Optional[Dict[str, Any]] = None
    room: Optional[Dict[str, Any]] = None


class ContentResponse(BaseModel):
    """Complete content generation response."""
    foundation: FoundationOutput
    customized: Optional[Dict[str, Any]] = None
    interactions: Optional[List[Dict[str, Any]]] = None
    orchestration: Optional[Dict[str, Any]] = None


class BattleExecutionPlan(BaseModel):
    """Plan for battle execution."""
    monster_actions: List[Dict[str, Any]]
    coordinator_plan: Dict[str, Any]

