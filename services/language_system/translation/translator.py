from __future__ import annotations

# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Translation Module
==================

Provides translation between languages with context awareness.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

if TYPE_CHECKING:
    from services.language_system.core.language_definition import LanguageRegistry, LanguageDefinition
    from services.language_system.generation.ai_language_generator import AILanguageGenerator
else:
    from services.language_system.core.language_definition import LanguageRegistry, LanguageDefinition
    from services.language_system.generation.ai_language_generator import AILanguageGenerator

logger = logging.getLogger(__name__)


@dataclass
class TranslationRequest:
    """Request for translation."""
    text: str
    from_language: str
    to_language: str
    context: Dict[str, Any] = field(default_factory=dict)
    player_skill_level: float = 0.5  # 0.0 to 1.0, affects translation quality
    preserve_cultural_nuance: bool = True


@dataclass
class TranslationResult:
    """Result of translation."""
    translated_text: str
    original_text: str
    from_language: str
    to_language: str
    confidence: float  # 0.0 to 1.0
    cultural_notes: List[str] = field(default_factory=list)
    alternative_translations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Translator:
    """
    Translation engine for converting between languages.
    
    Supports:
    - Direct vocabulary translation
    - AI-powered translation for complex sentences
    - Cultural nuance preservation
    - Skill-based translation quality
    """
    
    def __init__(
        self,
        language_registry: Optional[LanguageRegistry] = None,
        ai_generator: Optional[AILanguageGenerator] = None
    ):
        """
        Initialize Translator.
        
        Args:
            language_registry: Registry of language definitions
            ai_generator: AI language generator for complex translations
        """
        self.language_registry = language_registry or LanguageRegistry()
        self.ai_generator = ai_generator
        self.translation_cache: Dict[str, TranslationResult] = {}
        
        logger.info("Translator initialized")
    
    async def translate(
        self,
        request: TranslationRequest
    ) -> TranslationResult:
        """
        Translate text from one language to another.
        
        Args:
            request: Translation request
            
        Returns:
            TranslationResult with translated text and metadata
        """
        logger.info(
            f"Translating from {request.from_language} to {request.to_language}: "
            f"{request.text[:50]}..."
        )
        
        # Check cache
        cache_key = self._get_cache_key(request)
        if cache_key in self.translation_cache:
            logger.debug("Using cached translation")
            return self.translation_cache[cache_key]
        
        # Get language definitions
        from_lang = self.language_registry.get(request.from_language)
        to_lang = self.language_registry.get(request.to_language)
        
        if not from_lang:
            raise ValueError(f"Unknown source language: {request.from_language}")
        if not to_lang:
            raise ValueError(f"Unknown target language: {request.to_language}")
        
        # Simple translation for basic vocabulary
        if self._is_simple_translation(request.text, from_lang):
            result = await self._simple_translate(request, from_lang, to_lang)
        else:
            # Complex translation using AI
            result = await self._ai_translate(request, from_lang, to_lang)
        
        # Apply skill-based quality adjustment
        result = self._adjust_for_skill_level(result, request.player_skill_level)
        
        # Cache result
        self.translation_cache[cache_key] = result
        
        return result
    
    async def translate_batch(
        self,
        requests: List[TranslationRequest]
    ) -> List[TranslationResult]:
        """
        Translate multiple texts in parallel.
        
        Args:
            requests: List of translation requests
            
        Returns:
            List of translation results
        """
        import asyncio
        
        tasks = [self.translate(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error translating request {i}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def _is_simple_translation(self, text: str, language: LanguageDefinition) -> bool:
        """Check if translation can be done with simple vocabulary lookup."""
        # Simple heuristic: if all words are in lexicon, use simple translation
        words = text.lower().split()
        
        # Check if words are in root_words or semantic_domains
        known_words = 0
        for word in words:
            if any(word in concept.lower() or concept.lower() in word 
                   for concept in language.lexicon.root_words.keys()):
                known_words += 1
            elif any(word in domain_words 
                     for domain_words in language.lexicon.semantic_domains.values()):
                known_words += 1
        
        return known_words >= len(words) * 0.7  # 70% match threshold
    
    async def _simple_translate(
        self,
        request: TranslationRequest,
        from_lang: LanguageDefinition,
        to_lang: LanguageDefinition
    ) -> TranslationResult:
        """Simple vocabulary-based translation."""
        words = request.text.split()
        translated_words = []
        
        for word in words:
            # Try to find word in from_lang lexicon
            translated_word = None
            
            # Check root words
            for concept, lang_word in from_lang.lexicon.root_words.items():
                if word.lower() == lang_word.lower():
                    # Find corresponding concept in to_lang
                    if concept in to_lang.lexicon.root_words:
                        translated_word = to_lang.lexicon.root_words[concept]
                        break
            
            if not translated_word:
                # Word not found, keep original or use placeholder
                translated_word = f"[{word}]"  # Mark as untranslated
            
            translated_words.append(translated_word)
        
        translated_text = " ".join(translated_words)
        
        return TranslationResult(
            translated_text=translated_text,
            original_text=request.text,
            from_language=request.from_language,
            to_language=request.to_language,
            confidence=0.6,  # Lower confidence for simple translation
            cultural_notes=[],
            alternative_translations=[],
            metadata={"method": "simple_vocabulary"}
        )
    
    async def _ai_translate(
        self,
        request: TranslationRequest,
        from_lang: LanguageDefinition,
        to_lang: LanguageDefinition
    ) -> TranslationResult:
        """AI-powered translation for complex sentences."""
        if not self.ai_generator:
            # Fallback to simple translation
            return await self._simple_translate(request, from_lang, to_lang)
        
        # Build translation prompt
        prompt = f"""Translate the following text from {from_lang.name} to {to_lang.name}.

Source text ({from_lang.name}): {request.text}

Target language: {to_lang.name}
- Type: {to_lang.language_type.value}
- Grammar: {to_lang.grammar_rules.word_order}
- Culture: {to_lang.culture}

Instructions:
1. Translate the text accurately
2. Preserve cultural nuances if possible
3. Use appropriate grammar for target language
4. Maintain the original meaning and intent

Translated text ({to_lang.name}):"""
        
        # Use AI generator for translation
        lang_request = LanguageRequest(
            language=to_lang,
            intent=f"translate: {request.text}",
            context={
                "source_language": from_lang.name,
                "source_text": request.text,
                "translation_context": request.context,
            },
            complexity=3,  # Medium complexity for translation
        )
        
        result = await self.ai_generator.generate_language_content(lang_request)
        
        # Extract cultural notes and alternatives (simplified)
        cultural_notes = self._extract_cultural_notes(request.text, from_lang, to_lang)
        
        return TranslationResult(
            translated_text=result.generated_text,
            original_text=request.text,
            from_language=request.from_language,
            to_language=request.to_language,
            confidence=result.confidence,
            cultural_notes=cultural_notes,
            alternative_translations=[],
            metadata={
                "method": "ai_generation",
                "model_tier": result.model_tier,
                "latency_ms": result.latency_ms,
            }
        )
    
    def _adjust_for_skill_level(
        self,
        result: TranslationResult,
        skill_level: float
    ) -> TranslationResult:
        """Adjust translation quality based on player skill level."""
        if skill_level >= 0.9:
            # Expert: Full translation with all nuances
            return result
        elif skill_level >= 0.7:
            # Advanced: Mostly accurate, some nuances lost
            result.confidence *= 0.9
            result.cultural_notes = result.cultural_notes[:2]  # Fewer notes
        elif skill_level >= 0.5:
            # Intermediate: Basic translation, cultural notes reduced
            result.confidence *= 0.8
            result.cultural_notes = []
        elif skill_level >= 0.3:
            # Beginner: Partial translation, marked uncertain words
            result.confidence *= 0.6
            result.cultural_notes = []
            # Mark uncertain words
            words = result.translated_text.split()
            if len(words) > 3:
                # Mark some words as uncertain
                result.translated_text = " ".join([
                    f"[{w}]" if i % 3 == 0 else w
                    for i, w in enumerate(words)
                ])
        else:
            # Novice: Very poor translation
            result.confidence *= 0.4
            result.translated_text = f"[Unclear: {result.translated_text[:50]}...]"
        
        return result
    
    def _extract_cultural_notes(
        self,
        text: str,
        from_lang: LanguageDefinition,
        to_lang: LanguageDefinition
    ) -> List[str]:
        """Extract cultural notes from services.language_system.translation."""
        notes = []
        
        # Check for cultural differences
        if from_lang.culture != to_lang.culture:
            notes.append(f"Cultural context shifts from {from_lang.culture} to {to_lang.culture}")
        
        # Check for language type differences
        if from_lang.language_type != to_lang.language_type:
            notes.append(
                f"Translation crosses language types: "
                f"{from_lang.language_type.value} → {to_lang.language_type.value}"
            )
        
        return notes
    
    def _get_cache_key(self, request: TranslationRequest) -> str:
        """Generate cache key for translation request."""
        return f"{request.from_language}:{request.to_language}:{request.text}:{request.player_skill_level}"



