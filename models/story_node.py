"""
Story Node Model
Represents story progression and narrative state.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class StoryNode(Base):
    """
    Story progression and narrative state model.
    
    Tracks the player's progression through narrative arcs, quest chains,
    and story beats. Supports branching narratives and player choices.
    
    Attributes:
        id: Unique story node identifier
        player_id: Foreign key to players table
        node_type: Type of story node (quest, event, dialogue, etc.)
        title: Story node title/name
        description: Detailed description of the story node
        narrative_content: AI-generated narrative content
        choices: Available choices/paths from this node
        status: Current status (active, completed, failed, locked)
        prerequisites: Required story nodes/conditions
        consequences: Effects of completing this node
        meta_data: Additional story meta_data as JSONB
        created_at: Node creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "story_nodes"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    player_id = Column(PGUUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Story node details
    node_type = Column(String(50), nullable=False)  # quest, event, dialogue, choice
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Narrative content (AI-generated)
    narrative_content = Column(Text, nullable=True)
    
    # Branching narrative
    choices = Column(JSONB, nullable=False, default=[])  # [{choice_id, text, leads_to}, ...]
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # active, completed, failed, locked
    
    # Prerequisites for unlocking this node
    prerequisites = Column(JSONB, nullable=False, default=[])  # [node_id, condition, ...]
    
    # Consequences of completing this node
    consequences = Column(JSONB, nullable=False, default={})  # {stat_changes, unlocks, triggers, ...}
    
    # Additional meta_data
    meta_data = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="story_nodes")
    
    def to_dict(self) -> Dict:
        """Convert story node to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "player_id": str(self.player_id),
            "node_type": self.node_type,
            "title": self.title,
            "description": self.description,
            "narrative_content": self.narrative_content,
            "choices": self.choices,
            "status": self.status,
            "prerequisites": self.prerequisites,
            "consequences": self.consequences,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert story node to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<StoryNode(id={self.id}, player_id={self.player_id}, type={self.node_type}, status={self.status})>"

