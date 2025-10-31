"""
Causal Chain - Event propagation and consequence tracking.
Tracks action → consequence relationships and propagates events through the world.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class CausalChain:
    """
    Tracks causal relationships between events and actions.
    Propagates consequences through the world simulation.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._causal_graph: Dict[str, List[str]] = {}  # event_id -> [consequence_ids]
        self._pending_consequences: List[Dict[str, Any]] = []
    
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
    
    async def register_event(self, event: Dict[str, Any], world_state_id: str) -> Dict[str, Any]:
        """
        Register an event and track its potential consequences.
        
        Args:
            event: Event dictionary with id, type, data, etc.
            world_state_id: World state UUID
        
        Returns:
            Registration confirmation with consequence IDs
        """
        event_id = event.get("id", str(uuid4()))
        event["id"] = event_id
        event["timestamp"] = event.get("timestamp", time.time())
        event["world_state_id"] = world_state_id
        
        # Store event in database
        await self._store_event(event, world_state_id)
        
        # Generate potential consequences
        consequences = await self._generate_consequences(event, world_state_id)
        
        # Link consequences to event
        self._causal_graph[event_id] = [c["id"] for c in consequences]
        
        # Store causal relationships
        await self._store_causal_relationships(event_id, consequences, world_state_id)
        
        return {
            "event_id": event_id,
            "consequences": consequences,
            "status": "registered"
        }
    
    async def _store_event(self, event: Dict[str, Any], world_state_id: str):
        """Store event in database."""
        postgres = await self._get_postgres()
        
        # Note: story_nodes requires player_id (NOT NULL constraint)
        # For simulation events, skip story_nodes insertion
        # Events are tracked internally in causal_chain
        # In production, create a system player for simulation events or use a separate table
        pass
    
    async def _generate_consequences(self, event: Dict[str, Any], world_state_id: str) -> List[Dict[str, Any]]:
        """Generate potential consequences for an event."""
        event_type = event.get("type")
        consequences = []
        
        # Generate consequences based on event type
        if event_type == "faction_action":
            # Faction actions may affect relationships, power, territory
            consequences.extend(await self._generate_faction_consequences(event, world_state_id))
        
        elif event_type == "npc_action":
            # NPC actions may affect relationships, location, state
            consequences.extend(await self._generate_npc_consequences(event, world_state_id))
        
        elif event_type == "economic_event":
            # Economic events may affect prices, supply, demand
            consequences.extend(await self._generate_economic_consequences(event, world_state_id))
        
        elif event_type == "territory_change":
            # Territory changes may affect faction power, NPC locations
            consequences.extend(await self._generate_territory_consequences(event, world_state_id))
        
        elif event_type == "player_action":
            # Player actions may trigger NPC reactions, faction responses
            consequences.extend(await self._generate_player_consequences(event, world_state_id))
        
        return consequences
    
    async def _generate_faction_consequences(self, event: Dict[str, Any], world_state_id: str) -> List[Dict[str, Any]]:
        """Generate consequences for faction events."""
        consequences = []
        event_data = event.get("data", {})
        faction_id = event_data.get("faction_id")
        
        if not faction_id:
            return consequences
        
        # Check if action affects other factions
        action_type = event_data.get("action_type")
        
        if action_type in ["military_expansion", "territory_conquest"]:
            # May trigger defensive responses from other factions
            consequences.append({
                "id": str(uuid4()),
                "type": "faction_response",
                "data": {
                    "triggering_faction": faction_id,
                    "response_type": "defensive",
                    "priority": "high"
                },
                "delay": 1.0,  # 1 game day delay
                "probability": 0.7
            })
        
        elif action_type == "alliance_formation":
            # May trigger counter-alliances
            consequences.append({
                "id": str(uuid4()),
                "type": "faction_response",
                "data": {
                    "triggering_faction": faction_id,
                    "response_type": "counter_alliance",
                    "priority": "medium"
                },
                "delay": 2.0,  # 2 game days delay
                "probability": 0.5
            })
        
        return consequences
    
    async def _generate_npc_consequences(self, event: Dict[str, Any], world_state_id: str) -> List[Dict[str, Any]]:
        """Generate consequences for NPC events."""
        consequences = []
        event_data = event.get("data", {})
        npc_id = event_data.get("npc_id")
        
        if not npc_id:
            return consequences
        
        action_type = event_data.get("action_type")
        
        if action_type == "kill":
            # NPC death may trigger faction retaliation, NPC fear responses
            consequences.append({
                "id": str(uuid4()),
                "type": "npc_reaction",
                "data": {
                    "triggering_npc": npc_id,
                    "reaction_type": "fear",
                    "affected_npcs": "nearby"
                },
                "delay": 0.5,  # 0.5 game day delay
                "probability": 0.8
            })
        
        elif action_type == "betrayal":
            # Betrayal may affect relationships
            consequences.append({
                "id": str(uuid4()),
                "type": "relationship_change",
                "data": {
                    "triggering_npc": npc_id,
                    "relationship_delta": -0.3
                },
                "delay": 0.0,  # Immediate
                "probability": 1.0
            })
        
        return consequences
    
    async def _generate_economic_consequences(self, event: Dict[str, Any], world_state_id: str) -> List[Dict[str, Any]]:
        """Generate consequences for economic events."""
        consequences = []
        event_data = event.get("data", {})
        event_type = event_data.get("economic_event_type")
        
        if event_type == "price_spike":
            # Price spike may cause NPCs to change behavior (hoarding, stealing)
            consequences.append({
                "id": str(uuid4()),
                "type": "npc_behavior_change",
                "data": {
                    "behavior_type": "resource_hoarding",
                    "priority": "medium"
                },
                "delay": 1.0,
                "probability": 0.6
            })
        
        elif event_type == "shortage":
            # Shortage may trigger conflicts
            consequences.append({
                "id": str(uuid4()),
                "type": "conflict_trigger",
                "data": {
                    "conflict_type": "resource_war",
                    "intensity": "medium"
                },
                "delay": 2.0,
                "probability": 0.7
            })
        
        return consequences
    
    async def _generate_territory_consequences(self, event: Dict[str, Any], world_state_id: str) -> List[Dict[str, Any]]:
        """Generate consequences for territory changes."""
        consequences = []
        event_data = event.get("data", {})
        territory_id = event_data.get("territory_id")
        new_owner = event_data.get("new_owner")
        old_owner = event_data.get("old_owner")
        
        if old_owner:
            # Old owner may attempt to reclaim territory
            consequences.append({
                "id": str(uuid4()),
                "type": "faction_action",
                "data": {
                    "faction_id": old_owner,
                    "action_type": "reclaim_territory",
                    "target_territory": territory_id
                },
                "delay": 3.0,  # 3 game days delay
                "probability": 0.5
            })
        
        # NPCs in territory may react to ownership change
        consequences.append({
            "id": str(uuid4()),
            "type": "npc_behavior_change",
            "data": {
                "territory_id": territory_id,
                "behavior_type": "loyalty_shift",
                "new_faction": new_owner
            },
            "delay": 1.0,
            "probability": 0.8
        })
        
        return consequences
    
    async def _generate_player_consequences(self, event: Dict[str, Any], world_state_id: str) -> List[Dict[str, Any]]:
        """Generate consequences for player actions."""
        consequences = []
        event_data = event.get("data", {})
        action_type = event_data.get("action_type")
        
        if action_type == "kill_npc":
            # Killing NPC may trigger faction retaliation
            npc_id = event_data.get("npc_id")
            if npc_id:
                consequences.append({
                    "id": str(uuid4()),
                    "type": "faction_response",
                    "data": {
                        "response_type": "retaliation",
                        "target": "player",
                        "triggering_npc": npc_id
                    },
                    "delay": 2.0,
                    "probability": 0.9
                })
        
        elif action_type == "steal":
            # Stealing may trigger NPC hostility
            consequences.append({
                "id": str(uuid4()),
                "type": "npc_reaction",
                "data": {
                    "reaction_type": "hostile",
                    "affected_npcs": "witnesses"
                },
                "delay": 0.5,
                "probability": 0.7
            })
        
        return consequences
    
    async def _store_causal_relationships(self, event_id: str, consequences: List[Dict[str, Any]], world_state_id: str):
        """Store causal relationships in database."""
        postgres = await self._get_postgres()
        
        for consequence in consequences:
            # Note: story_nodes requires player_id (NOT NULL constraint)
            # For simulation consequences, skip story_nodes insertion
            # Consequences are tracked internally in causal_chain
            # In production, create a system player for simulation events or use a separate table
            pass
    
    async def process_pending_consequences(self, world_state_id: str, current_game_time: float) -> List[Dict[str, Any]]:
        """
        Process pending consequences that should trigger now.
        
        Args:
            world_state_id: World state UUID
            current_game_time: Current game time (days)
        
        Returns:
            List of consequences that were triggered
        """
        postgres = await self._get_postgres()
        
        # Load pending consequences from internal storage
        # Note: story_nodes can't be used due to player_id NOT NULL constraint
        # In production, use a separate simulation_events table or system player
        # For now, return empty list (consequences tracked internally)
        consequences = []
        
        triggered = []
        
        for consequence in consequences:
            meta_data = consequence.get("meta_data")
            if isinstance(meta_data, str):
                meta_data = json.loads(meta_data)
            
            if not isinstance(meta_data, dict):
                continue
            
            parent_event_id = meta_data.get("parent_event_id")
            delay = meta_data.get("delay", 0.0)
            probability = meta_data.get("probability", 1.0)
            
            # Get parent event timestamp
            parent_event = await postgres.fetch(
                "SELECT meta_data FROM story_nodes WHERE id = $1",
                parent_event_id
            )
            
            if not parent_event:
                continue
            
            parent_meta = parent_event.get("meta_data")
            if isinstance(parent_meta, str):
                parent_meta = json.loads(parent_meta)
            
            parent_timestamp = parent_meta.get("timestamp", 0)
            
            # Check if consequence should trigger
            time_since_event = current_game_time - parent_timestamp
            
            if time_since_event >= delay:
                # Check probability
                import random
                if random.random() < probability:
                    # Trigger consequence
                    consequence_data = consequence.get("content")
                    if isinstance(consequence_data, str):
                        consequence_data = json.loads(consequence_data)
                    
                    triggered_consequence = await self._trigger_consequence(
                        consequence["id"],
                        consequence_data,
                        world_state_id
                    )
                    
                    triggered.append(triggered_consequence)
                    
                    # Update consequence status
                    meta_data["status"] = "triggered"
                    meta_data["triggered_at"] = current_game_time
                    
                    await postgres.execute(
                        "UPDATE story_nodes SET meta_data = $1::jsonb, updated_at = NOW() WHERE id = $2",
                        json.dumps(meta_data),
                        consequence["id"]
                    )
        
        return triggered
    
    async def _trigger_consequence(self, consequence_id: str, consequence_data: Dict[str, Any], world_state_id: str) -> Dict[str, Any]:
        """Trigger a consequence and propagate it through the system."""
        consequence_type = consequence_data.get("type")
        
        # Create event for the consequence
        event = {
            "id": str(uuid4()),
            "type": consequence_type,
            "data": consequence_data,
            "timestamp": time.time(),
            "world_state_id": world_state_id,
            "parent_consequence_id": consequence_id
        }
        
        # Register the consequence as a new event (which may generate more consequences)
        result = await self.register_event(event, world_state_id)
        
        return {
            "consequence_id": consequence_id,
            "event_id": event["id"],
            "type": consequence_type,
            "status": "triggered"
        }
    
    async def get_causal_chain(self, event_id: str, world_state_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """Get full causal chain for an event."""
        if event_id not in self._causal_graph:
            return {"event_id": event_id, "chain": [], "depth": 0}
        
        chain = []
        visited = set()
        
        def traverse(e_id: str, depth: int):
            if depth > max_depth or e_id in visited:
                return
            
            visited.add(e_id)
            chain.append({"event_id": e_id, "depth": depth})
            
            if e_id in self._causal_graph:
                for consequence_id in self._causal_graph[e_id]:
                    traverse(consequence_id, depth + 1)
        
        traverse(event_id, 0)
        
        return {
            "event_id": event_id,
            "chain": chain,
            "depth": len(chain) - 1
        }

