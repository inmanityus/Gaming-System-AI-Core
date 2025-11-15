# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Language Definitions Data
==========================

Pre-defined language definitions for all game languages.
"""

from services.language_system.core.language_definition import (
    LanguageDefinition,
    LanguageType,
    PhonemeInventory,
    GrammarRules,
    Lexicon,
)


def create_vampire_language() -> LanguageDefinition:
    """Create Vampire language (Volkh) definition."""
    return LanguageDefinition(
        name="Vampire",
        language_type=LanguageType.MONSTER,
        language_family="Volkh",
        culture="Vampire",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u", "ɔ", "ʌ"],  # Dark vowels
            consonants=["s", "z", "sh", "zh", "f", "v", "th", "h"],
            unique_sounds=["sh", "zh"],
            phonotactics={"max_syllables": 3, "allow_clusters": True},
            stress_patterns=["initial", "final"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="fusional",
            grammatical_categories={"cases": ["nominative", "genitive", "dative", "accusative"]},
            agreement_rules={"subject_verb": True, "noun_adjective": True},
        ),
        lexicon=Lexicon(
            root_words={
                "blood": "sang",
                "hunt": "kru",
                "night": "volkh",
                "lineage": "drak",
                "ritual": "zakhar",
                "power": "vasht",
            },
            semantic_domains={
                "hierarchy": ["drak", "vasht", "zakhar"],
                "hunting": ["sang", "kru", "volkh"],
            },
        ),
        seed_words=["sang", "kru", "volkh", "drak", "zakhar"],
        ai_model_hints="Dark, sibilant sounds. Ritualistic language. Focus on hierarchy and blood.",
    )


def create_werewolf_language() -> LanguageDefinition:
    """Create Werewolf language (Lycan) definition."""
    return LanguageDefinition(
        name="Werewolf",
        language_type=LanguageType.MONSTER,
        language_family="Lycan",
        culture="Werewolf",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u"],
            consonants=["k", "g", "x", "ʁ", "r", "h"],  # Guttural sounds
            unique_sounds=["ʁ", "x"],  # Growling sounds
            phonotactics={"max_syllables": 2, "prefer_gutturals": True},
            stress_patterns=["initial"],
        ),
        grammar_rules=GrammarRules(
            word_order="SOV",
            morphological_type="agglutinative",
            grammatical_categories={"aggression": ["low", "medium", "high"]},
            agreement_rules={"pack_hierarchy": True},
        ),
        lexicon=Lexicon(
            root_words={
                "pack": "ruk",
                "hunt": "gar",
                "territory": "thak",
                "alpha": "khan",
                "fight": "rak",
            },
            semantic_domains={
                "pack": ["ruk", "khan"],
                "hunting": ["gar", "thak", "rak"],
            },
        ),
        seed_words=["ruk", "gar", "thak", "khan", "rak"],
        ai_model_hints="Guttural, aggressive sounds. Pack dynamics. Focus on territory and hunting.",
    )


def create_zombie_language() -> LanguageDefinition:
    """Create Zombie language definition."""
    return LanguageDefinition(
        name="Zombie",
        language_type=LanguageType.MONSTER,
        language_family="Decayed",
        culture="Zombie",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "o"],  # Simplified
            consonants=["m", "n", "h", "g"],  # Decayed sounds
            unique_sounds=[],
            phonotactics={"max_syllables": 1, "simplified": True},
            stress_patterns=["monotone"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="isolating",  # Very simple
            grammatical_categories={},
            agreement_rules={},
        ),
        lexicon=Lexicon(
            root_words={
                "hunger": "brains",
                "eat": "eat",
                "hunt": "hunt",
            },
            semantic_domains={
                "basic_needs": ["brains", "eat", "hunt"],
            },
        ),
        seed_words=["brains", "eat", "hunt"],
        ai_model_hints="Decayed, simplified language. Basic needs only. Monotone delivery.",
    )


def create_ghoul_language() -> LanguageDefinition:
    """Create Ghoul language definition."""
    return LanguageDefinition(
        name="Ghoul",
        language_type=LanguageType.MONSTER,
        language_family="Guttural",
        culture="Ghoul",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "u"],
            consonants=["g", "k", "h", "x", "ʁ"],
            unique_sounds=["x", "ʁ"],
            phonotactics={"max_syllables": 2},
            stress_patterns=["initial"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="isolating",
            grammatical_categories={"hunger_level": ["low", "high"]},
            agreement_rules={},
        ),
        lexicon=Lexicon(
            root_words={
                "flesh": "gak",
                "eat": "hak",
                "hunger": "gah",
            },
            semantic_domains={
                "hunger": ["gak", "hak", "gah"],
            },
        ),
        seed_words=["gak", "hak", "gah"],
        ai_model_hints="Guttural, hunger-focused. Simple language about eating and hunger.",
    )


def create_lich_language() -> LanguageDefinition:
    """Create Lich language definition."""
    return LanguageDefinition(
        name="Lich",
        language_type=LanguageType.ANCIENT,
        language_family="Ritual",
        culture="Lich",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o"],
            consonants=["k", "th", "z", "sh", "v"],
            unique_sounds=["th", "z"],
            phonotactics={"max_syllables": 4, "ritualistic": True},
            stress_patterns=["ritual"],
        ),
        grammar_rules=GrammarRules(
            word_order="VSO",  # Verb-first for ritual
            morphological_type="fusional",
            grammatical_categories={"power_level": ["low", "medium", "high", "ultimate"]},
            agreement_rules={"ritual_complexity": True},
        ),
        lexicon=Lexicon(
            root_words={
                "power": "zath",
                "death": "mort",
                "ritual": "zak",
                "knowledge": "lore",
                "ancient": "veth",
            },
            semantic_domains={
                "power": ["zath", "zak", "veth"],
                "death": ["mort", "lore"],
            },
        ),
        seed_words=["zath", "mort", "zak", "lore", "veth"],
        ai_model_hints="Ancient, ritualistic language. Focus on power, death, and knowledge. Complex grammar.",
    )


def create_italian_language() -> LanguageDefinition:
    """Create Italian language definition."""
    return LanguageDefinition(
        name="Italian",
        language_type=LanguageType.HUMAN,
        language_family="Romance",
        culture="Italian",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u"],
            consonants=["b", "c", "d", "f", "g", "l", "m", "n", "p", "r", "s", "t", "v", "z"],
            unique_sounds=["r", "gl"],
            phonotactics={"max_syllables": 5},
            stress_patterns=["penultimate", "antepenultimate"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="fusional",
            grammatical_categories={"gender": ["masculine", "feminine"], "number": ["singular", "plural"]},
            agreement_rules={"gender_number": True},
        ),
        lexicon=Lexicon(
            root_words={},  # Would use real Italian vocabulary
            semantic_domains={},
        ),
        seed_words=[],
        ai_model_hints="Authentic Italian. Use proper grammar and vocabulary. Cultural context matters.",
    )


def create_french_language() -> LanguageDefinition:
    """Create French language definition."""
    return LanguageDefinition(
        name="French",
        language_type=LanguageType.HUMAN,
        language_family="Romance",
        culture="French",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u", "y", "ø", "œ"],
            consonants=["b", "c", "d", "f", "g", "j", "l", "m", "n", "p", "r", "s", "t", "v", "z"],
            unique_sounds=["r", "j"],
            phonotactics={"max_syllables": 4},
            stress_patterns=["final"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="fusional",
            grammatical_categories={"gender": ["masculine", "feminine"], "number": ["singular", "plural"]},
            agreement_rules={"gender_number": True},
        ),
        lexicon=Lexicon(
            root_words={},
            semantic_domains={},
        ),
        seed_words=[],
        ai_model_hints="Authentic French. Use proper grammar and vocabulary. Cultural context matters.",
    )


def create_spanish_language() -> LanguageDefinition:
    """Create Spanish language definition."""
    return LanguageDefinition(
        name="Spanish",
        language_type=LanguageType.HUMAN,
        language_family="Romance",
        culture="Spanish",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u"],
            consonants=["b", "c", "d", "f", "g", "j", "l", "m", "n", "p", "r", "s", "t", "v", "z"],
            unique_sounds=["r", "rr", "j"],
            phonotactics={"max_syllables": 5},
            stress_patterns=["penultimate", "antepenultimate"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="fusional",
            grammatical_categories={"gender": ["masculine", "feminine"], "number": ["singular", "plural"]},
            agreement_rules={"gender_number": True},
        ),
        lexicon=Lexicon(
            root_words={},
            semantic_domains={},
        ),
        seed_words=[],
        ai_model_hints="Authentic Spanish. Use proper grammar and vocabulary. Cultural context matters.",
    )


def create_common_language() -> LanguageDefinition:
    """Create Common language definition."""
    return LanguageDefinition(
        name="Common",
        language_type=LanguageType.HUMAN,
        language_family="Universal",
        culture="Common",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u"],
            consonants=["b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "z"],
            unique_sounds=[],
            phonotactics={"max_syllables": 5},
            stress_patterns=["variable"],
        ),
        grammar_rules=GrammarRules(
            word_order="SVO",
            morphological_type="isolating",
            grammatical_categories={},
            agreement_rules={},
        ),
        lexicon=Lexicon(
            root_words={},  # Would use English vocabulary
            semantic_domains={},
        ),
        seed_words=[],
        ai_model_hints="Universal language. Simple and clear. Used by all characters.",
    )


def create_music_language() -> LanguageDefinition:
    """Create Music language definition (copyright-free)."""
    return LanguageDefinition(
        name="Music",
        language_type=LanguageType.MUSIC,
        language_family="Phonetic",
        culture="Musical",
        phoneme_inventory=PhonemeInventory(
            vowels=["a", "e", "i", "o", "u", "ai", "ei", "ou"],
            consonants=["l", "m", "n", "r", "s", "v", "z"],
            unique_sounds=["ai", "ei", "ou"],
            phonotactics={"max_syllables": 3, "melodic": True},
            stress_patterns=["melodic"],
        ),
        grammar_rules=GrammarRules(
            word_order="free",  # Flexible for music
            morphological_type="isolating",
            grammatical_categories={},
            agreement_rules={},
        ),
        lexicon=Lexicon(
            root_words={},  # Generated procedurally
            semantic_domains={},
        ),
        seed_words=[],
        ai_model_hints="Phoneme-based generation for lyrics. No recognizable linguistic structure. Melodic patterns.",
    )


