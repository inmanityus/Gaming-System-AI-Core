"""
Tests for Dialogue Style Profile System.

Implements REQ-NPC-001: Dialogue Style Profile System.
"""

import pytest
from uuid import uuid4

from services.npc_behavior.dialogue_style_profile import (
    DialogueStyleProfile,
    DialogueStyleGenerator,
    DialogueStyleManager,
    FormalityLevel,
    EmotionalRange,
)


def test_profile_creation():
    """Test creating a dialogue style profile."""
    npc_id = uuid4()
    profile = DialogueStyleProfile(npc_id=npc_id)
    
    assert profile.npc_id == npc_id
    assert profile.formality == FormalityLevel.NEUTRAL
    assert profile.emotional_range == EmotionalRange.MODERATE
    assert 0.0 <= profile.vocabulary_complexity <= 1.0


def test_profile_float_validation():
    """Test float range validation in profile."""
    npc_id = uuid4()
    
    # Valid values should work
    profile = DialogueStyleProfile(
        npc_id=npc_id,
        vocabulary_complexity=0.5,
        speaking_pace=0.7
    )
    assert profile.vocabulary_complexity == 0.5
    assert profile.speaking_pace == 0.7
    
    # Invalid values should raise
    with pytest.raises(ValueError):
        DialogueStyleProfile(npc_id=npc_id, vocabulary_complexity=1.5)
    
    with pytest.raises(ValueError):
        DialogueStyleProfile(npc_id=npc_id, vocabulary_complexity=-0.1)


def test_profile_to_dict():
    """Test converting profile to dictionary."""
    npc_id = uuid4()
    profile = DialogueStyleProfile(npc_id=npc_id)
    
    data = profile.to_dict()
    
    assert data["npc_id"] == str(npc_id)
    assert data["formality"] == "neutral"
    assert isinstance(data["preferred_words"], list)
    # Should be copies, not references
    assert data["preferred_words"] is not profile.preferred_words


def test_profile_from_dict():
    """Test creating profile from dictionary."""
    npc_id = uuid4()
    data = {
        "npc_id": str(npc_id),
        "formality": "formal",
        "emotional_range": "expressive",
        "vocabulary_complexity": 0.8,
    }
    
    profile = DialogueStyleProfile.from_dict(data)
    
    assert profile.npc_id == npc_id
    assert profile.formality == FormalityLevel.FORMAL
    assert profile.emotional_range == EmotionalRange.EXPRESSIVE
    assert profile.vocabulary_complexity == 0.8


def test_profile_from_dict_validation():
    """Test validation in from_dict."""
    # Missing required fields
    with pytest.raises(ValueError):
        DialogueStyleProfile.from_dict({"npc_id": str(uuid4())})
    
    # Invalid UUID
    with pytest.raises(ValueError):
        DialogueStyleProfile.from_dict({
            "npc_id": "invalid-uuid",
            "formality": "formal",
            "emotional_range": "expressive"
        })
    
    # Invalid float range
    with pytest.raises(ValueError):
        DialogueStyleProfile.from_dict({
            "npc_id": str(uuid4()),
            "formality": "formal",
            "emotional_range": "expressive",
            "vocabulary_complexity": 1.5
        })


def test_generator_noble_profile():
    """Test generating noble NPC profile."""
    generator = DialogueStyleGenerator()
    npc_id = uuid4()
    
    profile = generator.generate_profile(npc_id, npc_type="noble")
    
    assert profile.formality == FormalityLevel.FORMAL
    assert profile.vocabulary_complexity == 0.8
    assert "indeed" in profile.preferred_words or "certainly" in profile.preferred_words


def test_generator_personality_modification():
    """Test personality affecting profile."""
    generator = DialogueStyleGenerator()
    npc_id = uuid4()
    
    personality = {
        "extraversion": 0.9,  # High extraversion
        "openness": 0.8,
    }
    
    profile = generator.generate_profile(
        npc_id,
        npc_type="commoner",
        personality=personality
    )
    
    # High extraversion should make emotional range expressive
    assert profile.emotional_range == EmotionalRange.EXPRESSIVE
    assert profile.use_exclamations > 0.2


def test_generator_input_validation():
    """Test input validation in generator."""
    generator = DialogueStyleGenerator()
    npc_id = uuid4()
    
    # Invalid npc_id
    with pytest.raises(TypeError):
        generator.generate_profile("not-a-uuid", npc_type="noble")
    
    # Invalid npc_type
    with pytest.raises(TypeError):
        generator.generate_profile(npc_id, npc_type=123)
    
    # Invalid personality
    with pytest.raises(TypeError):
        generator.generate_profile(npc_id, personality="not-a-dict")
    
    # Invalid personality values
    with pytest.raises(ValueError):
        generator.generate_profile(
            npc_id,
            personality={"extraversion": 1.5}  # Out of range
        )


def test_manager_get_or_generate():
    """Test manager getting or generating profile."""
    manager = DialogueStyleManager()
    npc_id = uuid4()
    
    # First call should generate
    profile1 = manager.get_or_generate_profile(npc_id, npc_type="noble")
    assert profile1 is not None
    
    # Second call should return same
    profile2 = manager.get_or_generate_profile(npc_id, npc_type="noble")
    assert profile1.npc_id == profile2.npc_id
    assert profile1.formality == profile2.formality


def test_manager_apply_style_to_prompt():
    """Test applying style to prompt."""
    manager = DialogueStyleManager()
    npc_id = uuid4()
    
    profile = manager.get_or_generate_profile(npc_id, npc_type="scholar")
    
    base_prompt = "Generate dialogue for this NPC."
    styled_prompt = manager.apply_style_to_prompt(profile, base_prompt)
    
    assert "DIALOGUE STYLE INSTRUCTIONS" in styled_prompt
    assert base_prompt in styled_prompt


def test_generator_thread_safety():
    """Test thread safety of generator."""
    import threading
    
    generator = DialogueStyleGenerator()
    npc_ids = [uuid4() for _ in range(10)]
    
    def generate_profile(npc_id):
        return generator.generate_profile(npc_id, npc_type="noble")
    
    # Generate profiles concurrently
    threads = []
    results = []
    
    def worker(npc_id):
        results.append(generate_profile(npc_id))
    
    for npc_id in npc_ids:
        thread = threading.Thread(target=worker, args=(npc_id,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert len(results) == 10
    assert all(isinstance(r, DialogueStyleProfile) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



