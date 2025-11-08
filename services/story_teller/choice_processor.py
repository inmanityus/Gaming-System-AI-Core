"""
Choice Processor - Handles player choice validation and processing.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from database_connection import get_postgres
import asyncpg


class ChoiceValidationError(Exception):
    """Raised when a choice validation fails."""
    pass


class ChoiceProcessor:
    """
    Processes player choices and validates them against story context.
    Handles choice consequences and story progression.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def validate_choice(
        self,
        player_id: UUID,
        node_id: UUID,
        choice_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a player choice against current story state.
        
        Args:
            player_id: Player UUID
            node_id: Story node UUID
            choice_id: Choice ID to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get the story node
            postgres = await self._get_postgres()
            node_query = """
                SELECT choices, prerequisites, status
                FROM story_nodes
                WHERE id = $1 AND player_id = $2
            """
            node_result = await postgres.fetch(node_query, node_id, player_id)
            
            if not node_result:
                return False, "Story node not found"
            
            if node_result["status"] != "active":
                return False, "Story node is not active"
            
            choices = json.loads(node_result["choices"]) if isinstance(node_result["choices"], str) else node_result["choices"]
            prerequisites = json.loads(node_result["prerequisites"]) if isinstance(node_result["prerequisites"], str) else node_result["prerequisites"]
            
            # Find the choice
            choice = None
            for c in choices:
                if c.get("id") == choice_id:
                    choice = c
                    break
            
            if not choice:
                return False, "Choice not found"
            
            # Validate choice prerequisites
            choice_prereqs = choice.get("prerequisites", {})
            if choice_prereqs:
                is_valid, error = await self._validate_prerequisites(
                    player_id, choice_prereqs
                )
                if not is_valid:
                    return False, f"Prerequisites not met: {error}"
            
            # Validate node prerequisites
            if prerequisites:
                is_valid, error = await self._validate_prerequisites(
                    player_id, prerequisites
                )
                if not is_valid:
                    return False, f"Node prerequisites not met: {error}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    async def _validate_prerequisites(
        self, 
        player_id: UUID, 
        prerequisites: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate prerequisites against player state."""
        postgres = await self._get_postgres()
        
        # Check level requirement
        if "level" in prerequisites:
            level_query = "SELECT level FROM players WHERE id = $1"
            level_result = await postgres.fetch(level_query, player_id)
            if not level_result or level_result["level"] < prerequisites["level"]:
                return False, f"Level {prerequisites['level']} required"
        
        # Check money requirement
        if "money" in prerequisites:
            money_query = "SELECT money FROM players WHERE id = $1"
            money_result = await postgres.fetch(money_query, player_id)
            if not money_result or money_result["money"] < prerequisites["money"]:
                return False, f"${prerequisites['money']} required"
        
        # Check reputation requirement
        if "reputation" in prerequisites:
            rep_query = "SELECT reputation FROM players WHERE id = $1"
            rep_result = await postgres.fetch(rep_query, player_id)
            if not rep_result or rep_result["reputation"] < prerequisites["reputation"]:
                return False, f"Reputation {prerequisites['reputation']} required"
        
        # Check item requirements
        if "items" in prerequisites:
            items_query = "SELECT inventory FROM players WHERE id = $1"
            items_result = await postgres.fetch(items_query, player_id)
            if not items_result:
                return False, "Player inventory not found"
            
            inventory = json.loads(items_result["inventory"]) if isinstance(items_result["inventory"], str) else items_result["inventory"]
            required_items = prerequisites["items"]
            
            for item in required_items:
                if item not in inventory:
                    return False, f"Item '{item}' required"
        
        # Check story progress requirements
        if "story_nodes" in prerequisites:
            story_query = """
                SELECT COUNT(*) as count
                FROM story_nodes
                WHERE player_id = $1 AND id = ANY($2) AND status = 'completed'
            """
            story_result = await postgres.fetch(
                story_query, 
                player_id, 
                prerequisites["story_nodes"]
            )
            if not story_result or story_result["count"] < len(prerequisites["story_nodes"]):
                return False, "Required story nodes not completed"
        
        return True, ""
    
    async def process_choice(
        self,
        player_id: UUID,
        node_id: UUID,
        choice_id: str,
    ) -> Dict[str, Any]:
        """
        Process a validated player choice and apply consequences.
        
        Args:
            player_id: Player UUID
            node_id: Story node UUID
            choice_id: Choice ID to process
        
        Returns:
            Processing result with consequences applied
        """
        try:
            # Validate choice first
            is_valid, error = await self.validate_choice(player_id, node_id, choice_id)
            if not is_valid:
                raise ChoiceValidationError(error)
            
            # Get choice details
            postgres = await self._get_postgres()
            choice_query = """
                SELECT choices, consequences
                FROM story_nodes
                WHERE id = $1 AND player_id = $2
            """
            choice_result = await postgres.fetch(choice_query, node_id, player_id)
            
            if not choice_result:
                raise ChoiceValidationError("Story node not found")
            
            choices = json.loads(choice_result["choices"]) if isinstance(choice_result["choices"], str) else choice_result["choices"]
            node_consequences = json.loads(choice_result["consequences"]) if isinstance(choice_result["consequences"], str) else choice_result["consequences"]
            
            # Find the specific choice
            choice = None
            for c in choices:
                if c.get("id") == choice_id:
                    choice = c
                    break
            
            if not choice:
                raise ChoiceValidationError("Choice not found")
            
            # Apply choice consequences
            choice_consequences = choice.get("consequences", {})
            all_consequences = {**node_consequences, **choice_consequences}
            
            result = await self._apply_consequences(player_id, all_consequences)
            
            # Mark choice as processed
            await self._mark_choice_processed(player_id, node_id, choice_id)
            
            return {
                "success": True,
                "choice_id": choice_id,
                "consequences_applied": result,
                "message": "Choice processed successfully"
            }
            
        except ChoiceValidationError as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Choice validation failed"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "message": "Failed to process choice"
            }
    
    async def _apply_consequences(
        self, 
        player_id: UUID, 
        consequences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply consequences to player state."""
        postgres = await self._get_postgres()
        applied = {}
        
        # Apply money changes
        if "money" in consequences:
            money_query = """
                UPDATE players 
                SET money = money + $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                RETURNING money
            """
            money_result = await postgres.fetch(money_query, consequences["money"], player_id)
            if money_result:
                applied["money"] = money_result["money"]
        
        # Apply reputation changes
        if "reputation" in consequences:
            rep_query = """
                UPDATE players 
                SET reputation = reputation + $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                RETURNING reputation
            """
            rep_result = await postgres.fetch(rep_query, consequences["reputation"], player_id)
            if rep_result:
                applied["reputation"] = rep_result["reputation"]
        
        # Apply experience changes
        if "experience" in consequences:
            xp_query = """
                UPDATE players 
                SET xp = xp + $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                RETURNING xp, level
            """
            xp_result = await postgres.fetch(xp_query, consequences["experience"], player_id)
            if xp_result:
                applied["experience"] = xp_result["xp"]
                applied["level"] = xp_result["level"]
        
        # Apply relationship changes
        if "relationships" in consequences:
            rel_query = """
                SELECT relationships FROM players WHERE id = $1
            """
            rel_result = await postgres.fetch(rel_query, player_id)
            if rel_result:
                current_rels = json.loads(rel_result["relationships"]) if isinstance(rel_result["relationships"], str) else rel_result["relationships"]
                
                # Update relationships
                for npc, change in consequences["relationships"].items():
                    current_rels[npc] = current_rels.get(npc, 0) + change
                
                # Save updated relationships
                update_query = """
                    UPDATE players 
                    SET relationships = $1::jsonb, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """
                await postgres.execute(update_query, json.dumps(current_rels), player_id)
                applied["relationships"] = current_rels
        
        # Apply inventory changes
        if "items" in consequences:
            inv_query = """
                SELECT inventory FROM players WHERE id = $1
            """
            inv_result = await postgres.fetch(inv_query, player_id)
            if inv_result:
                current_inv = json.loads(inv_result["inventory"]) if isinstance(inv_result["inventory"], str) else inv_result["inventory"]
                
                # Update inventory
                for item, change in consequences["items"].items():
                    if change > 0:
                        current_inv[item] = current_inv.get(item, 0) + change
                    elif change < 0:
                        current_inv[item] = max(0, current_inv.get(item, 0) + change)
                
                # Save updated inventory
                update_query = """
                    UPDATE players 
                    SET inventory = $1::jsonb, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """
                await postgres.execute(update_query, json.dumps(current_inv), player_id)
                applied["inventory"] = current_inv
        
        return applied
    
    async def _mark_choice_processed(
        self, 
        player_id: UUID, 
        node_id: UUID, 
        choice_id: str
    ) -> None:
        """Mark a choice as processed and update story node status."""
        postgres = await self._get_postgres()
        
        # Update story node status to completed
        update_query = """
            UPDATE story_nodes
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND player_id = $2
        """
        await postgres.execute(update_query, node_id, player_id)
        
        # TODO: Log choice processing for analytics
        # This could be stored in a separate choices_log table
