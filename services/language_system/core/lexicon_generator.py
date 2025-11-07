"""
Lexicon Generator Module
========================

Generates vocabulary (lexicon) for languages based on creature types,
cultural context, and seed words.
"""

import random
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from .language_definition import Lexicon, LanguageDefinition, LanguageType

logger = logging.getLogger(__name__)


# Semantic domains for different creature types
SEMANTIC_DOMAINS = {
    "vampire": {
        "lineage": ["blood", "ancestor", "sire", "progeny", "line", "house"],
        "ritual": ["ceremony", "sacrament", "offering", "rite", "prayer"],
        "seduction": ["charm", "allure", "entice", "lure", "tempt"],
        "hierarchy": ["lord", "master", "servant", "thrall", "elder"],
        "time": ["night", "darkness", "eternity", "age", "century"],
    },
    "werewolf": {
        "hunting": ["hunt", "prey", "track", "kill", "feast"],
        "pack": ["pack", "alpha", "beta", "omega", "member"],
        "territory": ["territory", "border", "claim", "mark", "domain"],
        "aggression": ["rage", "fury", "attack", "defend", "fight"],
        "nature": ["moon", "forest", "wild", "instinct", "beast"],
    },
    "zombie": {
        "hunger": ["hunger", "eat", "flesh", "consume", "devour"],
        "decay": ["rot", "decay", "flesh", "bone", "corpse"],
        "basic": ["walk", "move", "grab", "bite", "moan"],
    },
    "ghoul": {
        "hunger": ["crave", "devour", "consume", "feast", "hunger"],
        "death": ["corpse", "grave", "tomb", "decay", "rot"],
    },
    "lich": {
        "power": ["power", "magic", "spell", "ritual", "arcane"],
        "death": ["death", "undead", "necromancy", "soul", "spirit"],
        "knowledge": ["knowledge", "secret", "ancient", "forbidden", "lore"],
        "ritual": ["ritual", "ceremony", "sacrifice", "offering", "invocation"],
    },
}


class LexiconGenerator:
    """Generates vocabulary (lexicon) for languages."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize lexicon generator."""
        if seed is not None:
            random.seed(seed)
    
    def generate(
        self,
        language: LanguageDefinition,
        seed_words: Optional[List[str]] = None,
        semantic_focus: Optional[Dict[str, List[str]]] = None
    ) -> Lexicon:
        """
        Generate lexicon for a language.
        
        Args:
            language: Language definition
            seed_words: Optional seed words to start with
            semantic_focus: Optional semantic domains to focus on
            
        Returns:
            Generated lexicon
        """
        # Use seed words from language definition if not provided
        if seed_words is None:
            seed_words = language.seed_words or []
        
        # Get semantic domains for creature type
        creature_name = language.metadata.get("creature_type", "").lower()
        if semantic_focus is None:
            semantic_focus = SEMANTIC_DOMAINS.get(creature_name, {})
        
        # Generate root words
        root_words = self._generate_root_words(
            language,
            seed_words,
            semantic_focus
        )
        
        # Generate affixes
        affixes = self._generate_affixes(language)
        
        # Generate compounds
        compounds = self._generate_compounds(language, root_words)
        
        # Organize semantic domains
        semantic_domains = self._organize_semantic_domains(root_words, semantic_focus)
        
        # Generate loanwords (borrowed from other languages)
        loanwords = self._generate_loanwords(language, root_words)
        
        return Lexicon(
            root_words=root_words,
            affixes=affixes,
            compounds=compounds,
            semantic_domains=semantic_domains,
            loanwords=loanwords,
        )
    
    def _generate_root_words(
        self,
        language: LanguageDefinition,
        seed_words: List[str],
        semantic_focus: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """Generate root words from seed words and semantic domains."""
        root_words = {}
        
        # Add seed words (these are concepts, we'll generate words for them)
        for concept in seed_words:
            word = self._generate_word_for_concept(language, concept)
            root_words[concept] = word
        
        # Add words from semantic domains
        for domain, concepts in semantic_focus.items():
            for concept in concepts:
                if concept not in root_words:
                    word = self._generate_word_for_concept(language, concept)
                    root_words[concept] = word
        
        return root_words
    
    def _generate_word_for_concept(
        self,
        language: LanguageDefinition,
        concept: str
    ) -> str:
        """Generate a word for a concept using the language's phonemes."""
        # Get phonemes from language definition
        vowels = language.phoneme_inventory.vowels
        consonants = language.phoneme_inventory.consonants
        
        if not vowels or not consonants:
            # Fallback: use simple word generation
            return self._fallback_word_generation(concept)
        
        # Generate word based on phonotactics
        phonotactics = language.phoneme_inventory.phonotactics
        syllable_structures = phonotactics.get("syllable_structures", ["CV", "CVC"])
        max_syllables = phonotactics.get("max_syllables_per_word", 2)
        
        # Select syllable structure
        structure = random.choice(syllable_structures)
        num_syllables = random.randint(1, max_syllables)
        
        word_parts = []
        for _ in range(num_syllables):
            syllable = self._build_syllable(structure, vowels, consonants)
            word_parts.append(syllable)
        
        return "".join(word_parts)
    
    def _build_syllable(
        self,
        structure: str,
        vowels: List[str],
        consonants: List[str]
    ) -> str:
        """Build a syllable from a structure."""
        syllable = ""
        for char in structure:
            if char == "C":
                syllable += random.choice(consonants) if consonants else ""
            elif char == "V":
                syllable += random.choice(vowels) if vowels else ""
        return syllable
    
    def _fallback_word_generation(self, concept: str) -> str:
        """Fallback word generation if phonemes not available."""
        # Simple hash-based generation
        hash_val = hash(concept) % 10000
        return f"word{hash_val}"
    
    def _generate_affixes(self, language: LanguageDefinition) -> Dict[str, List[str]]:
        """Generate affixes (prefixes, suffixes, infixes) for a language."""
        vowels = language.phoneme_inventory.vowels
        consonants = language.phoneme_inventory.consonants
        
        if not vowels or not consonants:
            return {}
        
        affixes = {
            "prefixes": [],
            "suffixes": [],
            "infixes": [],
        }
        
        # Generate 3-8 prefixes
        num_prefixes = random.randint(3, 8)
        for _ in range(num_prefixes):
            prefix = self._build_syllable("CV", vowels, consonants)
            affixes["prefixes"].append(prefix)
        
        # Generate 3-8 suffixes
        num_suffixes = random.randint(3, 8)
        for _ in range(num_suffixes):
            suffix = self._build_syllable("VC", vowels, consonants)
            affixes["suffixes"].append(suffix)
        
        # Generate 0-3 infixes (less common)
        num_infixes = random.randint(0, 3)
        for _ in range(num_infixes):
            infix = self._build_syllable("CV", vowels, consonants)
            affixes["infixes"].append(infix)
        
        return affixes
    
    def _generate_compounds(
        self,
        language: LanguageDefinition,
        root_words: Dict[str, str]
    ) -> Dict[str, str]:
        """Generate compound words from root words."""
        compounds = {}
        
        if len(root_words) < 2:
            return compounds
        
        # Generate 5-15 compound words
        num_compounds = random.randint(5, 15)
        root_list = list(root_words.keys())
        
        for _ in range(num_compounds):
            # Select two random root words
            word1 = random.choice(root_list)
            word2 = random.choice(root_list)
            
            if word1 != word2:
                compound_concept = f"{word1}-{word2}"
                compound_word = root_words[word1] + root_words[word2]
                compounds[compound_concept] = compound_word
        
        return compounds
    
    def _organize_semantic_domains(
        self,
        root_words: Dict[str, str],
        semantic_focus: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Organize root words into semantic domains."""
        semantic_domains = {}
        
        for domain, concepts in semantic_focus.items():
            domain_words = []
            for concept in concepts:
                if concept in root_words:
                    domain_words.append(root_words[concept])
            if domain_words:
                semantic_domains[domain] = domain_words
        
        return semantic_domains
    
    def _generate_loanwords(
        self,
        language: LanguageDefinition,
        root_words: Dict[str, str]
    ) -> Dict[str, str]:
        """Generate loanwords (borrowed from other languages)."""
        loanwords = {}
        
        # Only generate loanwords if language has contact with others
        if language.metadata.get("has_contact", False):
            # Generate 2-5 loanwords
            num_loanwords = random.randint(2, 5)
            source_languages = ["common", "vampire", "werewolf", "ancient"]
            
            for _ in range(num_loanwords):
                source = random.choice(source_languages)
                # Borrow a random concept
                if root_words:
                    concept = random.choice(list(root_words.keys()))
                    loanword = f"{concept} (from {source})"
                    loanwords[loanword] = source
        
        return loanwords




