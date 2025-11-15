"""
Engagement & Addiction Analytics schemas and data models.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

# Enums (R-EMO-DATA-002)
class ActorType(str, Enum):
    REAL_PLAYER = "real_player"
    AI_PLAYER = "ai_player"

class EventType(str, Enum):
    NPC_INTERACTION = "npc_interaction"
    MORAL_CHOICE = "moral_choice"
    SESSION_METRICS = "session_metrics"
    AI_RUN = "ai_run"

class InteractionType(str, Enum):
    DIALOGUE = "dialogue"
    GIFT = "gift"
    ASSIST = "assist"
    HARM = "harm"
    IGNORE = "ignore"

class HelpHarmFlag(str, Enum):
    HELPFUL = "helpful"
    HARMFUL = "harmful"
    NEUTRAL = "neutral"

class TimeOfDayBucket(str, Enum):
    EARLY_MORNING = "early_morning"  # 00:00 - 06:00
    MORNING = "morning"              # 06:00 - 12:00
    AFTERNOON = "afternoon"          # 12:00 - 18:00
    EVENING = "evening"              # 18:00 - 22:00
    LATE_NIGHT = "late_night"        # 22:00 - 00:00

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AggregateType(str, Enum):
    NPC_ATTACHMENT = "npc_attachment"
    MORAL_TENSION = "moral_tension"
    ENGAGEMENT_PROFILE = "engagement_profile"

# Base event model
class EngagementEventBase(BaseModel):
    """Base model for all engagement events (R-EMO-DATA-001)."""
    session_id: UUID
    player_id: Optional[UUID] = None  # Pseudonymized
    actor_type: ActorType
    event_type: EventType
    timestamp: datetime
    build_id: str
    environment: Optional[str] = None

# NPC Interaction Event (R-EMO-DATA-001)
class NPCInteractionEvent(EngagementEventBase):
    """Tracks player-NPC interactions."""
    event_type: EventType = EventType.NPC_INTERACTION
    npc_id: str
    interaction_type: InteractionType
    choice_id: Optional[str] = None
    choice_label: Optional[str] = None
    help_harm_flag: HelpHarmFlag = HelpHarmFlag.NEUTRAL
    location_id: Optional[str] = None
    arc_id: Optional[str] = None
    experience_id: Optional[str] = None

# Moral Choice Event (R-EMO-DATA-002)
class MoralChoiceOption(BaseModel):
    """An available choice in a moral decision."""
    option_id: str
    option_label: str
    tags: List[str] = Field(default_factory=list)  # e.g., ["evil", "selfish", "pragmatic"]

class MoralChoiceEvent(EngagementEventBase):
    """Tracks moral decision points."""
    event_type: EventType = EventType.MORAL_CHOICE
    scene_id: str
    options: List[MoralChoiceOption]
    selected_option_id: str
    decision_latency_ms: int = Field(..., ge=0)
    num_retries: int = Field(default=0, ge=0)
    reloaded_save: bool = False
    arc_id: Optional[str] = None
    experience_id: Optional[str] = None

    @field_validator('options', mode='after')
    def validate_options(cls, v):
        if len(v) < 2:
            raise ValueError("Moral choices must have at least 2 options")
        return v

# Session Metrics Event (R-EMO-DATA-003)
class SessionMetricsEvent(EngagementEventBase):
    """Tracks session-level engagement patterns."""
    event_type: EventType = EventType.SESSION_METRICS
    session_start: datetime
    session_end: datetime
    total_duration_minutes: int = Field(..., ge=0)
    time_of_day_bucket: TimeOfDayBucket
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Sunday
    num_sessions_last_7_days: int = Field(..., ge=0)
    num_sessions_last_24_hours: int = Field(..., ge=0)
    is_return_session: bool = False
    time_since_last_session_seconds: Optional[int] = Field(None, ge=0)
    platform: Optional[str] = None
    region: Optional[str] = None

    @field_validator('total_duration_minutes', mode='after')
    def validate_duration(cls, v, values):
        """Ensure duration matches start/end times."""
        if 'session_start' in values.data and 'session_end' in values.data:
            actual_duration = int((values.data['session_end'] - values.data['session_start']).total_seconds() / 60)
            if abs(v - actual_duration) > 1:  # Allow 1 minute tolerance
                raise ValueError(f"Duration {v} doesn't match start/end times (actual: {actual_duration})")
        return v

# AI Player Run Event
class AIRunEvent(EngagementEventBase):
    """Tracks AI player simulation runs."""
    event_type: EventType = EventType.AI_RUN
    ai_run_id: str
    personality_profile: str
    total_npcs_interacted: int = Field(..., ge=0)
    moral_choices_made: int = Field(..., ge=0)
    help_harm_ratio: float = Field(..., ge=0.0, le=1.0)
    exploration_coverage: float = Field(..., ge=0.0, le=1.0)
    run_start: datetime
    run_end: datetime
    total_duration_hours: int = Field(..., ge=0)
    scenario_id: Optional[str] = None

# Aggregate models (R-EMO-MET-001, R-EMO-MET-002, R-EMO-MET-003)
class NPCAttachmentMetrics(BaseModel):
    """NPC attachment strength indicators."""
    npc_id: str
    protection_harm_ratio: float = Field(..., ge=0.0)
    attention_score: float = Field(..., ge=0.0, le=1.0)
    abandonment_frequency: float = Field(..., ge=0.0, le=1.0)
    total_interactions: int = Field(..., ge=0)
    helpful_actions: int = Field(..., ge=0)
    harmful_actions: int = Field(..., ge=0)
    neutral_actions: int = Field(..., ge=0)
    total_proximity_time_seconds: int = Field(..., ge=0)

class MoralTensionMetrics(BaseModel):
    """Moral decision tension indicators."""
    scene_id: str
    tension_index: float = Field(..., ge=0.0, le=1.0)
    choice_distribution_entropy: float = Field(..., ge=0.0)
    avg_decision_latency_seconds: float = Field(..., ge=0.0)
    total_choices: int = Field(..., ge=0)
    reload_count: int = Field(..., ge=0)
    option_counts: Dict[str, int] = Field(default_factory=dict)

class EngagementProfile(BaseModel):
    """Player engagement archetype classification."""
    profile_id: str
    profile_name: str  # e.g., "lore-driven explorer"
    profile_confidence: float = Field(..., ge=0.0, le=1.0)
    characteristic_behaviors: List[str] = Field(default_factory=list)

class EngagementAggregate(BaseModel):
    """Aggregated engagement metrics."""
    aggregate_type: AggregateType
    cohort_id: Optional[str] = None
    build_id: str
    period_start: datetime
    period_end: datetime
    
    # Type-specific metrics
    npc_attachment: Optional[NPCAttachmentMetrics] = None
    moral_tension: Optional[MoralTensionMetrics] = None
    engagement_profile: Optional[EngagementProfile] = None
    
    # Additional computed metrics
    metrics: Dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime = Field(default_factory=datetime.utcnow)

# Addiction risk models (R-EMO-ADD-001, R-EMO-ADD-003)
class AddictionRiskIndicators(BaseModel):
    """Behavioral indicators of potential addiction risk."""
    avg_daily_session_hours: float = Field(..., ge=0.0)
    night_time_play_fraction: float = Field(..., ge=0.0, le=1.0)
    rapid_session_return_rate: float = Field(..., ge=0.0, le=1.0)
    weekend_spike_ratio: float = Field(..., ge=0.0)
    high_risk_patterns: List[str] = Field(default_factory=list)
    associated_systems: List[str] = Field(default_factory=list)

class AddictionRiskReport(BaseModel):
    """Cohort-level addiction risk assessment (R-EMO-ADD-002: No individual data)."""
    cohort_id: str
    region: Optional[str] = None
    age_band: Optional[str] = None  # e.g., "18-25"
    platform: Optional[str] = None
    cohort_size: int = Field(..., gt=0)
    report_period: str  # e.g., "2025-11-14/P7D"
    
    risk_indicators: AddictionRiskIndicators
    overall_risk_level: RiskLevel
    risk_summary: str
    recommendations: List[str] = Field(default_factory=list)
    
    build_id: str
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_percentage: int = Field(..., ge=0, le=100)
    notes: Optional[str] = None

    @field_validator('cohort_size', mode='after')
    def validate_cohort_size(cls, v):
        """Ensure cohort is large enough for privacy."""
        if v < 100:  # R-EMO-ADD-002: Minimum cohort size for privacy
            raise ValueError(f"Cohort size {v} is too small for privacy protection (min: 100)")
        return v

# Cohort definition for analytics
class CohortDefinition(BaseModel):
    """Defines a player cohort for aggregate analytics."""
    cohort_id: str
    region: Optional[str] = None
    age_band: Optional[str] = None
    platform: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Generate human-readable cohort name."""
        parts = []
        if self.region:
            parts.append(self.region)
        if self.age_band:
            parts.append(self.age_band)
        if self.platform:
            parts.append(self.platform)
        return "-".join(parts) if parts else "global"

# Event request/response models for API
class RecordEngagementEventRequest(BaseModel):
    """Request to record an engagement event."""
    event: Union[NPCInteractionEvent, MoralChoiceEvent, SessionMetricsEvent, AIRunEvent]

class GetEngagementMetricsRequest(BaseModel):
    """Request to retrieve engagement metrics."""
    cohort_id: Optional[str] = None
    metric_type: Optional[str] = None  # "npc_attachment", "moral_tension", etc.
    build_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class EngagementMetricsResponse(BaseModel):
    """Response containing engagement metrics."""
    aggregates: List[EngagementAggregate]
    total_count: int
    query_time_ms: int
