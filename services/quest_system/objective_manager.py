"""
Objective Manager - Quest objective tracking and completion.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.quest_system.quest_manager import QuestManager


class ObjectiveManager:
    """
    Manages quest objectives tracking and completion.
    Handles objective updates, progress tracking, and completion verification.
    """
    
    def __init__(self):
        self.quest_manager = QuestManager()
    
    async def get_objectives(self, quest_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all objectives for a quest.
        
        Args:
            quest_id: Quest UUID
        
        Returns:
            List of objectives
        """
        quest = await self.quest_manager.get_quest(quest_id)
        if not quest:
            raise ValueError(f"Quest not found: {quest_id}")
        
        return quest.get("objectives", [])
    
    async def update_objective_progress(
        self,
        quest_id: UUID,
        objective_id: str,
        progress: int,
        completed: bool = False
    ) -> Dict[str, Any]:
        """
        Update objective progress.
        
        Args:
            quest_id: Quest UUID
            objective_id: Objective ID
            progress: Current progress value
            completed: Whether objective is completed
        
        Returns:
            Updated quest data
        """
        quest = await self.quest_manager.get_quest(quest_id)
        if not quest:
            raise ValueError(f"Quest not found: {quest_id}")
        
        objectives = quest.get("objectives", [])
        
        # Find and update objective
        updated = False
        for obj in objectives:
            if obj.get("id") == objective_id:
                obj["progress"] = progress
                obj["completed"] = completed
                if completed:
                    obj["completed_at"] = "2025-01-29T00:00:00Z"  # Would use actual timestamp
                updated = True
                break
        
        if not updated:
            raise ValueError(f"Objective not found: {objective_id}")
        
        # Update quest with new objectives
        updated_quest = await self.quest_manager.update_quest_objectives(quest_id, objectives)
        
        # Check if all objectives are completed
        all_completed = all(obj.get("completed", False) for obj in objectives)
        if all_completed and updated_quest["status"] != "completed":
            await self.quest_manager.update_quest_status(quest_id, "in_progress")
        
        return updated_quest
    
    async def complete_objective(self, quest_id: UUID, objective_id: str) -> Dict[str, Any]:
        """
        Mark an objective as completed.
        
        Args:
            quest_id: Quest UUID
            objective_id: Objective ID
        
        Returns:
            Updated quest data
        """
        objectives = await self.get_objectives(quest_id)
        
        # Find objective to get target count
        objective = next((obj for obj in objectives if obj.get("id") == objective_id), None)
        if not objective:
            raise ValueError(f"Objective not found: {objective_id}")
        
        target_count = objective.get("count", 1)
        
        return await self.update_objective_progress(
            quest_id,
            objective_id,
            target_count,
            completed=True
        )
    
    async def verify_objective_completion(
        self,
        quest_id: UUID,
        objective_id: str,
        player_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Verify if an objective should be completed based on player actions.
        
        Args:
            quest_id: Quest UUID
            objective_id: Objective ID
            player_id: Player UUID
            context: Optional context for verification
        
        Returns:
            True if objective should be completed
        """
        objectives = await self.get_objectives(quest_id)
        objective = next((obj for obj in objectives if obj.get("id") == objective_id), None)
        
        if not objective:
            return False
        
        obj_type = objective.get("type", "")
        target = objective.get("target", "")
        required_count = objective.get("count", 1)
        current_progress = objective.get("progress", 0)
        
        # Simple verification logic (would be more sophisticated in production)
        if context:
            if obj_type == "kill" and context.get("killed_npc") == target:
                return current_progress + 1 >= required_count
            elif obj_type == "collect" and context.get("collected_item") == target:
                return current_progress + 1 >= required_count
            elif obj_type == "talk" and context.get("talked_to_npc") == target:
                return True
            elif obj_type == "go" and context.get("visited_location") == target:
                return True
        
        return False
    
    async def check_all_objectives_complete(self, quest_id: UUID) -> bool:
        """
        Check if all objectives in a quest are completed.
        
        Args:
            quest_id: Quest UUID
        
        Returns:
            True if all objectives are completed
        """
        objectives = await self.get_objectives(quest_id)
        return all(obj.get("completed", False) for obj in objectives)

