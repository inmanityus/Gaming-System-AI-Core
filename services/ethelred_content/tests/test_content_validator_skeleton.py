"""
Tests for Ethelred Content Validator skeleton.

These tests verify that:
- content observations can be fused across modalities, and
- the violation engine correctly flags over-level content compared to a
  session policy snapshot.
"""

from uuid import uuid4

import pytest

from services.ethelred_content.content_models import ContentObservation
from services.ethelred_content.content_validator import (
    ContentContextCrossChecker,
    ContentViolationEngine,
)
from services.settings.content_schemas import SessionContentPolicySnapshot


@pytest.mark.asyncio
async def test_cross_checker_fuses_max_levels_per_category():
    session_id = uuid4()

    obs_text = ContentObservation(
        session_id=session_id,
        scene_id="scene-1",
        content_ids=["line-1"],
        category_scores={"violence_gore": 2, "horror_intensity": 1},
        modality="text",
    )
    obs_vision = ContentObservation(
        session_id=session_id,
        scene_id="scene-1",
        content_ids=["asset-1"],
        category_scores={"violence_gore": 4},
        modality="vision",
    )

    cross_checker = ContentContextCrossChecker()
    fused = await cross_checker.fuse_observations([obs_text, obs_vision])

    assert fused.modality == "fused"
    # Highest level wins
    assert fused.category_scores["violence_gore"] == 4
    # Category only present in one observation is preserved
    assert fused.category_scores["horror_intensity"] == 1
    # Content IDs are union of sources
    assert set(fused.content_ids) == {"line-1", "asset-1"}


@pytest.mark.asyncio
async def test_violation_engine_flags_over_level_content():
    session_id = uuid4()
    player_id = uuid4()

    observation = ContentObservation(
        session_id=session_id,
        scene_id="scene-1",
        player_id=player_id,
        content_ids=["line-99"],
        category_scores={"violence_gore": 4, "horror_intensity": 2},
        modality="fused",
    )

    policy = SessionContentPolicySnapshot(
        session_id=session_id,
        player_id=player_id,
        policy_version=1,
        base_profile_id=uuid4(),
        base_profile_name="TeenSafe",
        effective_levels={"violence_gore": 2, "horror_intensity": 2},
        overrides={},
        custom_rules={},
    )

    engine = ContentViolationEngine()
    violations = await engine.evaluate(
        observation,
        policy,
        content_type="story_output",
        evidence_refs=["redalert://media/example"],
    )

    # One violation for violence_gore; horror_intensity is at allowed level
    assert len(violations) == 1
    v = violations[0]
    assert v.category == "violence_gore"
    assert v.expected_level == 2
    assert v.observed_level == 4
    assert v.severity in ("high", "critical")
    assert v.detected_by == "ethelred_content_validator"
    assert v.content_type == "story_output"
    assert v.session_id == session_id
    assert v.player_id == player_id
    assert v.evidence_refs == ["redalert://media/example"]


