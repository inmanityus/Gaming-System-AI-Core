"""
Behavior Engine - Core NPC behavior processing.
Handles NPC decision-making, action selection, and state updates.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class BehaviorEngine:
    """
    Core engine for NPC behavior processing.
    Handles NPC updates, decision-making, and state management.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._update_queue: List[UUID] = []
        self._processing = False
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = await get_redis_pool()
        return self.redis
    
    async def update_npc(self, npc_id: UUID) -> Dict[str, Any]:
        """
        Update NPC behavior and state.
        
        Args:
            npc_id: NPC UUID
        
        Returns:
            Update result with actions taken
        """
        postgres = await self._get_postgres()
        
        # Get NPC data
        npc_query = """
            SELECT id, name, npc_type, personality_vector, stats, goal_stack,
                   relationships, meta_data
            FROM npcs
            WHERE id = $1
        """
        
        npc_result = await postgres.fetch(npc_query, npc_id)
        
        if not npc_result:
            raise ValueError(f"NPC {npc_id} not found")
        
        # Get NPC context (world state, nearby NPCs, etc.)
        context = await self._get_npc_context(npc_id)
        
        # Process behavior decision
        decision = await self._make_decision(npc_result, context)
        
        # Apply decision actions
        actions_taken = await self._apply_actions(npc_id, decision, context)
        
        # Update NPC state
        await self._update_npc_state(npc_id, decision, actions_taken)
        
        return {
            "npc_id": str(npc_id),
            "decision": decision,
            "actions": actions_taken,
            "timestamp": "2025-10-29T23:17:17Z",
        }
    
    async def _get_npc_context(self, npc_id: UUID) -> Dict[str, Any]:
        """Get context for NPC decision-making."""
        postgres = await self._get_postgres()
        
        # Get faction info
        npc_query = "SELECT faction_id FROM npcs WHERE id = $1"
        npc_result = await postgres.fetch(npc_query, npc_id)
        
        context = {
            "world_state": {},
            "nearby_npcs": [],
            "faction_info": {},
            "player_interactions": [],
        }
        
        # Get world state (simplified - would integrate with WorldStateManager)
        world_query = """
            SELECT economic_state, faction_power
            FROM world_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        world_result = await postgres.fetch(world_query)
        
        if world_result:
            context["world_state"] = {
                "economic_state": json.loads(world_result["economic_state"]) if isinstance(world_result["economic_state"], str) else world_result["economic_state"],
                "faction_power": json.loads(world_result["faction_power"]) if isinstance(world_result["faction_power"], str) else world_result["faction_power"],
            }
        
        # Get faction info if available
        if npc_result and npc_result["faction_id"]:
            faction_query = "SELECT name, power_level FROM factions WHERE id = $1"
            faction_result = await postgres.fetch(faction_query, npc_result["faction_id"])
            
            if faction_result:
                context["faction_info"] = {
                    "name": faction_result["name"],
                    "power_level": faction_result["power_level"],
                }
        
        return context
    
    async def _make_decision(self, npc_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Make behavior decision based on NPC personality and context."""
        personality = json.loads(npc_data["personality_vector"]) if isinstance(npc_data["personality_vector"], str) else npc_data["personality_vector"]
        goal_stack = json.loads(npc_data["goal_stack"]) if isinstance(npc_data["goal_stack"], str) else npc_data["goal_stack"]
        
        # Simple decision-making based on personality and goals
        # In production, this would use more sophisticated AI decision-making
        decision = {
            "action_type": "idle",  # Default action
            "target": None,
            "priority": 0.5,
            "reasoning": "Default decision",
        }
        
        # Check goal stack for priority actions
        if goal_stack and len(goal_stack) > 0:
            top_goal = goal_stack[0] if isinstance(goal_stack, list) else goal_stack
            if isinstance(top_goal, dict):
                goal_type = top_goal.get("type", "unknown")
                decision["action_type"] = f"pursue_goal_{goal_type}"
                decision["target"] = top_goal.get("target")
                decision["priority"] = top_goal.get("priority", 0.5)
                decision["reasoning"] = f"Pursuing goal: {goal_type}"
        
        # Adjust based on personality traits
        if personality:
            # Example: aggressive personality -> more combat actions
            if personality.get("aggression", 0) > 0.7:
                decision["action_type"] = "combat_ready"
                decision["priority"] = 0.8
            
            # Example: social personality -> more interaction actions
            if personality.get("social", 0) > 0.7:
                decision["action_type"] = "seek_interaction"
                decision["priority"] = 0.7
        
        return decision
    
    async def _apply_actions(self, npc_id: UUID, decision: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply decision actions to NPC state."""
        actions_taken = []
        
        action_type = decision.get("action_type", "idle")
        
        # Apply action effects (simplified - would integrate with game systems)
        if action_type == "pursue_goal_combat":
            actions_taken.append({
                "type": "combat_preparation",
                "effect": "increased_combat_readiness",
                "duration": 60,  # seconds
            })
        
        elif action_type == "seek_interaction":
            actions_taken.append({
                "type": "social_interaction",
                "effect": "relationship_change",
                "target": decision.get("target"),
                "duration": 30,
            })
        
        elif action_type == "idle":
            actions_taken.append({
                "type": "idle",
                "effect": "maintain_state",
                "duration": 10,
            })
        
        return actions_taken
    
    async def _update_npc_state(self, npc_id: UUID, decision: Dict[str, Any], actions: List[Dict[str, Any]]):
        """Update NPC state in database and cache."""
        postgres = await self._get_postgres()
        
        # Update meta_data with last decision
        meta_query = "SELECT meta_data FROM npcs WHERE id = $1"
        meta_result = await postgres.fetch(meta_query, npc_id)
        
        current_meta = json.loads(meta_result["meta_data"]) if isinstance(meta_result["meta_data"], str) else meta_result["meta_data"]
        current_meta = current_meta or {}
        
        # Add behavior update to metadata
        current_meta["last_decision"] = decision
        current_meta["last_actions"] = actions
        current_meta["last_update_time"] = "2025-10-29T23:17:17Z"
        
        # Update database
        update_query = """
            UPDATE npcs
            SET meta_data = $1::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await postgres.execute(update_query, json.dumps(current_meta), npc_id)
        
        # Update Redis cache
        redis = await self._get_redis()
        cache_key = f"npc:state:{npc_id}"
        await redis.hset(cache_key, mapping={
            "last_decision": json.dumps(decision),
            "last_update": "2025-10-29T23:17:17Z",
        })
        await redis.expire(cache_key, 3600)  # 1 hour TTL
    
    async def batch_update_npcs(self, npc_ids: List[UUID], max_concurrent: int = 10) -> Dict[str, Any]:
        """
        Batch update multiple NPCs with concurrency control.
        
        Args:
            npc_ids: List of NPC UUIDs to update
            max_concurrent: Maximum concurrent updates
        
        Returns:
            Batch update results
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(npc_ids),
        }
        
        # Process in batches to avoid overwhelming the system
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def update_with_semaphore(npc_id: UUID):
            async with semaphore:
                try:
                    result = await self.update_npc(npc_id)
                    results["successful"].append(result)
                except Exception as e:
                    results["failed"].append({
                        "npc_id": str(npc_id),
                        "error": str(e),
                    })
        
        # Execute all updates concurrently (with semaphore limiting)
        await asyncio.gather(*[update_with_semaphore(npc_id) for npc_id in npc_ids], return_exceptions=True)
        
        return results
    
    async def queue_npc_update(self, npc_id: UUID):
        """Queue NPC for update processing."""
        if npc_id not in self._update_queue:
            self._update_queue.append(npc_id)
        
        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_update_queue())
    
    async def _process_update_queue(self):
        """Process queued NPC updates."""
        self._processing = True
        
        while self._update_queue:
            npc_id = self._update_queue.pop(0)
            try:
                await self.update_npc(npc_id)
            except Exception as e:
                print(f"Error updating NPC {npc_id}: {e}")
        
        self._processing = False
