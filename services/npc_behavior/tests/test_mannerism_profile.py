"""
Tests for Mannerism & Movement Profile System.

Implements REQ-NPC-002: Mannerism & Movement Profile System.
"""

import pytest
from uuid import uuid4

from services.npc_behavior.mannerism_profile import (
    MannerismProfile,
    MannerismGenerator,
    MannerismManager,
    MovementStyle,
    GestureFrequency,
)


def test_profile_creation():
    """Test creating a mannerism profile."""
    npc_id = uuid4()
    profile = MannerismProfile(npc_id=npc_id)
    
    assert profile.npc_id == npc_id
    assert profile.movement_style == MovementStyle.NEUTRAL
    assert profile.walking_speed_multiplier == 1.0
    assert 0.0 <= profile.movement_confidence <= 1.0


def test_profile_float_validation():
    """Test float range validation."""
    npc_id = uuid4()
    
    # Valid 0.0-1.0 values
    profile = MannerismProfile(
        npc_id=npc_id,
        movement_confidence=0.5,
        gesture_intensity=0.7
    )
    assert profile.movement_confidence == 0.5
    assert profile.gesture_intensity == 0.7
    
    # Valid 0.5-1.5 values
    profile = MannerismProfile(
        npc_id=npc_id,
        walking_speed_multiplier=1.2,
        stride_length=0.8
    )
    assert profile.walking_speed_multiplier == 1.2
    assert profile.stride_length == 0.8
    
    # Invalid values should raise
    with pytest.raises(ValueError):
        MannerismProfile(npc_id=npc_id, movement_confidence=1.5)
    
    with pytest.raises(ValueError):
        MannerismProfile(npc_id=npc_id, walking_speed_multiplier=2.0)


def test_profile_to_dict():
    """Test converting profile to dictionary."""
    npc_id = uuid4()
    profile = MannerismProfile(npc_id=npc_id)
    
    data = profile.to_dict()
    
    assert data["npc_id"] == str(npc_id)
    assert data["movement_style"] == "neutral"
    assert isinstance(data["preferred_gestures"], list)
    # Should be copies
    assert data["preferred_gestures"] is not profile.preferred_gestures


def test_profile_from_dict():
    """Test creating profile from dictionary."""
    npc_id = uuid4()
    data = {
        "npc_id": str(npc_id),
        "movement_style": "elegant",
        "gesture_frequency": "frequently",
        "movement_confidence": 0.8,
        "walking_speed_multiplier": 1.2,
    }
    
    profile = MannerismProfile.from_dict(data)
    
    assert profile.npc_id == npc_id
    assert profile.movement_style == MovementStyle.ELEGANT
    assert profile.gesture_frequency == GestureFrequency.FREQUENTLY
    assert profile.movement_confidence == 0.8
    assert profile.walking_speed_multiplier == 1.2


def test_profile_from_dict_validation():
    """Test validation in from_dict."""
    # Missing required fields
    with pytest.raises(ValueError):
        MannerismProfile.from_dict({})
    
    # Invalid UUID
    with pytest.raises(ValueError):
        MannerismProfile.from_dict({
            "npc_id": "invalid-uuid",
            "movement_style": "elegant",
            "gesture_frequency": "frequently"
        })
    
    # Invalid float range
    with pytest.raises(ValueError):
        MannerismProfile.from_dict({
            "npc_id": str(uuid4()),
            "movement_style": "elegant",
            "gesture_frequency": "frequently",
            "movement_confidence": 1.5
        })


def test_generator_noble_profile():
    """Test generating noble NPC profile."""
    generator = MannerismGenerator()
    npc_id = uuid4()
    
    profile = generator.generate_profile(npc_id, npc_type="noble")
    
    assert profile.movement_style == MovementStyle.ELEGANT
    assert profile.walking_speed_multiplier < 1.0
    assert profile.posture == "upright"


def test_generator_personality_modification():
    """Test personality affecting mannerisms."""
    generator = MannerismGenerator()
    npc_id = uuid4()
    
    personality = {
        "extraversion": 0.9,
        "neuroticism": 0.8,
    }
    
    profile = generator.generate_profile(
        npc_id,
        npc_type="commoner",
        personality=personality
    )
    
    # High extraversion should increase gesture frequency
    assert profile.gesture_frequency == GestureFrequency.FREQUENTLY
    # High neuroticism should increase walking speed
    assert profile.walking_speed_multiplier > 1.0


def test_generator_context_modification():
    """Test context affecting mannerisms."""
    generator = MannerismGenerator()
    npc_id = uuid4()
    
    context = {
        "injured": True,
        "excited": False,
    }
    
    profile = generator.generate_profile(
        npc_id,
        npc_type="warrior",
        context=context
    )
    
    # Injured should reduce speed and confidence
    assert profile.walking_speed_multiplier < 1.0
    assert profile.movement_confidence < 1.0
    assert profile.posture == "hunched"


def test_generator_input_validation():
    """Test input validation in generator."""
    generator = MannerismGenerator()
    npc_id = uuid4()
    
    # Invalid npc_id
    with pytest.raises(TypeError):
        generator.generate_profile("not-a-uuid")
    
    # Invalid personality values
    with pytest.raises(ValueError):
        generator.generate_profile(
            npc_id,
            personality={"extraversion": 1.5}
        )
    
    # Invalid context
    with pytest.raises(TypeError):
        generator.generate_profile(
            npc_id,
            context={"injured": "yes"}  # Should be bool
        )


def test_manager_get_movement_parameters():
    """Test getting movement parameters."""
    manager = MannerismManager()
    npc_id = uuid4()
    
    manager.get_or_generate_profile(npc_id, npc_type="warrior")
    
    params = manager.get_movement_parameters(npc_id)
    
    assert "walking_speed_multiplier" in params
    assert "posture" in params
    assert "movement_style" in params


def test_manager_get_gesture_parameters():
    """Test getting gesture parameters."""
    manager = MannerismManager()
    npc_id = uuid4()
    
    manager.get_or_generate_profile(npc_id, npc_type="noble")
    
    params = manager.get_gesture_parameters(npc_id)
    
    assert "gesture_frequency" in params
    assert "preferred_gestures" in params
    assert "gesture_intensity" in params


def test_manager_get_idle_parameters():
    """Test getting idle animation parameters."""
    manager = MannerismManager()
    npc_id = uuid4()
    
    manager.get_or_generate_profile(npc_id, npc_type="scholar")
    
    params = manager.get_idle_parameters(npc_id)
    
    assert "idle_animations" in params
    assert "fidget_behaviors" in params
    assert "blinking_rate" in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



