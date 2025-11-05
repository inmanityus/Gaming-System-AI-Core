"""
Language of Power Module
========================

Gameplay mechanic for magical language system.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.language_system.core.language_definition import LanguageDefinition
from services.language_system.generation.ai_language_generator import AILanguageGenerator, LanguageRequest

logger = logging.getLogger(__name__)


@dataclass
class SpellRequest:
    """Request to cast a spell using language of power."""
    spell_words: str
    pronunciation_accuracy: float = 1.0  # 0.0 to 1.0
    caster_level: int = 1
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpellResult:
    """Result of spell casting."""
    success: bool
    power_level: float  # 0.0 to 1.0
    effect: str
    damage: Optional[float] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None


class LanguageOfPower:
    """
    Gameplay mechanic for magical language system.
    
    Features:
    - Spell casting through language
    - Pronunciation accuracy affects power
    - Mastery unlocks advanced abilities
    - Artifact translation
    """
    
    def __init__(
        self,
        ai_generator: Optional[AILanguageGenerator] = None
    ):
        """
        Initialize Language of Power.
        
        Args:
            ai_generator: AI language generator for artifact deciphering
        """
        # Spell database
        self.spells = {
            "volkh-kru 'incendio'": {
                "type": "fire",
                "base_power": 0.5,
                "description": "Simple fire spell",
            },
            "volkh-kru 'vita' 'mortis'": {
                "type": "necromancy",
                "base_power": 0.9,
                "description": "Powerful necromancy spell",
            },
        }
        
        self.ai_generator = ai_generator
        
        logger.info("LanguageOfPower initialized")
    
    def cast_spell(self, request: SpellRequest) -> SpellResult:
        """
        Cast a spell using language of power.
        
        Args:
            request: Spell casting request
            
        Returns:
            SpellResult with outcome
        """
        logger.info(f"Casting spell: {request.spell_words}")
        
        # Check if spell exists
        if request.spell_words not in self.spells:
            return SpellResult(
                success=False,
                power_level=0.0,
                effect="unknown_spell",
                error_message=f"Unknown spell: {request.spell_words}"
            )
        
        spell_info = self.spells[request.spell_words]
        
        # Calculate power based on pronunciation and level
        base_power = spell_info["base_power"]
        power_multiplier = request.pronunciation_accuracy * (1.0 + request.caster_level * 0.1)
        final_power = min(1.0, base_power * power_multiplier)
        
        # Check if pronunciation is sufficient
        if request.pronunciation_accuracy < 0.5:
            return SpellResult(
                success=False,
                power_level=final_power,
                effect=spell_info["type"],
                error_message="Incorrect pronunciation - spell failed"
            )
        
        # Success
        return SpellResult(
            success=True,
            power_level=final_power,
            effect=spell_info["type"],
            damage=final_power * 100,  # Example damage calculation
            duration=final_power * 60,  # Example duration in seconds
        )
    
    async def decipher_artifact(
        self,
        artifact_text: str,
        language: Optional[LanguageDefinition] = None
    ) -> Dict[str, Any]:
        """
        Decipher an ancient artifact to extract language fragments using AI.
        
        Uses AI language generator to translate and extract meaningful fragments
        from artifact text, then identifies spell words and unlocks new abilities.
        
        Args:
            artifact_text: Text from artifact
            language: Language definition for the artifact (if known)
            
        Returns:
            Decipherment result with fragments, meaning, and unlocked spells
        """
        logger.info(f"Deciphering artifact: {artifact_text[:50]}...")
        
        # If AI generator is available, use it for real deciphering
        if self.ai_generator and language:
            try:
                # Create language request for artifact deciphering
                lang_request = LanguageRequest(
                    language=language,
                    intent=f"decipher artifact: {artifact_text}",
                    context={
                        "artifact_text": artifact_text,
                        "task": "artifact_deciphering",
                        "extract_fragments": True,
                    },
                    complexity=4,  # High complexity for artifact deciphering
                    max_latency_ms=2000.0,  # Allow more time for complex deciphering
                    task_type="language_generation",
                )
                
                # Generate decipherment using AI
                result = await self.ai_generator.generate_language_content(lang_request)
                
                # Extract fragments from the generated text
                # Parse the AI response to extract language fragments
                deciphered_text = result.generated_text
                fragments = self._extract_fragments_from_text(deciphered_text, language)
                
                # Identify unlocked spells based on fragments
                unlocked_spells = self._identify_spells_from_fragments(fragments)
                
                return {
                    "fragments": fragments,
                    "meaning": deciphered_text,
                    "unlocked_spells": unlocked_spells,
                    "skill_points": len(fragments) * 0.05,  # 0.05 per fragment
                    "confidence": result.confidence,
                    "model_used": result.model_used,
                    "latency_ms": result.latency_ms,
                }
                
            except Exception as e:
                logger.error(f"Error in AI artifact deciphering: {e}")
                # Fall through to fallback logic
        
        # Fallback: Use pattern matching for known language structures
        fragments = self._extract_fragments_fallback(artifact_text)
        unlocked_spells = self._identify_spells_from_fragments(fragments)
        
        return {
            "fragments": fragments,
            "meaning": f"Deciphered artifact text: {artifact_text[:100]}...",
            "unlocked_spells": unlocked_spells,
            "skill_points": len(fragments) * 0.05,
            "confidence": 0.5,  # Lower confidence for fallback
            "method": "fallback_pattern_matching",
        }
    
    def _extract_fragments_from_text(
        self,
        text: str,
        language: LanguageDefinition
    ) -> List[str]:
        """
        Extract language fragments from deciphered text.
        
        Parses the AI-generated text to identify language fragments
        based on the language definition's lexicon and grammar.
        """
        fragments = []
        
        # Split text into words
        words = text.split()
        
        # Check each word against language lexicon
        for word in words:
            # Clean word (remove punctuation)
            clean_word = word.strip(".,!?;:'\"()[]{}")
            
            # Check if word exists in language lexicon
            if language and hasattr(language, 'lexicon'):
                # Check root words
                if hasattr(language.lexicon, 'root_words'):
                    for concept, lang_word in language.lexicon.root_words.items():
                        if clean_word.lower() == lang_word.lower():
                            fragments.append(clean_word)
                            break
                
                # Check if word matches any lexicon value (root_words or vocabulary if exists)
                # Vocabulary is a dict, check both keys and values
                if hasattr(language.lexicon, 'vocabulary') and language.lexicon.vocabulary:
                    if isinstance(language.lexicon.vocabulary, dict):
                        if clean_word.lower() in language.lexicon.vocabulary.values() or clean_word.lower() in language.lexicon.vocabulary:
                            fragments.append(clean_word)
                    elif isinstance(language.lexicon.vocabulary, (list, set)):
                        if clean_word.lower() in language.lexicon.vocabulary:
                            fragments.append(clean_word)
        
        return fragments
    
    def _extract_fragments_fallback(self, text: str) -> List[str]:
        """
        Fallback fragment extraction using pattern matching.
        
        Extracts potential language fragments from artifact text
        using simple pattern matching when AI is not available.
        """
        fragments = []
        
        # Look for known spell patterns
        known_fragments = ["volkh", "kru", "incendio", "vita", "mortis", "lumen", "tenebris"]
        
        text_lower = text.lower()
        for fragment in known_fragments:
            if fragment in text_lower:
                fragments.append(fragment)
        
        # If no known fragments found, extract words that look like language fragments
        # (simple heuristic: words with apostrophes or special formatting)
        if not fragments:
            words = text.split()
            for word in words:
                # Look for words with special characters that might indicate language fragments
                if "'" in word or "-" in word:
                    clean_word = word.strip(".,!?;:'\"()[]{}")
                    if len(clean_word) > 2:
                        fragments.append(clean_word)
        
        return fragments if fragments else ["unknown"]
    
    def _identify_spells_from_fragments(self, fragments: List[str]) -> List[str]:
        """
        Identify unlocked spells based on extracted fragments.
        
        Matches fragments against known spell patterns to unlock spells.
        """
        unlocked_spells = []
        
        # Check if fragments match known spell patterns
        fragment_str = "-".join(fragments).lower()
        
        for spell_name in self.spells.keys():
            # Check if all key words from spell are in fragments
            spell_words = spell_name.lower().replace("'", "").replace("-", " ").split()
            if any(word in fragment_str for word in spell_words if len(word) > 3):
                unlocked_spells.append(spell_name)
        
        # If no exact matches, check for partial matches
        if not unlocked_spells:
            # Look for fire-related fragments
            fire_keywords = ["incendio", "volkh", "fire", "flame"]
            if any(keyword in fragment_str for keyword in fire_keywords):
                unlocked_spells.append("volkh-kru 'incendio'")
            
            # Look for necromancy-related fragments
            necro_keywords = ["vita", "mortis", "death", "life"]
            if any(keyword in fragment_str for keyword in necro_keywords):
                unlocked_spells.append("volkh-kru 'vita' 'mortis'")
        
        return unlocked_spells
    
    def learn_fragment(self, fragment: str, language: LanguageDefinition) -> Dict[str, Any]:
        """
        Learn a language fragment to unlock new abilities.
        
        Args:
            fragment: Language fragment to learn
            language: Language definition
            
        Returns:
            Learning result
        """
        logger.info(f"Learning fragment: {fragment}")
        
        return {
            "fragment": fragment,
            "learned": True,
            "skill_points": 0.05,
            "unlocked_abilities": [],
        }

