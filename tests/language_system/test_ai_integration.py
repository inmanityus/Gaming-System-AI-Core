"""
Tests for AI Model Integration (Phase 2, Task 1)
=================================================

Tests integration with:
- LLMClient
- CostBenefitRouter
- SRL→RLVR training system
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.language_system.generation.ai_language_generator import (
    AILanguageGenerator,
    LanguageGenerator,
    LanguageRequest,
)
from services.language_system.core.language_definition import (
    LanguageDefinition,
    LanguageType,
    PhonemeInventory,
    GrammarRules,
    Lexicon,
)


@pytest.fixture
def sample_language():
    """Create a sample language definition for testing."""
    return LanguageDefinition(
        name="Vampire",
        language_type=LanguageType.MONSTER,
        language_family="Volkh",
        culture="Vampire",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u"],
            consonants=["s", "z", "sh", "zh", "f", "v"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="fusional",
        ),
        lexicon=Lexicon(
            root_words={
                "blood": "sang",
                "hunt": "kru",
                "night": "volkh",
            }
        ),
        seed_words=["sang", "kru", "volkh"],
        ai_model_hints="Dark, sibilant sounds. Ritualistic language."
    )


@pytest.fixture
def mock_llm_client():
    """Create a mock LLMClient."""
    client = Mock()
    client.generate_text = AsyncMock(return_value={
        "text": "sang kru volkh",
        "tokens_used": 10,
    })
    return client


@pytest.fixture
def mock_router():
    """Create a mock CostBenefitRouter."""
    router = Mock()
    router.select_model = AsyncMock(return_value=Mock(
        selected_model_id="test-model-1",
        selected_model_name="Test Model",
        confidence=0.9,
        reasoning="tier: gold",
        cost_estimate=0.001,
        latency_estimate=150.0,
    ))
    return router


@pytest.mark.asyncio
async def test_ai_language_generator_initialization(mock_llm_client, mock_router):
    """Test AI language generator initialization."""
    generator = AILanguageGenerator(
        llm_client=mock_llm_client,
        cost_benefit_router=mock_router
    )
    
    assert generator.llm_client == mock_llm_client
    assert generator.router == mock_router


@pytest.mark.asyncio
async def test_generate_language_content(sample_language, mock_llm_client, mock_router):
    """Test language content generation."""
    generator = AILanguageGenerator(
        llm_client=mock_llm_client,
        cost_benefit_router=mock_router
    )
    
    request = LanguageRequest(
        language=sample_language,
        intent="I want to hunt for blood",
        complexity=3,
        max_latency_ms=500.0
    )
    
    result = await generator.generate_language_content(request)
    
    assert result.generated_text is not None
    assert result.language == "Vampire"
    assert result.model_used is not None
    assert result.latency_ms >= 0
    assert result.cost_estimate >= 0
    
    # Verify LLMClient was called
    mock_llm_client.generate_text.assert_called_once()
    
    # Verify router was called
    mock_router.select_model.assert_called_once()


@pytest.mark.asyncio
async def test_generate_batch(sample_language, mock_llm_client, mock_router):
    """Test batch language generation."""
    generator = AILanguageGenerator(
        llm_client=mock_llm_client,
        cost_benefit_router=mock_router
    )
    
    requests = [
        LanguageRequest(
            language=sample_language,
            intent="hunt",
            complexity=1
        ),
        LanguageRequest(
            language=sample_language,
            intent="blood",
            complexity=2
        ),
    ]
    
    results = await generator.generate_batch(requests)
    
    assert len(results) == 2
    assert all(isinstance(r, type(results[0])) for r in results)


@pytest.mark.asyncio
async def test_language_generator_hybrid(sample_language, mock_llm_client, mock_router):
    """Test LanguageGenerator hybrid mode (procedural + AI)."""
    with patch('services.language_system.generation.ai_language_generator.AILanguageGenerator') as mock_ai:
        mock_ai_instance = Mock()
        mock_ai_instance.generate_language_content = AsyncMock(return_value=Mock(
            generated_text="ai generated text"
        ))
        mock_ai.return_value = mock_ai_instance
        
        generator = LanguageGenerator(use_ai=True)
        
        # Simple sentence - should use procedural
        result = await generator.generate_sentence(
            language=sample_language,
            intent="simple greeting",
            complexity=1,
            use_ai=False
        )
        
        assert result is not None
        
        # Complex sentence - should use AI
        result = await generator.generate_sentence(
            language=sample_language,
            intent="complex ritual chant",
            complexity=4,
            use_ai=True
        )
        
        assert result is not None


@pytest.mark.asyncio
async def test_task_type_determination():
    """Test task type determination based on complexity."""
    generator = AILanguageGenerator()
    
    assert generator._determine_task_type(1) == "interaction"  # Gold tier
    assert generator._determine_task_type(2) == "interaction"  # Gold tier
    assert generator._determine_task_type(3) == "customization"  # Silver tier
    assert generator._determine_task_type(4) == "customization"  # Silver tier
    assert generator._determine_task_type(5) == "coordination"  # Bronze tier


@pytest.mark.asyncio
async def test_prompt_building(sample_language, mock_router):
    """Test prompt building for language generation."""
    generator = AILanguageGenerator(cost_benefit_router=mock_router)
    
    request = LanguageRequest(
        language=sample_language,
        intent="hunt for blood",
        context={"location": "warehouse"},
        emotion="aggressive"
    )
    
    routing_decision = Mock(
        selected_model_name="Test Model",
        reasoning="gold tier"
    )
    
    prompt = generator._build_language_prompt(request, routing_decision)
    
    assert "Vampire" in prompt
    assert "hunt for blood" in prompt
    assert "warehouse" in prompt
    assert "aggressive" in prompt
    assert sample_language.grammar_rules.word_order in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

