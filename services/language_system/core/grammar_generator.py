"""
Grammar Generator Module
========================

Generates grammatical rules for languages based on creature types and
linguistic constraints.
"""

import random
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .language_definition import GrammarRules, LanguageDefinition, LanguageType

logger = logging.getLogger(__name__)


# Word order options
WORD_ORDERS = ["SVO", "SOV", "VSO", "VOS", "OSV", "OVS"]

# Morphological types
MORPHOLOGICAL_TYPES = {
    "agglutinative": "Words formed by stringing morphemes",
    "fusional": "Morphemes represent multiple categories",
    "isolating": "Words are single morphemes",
}


class GrammarGenerator:
    """Generates grammar rules for languages."""
    
    # Creature-specific grammar preferences
    CREATURE_GRAMMAR = {
        "vampire": {
            "word_order": ["SOV", "SVO"],  # Contemplative, hierarchical
            "morphological_type": "fusional",
            "grammatical_categories": {
                "cases": ["nominative", "accusative", "dative", "genitive", "vocative"],
                "gender": ["masculine", "feminine", "neuter"],
                "number": ["singular", "plural"],
                "tense": ["present", "past", "future", "perfect"],
            },
            "agreement_rules": {
                "noun_adjective": True,
                "subject_verb": True,
                "determiner_noun": True,
            },
        },
        "werewolf": {
            "word_order": ["VSO", "SVO"],  # Action-oriented, verb-first
            "morphological_type": "agglutinative",
            "grammatical_categories": {
                "cases": ["nominative", "accusative", "dative"],
                "number": ["singular", "plural", "pack"],
                "tense": ["present", "past"],
                "aggression": ["calm", "alert", "aggressive", "frenzied"],
            },
            "agreement_rules": {
                "noun_adjective": False,
                "subject_verb": True,
                "verb_aggression": True,  # Unique: verbs agree with aggression level
            },
        },
        "zombie": {
            "word_order": ["SVO"],  # Simplified
            "morphological_type": "isolating",
            "grammatical_categories": {
                "number": ["singular", "plural"],
                "tense": ["present"],  # Only present tense
            },
            "agreement_rules": {
                "noun_adjective": False,
                "subject_verb": False,
            },
        },
        "ghoul": {
            "word_order": ["SVO", "SOV"],
            "morphological_type": "fusional",
            "grammatical_categories": {
                "cases": ["nominative", "accusative"],
                "number": ["singular", "plural"],
                "tense": ["present", "past"],
            },
            "agreement_rules": {
                "noun_adjective": False,
                "subject_verb": True,
            },
        },
        "lich": {
            "word_order": ["SOV", "OVS"],  # Ancient, ritualistic
            "morphological_type": "fusional",
            "grammatical_categories": {
                "cases": ["nominative", "accusative", "dative", "genitive", "ablative", "vocative"],
                "number": ["singular", "plural", "collective"],
                "tense": ["present", "past", "future", "perfect", "pluperfect"],
                "mood": ["indicative", "subjunctive", "imperative"],
            },
            "agreement_rules": {
                "noun_adjective": True,
                "subject_verb": True,
                "determiner_noun": True,
            },
        },
    }
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize grammar generator."""
        if seed is not None:
            random.seed(seed)
    
    def generate(
        self,
        language: LanguageDefinition,
        custom_grammar: Optional[Dict[str, Any]] = None
    ) -> GrammarRules:
        """
        Generate grammar rules for a language.
        
        Args:
            language: Language definition
            custom_grammar: Optional custom grammar rules
            
        Returns:
            Generated grammar rules
        """
        if custom_grammar:
            return GrammarRules(
                word_order=custom_grammar.get("word_order", "SVO"),
                morphological_type=custom_grammar.get("morphological_type", "fusional"),
                grammatical_categories=custom_grammar.get("grammatical_categories", {}),
                agreement_rules=custom_grammar.get("agreement_rules", {}),
            )
        
        # Get creature-specific grammar
        creature_name = language.metadata.get("creature_type", "").lower()
        grammar_template = self.CREATURE_GRAMMAR.get(creature_name)
        
        if grammar_template:
            word_order = random.choice(grammar_template["word_order"])
            morphological_type = grammar_template["morphological_type"]
            grammatical_categories = grammar_template["grammatical_categories"].copy()
            agreement_rules = grammar_template["agreement_rules"].copy()
        else:
            # Default grammar
            word_order = random.choice(WORD_ORDERS)
            morphological_type = random.choice(list(MORPHOLOGICAL_TYPES.keys()))
            grammatical_categories = {
                "cases": ["nominative", "accusative"],
                "number": ["singular", "plural"],
                "tense": ["present", "past"],
            }
            agreement_rules = {
                "noun_adjective": random.choice([True, False]),
                "subject_verb": True,
            }
        
        return GrammarRules(
            word_order=word_order,
            morphological_type=morphological_type,
            grammatical_categories=grammatical_categories,
            agreement_rules=agreement_rules,
        )


