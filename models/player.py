"""
Player Model
Represents a player entity with stats, inventory, and augmentations.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .association import player_augmentations
from .base import Base


class Player(Base):
    """
    Player entity with stats, inventory, augmentations, and progression.
    
    Attributes:
        id: Unique player identifier (UUID)
        steam_id: Steam user ID (for authentication)
        username: Player's display name
        tier: Subscription tier (free/premium/whale)
        stats: Player statistics (health, strength, etc.) stored as JSONB
        inventory: Player inventory items stored as JSONB
        money: In-game currency balance
        reputation: Player reputation score
        level: Player progression level
        xp: Experience points
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "players"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    steam_id = Column(String(64), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    tier = Column(String(20), nullable=False, default="free")  # free/premium/whale
    
    # Stats stored as JSONB: {health: 100, strength: 50, speed: 30, ...}
    stats = Column(JSONB, nullable=False, default={})
    
    # Inventory stored as JSONB: [{item_id, quantity, slot}, ...]
    inventory = Column(JSONB, nullable=False, default=[])
    
    # Economy
    money = Column(Numeric(12, 2), nullable=False, default=0.0)
    reputation = Column(Integer, nullable=False, default=0)
    
    # Progression
    level = Column(Integer, nullable=False, default=1)
    xp = Column(Numeric(12, 2), nullable=False, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    game_states = relationship("GameState", back_populates="player", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="player", cascade="all, delete-orphan")
    story_nodes = relationship("StoryNode", back_populates="player", cascade="all, delete-orphan")
    augmentations = relationship("Augmentation", secondary="player_augmentations", back_populates="players")
    
    def to_dict(self) -> Dict:
        """Convert player to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "steam_id": self.steam_id,
            "username": self.username,
            "tier": self.tier,
            "stats": self.stats,
            "inventory": self.inventory,
            "money": float(self.money),
            "reputation": self.reputation,
            "level": self.level,
            "xp": float(self.xp),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert player to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<Player(id={self.id}, username={self.username}, tier={self.tier}, level={self.level})>"

