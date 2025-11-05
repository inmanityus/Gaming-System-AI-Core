"""
Tests for Translation & Interpretation Integration
"""

import pytest
from services.language_system.translation import Translator, Interpreter, LanguageLearner
from services.language_system.data.language_definitions import create_vampire_language, create_common_language


@pytest.fixture
def sample_languages():
    """Create sample languages for testing."""
    return {
        "vampire": create_vampire_language(),
        "common": create_common_language(),
    }


@pytest.mark.asyncio
async def test_translator_initialization():
    """Test translator initialization."""
    translator = Translator()
    assert translator is not None
    assert translator.language_registry is not None


@pytest.mark.asyncio
async def test_interpreter_initialization():
    """Test interpreter initialization."""
    interpreter = Interpreter()
    assert interpreter is not None


def test_language_learner():
    """Test language learner."""
    learner = LanguageLearner()
    assert learner is not None
    
    progress = learner.get_progress("vampire")
    assert progress.language == "vampire"
    assert progress.skill_level == 0.0


def test_language_learner_event():
    """Test language learning event."""
    learner = LanguageLearner()
    
    from services.language_system.translation import LearningEvent
    
    event = LearningEvent(
        language="vampire",
        event_type="artifact",
        artifact_id="artifact_1",
        quality_score=1.0
    )
    
    progress = learner.record_learning_event(event)
    assert progress.skill_level > 0.0
    assert "artifact_1" in progress.artifacts_found


def test_skill_level_thresholds():
    """Test skill level understanding thresholds."""
    learner = LanguageLearner()
    
    # Record enough events to raise skill
    from services.language_system.translation import LearningEvent
    
    for i in range(10):
        event = LearningEvent(
            language="vampire",
            event_type="interaction",
            quality_score=1.0
        )
        learner.record_learning_event(event)
    
    skill = learner.get_skill_level("vampire")
    assert skill > 0.0
    
    # Test understanding thresholds
    assert learner.can_understand("vampire", complexity=1) == (skill >= 0.1)
    assert learner.can_understand("vampire", complexity=2) == (skill >= 0.3)

