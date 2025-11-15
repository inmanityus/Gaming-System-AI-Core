"""
Story Memory schemas and data models.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ArcRole(str, Enum):
    """Story arc classification."""
    MAIN_ARC = "main_arc"
    SIDE_ARC = "side_arc"
    EXPERIENCE = "experience"
    AMBIENT = "ambient"


class ProgressState(str, Enum):
    """Arc progress states."""
    NOT_STARTED = "not_started"
    EARLY = "early"
    MID = "mid"
    LATE = "late"
    COMPLETED = "completed"


class DriftType(str, Enum):
    """Types of narrative drift."""
    TIME_ALLOCATION = "time_allocation"
    QUEST_ALLOCATION = "quest_allocation"
    THEME_CONSISTENCY = "theme_consistency"


class DriftSeverity(str, Enum):
    """Severity levels for drift."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class ConflictSeverity(str, Enum):
    """Severity levels for story conflicts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DarkWorldFamily(str, Enum):
    """The 8 Dark World client families."""
    CARRION_KIN = "carrion_kin"
    CHATTER_SWARM = "chatter_swarm"
    STITCH_GUILD = "stitch_guild"
    MOON_CLANS = "moon_clans"
    VAMPIRIC_HOUSES = "vampiric_houses"
    OBSIDIAN_SYNOD = "obsidian_synod"
    SILENT_COURT = "silent_court"
    LEVIATHAN_CONCLAVE = "leviathan_conclave"


class ArcProgress(BaseModel):
    """Progress tracking for a story arc."""
    arc_id: str
    arc_role: ArcRole
    progress_state: ProgressState
    last_beat_id: Optional[str] = None
    last_update_at: datetime


class StoryDecision(BaseModel):
    """A key player decision and its consequences."""
    decision_id: str
    arc_id: Optional[str] = None
    npc_id: Optional[str] = None
    choice_label: str
    outcome_tags: List[str] = Field(default_factory=list)
    moral_weight: float = 0.0
    timestamp: datetime


class EntityRelationship(BaseModel):
    """Relationship state with an NPC or faction."""
    entity_id: str
    entity_type: str  # 'npc' or 'faction'
    relationship_score: float = Field(ge=-100.0, le=100.0)
    flags: List[str] = Field(default_factory=list)
    last_interaction: Optional[str] = None
    last_interaction_at: Optional[datetime] = None


class Experience(BaseModel):
    """A major life experience (love, parenthood, addiction, etc.)."""
    experience_id: str
    status: str  # 'active', 'completed', 'failed', 'abandoned'
    emotional_impact: Dict[str, float] = Field(default_factory=dict)
    cross_references: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None


class DarkWorldStanding(BaseModel):
    """Standing with a Dark World family."""
    family_name: DarkWorldFamily
    standing_score: float = Field(ge=-100.0, le=100.0)
    favors_owed: int = Field(ge=0)
    debts_owed: int = Field(ge=0)
    betrayal_count: int = Field(ge=0)
    special_status: List[str] = Field(default_factory=list)
    last_interaction: Optional[datetime] = None


class StorySnapshot(BaseModel):
    """Complete story state snapshot for a player."""
    player_id: UUID
    
    # Core state
    surgeon_butcher_score: float = Field(ge=-1.0, le=1.0)
    broker_book_state: Dict[str, Any] = Field(default_factory=dict)
    debt_of_flesh_state: Dict[str, Any] = Field(default_factory=dict)
    
    # Progress tracking
    arc_progress: List[ArcProgress] = Field(default_factory=list)
    recent_decisions: List[StoryDecision] = Field(default_factory=list)
    
    # Relationships
    relationships: List[EntityRelationship] = Field(default_factory=list)
    dark_world_standings: List[DarkWorldStanding] = Field(default_factory=list)
    
    # Experiences
    active_experiences: List[Experience] = Field(default_factory=list)
    completed_experiences: List[Experience] = Field(default_factory=list)
    
    # Metadata
    snapshot_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('recent_decisions', mode='after')
    def limit_recent_decisions(cls, v):
        """Keep only the 20 most recent decisions."""
        return sorted(v, key=lambda d: d.timestamp, reverse=True)[:20]


class DriftMetrics(BaseModel):
    """Metrics for narrative drift detection."""
    drift_type: DriftType
    severity: DriftSeverity
    drift_score: float = Field(ge=0.0, le=1.0)
    
    # Detailed breakdowns
    quest_allocation: Optional[Dict[str, float]] = None
    time_allocation: Optional[Dict[str, float]] = None
    theme_consistency: Optional[float] = None
    
    # Remediation
    recommended_correction: Optional[str] = None
    canonical_reminder: Optional[str] = None


class StoryConflict(BaseModel):
    """A detected narrative inconsistency."""
    conflict_type: str
    involved_entities: List[str]
    conflicting_facts: Dict[str, Any]
    severity: ConflictSeverity
    detected_at: datetime
    resolution_notes: Optional[str] = None


class StoryEvent(BaseModel):
    """Base class for story events."""
    event_type: str
    player_id: UUID
    session_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_data: Dict[str, Any] = Field(default_factory=dict)


class ArcBeatReachedEvent(StoryEvent):
    """Event when player reaches a story beat."""
    event_type: str = "arc_beat_reached"
    arc_id: str
    beat_id: str
    arc_role: ArcRole


class QuestCompletedEvent(StoryEvent):
    """Event when player completes a quest."""
    event_type: str = "quest_completed"
    quest_id: str
    arc_id: Optional[str] = None
    quest_type: str  # For drift analysis


class ExperienceCompletedEvent(StoryEvent):
    """Event when player completes an experience."""
    event_type: str = "experience_completed"
    experience_id: str
    emotional_impact: Dict[str, float]


class RelationshipChangedEvent(StoryEvent):
    """Event when relationship changes significantly."""
    event_type: str = "relationship_changed"
    entity_id: str
    entity_type: str
    old_score: float
    new_score: float
    reason: str
