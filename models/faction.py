"""
Faction Model
Represents faction relationships and power dynamics.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Faction(Base):
    """
    Faction relationships and power dynamics model.
    
    Tracks monster houses, human organizations, and their relationships:
    - Power levels and influence
    - Territory control
    - Relationships with other factions (allies, enemies, neutral)
    - Membership and hierarchy
    
    Attributes:
        id: Unique faction identifier
        name: Faction name
        faction_type: Type of faction (vampire_house, werewolf_pack, human_org, etc.)
        description: Faction description
        power_level: Current power/influence level (0-100)
        territory: Controlled territories as JSONB
        relationships: Relationships with other factions
        hierarchy: Internal faction hierarchy
        goals: Faction goals and objectives
        meta_data: Additional faction meta_data as JSONB
        created_at: Faction creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "factions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Faction identity
    name = Column(String(100), nullable=False, unique=True)
    faction_type = Column(String(50), nullable=False)  # vampire_house, werewolf_pack, human_org, zombie_horde, etc.
    description = Column(Text, nullable=True)
    
    # Power dynamics
    power_level = Column(Integer, nullable=False, default=50)  # 0-100 scale
    
    # Territory: [{territory_id, control_level, influence}, ...]
    territory = Column(JSONB, nullable=False, default=[])
    
    # Relationships with other factions: {faction_id: {relationship_type, strength, history}, ...}
    # relationship_type: "ally", "enemy", "neutral", "rival", "subordinate", "overlord"
    relationships = Column(JSONB, nullable=False, default={})
    
    # Internal hierarchy: {role: {member_id, power_level}, ...}
    hierarchy = Column(JSONB, nullable=False, default={})
    
    # Goals: [{goal_id, priority, progress}, ...]
    goals = Column(JSONB, nullable=False, default=[])
    
    # Additional meta_data
    meta_data = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    npcs = relationship("NPC", back_populates="faction")
    
    def to_dict(self) -> Dict:
        """Convert faction to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "faction_type": self.faction_type,
            "description": self.description,
            "power_level": self.power_level,
            "territory": self.territory,
            "relationships": self.relationships,
            "hierarchy": self.hierarchy,
            "goals": self.goals,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert faction to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<Faction(id={self.id}, name={self.name}, type={self.faction_type}, power={self.power_level})>"

