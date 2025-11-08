"""
Faction Simulator - REAL agent simulation for faction dynamics.
Each faction acts as an autonomous agent with LLM-based decision making.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database_connection import get_postgres, get_redis
import asyncpg
import aioredis
# HTTP client for AI integration
import aiohttp
import os


class FactionSimulator:
    """
    Simulates faction dynamics with REAL agent behavior.
    Each faction makes autonomous decisions via LLM calls.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self.llm_client: Optional[LLMClient] = None
        self._faction_agents: Dict[str, Dict[str, Any]] = {}
        self._decision_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
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
    
    async def _get_llm_client(self) -> LLMClient:
        """Get LLM client instance."""
        if self.llm_client is None:
            self.llm_client = LLMClient()
        return self.llm_client
    
    async def simulate_faction_cycle(self, faction_id: str, world_state_id: str) -> Dict[str, Any]:
        """
        Simulate one decision cycle for a faction (REAL agent simulation).
        Each faction makes autonomous decisions via LLM calls.
        
        Args:
            faction_id: Faction UUID
            world_state_id: World state UUID
        
        Returns:
            Simulation result with actions taken
        """
        # Load faction data
        faction = await self._load_faction_data(faction_id)
        if not faction:
            raise ValueError(f"Faction {faction_id} not found")
        
        # Gather context for faction decision
        context = await self._gather_faction_context(faction_id, world_state_id)
        
        # Generate faction decision via LLM (REAL call)
        decision = await self._generate_faction_decision(faction, context)
        
        # Execute faction actions
        actions_taken = await self._execute_faction_actions(faction_id, decision, context)
        
        # Update faction state
        await self._update_faction_state(faction_id, decision, actions_taken)
        
        return {
            "faction_id": faction_id,
            "decision": decision,
            "actions": actions_taken,
            "timestamp": time.time()
        }
    
    async def _load_faction_data(self, faction_id: str) -> Optional[Dict[str, Any]]:
        """Load faction data from database."""
        postgres = await self._get_postgres()
        
        faction = await postgres.fetch(
            """
            SELECT id, name, description, faction_type, power_level, territory, 
                   relationships, hierarchy, meta_data
            FROM factions
            WHERE id = $1
            """,
            faction_id
        )
        
        if not faction:
            return None
        
        # Parse JSONB fields
        if isinstance(faction, dict):
            if isinstance(faction.get("territory"), str):
                faction["territory"] = json.loads(faction["territory"])
            if isinstance(faction.get("relationships"), str):
                faction["relationships"] = json.loads(faction["relationships"])
            if isinstance(faction.get("hierarchy"), str):
                faction["hierarchy"] = json.loads(faction["hierarchy"])
            if isinstance(faction.get("meta_data"), str):
                faction["meta_data"] = json.loads(faction["meta_data"])
        
        return faction
    
    async def _gather_faction_context(self, faction_id: str, world_state_id: str) -> Dict[str, Any]:
        """Gather context for faction decision-making."""
        postgres = await self._get_postgres()
        
        # Get faction NPCs
        npcs = await postgres.fetch_all(
            """
            SELECT id, name, stats
            FROM npcs
            WHERE faction_id = $1
            LIMIT 100
            """,
            faction_id
        )
        
        # Get other factions (for relationship tracking)
        # Note: factions table doesn't have world_state_id column
        # Filter by meta_data in Python
        all_factions = await postgres.fetch_all(
            """
            SELECT id, name, power_level, faction_type, meta_data
            FROM factions
            WHERE id != $1
            LIMIT 20
            """,
            faction_id
        )
        
        # Filter by world_state_id from meta_data
        other_factions = []
        for faction in all_factions:
            meta = faction.get("meta_data", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            if isinstance(meta, dict):
                meta_world_id = meta.get("world_state_id")
                if meta_world_id == world_state_id or not meta_world_id:
                    # Include if matches or no world_state_id set (legacy data)
                    other_factions.append({
                        "id": faction["id"],
                        "name": faction["name"],
                        "power_level": faction.get("power_level", 0.0),
                        "faction_type": faction.get("faction_type", "unknown")
                    })
        
        # Get recent events affecting this faction
        recent_events = await postgres.fetch_all(
            """
            SELECT id, node_type, title, narrative_content, meta_data, created_at
            FROM story_nodes
            WHERE meta_data->>'world_state_id' = $1 
              AND (meta_data->>'faction_id' = $2 OR narrative_content::text LIKE $3)
            ORDER BY created_at DESC
            LIMIT 10
            """,
            world_state_id,
            faction_id,
            f"%{faction_id}%"
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
            "faction_id": faction_id,
            "world_state_id": world_state_id,
            "npcs": [
                {
                    "id": str(npc["id"]),
                    "name": npc["name"],
                    "level": json.loads(npc["stats"]).get("level", 1) if isinstance(npc["stats"], str) else (npc["stats"] or {}).get("level", 1) if isinstance(npc["stats"], dict) else 1
                }
                for npc in npcs
            ],
            "other_factions": [
                {
                    "id": str(faction["id"]),
                    "name": faction["name"],
                    "power_level": faction.get("power_level", 0.0)
                }
                for faction in other_factions
            ],
            "recent_events": len(recent_events),
            "game_time": game_time
        }
        
        return context
    
    async def _generate_faction_decision(self, faction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate faction decision via LLM (REAL call).
        Each faction makes autonomous decisions.
        
        Args:
            faction: Faction data
            context: Faction context
        
        Returns:
            Faction decision dictionary
        """
        # Build prompt for faction decision
        prompt = self._build_faction_decision_prompt(faction, context)
        
        # Call LLM (REAL call, not mocked)
        llm = await self._get_llm_client()
        
        try:
            # Use coordination layer for faction decisions
            response = await llm.generate_text(
                layer="coordination",
                prompt=prompt,
                context={"faction_id": faction["id"], "world_state_id": context["world_state_id"]},
                max_tokens=512,
                temperature=0.8  # Higher temperature for more creative decisions
            )
            
            # Parse LLM response
            decision = self._parse_faction_decision(response.get("text", ""), faction, context)
        except Exception as e:
            print(f"[WARNING] LLM call failed for faction {faction['id']}: {e}")
            # Fallback to rule-based decision
            decision = self._generate_fallback_decision(faction, context)
        
        return decision
    
    def _build_faction_decision_prompt(self, faction: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build prompt for faction decision-making."""
        npc_summary = f"{len(context['npcs'])} active NPCs"
        other_factions_summary = ", ".join([f["name"] for f in context["other_factions"][:5]])
        
        prompt = f"""You are the leader of the {faction['name']} faction in a cyberpunk dystopian world.

Faction Details:
- Name: {faction['name']}
- Description: {faction.get('description', 'A powerful faction')}
- Type: {faction.get('faction_type', 'unknown')}
- Power Level: {faction.get('power_level', 0.5)}
- Active NPCs: {npc_summary}

Current Situation:
- Game Time: Day {context['game_time']}
- Other Active Factions: {other_factions_summary or 'None'}
- Recent Events: {context['recent_events']} events affecting your faction

Your faction is autonomous and must make strategic decisions. Based on the current situation, what actions should your faction take?

Respond with a JSON object containing:
{{
  "primary_goal": "main goal for this cycle",
  "actions": ["action1", "action2", "action3"],
  "target_faction_id": "faction to interact with (if any)",
  "territory_expansion": true/false,
  "resource_allocation": {{"military": 0.3, "economic": 0.4, "diplomatic": 0.3}},
  "reasoning": "brief explanation of decisions"
}}"""
        
        return prompt
    
    def _parse_faction_decision(self, response: str, faction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into faction decision."""
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
            decision = self._generate_fallback_decision(faction, context)
        
        # Validate and normalize decision
        decision.setdefault("primary_goal", "maintain_status_quo")
        decision.setdefault("actions", [])
        decision.setdefault("target_faction_id", None)
        decision.setdefault("territory_expansion", False)
        decision.setdefault("resource_allocation", {"military": 0.3, "economic": 0.4, "diplomatic": 0.3})
        decision.setdefault("reasoning", "Automated faction decision")
        
        return decision
    
    def _generate_fallback_decision(self, faction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback decision if LLM fails."""
        power_level = faction.get("power_level", 0.5)
        
        if power_level > 0.7:
            goal = "expand_territory"
            actions = ["increase_military", "negotiate_alliances"]
        elif power_level < 0.3:
            goal = "consolidate_power"
            actions = ["recruit_npcs", "strengthen_economy"]
        else:
            goal = "maintain_status_quo"
            actions = ["diplomatic_outreach", "resource_management"]
        
        return {
            "primary_goal": goal,
            "actions": actions,
            "target_faction_id": None,
            "territory_expansion": power_level > 0.6,
            "resource_allocation": {"military": 0.3, "economic": 0.4, "diplomatic": 0.3},
            "reasoning": "Fallback rule-based decision"
        }
    
    async def _execute_faction_actions(self, faction_id: str, decision: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute faction actions based on decision."""
        actions_taken = []
        
        for action in decision.get("actions", []):
            try:
                if action == "increase_military":
                    result = await self._increase_faction_military(faction_id)
                    actions_taken.append({"action": action, "result": result})
                elif action == "expand_territory":
                    result = await self._expand_faction_territory(faction_id)
                    actions_taken.append({"action": action, "result": result})
                elif action == "recruit_npcs":
                    result = await self._recruit_faction_npcs(faction_id, context["world_state_id"])
                    actions_taken.append({"action": action, "result": result})
                elif action == "negotiate_alliances":
                    target_id = decision.get("target_faction_id")
                    if target_id:
                        result = await self._negotiate_alliance(faction_id, target_id)
                        actions_taken.append({"action": action, "result": result})
                # Add more action handlers as needed
            except Exception as e:
                print(f"[ERROR] Failed to execute action {action}: {e}")
                actions_taken.append({"action": action, "result": {"status": "failed", "error": str(e)}})
        
        return actions_taken
    
    async def _increase_faction_military(self, faction_id: str) -> Dict[str, Any]:
        """Increase faction military power."""
        postgres = await self._get_postgres()
        
        await postgres.execute(
            """
            UPDATE factions
            SET power_level = LEAST(1.0, power_level + 0.05),
                updated_at = NOW()
            WHERE id = $1
            """,
            faction_id
        )
        
        return {"status": "success", "power_increase": 0.05}
    
    async def _expand_faction_territory(self, faction_id: str) -> Dict[str, Any]:
        """Expand faction territory."""
        postgres = await self._get_postgres()
        
        # Get current territory
        faction = await postgres.fetch(
            "SELECT territory FROM factions WHERE id = $1",
            faction_id
        )
        
        if faction:
            territory = json.loads(faction["territory"]) if isinstance(faction["territory"], str) else (faction["territory"] or [])
            new_territory_id = f"territory_{int(time.time())}"
            territory.append(new_territory_id)
            
            await postgres.execute(
                "UPDATE factions SET territory = $1::jsonb, updated_at = NOW() WHERE id = $2",
                json.dumps(territory),
                faction_id
            )
            
            return {"status": "success", "new_territory": new_territory_id}
        
        return {"status": "failed", "error": "Faction not found"}
    
    async def _recruit_faction_npcs(self, faction_id: str, world_state_id: str) -> Dict[str, Any]:
        """Recruit new NPCs for faction."""
        # This would create new NPCs - simplified for now
        return {"status": "success", "recruited": 0}
    
    async def _negotiate_alliance(self, faction_id: str, target_faction_id: str) -> Dict[str, Any]:
        """Negotiate alliance with another faction."""
        postgres = await self._get_postgres()
        
        # Update relationships
        faction = await postgres.fetch(
            "SELECT relationships FROM factions WHERE id = $1",
            faction_id
        )
        
        if faction:
            relationships = json.loads(faction["relationships"]) if isinstance(faction["relationships"], str) else (faction["relationships"] or {})
            relationships[target_faction_id] = relationships.get(target_faction_id, 0.0) + 0.1
            
            await postgres.execute(
                "UPDATE factions SET relationships = $1::jsonb, updated_at = NOW() WHERE id = $2",
                json.dumps(relationships),
                faction_id
            )
            
            return {"status": "success", "alliance_strength": relationships[target_faction_id]}
        
        return {"status": "failed", "error": "Faction not found"}
    
    async def _update_faction_state(self, faction_id: str, decision: Dict[str, Any], actions_taken: List[Dict[str, Any]]):
        """Update faction state after simulation cycle."""
        postgres = await self._get_postgres()
        
        # Store decision in meta_data
        faction = await postgres.fetch(
            "SELECT meta_data FROM factions WHERE id = $1",
            faction_id
        )
        
        if faction:
            meta_data = json.loads(faction["meta_data"]) if isinstance(faction["meta_data"], str) else (faction["meta_data"] or {})
            
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
                "UPDATE factions SET meta_data = $1::jsonb, updated_at = NOW() WHERE id = $2",
                json.dumps(meta_data),
                faction_id
            )
    
    async def simulate_all_factions(self, world_state_id: str) -> Dict[str, Any]:
        """
        Simulate all active factions in parallel.
        
        Args:
            world_state_id: World state UUID
        
        Returns:
            Simulation results for all factions
        """
        postgres = await self._get_postgres()
        
        # Get all active factions
        factions = await postgres.fetch_all(
            # Note: factions table doesn't have world_state_id column
            # For simulation, get all factions (filtering by world_state would require meta_data lookup)
            "SELECT id FROM factions LIMIT 50"
        )
        
        # Simulate all factions in parallel
        tasks = [
            self.simulate_faction_cycle(str(faction["id"]), world_state_id)
            for faction in factions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and format results
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "faction_id": str(factions[i]["id"]),
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        return {
            "total_factions": len(factions),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "results": successful_results,
            "errors": failed_results
        }

