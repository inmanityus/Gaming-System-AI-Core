"""
Content Governance Schemas for Settings Service
==============================================

Defines typed models for:
- Content category level scales
- Content profiles (system + custom)
- Per-player content policies
- Per-session content policy snapshots

These models are intentionally implementation-aware but transport-agnostic.
They can be used by HTTP, NATS, or background workers without leaking DB details.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Canonical content categories from CONTENT-GOVERNANCE-REQUIREMENTS.md
CONTENT_CATEGORIES = (
    "violence_gore",
    "sexual_content_nudity",
    "language_profanity",
    "horror_intensity",
    "drugs_substances",
    "sensitive_themes",
    "moral_complexity",
)


class CategoryLevels(BaseModel):
    """
    Per‑category intensity levels for a content profile or snapshot.

    The concrete semantics of each level are defined in design docs; here we
    only enforce the allowed numeric range.
    """

    violence_gore: int = Field(0, ge=0, le=4)
    sexual_content_nudity: int = Field(0, ge=0, le=4)
    language_profanity: int = Field(0, ge=0, le=4)
    horror_intensity: int = Field(0, ge=0, le=4)
    drugs_substances: int = Field(0, ge=0, le=4)
    sensitive_themes: int = Field(0, ge=0, le=4)
    moral_complexity: int = Field(0, ge=0, le=4)

    def to_mapping(self) -> Dict[str, int]:
        """Return a simple dict keyed by canonical category names."""
        return {
            "violence_gore": self.violence_gore,
            "sexual_content_nudity": self.sexual_content_nudity,
            "language_profanity": self.language_profanity,
            "horror_intensity": self.horror_intensity,
            "drugs_substances": self.drugs_substances,
            "sensitive_themes": self.sensitive_themes,
            "moral_complexity": self.moral_complexity,
        }

    @classmethod
    def from_mapping(cls, levels: Dict[str, Any]) -> "CategoryLevels":
        """
        Build CategoryLevels from a loose mapping.

        Missing categories default to 0; extra keys are ignored. This makes it
        safe to hydrate from JSONB columns that may omit newer categories.
        """
        data: Dict[str, int] = {}
        for key in CONTENT_CATEGORIES:
            raw = levels.get(key, 0)
            try:
                data[key] = int(raw)
            except (TypeError, ValueError):
                data[key] = 0
        return cls(**data)


class ContentProfile(BaseModel):
    """
    System or custom content profile definition.

    This mirrors the `content_levels` table shape at a logical level.
    """

    id: Optional[UUID] = None
    name: str
    description: Optional[str] = ""

    levels: CategoryLevels

    # Arbitrary per-theme switches for sensitive topics
    sensitive_themes_flags: Dict[str, bool] = Field(default_factory=dict)

    is_system_default: bool = False
    target_age_rating: Optional[str] = None


class PlayerContentPolicy(BaseModel):
    """
    Effective content policy configuration for a single player.

    This corresponds to `player_content_profiles` plus resolved overrides.
    """

    player_id: UUID
    base_profile_id: Optional[UUID] = None
    base_profile_name: Optional[str] = None

    # Per-category overrides (category → level)
    overrides: Dict[str, int] = Field(default_factory=dict)

    # Arbitrary JSON rules such as "skip_torture_scenes"
    custom_rules: Dict[str, Any] = Field(default_factory=dict)


class SessionContentPolicySnapshot(BaseModel):
    """
    Frozen view of the content policy used for a specific session.

    This is what downstream systems (Guardrails, Ethelred) should rely on.
    """

    session_id: UUID
    player_id: UUID

    policy_version: int = 1

    base_profile_id: Optional[UUID] = None
    base_profile_name: Optional[str] = None

    # Fully-resolved effective levels for this session (after overrides)
    effective_levels: Dict[str, int]

    overrides: Dict[str, int] = Field(default_factory=dict)
    custom_rules: Dict[str, Any] = Field(default_factory=dict)


def compute_effective_levels(
    base: CategoryLevels,
    overrides: Optional[Dict[str, int]] = None,
) -> CategoryLevels:
    """
    Merge a base profile with per-category overrides into a new CategoryLevels.

    Invalid override keys are ignored; invalid values are clamped via model
    validation when CategoryLevels is constructed.
    """
    base_map = base.to_mapping()
    if overrides:
        for key, value in overrides.items():
            if key in base_map:
                try:
                    base_map[key] = int(value)
                except (TypeError, ValueError):
                    # Ignore non-numeric overrides – safety over failure
                    continue
    return CategoryLevels.from_mapping(base_map)


