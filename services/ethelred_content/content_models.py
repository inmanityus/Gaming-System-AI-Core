"""
Content Governance Event Models
===============================

Lightweight Pydantic models for:
- Content observations from text/vision/audio/fused classifiers
- Content violation events produced by the violation engine

These models mirror the contracts described in:
- ETHELRED-CONTENT-GOVERNANCE-SOLUTIONS.md (§3)
- CONTENT-GOVERNANCE-REQUIREMENTS.md (§4–5)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContentObservation(BaseModel):
    """
    Normalized observation event for a single scene/segment.

    This is modality-specific (text, vision, audio) or fused.
    """

    session_id: UUID
    scene_id: Optional[str] = None
    player_id: Optional[UUID] = None

    content_ids: List[str] = Field(
        default_factory=list,
        description="Identifiers for lines/assets/scenes involved in this observation.",
    )

    # Per-category content intensity scores (0–4) using canonical keys
    category_scores: Dict[str, int] = Field(default_factory=dict)

    modality: str = Field(
        ...,
        description="text | vision | audio | fused",
    )

    trace_id: Optional[str] = None
    build_id: Optional[str] = None


class ContentViolationEvent(BaseModel):
    """
    Runtime content violation produced when observed content exceeds policy.
    """

    violation_id: UUID = Field(default_factory=uuid4)

    session_id: UUID
    player_id: Optional[UUID] = None

    scene_id: Optional[str] = None
    content_type: str = Field(
        ...,
        description="story_output | npc_dialogue | visual_scene | audio_segment, etc.",
    )

    category: str
    expected_level: int
    observed_level: int

    severity: str = Field(
        ...,
        description="low | medium | high | critical",
    )

    detected_by: str = Field(
        ...,
        description="Subsystem that raised the violation (e.g. ethelred_content_validator).",
    )

    evidence_refs: List[str] = Field(default_factory=list)

    recommended_action: Optional[str] = Field(
        default=None,
        description="substitute | log_only | review_required, etc.",
    )

    # Optional human-readable excerpt or summary to aid debugging/audit
    flagged_excerpt: Optional[str] = None


