# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Behavior Engine - Core NPC behavior processing.
Handles NPC decision-making, action selection, and state updates.

UPDATED: Integrated with Behavioral Proxy architecture (REQ-PERF-003).
"""

import asyncio
import json
import time
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from threading import Lock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# REFACTORING: Direct database imports replaced with on-demand connections
# from state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool
import asyncpg
import redis.asyncio as redis
from typing import Optional, Any as PostgreSQLPool, Any as RedisPool, Any as LLMClient, Any as ProxyManager, Any as CognitiveLayer

_logger = logging.getLogger(__name__)


class BehaviorEngine:
    """
    Core engine for NPC behavior processing.
    Handles NPC updates, decision-making, and state management.
    
    UPDATED: Integrated with Behavioral Proxy architecture for 300+ FPS performance.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._update_queue: List[UUID] = []
        self._queue_lock = Lock()
        self._processing = False
        
        # Behavioral Proxy architecture (REQ-PERF-003)
        self.proxy_manager = ProxyManager()
        self.cognitive_layer: Optional[CognitiveLayer] = None
        if llm_client:
            self.cognitive_layer = CognitiveLayer(
                proxy_manager=self.proxy_manager,
                llm_client=llm_client,
                update_rate_hz=0.5  # 0.5 Hz = every 2 seconds
            )
            self.cognitive_layer.start()
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = get_state_manager_client()
        return self.redis
    
    async def update_npc(self, npc_id: UUID, frame_time_ms: float = 3.33, game_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update NPC behavior and state using Behavioral Proxy architecture.
        
        Args:
            npc_id: NPC UUID
            frame_time_ms: Available frame time in milliseconds (for 300 FPS = 3.33ms)
            game_state: Current game state (enemies, obstacles, etc.)
        
        Returns:
            Update result with actions taken
        
        Raises:
            ValueError: If inputs are invalid or NPC not found
        """
        # Input validation
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        if not isinstance(frame_time_ms, (int, float)) or frame_time_ms < 0:
            raise ValueError(f"frame_time_ms must be non-negative number, got {frame_time_ms}")
        if game_state is not None and not isinstance(game_state, dict):
            raise TypeError(f"game_state must be dict or None, got {type(game_state)}")
        
        # Get game state if not provided
        if game_state is None:
            try:
                game_state = await self._get_game_state_for_proxy(npc_id)
            except Exception as e:
                _logger.error(f"Error getting game state for NPC {npc_id}: {e}")
                game_state = {"enemies": [], "obstacles": [], "interactables": [], "social_areas": []}
        
        # Update proxy (fast, <0.5ms)
        try:
            proxy_action = self.proxy_manager.update_proxy(npc_id, frame_time_ms, game_state)
        except Exception as e:
            _logger.error(f"Error updating proxy for NPC {npc_id}: {e}")
            proxy_action = None
        
        # Queue for cognitive analysis (async, non-blocking)
        if self.cognitive_layer:
            try:
                self.cognitive_layer.queue_analysis(npc_id)
            except Exception as e:
                _logger.warning(f"Error queueing cognitive analysis for NPC {npc_id}: {e}")
        
        # Get NPC data for state updates
        try:
            postgres = await self._get_postgres()
            npc_query = """
                SELECT id, name, npc_type, personality_vector, stats, goal_stack,
                       relationships, meta_data
                FROM npcs
                WHERE id = $1
            """
            npc_result = await postgres.fetch(npc_query, npc_id)
        except Exception as e:
            _logger.error(f"Database error getting NPC {npc_id}: {e}")
            raise
        
        if not npc_result:
            raise ValueError(f"NPC {npc_id} not found")
        
        # Convert proxy action to decision format (for compatibility)
        decision = {
            "action_type": proxy_action.action_type.value if proxy_action else "idle",
            "target": proxy_action.target if proxy_action else None,
            "priority": proxy_action.priority if proxy_action else 0.1,
            "reasoning": "Behavioral Proxy decision",
        }
        
        # Apply actions
        actions_taken = []
        if proxy_action:
            actions_taken.append({
                "type": proxy_action.action_type.value,
                "target": proxy_action.target,
                "parameters": proxy_action.parameters,
                "priority": proxy_action.priority,
            })
        
        # Update NPC state
        try:
            await self._update_npc_state(npc_id, decision, actions_taken)
        except Exception as e:
            _logger.error(f"Error updating NPC state for {npc_id}: {e}")
            # Don't raise - state update failure shouldn't block response
        
        return {
            "npc_id": str(npc_id),
            "decision": decision,
            "actions": actions_taken,
            "proxy_action": proxy_action.action_type.value if proxy_action else None,
            "timestamp": time.time(),
        }
    
    async def _get_game_state_for_proxy(self, npc_id: UUID) -> Dict[str, Any]:
        """Get game state formatted for proxy (enemies, obstacles, etc.)."""
        # TODO: Integrate with game engine to get real-time state
        # For now, return empty state
        return {
            "enemies": [],
            "obstacles": [],
            "interactables": [],
            "social_areas": [],
        }
    
    async def _get_npc_context(self, npc_id: UUID) -> Dict[str, Any]:
        """Get context for NPC decision-making."""
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        
        try:
            postgres = await self._get_postgres()
        except Exception as e:
            _logger.error(f"Error getting postgres connection: {e}")
            return {
                "world_state": {},
                "nearby_npcs": [],
                "faction_info": {},
                "player_interactions": [],
            }
        
        # Get faction info
        try:
            npc_query = "SELECT faction_id FROM npcs WHERE id = $1"
            npc_result = await postgres.fetch(npc_query, npc_id)
        except Exception as e:
            _logger.error(f"Database error getting NPC context for {npc_id}: {e}")
            npc_result = None
        
        context = {
            "world_state": {},
            "nearby_npcs": [],
            "faction_info": {},
            "player_interactions": [],
        }
        
        # Get world state (simplified - would integrate with WorldStateManager)
        try:
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
        except Exception as e:
            _logger.warning(f"Error getting world state: {e}")
        
        # Get faction info if available
        if npc_result and npc_result.get("faction_id"):
            try:
                faction_query = "SELECT name, power_level FROM factions WHERE id = $1"
                faction_result = await postgres.fetch(faction_query, npc_result["faction_id"])
                
                if faction_result:
                    context["faction_info"] = {
                        "name": faction_result["name"],
                        "power_level": faction_result["power_level"],
                    }
            except Exception as e:
                _logger.warning(f"Error getting faction info: {e}")
        
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
        # Input validation
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        if not isinstance(decision, dict):
            raise TypeError(f"decision must be dict, got {type(decision)}")
        if not isinstance(actions, list):
            raise TypeError(f"actions must be list, got {type(actions)}")
        
        try:
            postgres = await self._get_postgres()
        except Exception as e:
            _logger.error(f"Error getting postgres connection for state update: {e}")
            raise
        
        # Update meta_data with last decision
        try:
            meta_query = "SELECT meta_data FROM npcs WHERE id = $1"
            meta_result = await postgres.fetch(meta_query, npc_id)
            
            if not meta_result:
                _logger.warning(f"NPC {npc_id} not found for state update")
                return
            
            current_meta = json.loads(meta_result["meta_data"]) if isinstance(meta_result["meta_data"], str) else meta_result["meta_data"]
            current_meta = current_meta or {}
            
            # Add behavior update to metadata
            current_meta["last_decision"] = decision
            current_meta["last_actions"] = actions
            current_meta["last_update_time"] = datetime.now(timezone.utc).isoformat()
            
            # Update database
            update_query = """
                UPDATE npcs
                SET meta_data = $1::jsonb, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """
            
            await postgres.execute(update_query, json.dumps(current_meta), npc_id)
        except Exception as e:
            _logger.error(f"Database error updating NPC state for {npc_id}: {e}")
            raise
        
        # Update Redis cache
        try:
            redis = await self._get_redis()
            cache_key = f"npc:state:{npc_id}"
            await redis.hset(cache_key, mapping={
                "last_decision": json.dumps(decision),
                "last_update": datetime.now(timezone.utc).isoformat(),
            })
            await redis.expire(cache_key, 3600)  # 1 hour TTL
        except Exception as e:
            _logger.warning(f"Error updating Redis cache for NPC {npc_id}: {e}")
            # Don't raise - cache failures are non-critical
    
    async def batch_update_npcs(self, npc_ids: List[UUID], max_concurrent: int = 10) -> Dict[str, Any]:
        """
        Batch update multiple NPCs with concurrency control.
        
        Args:
            npc_ids: List of NPC UUIDs to update
            max_concurrent: Maximum concurrent updates
        
        Returns:
            Batch update results
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not isinstance(npc_ids, list):
            raise TypeError(f"npc_ids must be list, got {type(npc_ids)}")
        if not all(isinstance(npc_id, UUID) for npc_id in npc_ids):
            raise TypeError("All npc_ids must be UUIDs")
        if not isinstance(max_concurrent, int) or max_concurrent < 1:
            raise ValueError(f"max_concurrent must be positive integer, got {max_concurrent}")
        
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
        if not isinstance(npc_id, UUID):
            raise TypeError(f"npc_id must be UUID, got {type(npc_id)}")
        
        with self._queue_lock:
            if npc_id not in self._update_queue:
                self._update_queue.append(npc_id)
        
        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_update_queue())
    
    async def _process_update_queue(self):
        """Process queued NPC updates."""
        self._processing = True
        
        while True:
            with self._queue_lock:
                if not self._update_queue:
                    break
                npc_id = self._update_queue.pop(0)
            
            try:
                await self.update_npc(npc_id)
            except Exception as e:
                _logger.error(f"Error updating NPC {npc_id} from queue: {e}")
        
        self._processing = False
