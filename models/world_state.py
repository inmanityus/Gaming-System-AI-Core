"""
World State Model
Represents world simulation state for Story Teller service.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

from .base import Base


class WorldState(Base):
    """
    World simulation state model (Story Teller).
    
    Represents the continuous world simulation that runs independently
    of player sessions. Tracks time, factions, economic state, and
    world-wide events.
    
    Attributes:
        id: Unique world state identifier
        world_time: Current in-game time (separate from real time)
        day_phase: Current day phase (morning, afternoon, evening, night)
        weather: Current weather conditions
        faction_power: Faction power levels as JSONB
        global_events: Active global events as JSONB
        economic_state: Economic indicators (prices, supply, demand)
        npc_population: NPC population counts by type
        territory_control: Territory control map as JSONB
        simulation_data: Additional simulation data as JSONB
        version: Optimistic locking version number
        created_at: State creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "world_states"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Time tracking
    world_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    day_phase = Column(String(20), nullable=False, default="day")  # morning, afternoon, evening, night
    
    # Environment
    weather = Column(String(50), nullable=True)  # clear, rain, fog, storm, etc.
    
    # Faction power dynamics stored as JSONB: {faction_id: {power, influence, territory, ...}, ...}
    faction_power = Column(JSONB, nullable=False, default={})
    
    # Global events: [{event_id, type, description, impact, timestamp}, ...]
    global_events = Column(JSONB, nullable=False, default=[])
    
    # Economic state: {resource_prices, supply_demand, market_trends, ...}
    economic_state = Column(JSONB, nullable=False, default={})
    
    # NPC population counts: {npc_type: count, ...}
    npc_population = Column(JSONB, nullable=False, default={})
    
    # Territory control: {territory_id: {faction_id, control_level, ...}, ...}
    territory_control = Column(JSONB, nullable=False, default={})
    
    # Additional simulation data
    simulation_data = Column(JSONB, nullable=False, default={})
    
    # Optimistic locking
    version = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert world state to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "world_time": self.world_time.isoformat() if self.world_time else None,
            "day_phase": self.day_phase,
            "weather": self.weather,
            "faction_power": self.faction_power,
            "global_events": self.global_events,
            "economic_state": self.economic_state,
            "npc_population": self.npc_population,
            "territory_control": self.territory_control,
            "simulation_data": self.simulation_data,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert world state to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<WorldState(id={self.id}, world_time={self.world_time}, day_phase={self.day_phase}, version={self.version})>"

