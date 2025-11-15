from __future__ import annotations

"""
Language Definition Module
==========================

Defines the structure and metadata for all languages in the game.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class LanguageType(Enum):
    """Types of languages in the game."""
    MONSTER = "monster"
    HUMAN = "human"
    ANCIENT = "ancient"
    RITUAL = "ritual"
    MUSIC = "music"


@dataclass
class PhonemeInventory:
    """Phoneme inventory for a language."""
    vowels: List[str] = field(default_factory=list)
    consonants: List[str] = field(default_factory=list)
    unique_sounds: List[str] = field(default_factory=list)
    phonotactics: Dict[str, Any] = field(default_factory=dict)
    stress_patterns: List[str] = field(default_factory=list)


@dataclass
class GrammarRules:
    """Grammar rules for a language."""
    word_order: str = "SVO"  # Subject-Verb-Object, SOV, VSO, etc.
    morphological_type: str = "fusional"  # agglutinative, fusional, isolating
    grammatical_categories: Dict[str, Any] = field(default_factory=dict)
    agreement_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Lexicon:
    """Vocabulary for a language."""
    root_words: Dict[str, str] = field(default_factory=dict)  # concept -> word
    affixes: Dict[str, List[str]] = field(default_factory=dict)  # type -> affixes
    compounds: Dict[str, str] = field(default_factory=dict)  # compound -> meaning
    semantic_domains: Dict[str, List[str]] = field(default_factory=dict)  # domain -> words
    loanwords: Dict[str, str] = field(default_factory=dict)  # loanword -> source


@dataclass
class LanguageDefinition:
    """
    Complete definition of a language in the game.
    
    Stores all metadata, rules, and vocabulary for a language.
    """
    name: str
    language_type: LanguageType
    language_family: str = ""
    culture: str = ""
    phoneme_inventory: PhonemeInventory = field(default_factory=PhonemeInventory)
    grammar_rules: GrammarRules = field(default_factory=GrammarRules)
    lexicon: Lexicon = field(default_factory=Lexicon)
    prestige_dialect: str = "standard"
    seed_words: List[str] = field(default_factory=list)
    level: int = 1  # Complexity/understanding level (1-10)
    ai_model_hints: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate language definition after initialization."""
        if not self.name:
            raise ValueError("Language name is required")
        if not self.phoneme_inventory.vowels and not self.phoneme_inventory.consonants:
            raise ValueError("Language must have at least some phonemes")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert language definition to dictionary."""
        return {
            "name": self.name,
            "language_type": self.language_type.value,
            "language_family": self.language_family,
            "culture": self.culture,
            "phoneme_inventory": {
                "vowels": self.phoneme_inventory.vowels,
                "consonants": self.phoneme_inventory.consonants,
                "unique_sounds": self.phoneme_inventory.unique_sounds,
                "phonotactics": self.phoneme_inventory.phonotactics,
                "stress_patterns": self.phoneme_inventory.stress_patterns,
            },
            "grammar_rules": {
                "word_order": self.grammar_rules.word_order,
                "morphological_type": self.grammar_rules.morphological_type,
                "grammatical_categories": self.grammar_rules.grammatical_categories,
                "agreement_rules": self.grammar_rules.agreement_rules,
            },
            "lexicon": {
                "root_words": self.lexicon.root_words,
                "affixes": self.lexicon.affixes,
                "compounds": self.lexicon.compounds,
                "semantic_domains": self.lexicon.semantic_domains,
                "loanwords": self.lexicon.loanwords,
            },
            "prestige_dialect": self.prestige_dialect,
            "seed_words": self.seed_words,
            "level": self.level,
            "ai_model_hints": self.ai_model_hints,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LanguageDefinition":
        """Create language definition from dictionary."""
        return cls(
            name=data["name"],
            language_type=LanguageType(data["language_type"]),
            language_family=data.get("language_family", ""),
            culture=data.get("culture", ""),
            phoneme_inventory=PhonemeInventory(
                vowels=data.get("phoneme_inventory", {}).get("vowels", []),
                consonants=data.get("phoneme_inventory", {}).get("consonants", []),
                unique_sounds=data.get("phoneme_inventory", {}).get("unique_sounds", []),
                phonotactics=data.get("phoneme_inventory", {}).get("phonotactics", {}),
                stress_patterns=data.get("phoneme_inventory", {}).get("stress_patterns", []),
            ),
            grammar_rules=GrammarRules(
                word_order=data.get("grammar_rules", {}).get("word_order", "SVO"),
                morphological_type=data.get("grammar_rules", {}).get("morphological_type", "fusional"),
                grammatical_categories=data.get("grammar_rules", {}).get("grammatical_categories", {}),
                agreement_rules=data.get("grammar_rules", {}).get("agreement_rules", {}),
            ),
            lexicon=Lexicon(
                root_words=data.get("lexicon", {}).get("root_words", {}),
                affixes=data.get("lexicon", {}).get("affixes", {}),
                compounds=data.get("lexicon", {}).get("compounds", {}),
                semantic_domains=data.get("lexicon", {}).get("semantic_domains", {}),
                loanwords=data.get("lexicon", {}).get("loanwords", {}),
            ),
            prestige_dialect=data.get("prestige_dialect", "standard"),
            seed_words=data.get("seed_words", []),
            level=data.get("level", 1),
            ai_model_hints=data.get("ai_model_hints", ""),
            metadata=data.get("metadata", {}),
        )


class LanguageRegistry:
    """Registry for all language definitions."""
    
    def __init__(self):
        self._languages: Dict[str, LanguageDefinition] = {}
    
    def register(self, language: LanguageDefinition):
        """Register a language definition."""
        self._languages[language.name.lower()] = language
    
    def get(self, name: str) -> Optional[LanguageDefinition]:
        """Get a language definition by name."""
        return self._languages.get(name.lower())
    
    def list_all(self) -> List[str]:
        """List all registered language names."""
        return list(self._languages.keys())
    
    def exists(self, name: str) -> bool:
        """Check if a language exists."""
        return name.lower() in self._languages










