"""
World State Service - Dynamic world state management.

This service handles:
- Real-time world state tracking and updates
- Global event generation and processing
- Faction power and territory control
- Economic state and market dynamics
"""

from world_state_manager import WorldStateManager
from event_system import EventSystem
from faction_manager import FactionManager
from economic_manager import EconomicManager

__all__ = [
    "WorldStateManager",
    "EventSystem",
    "FactionManager",
    "EconomicManager",
]
