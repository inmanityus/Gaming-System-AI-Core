"""
Ethelred Content Validator – Skeleton Implementation
====================================================

Provides initial, production-intent skeletons for:
- TextContentClassifier
- VisionContentClassifier
- AudioContentClassifier
- ContentContextCrossChecker
- ContentViolationEngine

The classifiers intentionally use extremely simple heuristics for now –
their purpose in this milestone is to exercise contracts and end-to-end
flows, not to provide final moderation quality.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from services.settings.content_schemas import SessionContentPolicySnapshot

from .content_models import ContentObservation, ContentViolationEvent


class TextContentClassifier:
    """
    Extremely small, real implementation for text content classification.

    This is a placeholder that can later be replaced with model-backed
    classifiers. For now, it performs simple keyword checks to emit a
    plausible category_scores mapping.
    """

    async def classify_text(
        self,
        session_id: UUID,
        text: str,
        *,
        scene_id: Optional[str] = None,
        player_id: Optional[UUID] = None,
        content_ids: Optional[List[str]] = None,
    ) -> ContentObservation:
        text_lower = text.lower()

        scores: Dict[str, int] = {}

        # Very coarse keyword-based heuristics – good enough for skeleton tests
        if any(word in text_lower for word in ["blood", "gore", "dismembered"]):
            scores["violence_gore"] = 3
        if any(word in text_lower for word in ["fuck", "shit", "bastard"]):
            scores["language_profanity"] = 3
        if any(word in text_lower for word in ["scream", "terrifying", "unnerving"]):
            scores["horror_intensity"] = 2

        return ContentObservation(
            session_id=session_id,
            scene_id=scene_id,
            player_id=player_id,
            content_ids=content_ids or [],
            category_scores=scores,
            modality="text",
        )


class VisionContentClassifier:
    """
    Stub classifier that will ultimately consume 4D Vision QA outputs.

    For this milestone, it simply echoes the supplied category_scores.
    """

    async def classify_vision(
        self,
        session_id: UUID,
        scene_id: str,
        *,
        player_id: Optional[UUID] = None,
        inferred_scores: Optional[Dict[str, int]] = None,
        content_ids: Optional[List[str]] = None,
    ) -> ContentObservation:
        return ContentObservation(
            session_id=session_id,
            scene_id=scene_id,
            player_id=player_id,
            content_ids=content_ids or [],
            category_scores=inferred_scores or {},
            modality="vision",
        )


class AudioContentClassifier:
    """
    Stub classifier that will ultimately consume Audio QA metrics.

    For this milestone, it simply echoes the supplied category_scores.
    """

    async def classify_audio(
        self,
        session_id: UUID,
        scene_id: str,
        *,
        player_id: Optional[UUID] = None,
        inferred_scores: Optional[Dict[str, int]] = None,
        content_ids: Optional[List[str]] = None,
    ) -> ContentObservation:
        return ContentObservation(
            session_id=session_id,
            scene_id=scene_id,
            player_id=player_id,
            content_ids=content_ids or [],
            category_scores=inferred_scores or {},
            modality="audio",
        )


class ContentContextCrossChecker:
    """
    Fuse modality-specific observations into a single fused view and
    detect simple cross-modal inconsistencies.
    """

    async def fuse_observations(
        self,
        observations: List[ContentObservation],
    ) -> ContentObservation:
        if not observations:
            raise ValueError("At least one observation is required to fuse context")

        # Ensure we are not accidentally fusing cross-session or cross-player data.
        session_ids = {obs.session_id for obs in observations}
        if len(session_ids) != 1:
            raise ValueError("All observations must share the same session_id")

        player_ids = {obs.player_id for obs in observations if obs.player_id is not None}
        if player_ids and len(player_ids) != 1:
            raise ValueError("All observations must share the same player_id when set")

        base = observations[0]
        fused_scores: Dict[str, int] = {}

        for obs in observations:
            for category, level in obs.category_scores.items():
                prev = fused_scores.get(category, 0)
                fused_scores[category] = max(prev, int(level))

        return ContentObservation(
            session_id=base.session_id,
            scene_id=base.scene_id,
            player_id=base.player_id,
            content_ids=[
                cid for obs in observations for cid in (obs.content_ids or [])
            ],
            category_scores=fused_scores,
            modality="fused",
        )


class ContentViolationEngine:
    """
    Compare fused content observations against a session policy snapshot.

    This is the core of Milestone 2 – it implements real comparison logic
    that will remain valid even as classifiers become more sophisticated.
    """

    async def evaluate(
        self,
        observation: ContentObservation,
        policy: SessionContentPolicySnapshot,
        *,
        content_type: str = "unknown",
        detected_by: str = "ethelred_content_validator",
        evidence_refs: Optional[List[str]] = None,
    ) -> List[ContentViolationEvent]:
        violations: List[ContentViolationEvent] = []

        for category, observed in observation.category_scores.items():
            allowed = policy.effective_levels.get(category)
            if allowed is None:
                # Unknown to the policy – skip for now
                continue

            try:
                raw_observed = int(observed)
                raw_allowed = int(allowed)
            except (TypeError, ValueError):
                # If values are not numeric, skip; schema should prevent this
                continue

            # Clamp to the 0–4 scale required by DB constraints while still
            # allowing “over the top” observations to be treated as violations.
            observed_level = max(0, min(4, raw_observed))
            allowed_level = max(0, min(4, raw_allowed))

            if observed_level <= allowed_level:
                continue

            diff = observed_level - allowed_level
            if diff >= 3:
                severity = "critical"
            elif diff == 2:
                severity = "high"
            else:
                severity = "medium"

            recommended = "review_required"
            if severity in ("high", "critical"):
                recommended = "substitute"

            violations.append(
                ContentViolationEvent(
                    session_id=observation.session_id,
                    player_id=observation.player_id or policy.player_id,
                    scene_id=observation.scene_id,
                    content_type=content_type,
                    category=category,
                    expected_level=allowed_level,
                    observed_level=observed_level,
                    severity=severity,
                    detected_by=detected_by,
                    evidence_refs=evidence_refs or [],
                    recommended_action=recommended,
                    flagged_excerpt=None,
                )
            )

        return violations


