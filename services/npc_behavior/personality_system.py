"""
Personality System - NPC personality traits and decision influence.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID


class PersonalitySystem:
    """
    Manages NPC personality traits and their influence on behavior decisions.
    Uses Big Five personality model as base.
    """
    
    # Personality trait dimensions
    TRAIT_DIMENSIONS = {
        "openness": {"min": 0.0, "max": 1.0, "default": 0.5},
        "conscientiousness": {"min": 0.0, "max": 1.0, "default": 0.5},
        "extraversion": {"min": 0.0, "max": 1.0, "default": 0.5},
        "agreeableness": {"min": 0.0, "max": 1.0, "default": 0.5},
        "neuroticism": {"min": 0.0, "max": 1.0, "default": 0.5},
        "aggression": {"min": 0.0, "max": 1.0, "default": 0.3},
        "social": {"min": 0.0, "max": 1.0, "default": 0.5},
        "curiosity": {"min": 0.0, "max": 1.0, "default": 0.5},
    }
    
    def score_action(self, personality: Dict[str, float], action: str, context: Dict[str, Any]) -> float:
        """
        Score how likely an NPC is to take a given action based on personality.
        
        Args:
            personality: NPC personality traits
            action: Action type to score
            context: Context for the action
        
        Returns:
            Score from 0.0 to 1.0 (higher = more likely)
        """
        base_score = 0.5
        
        # Adjust based on action type
        if action == "combat" or action == "aggressive":
            # Aggressive personalities prefer combat
            aggression = personality.get("aggression", 0.3)
            neuroticism = personality.get("neuroticism", 0.5)
            base_score = (aggression * 0.6) + (neuroticism * 0.4)
        
        elif action == "social" or action == "interaction":
            # Extraverted and social personalities prefer interactions
            extraPeak = personality.get("extraversion", 0.5)
            social = personality.get("social", 0.5)
            base_score = (extraPeak * 0.6) + (social * 0.4)
        
        elif action == "explore" or action == "investigate":
            # Open and curious personalities prefer exploration
            openness = personality.get("openness", 0.5)
            curiosity = personality.get("curiosity", 0.5)
            base_score = (openness * 0.6) + (curiosity * 0.4)
        
        elif action == "help" or action == "cooperate":
            # Agreeable personalities prefer cooperation
            agreeableness = personality.get("agreeableness", 0.5)
            base_score = agreeableness
        
        elif action == "plan" or action == "organize":
            # Conscientious personalities prefer planning
            conscientiousness = personality.get("conscientiousness", 0.5)
            base_score = conscientiousness
        
        return max(0.0, min(1.0, base_score))
    
    def get_personality_traits(self, personality_vector: Any) -> Dict[str, float]:
        """
        Normalize and validate personality vector.
        
        Args:
            personality_vector: Raw personality data (dict or JSON string)
        
        Returns:
            Normalized personality traits
        """
        if isinstance(personality_vector, str):
            try:
                personality = json.loads(personality_vector)
            except json.JSONDecodeError:
                personality = {}
        else:
            personality = personality_vector or {}
        
        # Ensure all dimensions exist with defaults
        normalized = {}
        for trait, config in self.TRAIT_DIMENSIONS.items():
            value = personality.get(trait, config["default"])
            # Clamp to valid range
            normalized[trait] = max(config["min"], min(config["max"], float(value)))
        
        return normalized
    
    def generate_personality(self, npc_type: str = "generic") -> Dict[str, float]:
        """
        Generate personality traits based on NPC type.
        
        Args:
            npc_type: Type of NPC (merchant, guard, civilian, etc.)
        
        Returns:
            Generated personality traits
        """
        base_personality = {trait: config["default"] for trait, config in self.TRAIT_DIMENSIONS.items()}
        
        # Adjust based on NPC type
        type_modifiers = {
            "merchant": {
                "extraversion": 0.7,
                "agreeableness": 0.8,
                "conscientiousness": 0.7,
            },
            "guard": {
                "conscientiousness": 0.8,
                "aggression": 0.6,
                "neuroticism": 0.4,
            },
            "civilian": {
                "agreeableness": 0.6,
                "social": 0.6,
                "aggression": 0.2,
            },
            "criminal": {
                "aggression": 0.7,
                "neuroticism": 0.6,
                "agreeableness": 0.3,
            },
        }
        
        modifiers = type_modifiers.get(npc_type, {})
        for trait, value in modifiers.items():
            if trait in base_personality:
                base_personality[trait] = value
        
        return base_personality
