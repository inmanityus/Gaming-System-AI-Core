"""
Interaction Router - NPC interaction handling.
Routes NPC-NPC and NPC-player interactions to appropriate handlers.
"""

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID


class InteractionRouter:
    """
    Routes NPC interactions to appropriate handlers.
    Handles both NPC-NPC and NPC-player interactions.
    """
    
    def route(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route interaction intent to appropriate handler.
        
        Args:
            intent: Interaction intent with type, source, target, etc.
        
        Returns:
            Action result with outcome
        """
        interaction_type = intent.get("type", "unknown")
        source_id = intent.get("source_id")
        target_id = intent.get("target_id")
        
        # Route based on interaction type
        if interaction_type == "social":
            return self._handle_social_interaction(intent)
        
        elif interaction_type == "combat":
            return self._handle_combat_interaction(intent)
        
        elif interaction_type == "trade":
            return self._handle_trade_interaction(intent)
        
        elif interaction_type == "information":
            return self._handle_information_interaction(intent)
        
        else:
            return {
                "success": False,
                "error": f"Unknown interaction type: {interaction_type}",
            }
    
    def _handle_social_interaction(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social interaction."""
        return {
            "success": True,
            "type": "social",
            "outcome": "interaction_initiated",
            "relationship_change": 0.1,
            "duration": 30,
        }
    
    def _handle_combat_interaction(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle combat interaction."""
        return {
            "success": True,
            "type": "combat",
            "outcome": "combat_initiated",
            "damage": 0,
            "duration": 60,
        }
    
    def _handle_trade_interaction(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trade interaction."""
        return {
            "success": True,
            "type": "trade",
            "outcome": "trade_opportunity",
            "items": [],
            "duration": 45,
        }
    
    def _handle_information_interaction(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle information exchange interaction."""
        return {
            "success": True,
            "type": "information",
            "outcome": "information_exchanged",
            "knowledge": {},
            "duration": 20,
        }
