"""
Augmentation Model
Represents body modification catalog.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .association import player_augmentations
from .base import Base


class Augmentation(Base):
    """
    Body modification catalog model.
    
    Represents available body augmentations that players can acquire:
    - Supernatural powers (invisibility, super strength, speed)
    - Body modifications
    - Enhancement upgrades
    
    Attributes:
        id: Unique augmentation identifier
        name: Augmentation name
        description: Detailed description
        category: Augmentation category (power, modification, upgrade)
        cost: Purchase cost (in-game currency)
        stats_modifier: Stat changes applied by this augmentation
        requirements: Prerequisites to unlock this augmentation
        meta_data: Additional augmentation meta_data as JSONB
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "augmentations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Augmentation details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # power, modification, upgrade
    
    # Cost
    cost = Column(Numeric(12, 2), nullable=False, default=0.0)
    
    # Stat modifiers: {stat_name: modifier_value, ...}
    # e.g., {"strength": +20, "speed": +15, "invisibility": True}
    stats_modifier = Column(JSONB, nullable=False, default={})
    
    # Requirements: {level_required, quest_unlock, faction_reputation, ...}
    requirements = Column(JSONB, nullable=False, default={})
    
    # Additional meta_data
    meta_data = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (many-to-many with Player)
    players = relationship("Player", secondary="player_augmentations", back_populates="augmentations")
    
    def to_dict(self) -> Dict:
        """Convert augmentation to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "cost": float(self.cost),
            "stats_modifier": self.stats_modifier,
            "requirements": self.requirements,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert augmentation to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<Augmentation(id={self.id}, name={self.name}, category={self.category}, cost={self.cost})>"

