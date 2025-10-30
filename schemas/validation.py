"""
Pydantic validation schemas for The Body Broker models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


# ============================================================================
# PLAYER SCHEMAS
# ============================================================================

class PlayerBase(BaseModel):
    """Base player schema."""
    steam_id: str = Field(..., min_length=1, max_length=64)
    username: str = Field(..., min_length=1, max_length=100)
    tier: str = Field(default="free", pattern="^(free|premium|whale)$")
    stats: Dict[str, Any] = Field(default_factory=dict)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)
    money: float = Field(default=0.0, ge=0.0)
    reputation: int = Field(default=0)
    level: int = Field(default=1, ge=1)
    xp: float = Field(default=0.0, ge=0.0)


class PlayerCreate(PlayerBase):
    """Schema for creating a new player."""
    pass


class PlayerUpdate(BaseModel):
    """Schema for updating a player (all fields optional)."""
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    tier: Optional[str] = Field(None, pattern="^(free|premium|whale)$")
    stats: Optional[Dict[str, Any]] = None
    inventory: Optional[List[Dict[str, Any]]] = None
    money: Optional[float] = Field(None, ge=0.0)
    reputation: Optional[int] = None
    level: Optional[int] = Field(None, ge=1)
    xp: Optional[float] = Field(None, ge=0.0)


class PlayerResponse(PlayerBase):
    """Schema for player response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# GAME STATE SCHEMAS
# ============================================================================

class GameStateBase(BaseModel):
    """Base game state schema."""
    current_world: str = Field(default="day", pattern="^(day|night)$")
    location: Optional[str] = Field(None, max_length=100)
    position: Optional[Dict[str, float]] = None
    active_quests: List[str] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)


class GameStateCreate(GameStateBase):
    """Schema for creating a new game state."""
    player_id: UUID


class GameStateUpdate(BaseModel):
    """Schema for updating a game state."""
    current_world: Optional[str] = Field(None, pattern="^(day|night)$")
    location: Optional[str] = Field(None, max_length=100)
    position: Optional[Dict[str, float]] = None
    active_quests: Optional[List[str]] = None
    session_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class GameStateResponse(GameStateBase):
    """Schema for game state response."""
    id: UUID
    player_id: UUID
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STORY NODE SCHEMAS
# ============================================================================

class StoryNodeBase(BaseModel):
    """Base story node schema."""
    node_type: str = Field(..., pattern="^(quest|event|dialogue|choice)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    narrative_content: Optional[str] = None
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = Field(default="active", pattern="^(active|completed|failed|locked)$")
    prerequisites: List[Dict[str, Any]] = Field(default_factory=list)
    consequences: Dict[str, Any] = Field(default_factory=dict)
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class StoryNodeCreate(StoryNodeBase):
    """Schema for creating a new story node."""
    player_id: UUID


class StoryNodeUpdate(BaseModel):
    """Schema for updating a story node."""
    node_type: Optional[str] = Field(None, pattern="^(quest|event|dialogue|choice)$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    narrative_content: Optional[str] = None
    choices: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|failed|locked)$")
    prerequisites: Optional[List[Dict[str, Any]]] = None
    consequences: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


class StoryNodeResponse(StoryNodeBase):
    """Schema for story node response."""
    id: UUID
    player_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema."""
    transaction_type: str = Field(..., pattern="^(payment|purchase|refund|exchange)$")
    stripe_payment_intent_id: Optional[str] = Field(None, max_length=255)
    amount: float = Field(..., ge=0.0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    status: str = Field(default="pending", pattern="^(pending|completed|failed|refunded)$")
    description: Optional[str] = Field(None, max_length=500)
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    player_id: UUID


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    transaction_type: Optional[str] = Field(None, pattern="^(payment|purchase|refund|exchange)$")
    stripe_payment_intent_id: Optional[str] = Field(None, max_length=255)
    amount: Optional[float] = Field(None, ge=0.0)
    currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$")
    status: Optional[str] = Field(None, pattern="^(pending|completed|failed|refunded)$")
    description: Optional[str] = Field(None, max_length=500)
    meta_data: Optional[Dict[str, Any]] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    player_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# WORLD STATE SCHEMAS
# ============================================================================

class WorldStateBase(BaseModel):
    """Base world state schema."""
    world_time: Optional[datetime] = None
    day_phase: str = Field(default="day", pattern="^(morning|afternoon|evening|night|day)$")
    weather: Optional[str] = Field(None, max_length=50)
    faction_power: Dict[str, Any] = Field(default_factory=dict)
    global_events: List[Dict[str, Any]] = Field(default_factory=list)
    economic_state: Dict[str, Any] = Field(default_factory=dict)
    npc_population: Dict[str, int] = Field(default_factory=dict)
    territory_control: Dict[str, Any] = Field(default_factory=dict)
    simulation_data: Dict[str, Any] = Field(default_factory=dict)


class WorldStateCreate(WorldStateBase):
    """Schema for creating a new world state."""
    pass


class WorldStateUpdate(BaseModel):
    """Schema for updating a world state."""
    world_time: Optional[datetime] = None
    day_phase: Optional[str] = Field(None, pattern="^(morning|afternoon|evening|night|day)$")
    weather: Optional[str] = Field(None, max_length=50)
    faction_power: Optional[Dict[str, Any]] = None
    global_events: Optional[List[Dict[str, Any]]] = None
    economic_state: Optional[Dict[str, Any]] = None
    npc_population: Optional[Dict[str, int]] = None
    territory_control: Optional[Dict[str, Any]] = None
    simulation_data: Optional[Dict[str, Any]] = None


class WorldStateResponse(WorldStateBase):
    """Schema for world state response."""
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NPC SCHEMAS
# ============================================================================

class NPCBase(BaseModel):
    """Base NPC schema."""
    name: str = Field(..., min_length=1, max_length=100)
    npc_type: str = Field(..., pattern="^(human|vampire|werewolf|zombie|ghoul|lich)$")
    personality_vector: List[float] = Field(..., min_items=50, max_items=50)
    stats: Dict[str, Any] = Field(default_factory=dict)
    goal_stack: List[Dict[str, Any]] = Field(default_factory=list)
    current_location: Optional[str] = Field(None, max_length=100)
    current_state: str = Field(default="idle", pattern="^(idle|hunting|talking|combat|moving|dead)$")
    relationships: Dict[str, Any] = Field(default_factory=dict)
    episodic_memory_id: Optional[str] = Field(None, max_length=255)
    meta_data: Dict[str, Any] = Field(default_factory=dict)

    @validator('personality_vector')
    def validate_personality_vector(cls, v):
        """Validate personality vector is exactly 50 dimensions."""
        if len(v) != 50:
            raise ValueError('personality_vector must have exactly 50 dimensions')
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('personality_vector must contain only numbers')
        return v


class NPCCreate(NPCBase):
    """Schema for creating a new NPC."""
    world_state_id: UUID
    faction_id: Optional[UUID] = None


class NPCUpdate(BaseModel):
    """Schema for updating an NPC."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    npc_type: Optional[str] = Field(None, pattern="^(human|vampire|werewolf|zombie|ghoul|lich)$")
    personality_vector: Optional[List[float]] = Field(None, min_items=50, max_items=50)
    stats: Optional[Dict[str, Any]] = None
    goal_stack: Optional[List[Dict[str, Any]]] = None
    current_location: Optional[str] = Field(None, max_length=100)
    current_state: Optional[str] = Field(None, pattern="^(idle|hunting|talking|combat|moving|dead)$")
    relationships: Optional[Dict[str, Any]] = None
    episodic_memory_id: Optional[str] = Field(None, max_length=255)
    meta_data: Optional[Dict[str, Any]] = None
    faction_id: Optional[UUID] = None


class NPCResponse(NPCBase):
    """Schema for NPC response."""
    id: UUID
    world_state_id: UUID
    faction_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# FACTION SCHEMAS
# ============================================================================

class FactionBase(BaseModel):
    """Base faction schema."""
    name: str = Field(..., min_length=1, max_length=100)
    faction_type: str = Field(..., pattern="^(vampire_house|werewolf_pack|human_org|zombie_horde|ghoul_collective|lich_coven)$")
    description: Optional[str] = None
    power_level: int = Field(default=50, ge=0, le=100)
    territory: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: Dict[str, Any] = Field(default_factory=dict)
    hierarchy: Dict[str, Any] = Field(default_factory=dict)
    goals: List[Dict[str, Any]] = Field(default_factory=list)
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class FactionCreate(FactionBase):
    """Schema for creating a new faction."""
    pass


class FactionUpdate(BaseModel):
    """Schema for updating a faction."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    faction_type: Optional[str] = Field(None, pattern="^(vampire_house|werewolf_pack|human_org|zombie_horde|ghoul_collective|lich_coven)$")
    description: Optional[str] = None
    power_level: Optional[int] = Field(None, ge=0, le=100)
    territory: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[Dict[str, Any]] = None
    hierarchy: Optional[Dict[str, Any]] = None
    goals: Optional[List[Dict[str, Any]]] = None
    meta_data: Optional[Dict[str, Any]] = None


class FactionResponse(FactionBase):
    """Schema for faction response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# AUGMENTATION SCHEMAS
# ============================================================================

class AugmentationBase(BaseModel):
    """Base augmentation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(power|modification|upgrade)$")
    cost: float = Field(default=0.0, ge=0.0)
    stats_modifier: Dict[str, Any] = Field(default_factory=dict)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class AugmentationCreate(AugmentationBase):
    """Schema for creating a new augmentation."""
    pass


class AugmentationUpdate(BaseModel):
    """Schema for updating an augmentation."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(power|modification|upgrade)$")
    cost: Optional[float] = Field(None, ge=0.0)
    stats_modifier: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None


class AugmentationResponse(AugmentationBase):
    """Schema for augmentation response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

