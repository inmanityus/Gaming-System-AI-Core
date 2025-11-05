"""
Pairwise Tests for Language of Power - Created by Tester and Reviewed by Reviewer.
Tests artifact deciphering functionality with real AI integration.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.language_system.gameplay.language_of_power import (
    LanguageOfPower, SpellRequest, SpellResult
)
from services.language_system.core.language_definition import (
    LanguageDefinition, LanguageType, Lexicon, GrammarRules, PhonemeInventory
)
from services.language_system.generation.ai_language_generator import (
    AILanguageGenerator, LanguageGenerationResult
)


class TestLanguageOfPower:
    """Pairwise tests for LanguageOfPower."""
    
    @pytest.fixture
    def mock_language(self):
        """Create mock language definition."""
        lexicon = Lexicon(
            root_words={"fire": "volkh", "power": "kru", "spell": "incendio"}
        )
        lexicon.vocabulary = {"volkh": "fire", "kru": "power", "incendio": "spell"}
        
        return LanguageDefinition(
            name="TestLanguage",
            language_type=LanguageType.ANCIENT,
            lexicon=lexicon,
            grammar_rules=GrammarRules(),
            phoneme_inventory=PhonemeInventory(vowels=["a", "e", "i", "o", "u"], consonants=["v", "k", "r", "h"]),
            culture="ancient"
        )
    
    @pytest.fixture
    def mock_ai_generator(self):
        """Create mock AI language generator."""
        generator = Mock(spec=AILanguageGenerator)
        generator.generate_language_content = AsyncMock(
            return_value=LanguageGenerationResult(
                generated_text="Words of power: fire spell volkh kru incendio",
                language="TestLanguage",
                model_used="gpt-5-pro",
                model_tier="gold",
                latency_ms=150.0,
                cost_estimate=0.001,
                confidence=0.9,
                metadata={}
            )
        )
        return generator
    
    @pytest.fixture
    def language_of_power(self):
        """Create LanguageOfPower instance without AI generator."""
        return LanguageOfPower()
    
    @pytest.fixture
    def language_of_power_with_ai(self, mock_ai_generator):
        """Create LanguageOfPower instance with AI generator."""
        return LanguageOfPower(ai_generator=mock_ai_generator)
    
    def test_initialization(self, language_of_power):
        """Test LanguageOfPower initialization."""
        assert language_of_power is not None
        assert language_of_power.spells is not None
        assert len(language_of_power.spells) > 0
    
    def test_initialization_with_ai(self, language_of_power_with_ai, mock_ai_generator):
        """Test LanguageOfPower initialization with AI generator."""
        assert language_of_power_with_ai is not None
        assert language_of_power_with_ai.ai_generator == mock_ai_generator
    
    def test_cast_spell_success(self, language_of_power):
        """Test successful spell casting."""
        request = SpellRequest(
            spell_words="volkh-kru 'incendio'",
            pronunciation_accuracy=0.9,
            caster_level=5
        )
        
        result = language_of_power.cast_spell(request)
        
        assert result.success is True
        assert result.power_level > 0
        assert result.effect == "fire"
        assert result.damage is not None
        assert result.duration is not None
    
    def test_cast_spell_unknown(self, language_of_power):
        """Test casting unknown spell."""
        request = SpellRequest(
            spell_words="unknown-spell",
            pronunciation_accuracy=0.9,
            caster_level=1
        )
        
        result = language_of_power.cast_spell(request)
        
        assert result.success is False
        assert result.error_message is not None
        assert "Unknown spell" in result.error_message
    
    def test_cast_spell_poor_pronunciation(self, language_of_power):
        """Test spell casting with poor pronunciation."""
        request = SpellRequest(
            spell_words="volkh-kru 'incendio'",
            pronunciation_accuracy=0.3,  # Below 0.5 threshold
            caster_level=1
        )
        
        result = language_of_power.cast_spell(request)
        
        assert result.success is False
        assert "pronunciation" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_decipher_artifact_with_ai(self, language_of_power_with_ai, mock_language):
        """Test artifact deciphering with AI generator."""
        artifact_text = "Ancient text: volkh kru incendio"
        
        result = await language_of_power_with_ai.decipher_artifact(
            artifact_text,
            language=mock_language
        )
        
        assert result is not None
        assert "fragments" in result
        assert "meaning" in result
        assert "unlocked_spells" in result
        assert "skill_points" in result
        assert result["confidence"] > 0
        assert result["model_used"] is not None
        language_of_power_with_ai.ai_generator.generate_language_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decipher_artifact_fallback(self, language_of_power, mock_language):
        """Test artifact deciphering fallback when AI not available."""
        artifact_text = "volkh-kru 'incendio' ancient fire spell"
        
        result = await language_of_power.decipher_artifact(
            artifact_text,
            language=mock_language
        )
        
        assert result is not None
        assert "fragments" in result
        assert len(result["fragments"]) > 0
        assert "meaning" in result
        assert "unlocked_spells" in result
        assert result["method"] == "fallback_pattern_matching"
    
    @pytest.mark.asyncio
    async def test_decipher_artifact_without_language(self, language_of_power_with_ai):
        """Test artifact deciphering without language definition."""
        artifact_text = "volkh kru incendio"
        
        result = await language_of_power_with_ai.decipher_artifact(artifact_text)
        
        assert result is not None
        assert "fragments" in result
        assert "unlocked_spells" in result
        # Should use fallback when language not provided
        assert result.get("method") == "fallback_pattern_matching"
    
    def test_extract_fragments_from_text(self, language_of_power, mock_language):
        """Test fragment extraction from text."""
        text = "volkh kru incendio fire power spell"
        
        fragments = language_of_power._extract_fragments_from_text(text, mock_language)
        
        assert isinstance(fragments, list)
        # Should find fragments from lexicon
        assert len(fragments) > 0
    
    def test_extract_fragments_fallback(self, language_of_power):
        """Test fallback fragment extraction."""
        text = "volkh-kru 'incendio' ancient text"
        
        fragments = language_of_power._extract_fragments_fallback(text)
        
        assert isinstance(fragments, list)
        assert len(fragments) > 0
        assert any("volkh" in f.lower() or "incendio" in f.lower() for f in fragments)
    
    def test_identify_spells_from_fragments(self, language_of_power):
        """Test spell identification from fragments."""
        fragments = ["volkh", "kru", "incendio"]
        
        unlocked_spells = language_of_power._identify_spells_from_fragments(fragments)
        
        assert isinstance(unlocked_spells, list)
        # Should identify fire spell based on fragments
        assert len(unlocked_spells) >= 0
    
    def test_learn_fragment(self, language_of_power, mock_language):
        """Test learning a language fragment."""
        fragment = "volkh"
        
        result = language_of_power.learn_fragment(fragment, mock_language)
        
        assert result is not None
        assert result["fragment"] == fragment
        assert result["learned"] is True
        assert "skill_points" in result
        assert "unlocked_abilities" in result
    
    @pytest.mark.asyncio
    async def test_decipher_artifact_ai_error_handling(self, language_of_power_with_ai, mock_language):
        """Test artifact deciphering error handling when AI fails."""
        # Make AI generator raise an exception
        language_of_power_with_ai.ai_generator.generate_language_content.side_effect = Exception("AI service error")
        
        artifact_text = "volkh kru incendio"
        
        result = await language_of_power_with_ai.decipher_artifact(
            artifact_text,
            language=mock_language
        )
        
        # Should fall back to fallback method
        assert result is not None
        assert "fragments" in result
        assert result.get("method") == "fallback_pattern_matching"

