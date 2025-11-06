"""
Mannerism & Movement Profile System - Unique movement and gesture patterns per NPC.

Implements REQ-NPC-002: Mannerism & Movement Profile System.

Each NPC has unique mannerisms, movement patterns, and gesture styles that
make them visually and behaviorally distinct.
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


class MovementStyle(Enum):
    """Movement style."""
    NEUTRAL = "neutral"
    ELEGANT = "elegant"
    GRACEFUL = "graceful"
    CLUMSY = "clumsy"
    AGGRESSIVE = "aggressive"
    CAREFUL = "careful"
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    RELAXED = "relaxed"


class GestureFrequency(Enum):
    """Gesture frequency level."""
    RARELY = "rarely"      # Almost no gestures
    OCCASIONALLY = "occasionally"  # Some gestures
    FREQUENTLY = "frequently"  # Many gestures
    CONSTANTLY = "constantly"  # Gestures constantly


@dataclass
class MannerismProfile:
    """Mannerism and movement profile for an NPC."""
    npc_id: UUID
    
    # Movement characteristics
    movement_style: MovementStyle = MovementStyle.NEUTRAL
    walking_speed_multiplier: float = 1.0  # 0.5 (slow) to 1.5 (fast)
    posture: str = "normal"  # "upright", "slouched", "proud", "hunched"
    stride_length: float = 1.0  # 0.5 (short) to 1.5 (long)
    movement_confidence: float = 0.5  # 0.0 (hesitant) to 1.0 (confident)
    
    # Gesture patterns
    gesture_frequency: GestureFrequency = GestureFrequency.OCCASIONALLY
    preferred_gestures: List[str] = field(default_factory=list)  # "wave", "point", "scratch_head"
    gesture_intensity: float = 0.5  # 0.0 (subtle) to 1.0 (dramatic)
    gesture_speed: float = 0.5  # 0.0 (slow) to 1.0 (fast)
    
    # Idle behaviors
    idle_animations: List[str] = field(default_factory=list)  # "fidget", "look_around", "lean"
    idle_animation_frequency: float = 0.3  # How often idle animations play
    fidget_behaviors: List[str] = field(default_factory=list)  # "tap_foot", "twirl_hair", "adjust_clothes"
    
    # Facial expressions (while idle/moving)
    default_expression: str = "neutral"
    expression_variation: float = 0.3  # How much expressions vary
    blinking_rate: float = 0.5  # 0.0 (rare) to 1.0 (frequent)
    
    # Breathing and subtle movements
    breathing_rate: float = 0.5  # 0.0 (slow) to 1.0 (fast)
    breathing_intensity: float = 0.5  # 0.0 (shallow) to 1.0 (deep)
    micro_movements: bool = True  # Subtle head movements, weight shifts
    
    # Combat/posture transitions
    combat_stance: str = "default"  # "aggressive", "defensive", "balanced"
    transition_speed: float = 0.5  # How quickly NPC transitions between states
    
    # Cultural/character influences
    character_traits: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate all float values are in appropriate ranges."""
        # 0.0-1.0 range fields
        float_fields_01 = [
            'movement_confidence', 'gesture_intensity', 'gesture_speed',
            'idle_animation_frequency', 'expression_variation', 'blinking_rate',
            'breathing_rate', 'breathing_intensity', 'transition_speed'
        ]
        
        for field_name in float_fields_01:
            value = getattr(self, field_name, None)
            if value is not None:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"{field_name} must be numeric, got {type(value)}")
                value = float(value)
                if not 0.0 <= value <= 1.0:
                    raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")
                setattr(self, field_name, value)
        
        # 0.5-1.5 range fields (walking_speed_multiplier, stride_length)
        range_fields = {
            'walking_speed_multiplier': (0.5, 1.5),
            'stride_length': (0.5, 1.5)
        }
        
        for field_name, (min_val, max_val) in range_fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                if not isinstance(value, (int, float)):
                    raise TypeError(f"{field_name} must be numeric, got {type(value)}")
                value = float(value)
                if not min_val <= value <= max_val:
                    raise ValueError(f"{field_name} must be between {min_val} and {max_val}, got {value}")
                setattr(self, field_name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        if not isinstance(self.npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(self.npc_id)}")
        
        return {
            "npc_id": str(self.npc_id),
            "movement_style": self.movement_style.value,
            "walking_speed_multiplier": self.walking_speed_multiplier,
            "posture": self.posture,
            "stride_length": self.stride_length,
            "movement_confidence": self.movement_confidence,
            "gesture_frequency": self.gesture_frequency.value,
            "preferred_gestures": self.preferred_gestures.copy(),
            "gesture_intensity": self.gesture_intensity,
            "gesture_speed": self.gesture_speed,
            "idle_animations": self.idle_animations.copy(),
            "idle_animation_frequency": self.idle_animation_frequency,
            "fidget_behaviors": self.fidget_behaviors.copy(),
            "default_expression": self.default_expression,
            "expression_variation": self.expression_variation,
            "blinking_rate": self.blinking_rate,
            "breathing_rate": self.breathing_rate,
            "breathing_intensity": self.breathing_intensity,
            "micro_movements": self.micro_movements,
            "combat_stance": self.combat_stance,
            "transition_speed": self.transition_speed,
            "character_traits": self.character_traits.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MannerismProfile":
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        
        # Validate required fields
        required_fields = ["npc_id"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        try:
            npc_id = UUID(data["npc_id"])
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"Invalid npc_id: {e}")
        
        try:
            movement_style = MovementStyle(data.get("movement_style", "neutral"))
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid movement_style: {e}")
        
        try:
            gesture_frequency = GestureFrequency(data.get("gesture_frequency", "occasionally"))
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid gesture_frequency: {e}")
        
        # Helper to safely get and validate float in 0.0-1.0 range
        def get_float_01(key: str, default: float) -> float:
            value = data.get(key, default)
            if not isinstance(value, (int, float)):
                raise TypeError(f"{key} must be numeric, got {type(value)}")
            value = float(value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{key} must be between 0.0 and 1.0, got {value}")
            return value
        
        # Helper to safely get float in custom range
        def get_float_range(key: str, default: float, min_val: float, max_val: float) -> float:
            value = data.get(key, default)
            if not isinstance(value, (int, float)):
                raise TypeError(f"{key} must be numeric, got {type(value)}")
            value = float(value)
            if not min_val <= value <= max_val:
                raise ValueError(f"{key} must be between {min_val} and {max_val}, got {value}")
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
                movement_style=movement_style,
                walking_speed_multiplier=get_float_range("walking_speed_multiplier", 1.0, 0.5, 1.5),
                posture=data.get("posture", "normal"),
                stride_length=get_float_range("stride_length", 1.0, 0.5, 1.5),
                movement_confidence=get_float_01("movement_confidence", 0.5),
                gesture_frequency=gesture_frequency,
                preferred_gestures=get_list("preferred_gestures"),
                gesture_intensity=get_float_01("gesture_intensity", 0.5),
                gesture_speed=get_float_01("gesture_speed", 0.5),
                idle_animations=get_list("idle_animations"),
                idle_animation_frequency=get_float_01("idle_animation_frequency", 0.3),
                fidget_behaviors=get_list("fidget_behaviors"),
                default_expression=data.get("default_expression", "neutral"),
                expression_variation=get_float_01("expression_variation", 0.3),
                blinking_rate=get_float_01("blinking_rate", 0.5),
                breathing_rate=get_float_01("breathing_rate", 0.5),
                breathing_intensity=get_float_01("breathing_intensity", 0.5),
                micro_movements=data.get("micro_movements", True),
                combat_stance=data.get("combat_stance", "default"),
                transition_speed=get_float_01("transition_speed", 0.5),
                character_traits=get_dict("character_traits"),
            )
        except Exception as e:
            raise ValueError(f"Failed to create MannerismProfile from dict: {e}")


class MannerismGenerator:
    """
    Generates mannerism profiles for NPCs.
    
    Creates unique movement and gesture patterns based on NPC type, personality, and context.
    Thread-safe for concurrent profile generation.
    """
    
    def __init__(self):
        self._lock = Lock()
        # Templates for different NPC types (immutable)
        self._npc_type_templates = {
            "noble": {
                "movement_style": MovementStyle.ELEGANT,
                "walking_speed_multiplier": 0.8,
                "posture": "upright",
                "stride_length": 0.9,
                "movement_confidence": 0.9,
                "gesture_frequency": GestureFrequency.OCCASIONALLY,
                "preferred_gestures": ["regal_wave", "point_authoritatively", "adjust_crown"],
                "gesture_intensity": 0.7,
                "idle_animations": ["inspect_surroundings", "adjust_garments"],
                "fidget_behaviors": ["smooth_robe", "adjust_jewelry"],
            },
            "commoner": {
                "movement_style": MovementStyle.RELAXED,
                "walking_speed_multiplier": 1.0,
                "posture": "normal",
                "stride_length": 1.0,
                "movement_confidence": 0.6,
                "gesture_frequency": GestureFrequency.FREQUENTLY,
                "preferred_gestures": ["scratch_head", "wave_casually", "point"],
                "gesture_intensity": 0.5,
                "idle_animations": ["lean_against_wall", "look_around"],
                "fidget_behaviors": ["tap_foot", "adjust_clothes"],
            },
            "warrior": {
                "movement_style": MovementStyle.CONFIDENT,
                "walking_speed_multiplier": 1.1,
                "posture": "upright",
                "stride_length": 1.2,
                "movement_confidence": 0.9,
                "gesture_frequency": GestureFrequency.OCCASIONALLY,
                "preferred_gestures": ["clench_fist", "point_aggressively", "cross_arms"],
                "gesture_intensity": 0.8,
                "combat_stance": "aggressive",
                "idle_animations": ["survey_area", "check_weapon"],
                "fidget_behaviors": ["crack_knuckles", "adjust_armor"],
            },
            "scholar": {
                "movement_style": MovementStyle.CAREFUL,
                "walking_speed_multiplier": 0.7,
                "posture": "slightly_hunched",
                "stride_length": 0.8,
                "movement_confidence": 0.5,
                "gesture_frequency": GestureFrequency.FREQUENTLY,
                "preferred_gestures": ["adjust_glasses", "stroke_beard", "point_thoughtfully"],
                "gesture_intensity": 0.4,
                "idle_animations": ["read_book", "ponder", "look_through_lens"],
                "fidget_behaviors": ["twirl_pen", "adjust_glasses"],
            },
            "merchant": {
                "movement_style": MovementStyle.CONFIDENT,
                "walking_speed_multiplier": 1.0,
                "posture": "normal",
                "stride_length": 1.0,
                "movement_confidence": 0.8,
                "gesture_frequency": GestureFrequency.FREQUENTLY,
                "preferred_gestures": ["rub_hands", "show_goods", "point_at_item"],
                "gesture_intensity": 0.6,
                "idle_animations": ["organize_goods", "count_coins"],
                "fidget_behaviors": ["count_coins", "organize_items"],
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
    ) -> MannerismProfile:
        """
        Generate mannerism profile for NPC.
        
        Args:
            npc_id: NPC UUID
            npc_type: Type of NPC (noble, commoner, warrior, etc.)
            personality: Personality traits
            context: Additional context
        
        Returns:
            Mannerism profile
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
        profile = MannerismProfile(npc_id=npc_id)
        
        # Apply NPC type template (thread-safe)
        with self._lock:
            if npc_type in self._npc_type_templates:
                template = deepcopy(self._npc_type_templates[npc_type])
            else:
                template = None
        
        if template:
            for key, value in template.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
        
        # Adjust based on personality
        if personality:
            # Validate personality values
            for key, value in personality.items():
                if not isinstance(value, (int, float)):
                    raise TypeError(f"personality[{key}] must be numeric, got {type(value)}")
                if not 0.0 <= float(value) <= 1.0:
                    raise ValueError(f"personality[{key}] must be 0.0-1.0, got {value}")
            
            # Extraversion affects gesture frequency and movement confidence
            extraversion = personality.get("extraversion", 0.5)
            if extraversion > 0.7:
                profile.gesture_frequency = GestureFrequency.FREQUENTLY
                profile.movement_confidence = self._clamp(profile.movement_confidence + 0.2)
            elif extraversion < 0.3:
                profile.gesture_frequency = GestureFrequency.RARELY
                profile.movement_confidence = self._clamp(profile.movement_confidence - 0.2)
            
            # Neuroticism affects movement speed and fidgeting
            neuroticism = personality.get("neuroticism", 0.5)
            if neuroticism > 0.7:
                profile.walking_speed_multiplier = self._clamp(profile.walking_speed_multiplier + 0.2, 0.5, 1.5)
                profile.fidget_behaviors.extend(["tap_foot", "fidget_hands"])
                profile.idle_animation_frequency = self._clamp(profile.idle_animation_frequency + 0.3)
            elif neuroticism < 0.3:
                profile.walking_speed_multiplier = self._clamp(profile.walking_speed_multiplier - 0.1, 0.5, 1.5)
            
            # Agreeableness affects gesture intensity
            agreeableness = personality.get("agreeableness", 0.5)
            if agreeableness > 0.7:
                profile.gesture_intensity = self._clamp(profile.gesture_intensity + 0.2)
            elif agreeableness < 0.3:
                profile.gesture_intensity = self._clamp(profile.gesture_intensity - 0.2)
            
            # Aggression affects combat stance and movement style
            aggression = personality.get("aggression", 0.3)
            if aggression > 0.7:
                profile.combat_stance = "aggressive"
                profile.movement_style = MovementStyle.AGGRESSIVE
                profile.walking_speed_multiplier = self._clamp(profile.walking_speed_multiplier + 0.2, 0.5, 1.5)
        
        # Apply context modifiers
        if context:
            if context.get("injured", False):
                if not isinstance(context.get("injured"), bool):
                    raise TypeError("context['injured'] must be bool")
                profile.walking_speed_multiplier = self._clamp(profile.walking_speed_multiplier * 0.7, 0.5, 1.5)
                profile.movement_confidence = self._clamp(profile.movement_confidence * 0.6)
                profile.posture = "hunched"
            
            if context.get("excited", False):
                if not isinstance(context.get("excited"), bool):
                    raise TypeError("context['excited'] must be bool")
                profile.gesture_frequency = GestureFrequency.FREQUENTLY
                profile.gesture_intensity = self._clamp(profile.gesture_intensity + 0.3)
                profile.walking_speed_multiplier = self._clamp(profile.walking_speed_multiplier + 0.2, 0.5, 1.5)
            
            if context.get("tired", False):
                if not isinstance(context.get("tired"), bool):
                    raise TypeError("context['tired'] must be bool")
                profile.walking_speed_multiplier = self._clamp(profile.walking_speed_multiplier * 0.8, 0.5, 1.5)
                profile.movement_confidence = self._clamp(profile.movement_confidence * 0.7)
                profile.idle_animation_frequency = self._clamp(profile.idle_animation_frequency * 0.5)
        
        return profile


class MannerismManager:
    """
    Manages mannerism profiles for NPCs.
    
    Stores, retrieves, and applies mannerism profiles.
    """
    
    def __init__(self):
        self.profiles: Dict[UUID, MannerismProfile] = {}
        self.generator = MannerismGenerator()
    
    def get_or_generate_profile(
        self,
        npc_id: UUID,
        npc_type: str = "generic",
        personality: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MannerismProfile:
        """Get existing profile or generate new one."""
        if npc_id not in self.profiles:
            profile = self.generator.generate_profile(npc_id, npc_type, personality, context)
            self.profiles[npc_id] = profile
        return self.profiles[npc_id]
    
    def get_profile(self, npc_id: UUID) -> Optional[MannerismProfile]:
        """Get mannerism profile for NPC."""
        return self.profiles.get(npc_id)
    
    def save_profile(self, profile: MannerismProfile):
        """Save mannerism profile."""
        self.profiles[profile.npc_id] = profile
    
    def get_movement_parameters(self, npc_id: UUID) -> Dict[str, Any]:
        """Get movement parameters for game engine."""
        profile = self.get_profile(npc_id)
        if not profile:
            return {}
        
        return {
            "walking_speed_multiplier": profile.walking_speed_multiplier,
            "posture": profile.posture,
            "stride_length": profile.stride_length,
            "movement_confidence": profile.movement_confidence,
            "movement_style": profile.movement_style.value,
            "combat_stance": profile.combat_stance,
            "transition_speed": profile.transition_speed,
        }
    
    def get_gesture_parameters(self, npc_id: UUID) -> Dict[str, Any]:
        """Get gesture parameters for animation system."""
        profile = self.get_profile(npc_id)
        if not profile:
            return {}
        
        return {
            "gesture_frequency": profile.gesture_frequency.value,
            "preferred_gestures": profile.preferred_gestures,
            "gesture_intensity": profile.gesture_intensity,
            "gesture_speed": profile.gesture_speed,
        }
    
    def get_idle_parameters(self, npc_id: UUID) -> Dict[str, Any]:
        """Get idle animation parameters."""
        profile = self.get_profile(npc_id)
        if not profile:
            return {}
        
        return {
            "idle_animations": profile.idle_animations,
            "idle_animation_frequency": profile.idle_animation_frequency,
            "fidget_behaviors": profile.fidget_behaviors,
            "default_expression": profile.default_expression,
            "expression_variation": profile.expression_variation,
            "blinking_rate": profile.blinking_rate,
            "breathing_rate": profile.breathing_rate,
            "breathing_intensity": profile.breathing_intensity,
            "micro_movements": profile.micro_movements,
        }

