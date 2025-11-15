"""
Tests for Content Governance schemas and helpers.

These tests focus on pure logic (no database access) so they can run in
isolation while still providing real validation of category handling and
effective policy computation.
"""

from uuid import uuid4

import pytest

from services.settings.content_schemas import (
    CategoryLevels,
    SessionContentPolicySnapshot,
    compute_effective_levels,
)


def test_category_levels_round_trip_mapping():
    """CategoryLevels.to_mapping and from_mapping should be inverse-ish."""
    levels = CategoryLevels(
        violence_gore=3,
        sexual_content_nudity=1,
        language_profanity=2,
        horror_intensity=4,
        drugs_substances=0,
        sensitive_themes=2,
        moral_complexity=3,
    )

    as_map = levels.to_mapping()
    reconstructed = CategoryLevels.from_mapping(as_map)

    assert reconstructed == levels


def test_compute_effective_levels_applies_overrides():
    """Overrides should replace only matching categories."""
    base = CategoryLevels(
        violence_gore=2,
        sexual_content_nudity=0,
        language_profanity=1,
        horror_intensity=3,
        drugs_substances=0,
        sensitive_themes=1,
        moral_complexity=2,
    )

    overrides = {
        "violence_gore": 4,
        "language_profanity": 0,
        # Unknown category should be ignored
        "nonexistent_category": 5,
    }

    effective = compute_effective_levels(base, overrides)

    assert effective.violence_gore == 4
    assert effective.language_profanity == 0
    # Unchanged categories
    assert effective.horror_intensity == base.horror_intensity
    assert effective.sensitive_themes == base.sensitive_themes


@pytest.mark.parametrize(
    "override_value,expected",
    [
        ("3", 3),
        (3.9, 3),
        ("not-an-int", 0),
    ],
)
def test_compute_effective_levels_coerces_or_ignores_invalid_values(
    override_value, expected
):
    """compute_effective_levels should be robust against odd override values."""
    base = CategoryLevels()
    overrides = {"violence_gore": override_value}

    effective = compute_effective_levels(base, overrides)

    assert effective.violence_gore == expected


def test_session_content_policy_snapshot_basic_shape():
    """Ensure SessionContentPolicySnapshot accepts a realistic payload."""
    session_id = uuid4()
    player_id = uuid4()

    snapshot = SessionContentPolicySnapshot(
        session_id=session_id,
        player_id=player_id,
        policy_version=1,
        base_profile_id=uuid4(),
        base_profile_name="MatureFullExperience",
        effective_levels={
            "violence_gore": 4,
            "horror_intensity": 4,
            "language_profanity": 3,
        },
        overrides={"violence_gore": 4},
        custom_rules={"skip_torture_scenes": True},
    )

    assert snapshot.session_id == session_id
    assert snapshot.player_id == player_id
    assert snapshot.effective_levels["violence_gore"] == 4
    assert snapshot.overrides["violence_gore"] == 4
    assert snapshot.custom_rules["skip_torture_scenes"] is True


