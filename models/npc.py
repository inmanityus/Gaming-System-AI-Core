"""
NPC Model
Represents NPC entities with personality vectors.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class NPC(Base):
    """
    NPC entity with personality vectors and autonomous behavior.
    
    NPCs have:
    - 50-dimensional personality vector (stored as JSONB array)
    - Relationship graph with other NPCs and players
    - Goal stack for autonomous decision-making
    - Episodic memory (via vector DB reference)
    - Faction affiliation
    
    Attributes:
        id: Unique NPC identifier
        world_state_id: Foreign key to world_states table
        faction_id: Foreign key to factions table (optional)
        name: NPC name
        npc_type: Type of NPC (human, vampire, werewolf, zombie, ghoul, lich)
        personality_vector: 50-dimensional personality vector as JSONB array
        stats: NPC statistics (health, aggression, intelligence, charisma)
        goal_stack: Hierarchical goals for autonomous behavior
        current_location: Current location identifier
        current_state: Current NPC state (idle, hunting, talking, etc.)
        relationships: Relationship scores with other entities
        episodic_memory_id: Reference to vector DB memory entry
        meta_data: Additional NPC meta_data as JSONB
        created_at: NPC creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "npcs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    world_state_id = Column(PGUUID(as_uuid=True), ForeignKey("world_states.id"), nullable=False, index=True)
    faction_id = Column(PGUUID(as_uuid=True), ForeignKey("factions.id"), nullable=True, index=True)
    
    # NPC identity
    name = Column(String(100), nullable=False)
    npc_type = Column(String(50), nullable=False)  # human, vampire, werewolf, zombie, ghoul, lich
    
    # Personality vector (50-dimensional array stored as JSONB)
    # Enables similarity search and behavior prediction
    personality_vector = Column(JSONB, nullable=False)  # [0.5, 0.8, 0.2, ...] (50 values)
    
    # Stats stored as JSONB: {health: 100, aggression: 75, intelligence: 60, charisma: 80, ...}
    stats = Column(JSONB, nullable=False, default={})
    
    # Goal stack for autonomous behavior: [{goal_id, priority, status}, ...]
    goal_stack = Column(JSONB, nullable=False, default=[])
    
    # Location and state
    current_location = Column(String(100), nullable=True)
    current_state = Column(String(50), nullable=False, default="idle")  # idle, hunting, talking, combat, etc.
    
    # Relationships: {entity_id: {relationship_type, score, history}, ...}
    relationships = Column(JSONB, nullable=False, default={})
    
    # Vector DB reference for episodic memory
    episodic_memory_id = Column(String(255), nullable=True)  # Reference to Pinecone/Weaviate vector
    
    # Additional meta_data
    meta_data = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    faction = relationship("Faction", back_populates="npcs")
    
    def to_dict(self) -> Dict:
        """Convert NPC to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "world_state_id": str(self.world_state_id),
            "faction_id": str(self.faction_id) if self.faction_id else None,
            "name": self.name,
            "npc_type": self.npc_type,
            "personality_vector": self.personality_vector,
            "stats": self.stats,
            "goal_stack": self.goal_stack,
            "current_location": self.current_location,
            "current_state": self.current_state,
            "relationships": self.relationships,
            "episodic_memory_id": self.episodic_memory_id,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert NPC to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<NPC(id={self.id}, name={self.name}, type={self.npc_type}, faction_id={self.faction_id})>"

