"""
Goal Manager - NPC goal stack and priority management.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID


class GoalManager:
    """
    Manages NPC goal stack with priorities and decay.
    Handles goal planning, prioritization, and completion.
    """
    
    def plan(self, npc_id: UUID, personality: Dict[str, float], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate goal plan for NPC based on personality and context.
        
        Args:
            npc_id: NPC UUID
            personality: NPC personality traits
            context: Current context (world state, relationships, etc.)
        
        Returns:
            List of goals ordered by priority
        """
        goals = []
        
        # Generate goals based on personality
        aggression = personality.get("aggression", 0.3)
        social = personality.get("social", 0.5)
        curiosity = personality.get("curiosity", 0.5)
        conscientiousness = personality.get("conscientiousness", 0.5)
        
        # Aggressive NPCs want to fight
        if aggression > 0.6:
            goals.append({
                "type": "combat",
                "priority": aggression,
                "target": None,  # Would be set based on context
                "description": "Seek combat opportunities",
            })
        
        # Social NPCs want to interact
        if social > 0.6:
            goals.append({
                "type": "interaction",
                "priority": social,
                "target": None,  # Would target nearby NPCs/players
                "description": "Seek social interactions",
            })
        
        # Curious NPCs want to explore
        if curiosity > 0.6:
            goals.append({
                "type": "explore",
                "priority": curiosity,
                "target": None,
                "description": "Explore new areas",
            })
        
        # Conscientious NPCs want to complete tasks
        if conscientiousness > 0.6:
            goals.append({
                "type": "task",
                "priority": conscientiousness,
                "target": None,
                "description": "Complete assigned tasks",
            })
        
        # Default goal: maintain safety
        if not goals:
            goals.append({
                "type": "survive",
                "priority": 0.5,
                "target": None,
                "description": "Maintain safety and survival",
            })
        
        # Sort by priority (highest first)
        goals.sort(key=lambda g: g.get("priority", 0.5), reverse=True)
        
        return goals
    
    def update_goal_stack(self, goal_stack: Any, new_goals: List[Dict[str, Any]], decay_rate: float = 0.1) -> List[Dict[str, Any]]:
        """
        Update goal stack with new goals and apply decay to existing goals.
        
        Args:
            goal_stack: Current goal stack
            new_goals: New goals to add
            decay_rate: Priority decay rate per update
        
        Returns:
            Updated goal stack
        """
        # Parse existing goal stack
        if isinstance(goal_stack, str):
            try:
                current_goals = json.loads(goal_stack)
            except json.JSONDecodeError:
                current_goals = []
        elif isinstance(goal_stack, list):
            current_goals = goal_stack
        else:
            current_goals = []
        
        # Apply decay to existing goals
        for goal in current_goals:
            if isinstance(goal, dict):
                current_priority = goal.get("priority", 0.5)
                goal["priority"] = max(0.0, current_priority - decay_rate)
        
        # Add new goals
        current_goals.extend(new_goals)
        
        # Remove completed or low-priority goals
        current_goals = [
            goal for goal in current_goals
            if isinstance(goal, dict) and goal.get("priority", 0) > 0.1
        ]
        
        # Sort by priority
        current_goals.sort(key=lambda g: g.get("priority", 0.5), reverse=True)
        
        # Keep top 10 goals
        return current_goals[:10]
    
    def complete_goal(self, goal_stack: List[Dict[str, Any]], goal_index: int) -> List[Dict[str, Any]]:
        """
        Mark a goal as completed and remove it from stack.
        
        Args:
            goal_stack: Current goal stack
            goal_index: Index of goal to complete
        
        Returns:
            Updated goal stack
        """
        if 0 <= goal_index < len(goal_stack):
            goal_stack.pop(goal_index)
        return goal_stack
    
    def get_top_goal(self, goal_stack: Any) -> Optional[Dict[str, Any]]:
        """
        Get the highest priority goal from stack.
        
        Args:
            goal_stack: Current goal stack
        
        Returns:
            Top priority goal or None
        """
        if isinstance(goal_stack, str):
            try:
                goals = json.loads(goal_stack)
            except json.JSONDecodeError:
                return None
        elif isinstance(goal_stack, list):
            goals = goal_stack
        else:
            return None
        
        if not goals:
            return None
        
        # Sort by priority if needed
        if all(isinstance(g, dict) for g in goals):
            goals.sort(key=lambda g: g.get("priority", 0.5), reverse=True)
        
        return goals[0] if goals else None
