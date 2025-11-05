"""
Event Bus Service - Central event system for inter-service communication.
Provides pub/sub pattern for loose coupling between systems.
"""

from .event_bus import GameEventBus, GameEvent, EventType

__all__ = ["GameEventBus", "GameEvent", "EventType"]




