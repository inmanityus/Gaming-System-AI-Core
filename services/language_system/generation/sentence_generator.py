"""
Sentence Generator Module
=========================

Constructs grammatically correct sentences from language definitions.
"""

import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.language_definition import LanguageDefinition, GrammarRules, Lexicon

logger = logging.getLogger(__name__)


@dataclass
class SentenceRequest:
    """Request for sentence generation."""
    language: LanguageDefinition
    intent: str  # What the sentence should express
    context: Dict[str, Any] = None
    emotion: Optional[str] = None  # calm, angry, happy, etc.
    complexity: int = 1  # 1-5, complexity level


class SentenceGenerator:
    """Generates sentences from language definitions."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize sentence generator."""
        if seed is not None:
            random.seed(seed)
    
    def generate(self, request: SentenceRequest) -> str:
        """
        Generate a sentence based on request.
        
        Args:
            request: Sentence generation request
            
        Returns:
            Generated sentence
        """
        language = request.language
        grammar = language.grammar_rules
        lexicon = language.lexicon
        
        # Parse intent to determine sentence structure
        structure = self._parse_intent(request.intent, grammar)
        
        # Select words from lexicon
        words = self._select_words(lexicon, structure, request.intent)
        
        # Apply morphological inflections
        words = self._apply_inflections(words, grammar, request)
        
        # Arrange words according to word order
        sentence = self._arrange_words(words, grammar.word_order)
        
        # Apply phonotactics and pronunciation
        sentence = self._apply_phonotactics(sentence, language)
        
        return sentence
    
    def _parse_intent(self, intent: str, grammar: GrammarRules) -> Dict[str, Any]:
        """Parse intent to determine sentence structure."""
        # Simple structure: {subject, verb, object, etc.}
        structure = {
            "subject": True,
            "verb": True,
            "object": False,
        }
        
        # Determine if object is needed based on intent
        if any(word in intent.lower() for word in ["give", "take", "attack", "see"]):
            structure["object"] = True
        
        return structure
    
    def _select_words(
        self,
        lexicon: Lexicon,
        structure: Dict[str, Any],
        intent: str
    ) -> Dict[str, str]:
        """Select words from lexicon based on structure and intent."""
        words = {}
        
        # Select subject
        if structure.get("subject"):
            # Try to find relevant word from root_words
            intent_words = intent.lower().split()
            subject_word = None
            
            for root_word in lexicon.root_words.keys():
                if root_word in intent_words:
                    subject_word = lexicon.root_words[root_word]
                    break
            
            if not subject_word:
                # Fallback: use first available root word
                if lexicon.root_words:
                    subject_word = list(lexicon.root_words.values())[0]
                else:
                    subject_word = "subj"
            
            words["subject"] = subject_word
        
        # Select verb
        if structure.get("verb"):
            # Try to find verb-like word
            verb_word = None
            for root_word in lexicon.root_words.keys():
                if any(action in root_word for action in ["act", "do", "move", "go"]):
                    verb_word = lexicon.root_words[root_word]
                    break
            
            if not verb_word:
                # Fallback
                if lexicon.root_words:
                    verb_word = list(lexicon.root_words.values())[1 % len(lexicon.root_words)]
                else:
                    verb_word = "verb"
            
            words["verb"] = verb_word
        
        # Select object
        if structure.get("object"):
            if lexicon.root_words:
                object_word = list(lexicon.root_words.values())[2 % len(lexicon.root_words)]
            else:
                object_word = "obj"
            words["object"] = object_word
        
        return words
    
    def _apply_inflections(
        self,
        words: Dict[str, str],
        grammar: GrammarRules,
        request: SentenceRequest
    ) -> Dict[str, str]:
        """Apply morphological inflections to words."""
        # Simple inflection application
        # In a full implementation, this would apply proper affixes based on grammar rules
        
        inflected_words = {}
        for role, word in words.items():
            # Apply basic inflections based on grammatical categories
            if role == "verb":
                # Apply tense (if specified in grammar)
                if "tense" in grammar.grammatical_categories:
                    # Simple: add tense marker (simplified)
                    word = word + "-present"
            
            inflected_words[role] = word
        
        return inflected_words
    
    def _arrange_words(self, words: Dict[str, str], word_order: str) -> str:
        """Arrange words according to word order."""
        # Map word order to arrangement
        order_map = {
            "SVO": ["subject", "verb", "object"],
            "SOV": ["subject", "object", "verb"],
            "VSO": ["verb", "subject", "object"],
            "VOS": ["verb", "object", "subject"],
            "OSV": ["object", "subject", "verb"],
            "OVS": ["object", "verb", "subject"],
        }
        
        order = order_map.get(word_order, ["subject", "verb", "object"])
        
        # Build sentence
        sentence_parts = []
        for role in order:
            if role in words:
                sentence_parts.append(words[role])
        
        return " ".join(sentence_parts)
    
    def _apply_phonotactics(self, sentence: str, language: LanguageDefinition) -> str:
        """Apply phonotactics rules to sentence (simplified)."""
        # In a full implementation, this would adjust pronunciation
        # For now, just return the sentence as-is
        return sentence




