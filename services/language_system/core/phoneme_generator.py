from __future__ import annotations

"""
Phoneme Generator Module
=======================

Generates consistent phoneme inventories for languages based on creature types
and linguistic constraints.
"""

import random
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from services.language_system.core.language_definition import PhonemeInventory, LanguageDefinition, LanguageType

logger = logging.getLogger(__name__)


# IPA Phoneme Sets
VOWELS = {
    "front": ["i", "ɪ", "e", "ɛ", "æ"],
    "central": ["ə", "ɐ", "ɜ"],
    "back": ["u", "ʊ", "o", "ɔ", "ɑ", "ʌ"],
    "dark": ["ɔ", "ʌ", "ɑ"],  # For vampire languages
}

CONSONANTS = {
    "sibilants": ["s", "z", "ʃ", "ʒ", "ʂ", "ʐ"],  # For vampire languages
    "fricatives": ["f", "v", "θ", "ð", "x", "ɣ", "χ", "ʁ"],
    "guttural": ["k", "g", "x", "ɣ", "χ", "ʁ"],  # For werewolf languages
    "stops": ["p", "b", "t", "d", "k", "g"],
    "nasals": ["m", "n", "ŋ"],
    "liquids": ["l", "r", "ɹ", "ɾ"],
    "glides": ["j", "w"],
}

UNIQUE_SOUNDS = {
    "clicks": ["ʘ", "ǀ", "ǁ", "ǃ", "ǂ"],
    "trills": ["r", "ʀ"],
    "growling": ["ʁ", "ʀ"],  # For werewolf languages
}


@dataclass
class PhonemeConstraints:
    """Constraints for phoneme generation."""
    prefer_vowels: List[str] = None
    prefer_consonants: List[str] = None
    avoid_consonants: List[str] = None
    unique_sounds: List[str] = None
    vowel_ratio: float = 0.4  # Ratio of vowels to total phonemes
    min_phonemes: int = 15
    max_phonemes: int = 40


class PhonemeGenerator:
    """Generates phoneme inventories for languages."""
    
    # Creature-specific phoneme preferences
    CREATURE_PHONEMES = {
        "vampire": PhonemeConstraints(
            prefer_vowels=VOWELS["dark"] + VOWELS["back"],
            prefer_consonants=CONSONANTS["sibilants"] + CONSONANTS["fricatives"],
            avoid_consonants=CONSONANTS["guttural"],
            unique_sounds=[],
        ),
        "werewolf": PhonemeConstraints(
            prefer_vowels=VOWELS["back"] + VOWELS["central"],
            prefer_consonants=CONSONANTS["guttural"] + CONSONANTS["fricatives"],
            avoid_consonants=CONSONANTS["sibilants"][:2],  # Avoid s, z (labial-like)
            unique_sounds=UNIQUE_SOUNDS["growling"],
        ),
        "zombie": PhonemeConstraints(
            prefer_vowels=VOWELS["central"] + VOWELS["back"],
            prefer_consonants=CONSONANTS["stops"] + CONSONANTS["nasals"],
            avoid_consonants=CONSONANTS["sibilants"],  # Decayed, simplified
            unique_sounds=[],
        ),
        "ghoul": PhonemeConstraints(
            prefer_vowels=VOWELS["back"],
            prefer_consonants=CONSONANTS["guttural"] + CONSONANTS["fricatives"],
            avoid_consonants=[],
            unique_sounds=[],
        ),
        "lich": PhonemeConstraints(
            prefer_vowels=VOWELS["back"] + VOWELS["dark"],
            prefer_consonants=CONSONANTS["fricatives"] + CONSONANTS["stops"],
            avoid_consonants=[],
            unique_sounds=[],
        ),
    }
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize phoneme generator."""
        if seed is not None:
            random.seed(seed)
    
    def generate(
        self,
        language: LanguageDefinition,
        constraints: Optional[PhonemeConstraints] = None
    ) -> PhonemeInventory:
        """
        Generate phoneme inventory for a language.
        
        Args:
            language: Language definition
            constraints: Optional custom constraints
            
        Returns:
            Generated phoneme inventory
        """
        # Get creature-specific constraints if available
        if constraints is None:
            creature_name = language.metadata.get("creature_type", "").lower()
            constraints = self.CREATURE_PHONEMES.get(creature_name)
        
        if constraints is None:
            # Default constraints
            constraints = PhonemeConstraints()
        
        # Determine phoneme count
        phoneme_count = random.randint(
            constraints.min_phonemes,
            constraints.max_phonemes
        )
        
        # Generate vowels
        vowel_pool = constraints.prefer_vowels or VOWELS["front"] + VOWELS["back"] + VOWELS["central"]
        vowel_count = int(phoneme_count * constraints.vowel_ratio)
        vowels = random.sample(vowel_pool, min(vowel_count, len(vowel_pool)))
        
        # Generate consonants
        consonant_pool = constraints.prefer_consonants or (
            CONSONANTS["stops"] + CONSONANTS["fricatives"] + CONSONANTS["nasals"]
        )
        # Remove avoided consonants
        if constraints.avoid_consonants:
            consonant_pool = [c for c in consonant_pool if c not in constraints.avoid_consonants]
        
        consonant_count = phoneme_count - vowel_count
        consonants = random.sample(
            consonant_pool,
            min(consonant_count, len(consonant_pool))
        )
        
        # Add unique sounds if specified
        unique_sounds = constraints.unique_sounds or []
        if unique_sounds:
            # Add some unique sounds (20-30% chance)
            if random.random() < 0.25:
                unique_sounds_to_add = random.sample(
                    unique_sounds,
                    min(1, len(unique_sounds))
                )
                unique_sounds = unique_sounds_to_add
        
        # Generate phonotactics
        phonotactics = self._generate_phonotactics(language, consonants, vowels)
        
        # Generate stress patterns
        stress_patterns = self._generate_stress_patterns(language)
        
        return PhonemeInventory(
            vowels=vowels,
            consonants=consonants,
            unique_sounds=unique_sounds,
            phonotactics=phonotactics,
            stress_patterns=stress_patterns,
        )
    
    def _generate_phonotactics(
        self,
        language: LanguageDefinition,
        consonants: List[str],
        vowels: List[str]
    ) -> Dict[str, Any]:
        """Generate phonotactics rules for a language."""
        # Common syllable structures
        syllable_structures = [
            "CV",      # Consonant-Vowel (simple)
            "CVC",     # Consonant-Vowel-Consonant
            "CVCC",    # Consonant-Vowel-Consonant-Consonant
            "CCV",     # Consonant-Consonant-Vowel
            "CCVC",    # Consonant-Consonant-Vowel-Consonant
            "V",       # Vowel only
            "VC",      # Vowel-Consonant
        ]
        
        # Select 2-4 common structures
        num_structures = random.randint(2, 4)
        selected_structures = random.sample(
            syllable_structures,
            min(num_structures, len(syllable_structures))
        )
        
        # Common consonant clusters
        consonant_clusters = []
        if len(consonants) >= 2:
            # Generate some allowed clusters
            num_clusters = random.randint(3, 8)
            for _ in range(num_clusters):
                cluster = "".join(random.sample(consonants, min(2, len(consonants))))
                consonant_clusters.append(cluster)
        
        return {
            "syllable_structures": selected_structures,
            "allowed_clusters": consonant_clusters,
            "max_syllables_per_word": random.randint(1, 4),
        }
    
    def _generate_stress_patterns(
        self,
        language: LanguageDefinition
    ) -> List[str]:
        """Generate stress patterns for a language."""
        patterns = [
            "first",      # Stress on first syllable
            "last",       # Stress on last syllable
            "penultimate", # Stress on second-to-last syllable
            "variable",   # Variable stress
        ]
        
        # Select 1-2 patterns
        num_patterns = random.randint(1, 2)
        return random.sample(patterns, min(num_patterns, len(patterns)))






