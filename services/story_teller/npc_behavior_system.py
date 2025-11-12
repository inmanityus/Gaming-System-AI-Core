"""
NPC Behavior System - Autonomous NPC agents for world simulation.
Each NPC makes independent decisions via LLM calls in simulation context.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncpg
import redis.asyncio as aioredis
# HTTP client for AI integration
import aiohttp
import os


class NPCBehaviorSystem:
    """
    Autonomous NPC behavior system for world simulation.
    Each NPC makes independent decisions via LLM calls.
    
    NPCs have:
    - 50-dimensional personality vector
    - Goal stack (hierarchical objectives)
    - Episodic memory
    - Relationship graph
    - LLM-based decision making
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self.llm_client: Optional[LLMClient] = None
        self._npc_agents: Dict[str, Dict[str, Any]] = {}
        self._decision_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
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
    
    async def _get_llm_client(self) -> LLMClient:
        """Get LLM client instance."""
        if self.llm_client is None:
            self.llm_client = LLMClient()
        return self.llm_client
    
    async def simulate_npc_cycle(self, npc_id: str, world_state_id: str) -> Dict[str, Any]:
        """
        Simulate one decision cycle for an NPC (REAL agent simulation).
        Each NPC makes autonomous decisions via LLM calls.
        
        Args:
            npc_id: NPC UUID
            world_state_id: World state UUID
        
        Returns:
            Simulation result with actions taken
        """
        # Load NPC data
        npc = await self._load_npc_data(npc_id)
        if not npc:
            raise ValueError(f"NPC {npc_id} not found")
        
        # Gather context for NPC decision
        context = await self._gather_npc_context(npc_id, world_state_id)
        
        # Generate NPC decision via LLM (REAL call)
        decision = await self._generate_npc_decision(npc, context)
        
        # Execute NPC actions
        actions_taken = await self._execute_npc_actions(npc_id, decision, context)
        
        # Update NPC state
        await self._update_npc_state(npc_id, decision, actions_taken)
        
        return {
            "npc_id": npc_id,
            "decision": decision,
            "actions": actions_taken,
            "timestamp": time.time()
        }
    
    async def _load_npc_data(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """Load NPC data from database."""
        postgres = await self._get_postgres()
        
        npc = await postgres.fetch(
            """
            SELECT id, name, npc_type, personality_vector, stats, goal_stack,
                   current_location, current_state, relationships, episodic_memory_id,
                   meta_data, faction_id, world_state_id
            FROM npcs
            WHERE id = $1
            """,
            npc_id
        )
        
        if not npc:
            return None
        
        # Convert to dict if it's a Record object
        npc_dict = dict(npc) if not isinstance(npc, dict) else npc
        
        # Parse JSONB fields (they may come as strings from asyncpg)
        if isinstance(npc_dict.get("personality_vector"), str):
            try:
                npc_dict["personality_vector"] = json.loads(npc_dict["personality_vector"])
            except json.JSONDecodeError:
                npc_dict["personality_vector"] = []
        
        if isinstance(npc_dict.get("stats"), str):
            try:
                npc_dict["stats"] = json.loads(npc_dict["stats"])
            except json.JSONDecodeError:
                npc_dict["stats"] = {}
        
        if isinstance(npc_dict.get("goal_stack"), str):
            try:
                npc_dict["goal_stack"] = json.loads(npc_dict["goal_stack"])
            except json.JSONDecodeError:
                npc_dict["goal_stack"] = []
        
        if isinstance(npc_dict.get("relationships"), str):
            try:
                npc_dict["relationships"] = json.loads(npc_dict["relationships"])
            except json.JSONDecodeError:
                npc_dict["relationships"] = {}
        
        if isinstance(npc_dict.get("meta_data"), str):
            try:
                npc_dict["meta_data"] = json.loads(npc_dict["meta_data"])
            except json.JSONDecodeError:
                npc_dict["meta_data"] = {}
        
        return npc_dict
    
    async def _gather_npc_context(self, npc_id: str, world_state_id: str) -> Dict[str, Any]:
        """Gather context for NPC decision-making."""
        postgres = await self._get_postgres()
        
        # Get NPC's current location
        npc = await postgres.fetch(
            "SELECT current_location, current_state, faction_id FROM npcs WHERE id = $1",
            npc_id
        )
        
        # Get nearby NPCs (same location)
        nearby_npcs = []
        if npc and npc.get("current_location"):
            nearby_npcs = await postgres.fetch_all(
                """
                SELECT id, name, npc_type, current_state
                FROM npcs
                WHERE world_state_id = $1 
                  AND current_location = $2 
                  AND id != $3
                LIMIT 10
                """,
                world_state_id,
                npc["current_location"],
                npc_id
            )
        
        # Get faction info if NPC has faction
        faction_info = {}
        if npc and npc.get("faction_id"):
            faction = await postgres.fetch(
                "SELECT id, name, power_level, faction_type FROM factions WHERE id = $1",
                str(npc["faction_id"])
            )
            if faction:
                faction_info = {
                    "id": str(faction["id"]),
                    "name": faction["name"],
                    "power_level": faction.get("power_level", 0.0),
                    "faction_type": faction.get("faction_type", "unknown")
                }
        
        # Get recent events affecting this NPC
        recent_events = await postgres.fetch_all(
            """
            SELECT id, node_type, title, narrative_content, meta_data, created_at
            FROM story_nodes
            WHERE meta_data->>'world_state_id' = $1 
              AND (meta_data->>'npc_id' = $2 OR narrative_content::text LIKE $3)
            ORDER BY created_at DESC
            LIMIT 5
            """,
            world_state_id,
            npc_id,
            f"%{npc_id}%"
        )
        
        # Get world state
        world_state = await postgres.fetch(
            "SELECT simulation_data FROM world_states WHERE id = $1",
            world_state_id
        )
        
        # Get game_time from simulation_data
        game_time = 0
        if world_state:
            sim_data = world_state.get("simulation_data")
            if isinstance(sim_data, str):
                try:
                    sim_data = json.loads(sim_data)
                except json.JSONDecodeError:
                    sim_data = {}
            if isinstance(sim_data, dict):
                game_time = sim_data.get("game_time", 0)
        
        context = {
            "npc_id": npc_id,
            "world_state_id": world_state_id,
            "current_location": npc.get("current_location") if npc else None,
            "current_state": npc.get("current_state", "idle") if npc else "idle",
            "nearby_npcs": [
                {
                    "id": str(npc_data["id"]),
                    "name": npc_data["name"],
                    "type": npc_data["npc_type"],
                    "state": npc_data["current_state"]
                }
                for npc_data in nearby_npcs
            ],
            "faction": faction_info,
            "recent_events": len(recent_events),
            "game_time": game_time
        }
        
        return context
    
    async def _generate_npc_decision(self, npc: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate NPC decision via LLM (REAL call).
        Each NPC makes autonomous decisions.
        
        Args:
            npc: NPC data
            context: NPC context
        
        Returns:
            NPC decision dictionary
        """
        # Build prompt for NPC decision
        prompt = self._build_npc_decision_prompt(npc, context)
        
        # Call LLM (REAL call, not mocked)
        llm = await self._get_llm_client()
        
        try:
            # Use interaction layer for NPC decisions
            response = await llm.generate_text(
                layer="interaction",
                prompt=prompt,
                context={"npc_id": npc["id"], "world_state_id": context["world_state_id"]},
                max_tokens=512,
                temperature=0.8  # Higher temperature for more creative decisions
            )
            
            # Parse LLM response
            decision = self._parse_npc_decision(response.get("text", ""), npc, context)
        except Exception as e:
            print(f"[WARNING] LLM call failed for NPC {npc['id']}: {e}")
            # Fallback to rule-based decision
            decision = self._generate_fallback_decision(npc, context)
        
        return decision
    
    def _build_npc_decision_prompt(self, npc: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build prompt for NPC decision-making."""
        personality = npc.get("personality_vector", [])
        stats = npc.get("stats", {})
        goal_stack = npc.get("goal_stack", [])
        
        nearby_summary = f"{len(context['nearby_npcs'])} nearby NPCs"
        if context.get("nearby_npcs"):
            nearby_summary += f" ({', '.join([n['name'] for n in context['nearby_npcs'][:3]])})"
        
        prompt = f"""You are {npc['name']}, a {npc.get('npc_type', 'human')} NPC in a cyberpunk dystopian world.

NPC Details:
- Name: {npc['name']}
- Type: {npc.get('npc_type', 'human')}
- Personality: {personality[:5] if personality else 'neutral'} (first 5 dimensions shown)
- Stats: Aggression={stats.get('aggression', 50)}, Intelligence={stats.get('intelligence', 50)}, Charisma={stats.get('charisma', 50)}
- Current State: {context.get('current_state', 'idle')}
- Current Location: {context.get('current_location', 'unknown')}
- Active Goals: {len(goal_stack)} goals in stack

Current Situation:
- Game Time: Day {context.get('game_time', 0)}
- Nearby NPCs: {nearby_summary}
- Faction: {context.get('faction', {}).get('name', 'None')}
- Recent Events: {context.get('recent_events', 0)} events affecting you

You are autonomous and must make decisions based on your personality, goals, and current situation. What should you do?

Respond with a JSON object containing:
{{
  "primary_action": "main action to take (move, interact, rest, hunt, etc.)",
  "target_npc_id": "NPC to interact with (if any)",
  "target_location": "location to move to (if moving)",
  "goal_progress": "how this action advances your goals",
  "reasoning": "brief explanation of decision"
}}"""
        
        return prompt
    
    def _parse_npc_decision(self, response: str, npc: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into NPC decision."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[WARNING] Failed to parse LLM response: {e}")
            decision = self._generate_fallback_decision(npc, context)
        
        # Validate and normalize decision
        decision.setdefault("primary_action", "idle")
        decision.setdefault("target_npc_id", None)
        decision.setdefault("target_location", None)
        decision.setdefault("goal_progress", "maintaining_current_state")
        decision.setdefault("reasoning", "Automated NPC decision")
        
        return decision
    
    def _generate_fallback_decision(self, npc: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback decision if LLM fails."""
        stats = npc.get("stats", {})
        aggression = stats.get("aggression", 50)
        current_state = context.get("current_state", "idle")
        
        if current_state == "combat":
            action = "defend"
        elif aggression > 70:
            action = "hunt"
        elif aggression < 30:
            action = "rest"
        else:
            action = "patrol"
        
        return {
            "primary_action": action,
            "target_npc_id": None,
            "target_location": None,
            "goal_progress": "maintaining_status_quo",
            "reasoning": "Fallback rule-based decision"
        }
    
    async def _execute_npc_actions(self, npc_id: str, decision: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute NPC actions based on decision."""
        actions_taken = []
        
        primary_action = decision.get("primary_action", "idle")
        
        try:
            if primary_action == "move":
                result = await self._move_npc(npc_id, decision.get("target_location"))
                actions_taken.append({"action": "move", "result": result})
            elif primary_action in ["interact", "talk"]:
                target_npc_id = decision.get("target_npc_id")
                if target_npc_id:
                    result = await self._interact_with_npc(npc_id, target_npc_id)
                    actions_taken.append({"action": "interact", "result": result})
            elif primary_action == "hunt":
                result = await self._hunt_action(npc_id, context)
                actions_taken.append({"action": "hunt", "result": result})
            elif primary_action == "rest":
                result = await self._rest_action(npc_id)
                actions_taken.append({"action": "rest", "result": result})
            elif primary_action == "patrol":
                result = await self._patrol_action(npc_id, context)
                actions_taken.append({"action": "patrol", "result": result})
            else:
                # Idle action - just update state
                actions_taken.append({"action": "idle", "result": {"status": "success"}})
        except Exception as e:
            print(f"[ERROR] Failed to execute action {primary_action}: {e}")
            actions_taken.append({"action": primary_action, "result": {"status": "failed", "error": str(e)}})
        
        return actions_taken
    
    async def _move_npc(self, npc_id: str, target_location: Optional[str]) -> Dict[str, Any]:
        """Move NPC to target location."""
        if not target_location:
            return {"status": "failed", "error": "No target location specified"}
        
        postgres = await self._get_postgres()
        
        await postgres.execute(
            """
            UPDATE npcs
            SET current_location = $1, updated_at = NOW()
            WHERE id = $2
            """,
            target_location,
            npc_id
        )
        
        return {"status": "success", "new_location": target_location}
    
    async def _interact_with_npc(self, npc_id: str, target_npc_id: str) -> Dict[str, Any]:
        """NPC interacts with another NPC."""
        postgres = await self._get_postgres()
        
        # Update relationships
        npc = await postgres.fetch(
            "SELECT relationships FROM npcs WHERE id = $1",
            npc_id
        )
        
        if npc:
            relationships = json.loads(npc["relationships"]) if isinstance(npc["relationships"], str) else (npc["relationships"] or {})
            relationships[target_npc_id] = relationships.get(target_npc_id, 0.5) + 0.1
            
            await postgres.execute(
                "UPDATE npcs SET relationships = $1::jsonb, updated_at = NOW() WHERE id = $2",
                json.dumps(relationships),
                npc_id
            )
            
            return {"status": "success", "target_npc": target_npc_id, "relationship_change": 0.1}
        
        return {"status": "failed", "error": "NPC not found"}
    
    async def _hunt_action(self, npc_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """NPC performs hunt action."""
        postgres = await self._get_postgres()
        
        # Update NPC state to hunting
        await postgres.execute(
            "UPDATE npcs SET current_state = 'hunting', updated_at = NOW() WHERE id = $1",
            npc_id
        )
        
        return {"status": "success", "new_state": "hunting"}
    
    async def _rest_action(self, npc_id: str) -> Dict[str, Any]:
        """NPC performs rest action."""
        postgres = await self._get_postgres()
        
        # Update NPC state to resting
        await postgres.execute(
            "UPDATE npcs SET current_state = 'resting', updated_at = NOW() WHERE id = $1",
            npc_id
        )
        
        return {"status": "success", "new_state": "resting"}
    
    async def _patrol_action(self, npc_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """NPC performs patrol action."""
        postgres = await self._get_postgres()
        
        # Update NPC state to patrolling
        await postgres.execute(
            "UPDATE npcs SET current_state = 'patrolling', updated_at = NOW() WHERE id = $1",
            npc_id
        )
        
        return {"status": "success", "new_state": "patrolling"}
    
    async def _update_npc_state(self, npc_id: str, decision: Dict[str, Any], actions_taken: List[Dict[str, Any]]):
        """Update NPC state after simulation cycle."""
        postgres = await self._get_postgres()
        
        # Store decision in meta_data
        npc = await postgres.fetch(
            "SELECT meta_data FROM npcs WHERE id = $1",
            npc_id
        )
        
        if npc:
            meta_data = json.loads(npc["meta_data"]) if isinstance(npc["meta_data"], str) else (npc["meta_data"] or {})
            
            if "simulation_history" not in meta_data:
                meta_data["simulation_history"] = []
            
            meta_data["simulation_history"].append({
                "timestamp": time.time(),
                "decision": decision,
                "actions_taken": actions_taken
            })
            
            # Keep only last 50 entries
            if len(meta_data["simulation_history"]) > 50:
                meta_data["simulation_history"] = meta_data["simulation_history"][-50:]
            
            await postgres.execute(
                "UPDATE npcs SET meta_data = $1::jsonb, updated_at = NOW() WHERE id = $2",
                json.dumps(meta_data),
                npc_id
            )
    
    async def simulate_all_npcs(self, world_state_id: str, max_concurrent: int = 10) -> Dict[str, Any]:
        """
        Simulate all active NPCs in parallel (with concurrency limit).
        
        Args:
            world_state_id: World state UUID
            max_concurrent: Maximum number of concurrent NPC simulations
        
        Returns:
            Simulation results for all NPCs
        """
        postgres = await self._get_postgres()
        
        # Get all active NPCs
        npcs = await postgres.fetch_all(
            "SELECT id FROM npcs WHERE world_state_id = $1 LIMIT 1000",
            world_state_id
        )
        
        # Simulate NPCs in batches to limit concurrency
        results = []
        errors = []
        
        for i in range(0, len(npcs), max_concurrent):
            batch = npcs[i:i + max_concurrent]
            tasks = [
                self.simulate_npc_cycle(str(npc["id"]), world_state_id)
                for npc in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    errors.append({
                        "npc_id": str(batch[j]["id"]),
                        "error": str(result)
                    })
                else:
                    results.append(result)
        
        return {
            "total_npcs": len(npcs),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

