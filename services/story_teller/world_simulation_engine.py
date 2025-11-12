"""
World Simulation Engine - Core simulation orchestration.
Handles continuous background simulation with autonomous NPCs and faction dynamics.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncpg
import redis.asyncio as aioredis
from temporal_orchestrator import TemporalOrchestrator
from faction_simulator import FactionSimulator
from npc_behavior_system import NPCBehaviorSystem
from economic_simulator import EconomicSimulator
from spatial_manager import SpatialManager
from causal_chain import CausalChain


class WorldSimulationEngine:
    """
    Core engine for world simulation.
    Orchestrates continuous background simulation when player is offline.
    Manages event-driven simulation with state persistence.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._simulation_running = False
        self._simulation_task: Optional[asyncio.Task] = None
        self._event_queue: List[Dict[str, Any]] = []
        self._simulation_state: Dict[str, Any] = {
            "current_game_time": 0,
            "last_simulation_cycle": 0,
            "active_npcs": [],
            "active_factions": [],
            "pending_events": []
        }
        self._cycle_interval = 5.0  # 5 seconds per game day
        self._time_acceleration = 1.0  # Normal time speed
        
        # Initialize subsystems
        self.temporal_orchestrator = TemporalOrchestrator()
        self.faction_simulator = FactionSimulator()
        self.npc_behavior_system = NPCBehaviorSystem()
        self.economic_simulator = EconomicSimulator()
        self.spatial_manager = SpatialManager()
        self.causal_chain = CausalChain()
    
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
    
    async def start_simulation(self, world_state_id: UUID) -> Dict[str, Any]:
        """
        Start continuous world simulation.
        
        Args:
            world_state_id: World state UUID to simulate
        
        Returns:
            Simulation start confirmation
        """
        if self._simulation_running:
            return {
                "status": "already_running",
                "message": "Simulation is already running"
            }
        
        # Load initial world state
        postgres = await self._get_postgres()
        world_state = await postgres.fetch(
            "SELECT * FROM world_states WHERE id = $1",
            str(world_state_id)
        )
        
        if not world_state:
            raise ValueError(f"World state {world_state_id} not found")
        
        # Load time from database into temporal orchestrator
        await self.temporal_orchestrator.load_time_from_database(str(world_state_id))
        
        # Initialize simulation state
        # Get game_time from simulation_data
        sim_data = world_state.get("simulation_data")
        if isinstance(sim_data, str):
            try:
                sim_data = json.loads(sim_data)
            except json.JSONDecodeError:
                sim_data = {}
        if not isinstance(sim_data, dict):
            sim_data = {}
        
        game_time = sim_data.get("game_time", 0)
        self._simulation_state = {
            "world_state_id": str(world_state_id),
            "current_game_time": game_time,
            "last_simulation_cycle": time.time(),
            "active_npcs": [],
            "active_factions": [],
            "pending_events": []
        }
        
        # Start simulation loop
        self._simulation_running = True
        self._simulation_task = asyncio.create_task(self._simulation_loop())
        
        # Persist simulation state
        await self._persist_simulation_state()
        
        return {
            "status": "started",
            "world_state_id": str(world_state_id),
            "message": "Simulation started successfully"
        }
    
    async def stop_simulation(self) -> Dict[str, Any]:
        """
        Stop continuous world simulation.
        
        Returns:
            Simulation stop confirmation
        """
        if not self._simulation_running:
            return {
                "status": "not_running",
                "message": "Simulation is not running"
            }
        
        self._simulation_running = False
        
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass
        
        # Final state persistence
        await self._persist_simulation_state()
        
        return {
            "status": "stopped",
            "message": "Simulation stopped successfully"
        }
    
    async def _simulation_loop(self):
        """
        Core simulation loop that runs continuously.
        Processes simulation cycles at configured intervals.
        """
        try:
            while self._simulation_running:
                cycle_start = time.time()
                
                # Process one simulation cycle
                await self._process_simulation_cycle()
                
                # Calculate cycle time and sleep
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, self._cycle_interval - cycle_time)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    # Cycle took longer than interval - log warning
                    print(f"[WARNING] Simulation cycle took {cycle_time:.2f}s (exceeds {self._cycle_interval}s interval)")
        
        except asyncio.CancelledError:
            print("[INFO] Simulation loop cancelled")
        except Exception as e:
            print(f"[ERROR] Simulation loop error: {e}")
            self._simulation_running = False
    
    async def _process_simulation_cycle(self):
        """
        Process one simulation cycle (1 game day).
        Orchestrates all simulation subsystems.
        """
        # Advance game time first
        time_result = await self.temporal_orchestrator.advance_game_time(1.0)
        self._simulation_state["current_game_time"] = time_result["new_time"]
        self._simulation_state["last_simulation_cycle"] = time.time()
        
        # Process pending events
        await self._process_pending_events()
        
        # Get active NPCs and factions
        await self._refresh_active_entities()
        
        world_state_id = self._simulation_state.get("world_state_id")
        if not world_state_id:
            return
        
        # Process temporal orchestration (multi-speed time management)
        if self.temporal_orchestrator.should_update("npc", 1.0):
            # Process NPC autonomous decisions
            npc_results = await self.npc_behavior_system.simulate_all_npcs(
                world_state_id,
                max_concurrent=10
            )
            self._simulation_state["last_npc_simulation"] = npc_results
        
        if self.temporal_orchestrator.should_update("faction", 1.0):
            # Process faction dynamics
            faction_results = await self.faction_simulator.simulate_all_factions(world_state_id)
            self._simulation_state["last_faction_simulation"] = faction_results
        
        if self.temporal_orchestrator.should_update("economic", 1.0):
            # Process economic changes
            economic_results = await self.economic_simulator.simulate_economic_cycle(world_state_id)
            self._simulation_state["last_economic_simulation"] = economic_results
        
        if self.temporal_orchestrator.should_update("world", 1.0):
            # Process spatial/territory changes
            spatial_results = await self.spatial_manager.update_territory_control(world_state_id)
            self._simulation_state["last_spatial_simulation"] = spatial_results
        
        # Process causal chains (always check pending consequences)
        game_time = self._simulation_state["current_game_time"]
        triggered_consequences = await self.causal_chain.process_pending_consequences(
            world_state_id,
            float(game_time)
        )
        
        if triggered_consequences:
            self._simulation_state["triggered_consequences"] = triggered_consequences
        
        # Persist state after cycle
        await self._persist_simulation_state()
        
        # Cache simulation state in Redis
        redis = await self._get_redis()
        await redis.set(
            f"simulation:state:{self._simulation_state.get('world_state_id')}",
            json.dumps(self._simulation_state),
            ttl=3600  # 1 hour TTL
        )
    
    async def _process_pending_events(self):
        """Process all pending events in the queue."""
        events_to_process = self._event_queue.copy()
        self._event_queue.clear()
        
        for event in events_to_process:
            try:
                # Process event (will be enhanced by causal_chain.py)
                await self._handle_simulation_event(event)
            except Exception as e:
                print(f"[ERROR] Failed to process event {event.get('id')}: {e}")
    
    async def _handle_simulation_event(self, event: Dict[str, Any]):
        """
        Handle a single simulation event.
        
        Args:
            event: Event dictionary with id, type, data, etc.
        """
        world_state_id = self._simulation_state.get("world_state_id")
        if not world_state_id:
            return
        
        # Register event with causal chain system
        causal_result = await self.causal_chain.register_event(event, world_state_id)
        
        # Store event in database for history
        # Note: story_nodes requires player_id (NOT NULL constraint)
        # For simulation events, we'll store in meta_data only, not in story_nodes
        # Or create a system player - for now, skip story_nodes insertion for simulation events
        # Events are already stored in causal_chain._store_event
        pass
    
    async def _refresh_active_entities(self):
        """Refresh list of active NPCs and factions for simulation."""
        postgres = await self._get_postgres()
        world_state_id = self._simulation_state.get("world_state_id")
        
        if not world_state_id:
            return
        
        # Get active NPCs (note: npcs table doesn't have status column, get all)
        npcs = await postgres.fetch_all(
            """
            SELECT id, name, faction_id
            FROM npcs
            WHERE world_state_id = $1
            LIMIT 1000
            """,
            world_state_id
        )
        self._simulation_state["active_npcs"] = [
            {"id": str(npc["id"]), "name": npc["name"], "faction_id": str(npc["faction_id"]) if npc["faction_id"] else None}
            for npc in npcs
        ]
        
        # Get active factions
        # Note: factions table doesn't have world_state_id column
        # Filter by meta_data in Python
        all_factions = await postgres.fetch_all(
            """
            SELECT id, name, meta_data
            FROM factions
            LIMIT 50
            """
        )
        
        # Filter by world_state_id from meta_data
        filtered_factions = []
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
                    filtered_factions.append(faction)
        
        # Use filtered list or all if no matches (for testing with legacy data)
        factions = filtered_factions if filtered_factions else list(all_factions)
        self._simulation_state["active_factions"] = [
            {"id": str(faction["id"]), "name": faction["name"]}
            for faction in factions
        ]
    
    async def _persist_simulation_state(self):
        """Persist simulation state to PostgreSQL."""
        if not self._simulation_state.get("world_state_id"):
            return
        
        postgres = await self._get_postgres()
        world_state_id = self._simulation_state.get("world_state_id")
        
        # Get current simulation_data
        current_state = await postgres.fetch(
            "SELECT simulation_data FROM world_states WHERE id = $1",
            world_state_id
        )
        
        sim_data = {}
        if current_state:
            current_sim = current_state.get("simulation_data")
            if isinstance(current_sim, str):
                try:
                    sim_data = json.loads(current_sim)
                except json.JSONDecodeError:
                    sim_data = {}
            elif isinstance(current_sim, dict):
                sim_data = current_sim
        
        # Update simulation_data with game_time and simulation_state
        sim_data["game_time"] = self._simulation_state["current_game_time"]
        sim_data["simulation_state"] = {
            "last_cycle": self._simulation_state["last_simulation_cycle"],
            "active_npcs_count": len(self._simulation_state["active_npcs"]),
            "active_factions_count": len(self._simulation_state["active_factions"]),
            "pending_events_count": len(self._simulation_state["pending_events"])
        }
        
        # Update world state with simulation data
        await postgres.execute(
            """
            UPDATE world_states
            SET 
                simulation_data = $1::jsonb,
                updated_at = NOW()
            WHERE id = $2
            """,
            json.dumps(sim_data),
            world_state_id
        )
    
    async def get_simulation_status(self) -> Dict[str, Any]:
        """
        Get current simulation status.
        
        Returns:
            Simulation status dictionary
        """
        return {
            "running": self._simulation_running,
            "state": self._simulation_state.copy(),
            "cycle_interval": self._cycle_interval,
            "time_acceleration": self._time_acceleration
        }
    
    async def add_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add event to simulation queue.
        
        Args:
            event: Event dictionary with type, data, etc.
        
        Returns:
            Event addition confirmation
        """
        if "id" not in event:
            event["id"] = str(uuid4())
        if "timestamp" not in event:
            event["timestamp"] = time.time()
        
        self._event_queue.append(event)
        
        return {
            "status": "added",
            "event_id": event["id"],
            "message": "Event added to simulation queue"
        }

