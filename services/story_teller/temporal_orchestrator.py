"""
Temporal Orchestrator - Multi-speed time management.
Handles different time scales for NPCs, factions, economy, and world events.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from enum import Enum

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool, PostgreSQLPool, RedisPool


class TimeScale(Enum):
    """Time scales for different simulation subsystems."""
    REAL_TIME = 1.0        # Real-world time (1:1)
    NPC_TIME = 10.0        # NPC decisions (10x faster)
    FACTION_TIME = 100.0   # Faction dynamics (100x faster)
    ECONOMIC_TIME = 50.0   # Economic changes (50x faster)
    WORLD_TIME = 1.0       # World events (same as real-time)


class TemporalOrchestrator:
    """
    Orchestrates multi-speed time management for simulation subsystems.
    Allows different components to run at different time scales.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self.redis: Optional[RedisPool] = None
        self._time_scales: Dict[str, float] = {
            "npc": TimeScale.NPC_TIME.value,
            "faction": TimeScale.FACTION_TIME.value,
            "economic": TimeScale.ECONOMIC_TIME.value,
            "world": TimeScale.WORLD_TIME.value,
            "real": TimeScale.REAL_TIME.value
        }
        self._last_update_times: Dict[str, float] = {}
        self._time_accumulators: Dict[str, float] = {}
        self._base_time = time.time()
        self._game_time = 0  # Game days elapsed
    
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
    
    def get_game_time(self) -> int:
        """
        Get current game time (game days elapsed).
        
        Returns:
            Number of game days elapsed
        """
        return self._game_time
    
    def get_time_for_scale(self, scale_name: str) -> float:
        """
        Get scaled time for a specific subsystem.
        
        Args:
            scale_name: Name of time scale (npc, faction, economic, world, real)
        
        Returns:
            Scaled time value
        """
        if scale_name not in self._time_scales:
            return 0.0
        
        scale_factor = self._time_scales[scale_name]
        elapsed_real_time = time.time() - self._base_time
        return elapsed_real_time * scale_factor
    
    def should_update(self, scale_name: str, update_interval: float) -> bool:
        """
        Check if subsystem should update based on its time scale.
        
        Args:
            scale_name: Name of time scale
            update_interval: Minimum interval between updates (in scaled time)
        
        Returns:
            True if subsystem should update
        """
        if scale_name not in self._last_update_times:
            self._last_update_times[scale_name] = 0.0
            self._time_accumulators[scale_name] = 0.0
            return True
        
        current_time = self.get_time_for_scale(scale_name)
        last_update = self._last_update_times[scale_name]
        time_accumulator = self._time_accumulators[scale_name]
        
        # Accumulate time difference
        time_accumulator += (current_time - last_update)
        
        if time_accumulator >= update_interval:
            self._last_update_times[scale_name] = current_time
            self._time_accumulators[scale_name] = time_accumulator - update_interval
            return True
        
        return False
    
    async def advance_game_time(self, days: float = 1.0) -> Dict[str, Any]:
        """
        Advance game time by specified number of days.
        
        Args:
            days: Number of game days to advance
        
        Returns:
            Time advancement confirmation
        """
        old_time = self._game_time
        self._game_time += int(days)
        
        # Update all time accumulators
        for scale_name in self._time_scales.keys():
            if scale_name in self._last_update_times:
                # Reset to force immediate update on next check
                self._time_accumulators[scale_name] = float('inf')
        
        return {
            "status": "advanced",
            "old_time": old_time,
            "new_time": self._game_time,
            "days_advanced": days
        }
    
    async def set_time_scale(self, scale_name: str, scale_factor: float) -> Dict[str, Any]:
        """
        Set time scale factor for a subsystem.
        
        Args:
            scale_name: Name of time scale
            scale_factor: Multiplier for time (e.g., 10.0 = 10x faster)
        
        Returns:
            Scale update confirmation
        """
        if scale_name not in self._time_scales:
            raise ValueError(f"Unknown time scale: {scale_name}")
        
        old_factor = self._time_scales[scale_name]
        self._time_scales[scale_name] = scale_factor
        
        # Reset accumulator for this scale
        if scale_name in self._time_accumulators:
            self._time_accumulators[scale_name] = 0.0
        
        return {
            "status": "updated",
            "scale_name": scale_name,
            "old_factor": old_factor,
            "new_factor": scale_factor
        }
    
    async def get_time_status(self) -> Dict[str, Any]:
        """
        Get current time status for all scales.
        
        Returns:
            Time status dictionary
        """
        status = {
            "game_time": self._game_time,
            "base_time": self._base_time,
            "scales": {}
        }
        
        for scale_name, scale_factor in self._time_scales.items():
            scaled_time = self.get_time_for_scale(scale_name)
            last_update = self._last_update_times.get(scale_name, 0.0)
            accumulator = self._time_accumulators.get(scale_name, 0.0)
            
            status["scales"][scale_name] = {
                "scale_factor": scale_factor,
                "scaled_time": scaled_time,
                "last_update": last_update,
                "accumulator": accumulator
            }
        
        return status
    
    async def reset_time(self) -> Dict[str, Any]:
        """
        Reset all time accumulators and counters.
        
        Returns:
            Reset confirmation
        """
        self._base_time = time.time()
        self._game_time = 0
        self._last_update_times.clear()
        self._time_accumulators.clear()
        
        return {
            "status": "reset",
            "message": "All time scales reset"
        }
    
    async def get_next_update_time(self, scale_name: str, update_interval: float) -> float:
        """
        Get time (in real seconds) until next update for a subsystem.
        
        Args:
            scale_name: Name of time scale
            update_interval: Minimum interval between updates (in scaled time)
        
        Returns:
            Real seconds until next update
        """
        if scale_name not in self._time_scales:
            return 0.0
        
        scale_factor = self._time_scales[scale_name]
        accumulator = self._time_accumulators.get(scale_name, 0.0)
        
        if accumulator >= update_interval:
            return 0.0
        
        remaining_scaled_time = update_interval - accumulator
        remaining_real_time = remaining_scaled_time / scale_factor
        
        return remaining_real_time
    
    async def sync_time_to_database(self, world_state_id: str) -> Dict[str, Any]:
        """
        Sync game time to world state in database.
        
        Args:
            world_state_id: World state UUID
        
        Returns:
            Sync confirmation
        """
        postgres = await self._get_postgres()
        
        # Get current simulation_data
        world_state = await postgres.fetch(
            "SELECT simulation_data FROM world_states WHERE id = $1",
            world_state_id
        )
        
        sim_data = {}
        if world_state:
            current_sim = world_state.get("simulation_data")
            if isinstance(current_sim, str):
                try:
                    sim_data = json.loads(current_sim)
                except json.JSONDecodeError:
                    sim_data = {}
            elif isinstance(current_sim, dict):
                sim_data = current_sim
        
        # Update with game_time and temporal_state
        sim_data["game_time"] = self._game_time
        sim_data["temporal_state"] = {
            "base_time": self._base_time,
            "time_scales": self._time_scales,
            "last_update": time.time()
        }
        
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
        
        return {
            "status": "synced",
            "game_time": self._game_time,
            "world_state_id": world_state_id
        }
    
    async def load_time_from_database(self, world_state_id: str) -> Dict[str, Any]:
        """
        Load game time from world state in database.
        
        Args:
            world_state_id: World state UUID
        
        Returns:
            Load confirmation
        """
        postgres = await self._get_postgres()
        
        world_state = await postgres.fetch(
            "SELECT simulation_data FROM world_states WHERE id = $1",
            world_state_id
        )
        
        if not world_state:
            raise ValueError(f"World state {world_state_id} not found")
        
        # Load game_time from simulation_data
        sim_data = world_state.get("simulation_data")
        if isinstance(sim_data, str):
            try:
                sim_data = json.loads(sim_data)
            except json.JSONDecodeError:
                sim_data = {}
        
        if not isinstance(sim_data, dict):
            sim_data = {}
        
        # Load game_time
        self._game_time = sim_data.get("game_time", 0)
        
        # Load temporal state from simulation_data if available
        temporal_state = sim_data.get("temporal_state", {})
        if temporal_state:
            self._base_time = temporal_state.get("base_time", time.time())
            self._time_scales.update(temporal_state.get("time_scales", {}))
        
        return {
            "status": "loaded",
            "game_time": self._game_time,
            "world_state_id": world_state_id
        }

