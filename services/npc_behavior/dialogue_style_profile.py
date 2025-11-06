"""
Dialogue Style Profile System - Unique speaking patterns per NPC.

Implements REQ-NPC-001: Dialogue Style Profile System.

Each NPC has a unique dialogue style profile that influences:
- Vocabulary choices
- Sentence structure
- Formality level
- Emotional expression
- Speaking pace
- Rhetorical patterns
"""

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy
from threading import Lock

_logger = logging.getLogger(__name__)


class FormalityLevel(Enum):
    """Formality level."""
    VERY_FORMAL = "very_formal"
    FORMAL = "formal"
    NEUTRAL = "neutral"
    INFORMAL = "informal"
    VERY_INFORMAL = "very_informal"


class EmotionalRange(Enum):
    """Emotional expression range."""
    RESERVED = "reserved"      # Minimal emotional expression
    MODERATE = "moderate"      # Balanced emotional expression
    EXPRESSIVE = "expressive"  # Strong emotional expression
    DRAMATIC = "dramatic"      # Very strong emotional expression


@dataclass
class DialogueStyleProfile:
    """Dialogue style profile for an NPC."""
    npc_id: UUID
    
    # Core style parameters
    formality: FormalityLevel = FormalityLevel.NEUTRAL
    emotional_range: EmotionalRange = EmotionalRange.MODERATE
    vocabulary_complexity: float = 0.5  # 0.0 (simple) to 1.0 (complex)
    sentence_length_preference: float = 0.5  # 0.0 (short) to 1.0 (long)
    speaking_pace: float = 0.5  # 0.0 (slow) to 1.0 (fast)
    
    # Vocabulary preferences
    preferred_words: List[str] = field(default_factory=list)
    avoided_words: List[str] = field(default_factory=list)
    catchphrases: List[str] = field(default_factory=list)
    
    # Rhetorical patterns
    use_questions: float = 0.3  # Frequency of questions
    use_exclamations: float = 0.2  # Frequency of exclamations
    use_metaphors: float = 0.3  # Frequency of metaphors
    use_humor: float = 0.2  # Frequency of humor
    use_filler_words: float = 0.2  # Frequency of filler words
    
    # Speech patterns
    filler_words: List[str] = field(default_factory=list)  # "um", "uh", "like"
    discourse_markers: List[str] = field(default_factory=list)  # "well", "so", "actually"
    interjections: List[str] = field(default_factory=list)  # "oh", "ah", "hmm"
    
    # Sentence structure
    prefer_active_voice: bool = True
    sentence_complexity: float = 0.5  # Simple vs. complex sentences
    
    # Cultural/regional influences
    dialect_features: Dict[str, Any] = field(default_factory=dict)
    accent_markers: List[str] = field(default_factory=list)
    
    # Contextual modifiers
    context_modifiers: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate float ranges after initialization."""
        float_fields = [
            'vocabulary_complexity', 'sentence_length_preference', 'speaking_pace',
            'use_questions', 'use_exclamations', 'use_metaphors', 'use_humor',
            'sentence_complexity', 'use_filler_words'
        ]
        
        for field_name in float_fields:
            value = getattr(self, field_name, None)
            if value is not None:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"{field_name} must be numeric, got {type(value)}")
                value = float(value)
                if not 0.0 <= value <= 1.0:
                    raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")
                setattr(self, field_name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        if not isinstance(self.npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(self.npc_id)}")
        
        return {
            "npc_id": str(self.npc_id),
            "formality": self.formality.value,
            "emotional_range": self.emotional_range.value,
            "vocabulary_complexity": self.vocabulary_complexity,
            "sentence_length_preference": self.sentence_length_preference,
            "speaking_pace": self.speaking_pace,
            "preferred_words": self.preferred_words.copy(),
            "avoided_words": self.avoided_words.copy(),
            "catchphrases": self.catchphrases.copy(),
            "use_questions": self.use_questions,
            "use_exclamations": self.use_exclamations,
            "use_metaphors": self.use_metaphors,
            "use_humor": self.use_humor,
            "use_filler_words": self.use_filler_words,
            "filler_words": self.filler_words.copy(),
            "discourse_markers": self.discourse_markers.copy(),
            "interjections": self.interjections.copy(),
            "prefer_active_voice": self.prefer_active_voice,
            "sentence_complexity": self.sentence_complexity,
            "dialect_features": self.dialect_features.copy(),
            "accent_markers": self.accent_markers.copy(),
            "context_modifiers": self.context_modifiers.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueStyleProfile":
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        
        # Validate required fields
        required_fields = ["npc_id", "formality", "emotional_range"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        try:
            npc_id = UUID(data["npc_id"])
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"Invalid npc_id: {e}")
        
        try:
            formality = FormalityLevel(data["formality"])
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid formality level: {e}")
        
        try:
            emotional_range = EmotionalRange(data["emotional_range"])
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid emotional range: {e}")
        
        # Helper to safely get and validate float
        def get_float(key: str, default: float) -> float:
            value = data.get(key, default)
            if not isinstance(value, (int, float)):
                raise TypeError(f"{key} must be numeric, got {type(value)}")
            value = float(value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{key} must be between 0.0 and 1.0, got {value}")
            return value
        
        # Helper to safely get list
        def get_list(key: str, default: Optional[List] = None) -> List:
            value = data.get(key, default or [])
            if not isinstance(value, list):
                raise TypeError(f"{key} must be a list, got {type(value)}")
            return value
        
        # Helper to safely get dict
        def get_dict(key: str, default: Optional[Dict] = None) -> Dict:
            value = data.get(key, default or {})
            if not isinstance(value, dict):
                raise TypeError(f"{key} must be a dict, got {type(value)}")
            return value
        
        try:
            return cls(
                npc_id=npc_id,
                formality=formality,
                emotional_range=emotional_range,
                vocabulary_complexity=get_float("vocabulary_complexity", 0.5),
                sentence_length_preference=get_float("sentence_length_preference", 0.5),
                speaking_pace=get_float("speaking_pace", 0.5),
                preferred_words=get_list("preferred_words"),
                avoided_words=get_list("avoided_words"),
                catchphrases=get_list("catchphrases"),
                use_questions=get_float("use_questions", 0.3),
                use_exclamations=get_float("use_exclamations", 0.2),
                use_metaphors=get_float("use_metaphors", 0.3),
                use_humor=get_float("use_humor", 0.2),
                use_filler_words=get_float("use_filler_words", 0.2),
                filler_words=get_list("filler_words"),
                discourse_markers=get_list("discourse_markers"),
                interjections=get_list("interjections"),
                prefer_active_voice=data.get("prefer_active_voice", True),
                sentence_complexity=get_float("sentence_complexity", 0.5),
                dialect_features=get_dict("dialect_features"),
                accent_markers=get_list("accent_markers"),
                context_modifiers=get_dict("context_modifiers"),
            )
        except Exception as e:
            raise ValueError(f"Failed to create DialogueStyleProfile from dict: {e}")


class DialogueStyleGenerator:
    """
    Generates dialogue style profiles for NPCs.
    
    Creates unique speaking patterns based on NPC type, personality, and context.
    Thread-safe for concurrent profile generation.
    """
    
    def __init__(self):
        self._lock = Lock()
        # Templates for different NPC types (immutable)
        self._npc_type_templates = {
            "noble": {
                "formality": FormalityLevel.FORMAL,
                "vocabulary_complexity": 0.8,
                "sentence_length_preference": 0.7,
                "preferred_words": ["indeed", "certainly", "precisely", "perhaps"],
                "avoided_words": ["ain't", "gonna", "wanna"],
                "catchphrases": ["I assure you", "Quite so"],
            },
            "commoner": {
                "formality": FormalityLevel.INFORMAL,
                "vocabulary_complexity": 0.3,
                "sentence_length_preference": 0.3,
                "preferred_words": ["aye", "nay", "reckon"],
                "filler_words": ["um", "uh", "like"],
                "catchphrases": ["I reckon", "Well now"],
            },
            "scholar": {
                "formality": FormalityLevel.FORMAL,
                "vocabulary_complexity": 0.9,
                "sentence_length_preference": 0.9,
                "preferred_words": ["furthermore", "consequently", "nevertheless"],
                "use_metaphors": 0.6,
                "catchphrases": ["To be precise", "It follows that"],
            },
            "merchant": {
                "formality": FormalityLevel.NEUTRAL,
                "vocabulary_complexity": 0.5,
                "sentence_length_preference": 0.5,
                "preferred_words": ["indeed", "certainly", "absolutely"],
                "use_questions": 0.5,
                "catchphrases": ["Best price", "Quality goods"],
            },
            "warrior": {
                "formality": FormalityLevel.INFORMAL,
                "vocabulary_complexity": 0.4,
                "sentence_length_preference": 0.3,
                "preferred_words": ["aye", "nay", "bloody"],
                "use_exclamations": 0.4,
                "catchphrases": ["By the gods", "For honor"],
            },
        }
    
    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to range [min_val, max_val]."""
        return max(min_val, min(max_val, float(value)))
    
    def generate_profile(
        self,
        npc_id: UUID,
        npc_type: str = "generic",
        personality: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> DialogueStyleProfile:
        """
        Generate dialogue style profile for NPC.
        
        Args:
            npc_id: NPC UUID
            npc_type: Type of NPC (noble, commoner, scholar, etc.)
            personality: Personality traits (from personality_system)
            context: Additional context (background, culture, etc.)
        
        Returns:
            Dialogue style profile
        """
        # Validate inputs
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        
        if not isinstance(npc_type, str):
            raise TypeError(f"npc_type must be str, got {type(npc_type)}")
        
        if personality is not None and not isinstance(personality, dict):
            raise TypeError(f"personality must be dict or None, got {type(personality)}")
        
        if context is not None and not isinstance(context, dict):
            raise TypeError(f"context must be dict or None, got {type(context)}")
        
        # Start with base profile
        profile = DialogueStyleProfile(npc_id=npc_id)
        
        # Apply NPC type template (thread-safe)
        with self._lock:
            if npc_type in self._npc_type_templates:
                template = deepcopy(self._npc_type_templates[npc_type])
            else:
                template = None
        
        if template:
            
            if "formality" in template:
                profile.formality = template["formality"]
            if "vocabulary_complexity" in template:
                profile.vocabulary_complexity = template["vocabulary_complexity"]
            if "sentence_length_preference" in template:
                profile.sentence_length_preference = template["sentence_length_preference"]
            if "preferred_words" in template:
                profile.preferred_words = template["preferred_words"].copy()
            if "avoided_words" in template:
                profile.avoided_words = template["avoided_words"].copy()
            if "catchphrases" in template:
                profile.catchphrases = template["catchphrases"].copy()
            if "filler_words" in template:
                profile.filler_words = template["filler_words"].copy()
            if "use_questions" in template:
                profile.use_questions = template["use_questions"]
            if "use_exclamations" in template:
                profile.use_exclamations = template["use_exclamations"]
            if "use_metaphors" in template:
                profile.use_metaphors = template["use_metaphors"]
        
        # Adjust based on personality
        if personality:
            # Validate personality values
            for key, value in personality.items():
                if not isinstance(value, (int, float)):
                    raise TypeError(f"personality[{key}] must be numeric, got {type(value)}")
                if not 0.0 <= float(value) <= 1.0:
                    raise ValueError(f"personality[{key}] must be 0.0-1.0, got {value}")
            
            # Extraversion affects emotional expression
            extraversion = personality.get("extraversion", 0.5)
            if extraversion > 0.7:
                profile.emotional_range = EmotionalRange.EXPRESSIVE
                profile.use_exclamations = self._clamp(profile.use_exclamations + 0.2)
            elif extraversion < 0.3:
                profile.emotional_range = EmotionalRange.RESERVED
                profile.use_exclamations = self._clamp(profile.use_exclamations - 0.2)
            
            # Openness affects vocabulary complexity
            openness = personality.get("openness", 0.5)
            profile.vocabulary_complexity = self._clamp(
                profile.vocabulary_complexity + (openness - 0.5) * 0.3
            )
            
            # Agreeableness affects formality
            agreeableness = personality.get("agreeableness", 0.5)
            if agreeableness > 0.7:
                # More polite = more formal
                if profile.formality == FormalityLevel.INFORMAL:
                    profile.formality = FormalityLevel.NEUTRAL
                elif profile.formality == FormalityLevel.NEUTRAL:
                    profile.formality = FormalityLevel.FORMAL
            
            # Neuroticism affects speaking pace
            neuroticism = personality.get("neuroticism", 0.5)
            profile.speaking_pace = min(1.0, profile.speaking_pace + (neuroticism - 0.5) * 0.2)
        
        # Apply context modifiers
        if context:
            if context.get("stressed", False):
                if not isinstance(context.get("stressed"), bool):
                    raise TypeError("context['stressed'] must be bool")
                profile.speaking_pace = self._clamp(profile.speaking_pace + 0.2)
                profile.use_filler_words = self._clamp(profile.use_filler_words + 0.1)
            
            if context.get("excited", False):
                profile.use_exclamations = min(0.6, profile.use_exclamations + 0.3)
                profile.emotional_range = EmotionalRange.EXPRESSIVE
            
            if context.get("cultural_region"):
                # Add dialect features based on region
                region = context["cultural_region"]
                profile.dialect_features = self._get_dialect_features(region)
        
        return profile
    
    def _get_dialect_features(self, region: str) -> Dict[str, Any]:
        """Get dialect features for a region."""
        # Simplified dialect features
        dialect_templates = {
            "northern": {
                "accent_markers": ["aye", "nay"],
                "contractions": False,
            },
            "southern": {
                "accent_markers": ["y'all", "reckon"],
                "contractions": True,
            },
            "eastern": {
                "accent_markers": ["indeed", "quite"],
                "contractions": False,
            },
            "western": {
                "accent_markers": ["partner", "howdy"],
                "contractions": True,
            },
        }
        return dialect_templates.get(region, {})


class DialogueStyleManager:
    """
    Manages dialogue style profiles for NPCs.
    
    Stores, retrieves, and applies dialogue style profiles.
    """
    
    def __init__(self):
        self.profiles: Dict[UUID, DialogueStyleProfile] = {}
        self.generator = DialogueStyleGenerator()
    
    def get_or_generate_profile(
        self,
        npc_id: UUID,
        npc_type: str = "generic",
        personality: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> DialogueStyleProfile:
        """Get existing profile or generate new one."""
        if npc_id not in self.profiles:
            profile = self.generator.generate_profile(npc_id, npc_type, personality, context)
            self.profiles[npc_id] = profile
        return self.profiles[npc_id]
    
    def get_profile(self, npc_id: UUID) -> Optional[DialogueStyleProfile]:
        """Get dialogue style profile for NPC."""
        return self.profiles.get(npc_id)
    
    def save_profile(self, profile: DialogueStyleProfile):
        """Save dialogue style profile."""
        self.profiles[profile.npc_id] = profile
    
    def apply_style_to_prompt(
        self,
        profile: DialogueStyleProfile,
        base_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Apply dialogue style to prompt for LLM generation.
        
        Args:
            profile: Dialogue style profile
            base_prompt: Base prompt for dialogue generation
            context: Additional context
        
        Returns:
            Styled prompt
        """
        style_instructions = []
        
        # Formality
        formality_map = {
            FormalityLevel.VERY_FORMAL: "Use very formal language with proper grammar and titles.",
            FormalityLevel.FORMAL: "Use formal language with proper grammar.",
            FormalityLevel.NEUTRAL: "Use neutral, conversational language.",
            FormalityLevel.INFORMAL: "Use informal, casual language.",
            FormalityLevel.VERY_INFORMAL: "Use very informal, slang-heavy language.",
        }
        style_instructions.append(formality_map.get(profile.formality, ""))
        
        # Emotional range
        emotional_map = {
            EmotionalRange.RESERVED: "Express emotions minimally and subtly.",
            EmotionalRange.MODERATE: "Express emotions in a balanced way.",
            EmotionalRange.EXPRESSIVE: "Express emotions clearly and openly.",
            EmotionalRange.DRAMATIC: "Express emotions dramatically and intensely.",
        }
        style_instructions.append(emotional_map.get(profile.emotional_range, ""))
        
        # Vocabulary
        if profile.vocabulary_complexity > 0.7:
            style_instructions.append("Use sophisticated vocabulary and complex words.")
        elif profile.vocabulary_complexity < 0.3:
            style_instructions.append("Use simple, everyday vocabulary.")
        
        # Sentence length
        if profile.sentence_length_preference > 0.7:
            style_instructions.append("Use longer, more complex sentences.")
        elif profile.sentence_length_preference < 0.3:
            style_instructions.append("Use short, direct sentences.")
        
        # Preferred words
        if profile.preferred_words:
            style_instructions.append(f"Prefer using these words: {', '.join(profile.preferred_words)}")
        
        # Avoided words
        if profile.avoided_words:
            style_instructions.append(f"Avoid using these words: {', '.join(profile.avoided_words)}")
        
        # Catchphrases
        if profile.catchphrases:
            style_instructions.append(f"Include catchphrases occasionally: {', '.join(profile.catchphrases)}")
        
        # Rhetorical patterns
        if profile.use_questions > 0.4:
            style_instructions.append("Ask questions frequently.")
        if profile.use_exclamations > 0.4:
            style_instructions.append("Use exclamations frequently.")
        if profile.use_metaphors > 0.4:
            style_instructions.append("Use metaphors and analogies.")
        if profile.use_humor > 0.4:
            style_instructions.append("Include humor and wit.")
        
        # Combine instructions
        style_text = "\n".join([s for s in style_instructions if s])
        
        styled_prompt = f"""{base_prompt}

DIALOGUE STYLE INSTRUCTIONS:
{style_text}

Generate dialogue following these style guidelines."""
        
        return styled_prompt

