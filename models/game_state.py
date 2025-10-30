"""
Game State Model
Represents an active game session state.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class GameState(Base):
    """
    Active game session state model.
    
    Tracks the current state of a player's active game session including:
    - Current world (Day/Night)
    - Location coordinates
    - Active quests/missions
    - Session-specific data
    
    Attributes:
        id: Unique game state identifier
        player_id: Foreign key to players table
        current_world: "day" or "night"
        location: Current location identifier
        position: 3D coordinates {x, y, z}
        active_quests: List of active quest IDs
        session_data: Additional session-specific data as JSONB
        is_active: Whether this session is currently active
        version: Optimistic locking version number
        created_at: Session creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "game_states"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    player_id = Column(PGUUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # World state
    current_world = Column(String(20), nullable=False, default="day")  # day/night
    location = Column(String(100), nullable=True)
    
    # Position in world (3D coordinates)
    position = Column(JSONB, nullable=True)  # {x, y, z}
    
    # Active quests/missions
    active_quests = Column(JSONB, nullable=False, default=[])  # [quest_id, ...]
    
    # Session-specific data stored as JSONB
    session_data = Column(JSONB, nullable=False, default={})
    
    # Session status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Optimistic locking
    version = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="game_states")
    
    def to_dict(self) -> Dict:
        """Convert game state to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "player_id": str(self.player_id),
            "current_world": self.current_world,
            "location": self.location,
            "position": self.position,
            "active_quests": self.active_quests,
            "session_data": self.session_data,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert game state to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<GameState(id={self.id}, player_id={self.player_id}, world={self.current_world}, active={self.is_active})>"

