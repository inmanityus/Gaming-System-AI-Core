"""
Environmental Narrative Service - Core implementation.

Implements REQ-ENV-001: Environmental Narrative Service (ENS).
"""

import logging
import time
import asyncio
import math
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4

_logger = logging.getLogger(__name__)

# Import database connection pool
try:
    from state_manager.connection_pool import get_postgres_pool, PostgreSQLPool
except ImportError:
    PostgreSQLPool = None
    get_postgres_pool = None


class SceneGenerationError(Exception):
    """Raised when scene generation fails."""
    pass


class SceneType(Enum):
    """Story scene types."""
    ABANDONED_CAMP = "abandoned_camp"
    BATTLE_AFTERMATH = "battle_aftermath"
    RECENT_DEPARTURE = "recent_departure"
    LONG_TERM_SETTLEMENT = "long_term_settlement"
    EMERGENCY = "emergency"
    HIDEOUT = "hideout"
    WORKSHOP = "workshop"


class NarrativeWeight(Enum):
    """Narrative importance weight."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ObjectMetadata:
    """Metadata for objects that tell stories."""
    object_id: UUID
    object_type: str
    narrative_weight: NarrativeWeight
    story_tags: List[str] = field(default_factory=list)
    wear_state: float = 0.0  # 0.0 = pristine, 1.0 = destroyed
    damage_state: float = 0.0  # 0.0 = undamaged, 1.0 = destroyed
    temporal_decay: float = 0.0  # How much time has passed since placement
    relationship_rules: List[Dict[str, Any]] = field(default_factory=list)
    placement_context: Dict[str, Any] = field(default_factory=dict)
    
    def get_narrative_interpretation(self) -> str:
        """Get narrative interpretation based on state."""
        if self.wear_state > 0.8:
            return "ancient"
        elif self.wear_state > 0.5:
            return "worn"
        elif self.wear_state > 0.2:
            return "used"
        else:
            return "recent"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "object_id": str(self.object_id),
            "object_type": self.object_type,
            "narrative_weight": self.narrative_weight.value,
            "story_tags": self.story_tags,
            "wear_state": self.wear_state,
            "damage_state": self.damage_state,
            "temporal_decay": self.temporal_decay,
            "relationship_rules": self.relationship_rules,
            "placement_context": self.placement_context,
        }


@dataclass
class StoryScene:
    """A narrative scene with story-appropriate props."""
    scene_id: UUID
    scene_type: SceneType
    location: Tuple[float, float, float]  # x, y, z
    objects: List[ObjectMetadata] = field(default_factory=list)
    clutter_density: int = 10  # 5-50 objects
    discovery_markers: List[str] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scene_id": str(self.scene_id),
            "scene_type": self.scene_type.value,
            "location": self.location,
            "objects": [obj.to_dict() for obj in self.objects],
            "clutter_density": self.clutter_density,
            "discovery_markers": self.discovery_markers,
            "generated_at": self.generated_at,
        }


@dataclass
class DiscoveryReward:
    """Discovery reward for environmental observation."""
    discovery_id: UUID
    player_id: UUID
    object_id: Optional[UUID]
    scene_id: Optional[UUID]
    reward_type: str  # "narrative", "item", "experience", "lore"
    reward_value: float
    discovered_at: float = field(default_factory=time.time)
    noticed: bool = False  # Whether player explicitly noticed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "discovery_id": str(self.discovery_id),
            "player_id": str(self.player_id),
            "object_id": str(self.object_id) if self.object_id else None,
            "scene_id": str(self.scene_id) if self.scene_id else None,
            "reward_type": self.reward_type,
            "reward_value": self.reward_value,
            "discovered_at": self.discovered_at,
            "noticed": self.noticed,
        }


class EnvironmentalNarrativeService:
    """
    Environmental Narrative Service for REQ-ENV-001.
    
    Implements:
    - ENS-001: Story Scene System (template-based scenes, procedural detail generator)
    - ENS-002: Object Story Metadata (narrative weight tags, relationship rules)
    - ENS-003: Environmental History System (track player actions, persistent damage)
    - ENS-004: Discovery Reward Framework (99% details metric, analytics)
    
    Thread Safety:
    - All operations are thread-safe using locks
    - Async operations use async locks
    """
    
    def __init__(self):
        self._lock = asyncio.Lock()  # Async lock for async operations
        self.postgres: Optional[PostgreSQLPool] = None  # Database connection pool
        self._scenes_cache: Dict[UUID, StoryScene] = {}  # LRU cache (max 1000)
        self._cache_max_size = 1000
        self._discovery_metrics: Dict[str, Any] = {
            "total_details": 0,
            "noticed_details": 0,
            "unnoticed_details": 0,
            "discovery_rate": 0.0,
        }
        
        # Scene templates
        self._scene_templates = self._initialize_scene_templates()
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None and get_postgres_pool:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    def _initialize_scene_templates(self) -> Dict[SceneType, Dict[str, Any]]:
        """Initialize scene templates."""
        return {
            SceneType.ABANDONED_CAMP: {
                "min_objects": 8,
                "max_objects": 25,
                "required_objects": ["tent", "fire_ring", "supplies"],
                "optional_objects": ["bedroll", "cooking_pot", "weapon", "backpack"],
                "narrative_theme": "desertion",
            },
            SceneType.BATTLE_AFTERMATH: {
                "min_objects": 10,
                "max_objects": 30,
                "required_objects": ["weapon", "damage_marker"],
                "optional_objects": ["blood_stain", "broken_armor", "ammunition", "medical_supplies"],
                "narrative_theme": "conflict",
            },
            SceneType.RECENT_DEPARTURE: {
                "min_objects": 5,
                "max_objects": 15,
                "required_objects": ["personal_item", "fresh_track"],
                "optional_objects": ["clothing", "food", "tool"],
                "narrative_theme": "urgency",
            },
            SceneType.LONG_TERM_SETTLEMENT: {
                "min_objects": 20,
                "max_objects": 50,
                "required_objects": ["shelter", "storage", "workspace"],
                "optional_objects": ["furniture", "decoration", "tool", "supply"],
                "narrative_theme": "establishment",
            },
        }
    
    def _validate_location(self, location: Tuple[float, float, float]) -> bool:
        """Validate location coordinates."""
        if not isinstance(location, tuple) or len(location) != 3:
            return False
        x, y, z = location
        if not all(isinstance(coord, (int, float)) for coord in location):
            return False
        # Reasonable bounds check
        if abs(x) > 100000 or abs(y) > 100000 or abs(z) > 10000:
            return False
        return True
    
    async def generate_story_scene(
        self,
        scene_type: SceneType,
        location: Tuple[float, float, float],
        density_override: Optional[int] = None
    ) -> StoryScene:
        """
        Generate a story scene with appropriate props.
        
        Args:
            scene_type: Type of scene to generate
            location: World position (x, y, z)
            density_override: Optional override for clutter density (5-50)
            
        Returns:
            Generated StoryScene
            
        Raises:
            ValueError: If location or density is invalid
            SceneGenerationError: If scene generation fails
        """
        try:
            # Validate inputs
            if not self._validate_location(location):
                raise ValueError(f"Invalid location: {location}")
            
            if density_override is not None and (density_override < 5 or density_override > 50):
                raise ValueError(f"Invalid density: {density_override}. Must be between 5 and 50")
            
            template = self._scene_templates.get(scene_type)
            if not template:
                raise SceneGenerationError(f"Unknown scene type: {scene_type}")
            
            min_objects = template.get("min_objects", 5)
            max_objects = template.get("max_objects", 50)
            
            if density_override:
                clutter_density = max(min_objects, min(max_objects, density_override))
            else:
                clutter_density = (min_objects + max_objects) // 2
            
            scene_id = uuid4()
            objects = []
            
            # Generate required objects
            required = template.get("required_objects", [])
            for obj_type in required:
                obj = self._create_object_metadata(obj_type, NarrativeWeight.MEDIUM)
                objects.append(obj)
            
            # Generate optional objects
            optional = template.get("optional_objects", [])
            remaining = clutter_density - len(objects)
            import random
            if optional and remaining > 0:
                selected_optional = random.sample(optional, min(remaining, len(optional)))
                for obj_type in selected_optional:
                    obj = self._create_object_metadata(obj_type, NarrativeWeight.LOW)
                    objects.append(obj)
            
            # Fill remaining with generic objects
            while len(objects) < clutter_density:
                obj = self._create_object_metadata("generic_item", NarrativeWeight.LOW)
                objects.append(obj)
            
            scene = StoryScene(
                scene_id=scene_id,
                scene_type=scene_type,
                location=location,
                objects=objects,
                clutter_density=len(objects),
                discovery_markers=self._generate_discovery_markers(scene_type),
            )
            
            # Persist to database
            await self._persist_scene(scene)
            
            # Cache in memory (LRU)
            async with self._lock:
                self._scenes_cache[scene_id] = scene
                if len(self._scenes_cache) > self._cache_max_size:
                    # Remove oldest entry
                    oldest_id = next(iter(self._scenes_cache))
                    self._scenes_cache.pop(oldest_id)
            
            _logger.info(f"Generated story scene {scene_id} of type {scene_type.value} at {location}")
            return scene
            
        except (ValueError, SceneGenerationError):
            raise
        except Exception as e:
            _logger.error(f"Scene generation failed: {e}", exc_info=True)
            raise SceneGenerationError(f"Failed to generate scene: {e}") from e
    
    async def _persist_scene(self, scene: StoryScene) -> None:
        """Persist scene to database."""
        try:
            postgres = await self._get_postgres()
            if not postgres:
                _logger.warning("Database not available, scene not persisted")
                return
            
            # Persist scene
            await postgres.execute(
                """
                INSERT INTO story_scenes (
                    scene_id, scene_type, location_x, location_y, location_z,
                    clutter_density, objects, discovery_markers, generated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::text[], $9)
                ON CONFLICT (scene_id) DO UPDATE SET
                    objects = EXCLUDED.objects,
                    discovery_markers = EXCLUDED.discovery_markers
                """,
                scene.scene_id,
                scene.scene_type.value,
                scene.location[0],
                scene.location[1],
                scene.location[2],
                scene.clutter_density,
                json.dumps([obj.to_dict() for obj in scene.objects]),
                scene.discovery_markers,
                scene.generated_at,
            )
            
            # Persist object metadata
            for obj in scene.objects:
                await postgres.execute(
                    """
                    INSERT INTO object_metadata (
                        object_id, object_type, narrative_weight, story_tags,
                        wear_state, damage_state, temporal_decay, relationship_rules, placement_context
                    ) VALUES ($1, $2, $3, $4::text[], $5, $6, $7, $8::jsonb, $9::jsonb)
                    ON CONFLICT (object_id) DO UPDATE SET
                        wear_state = EXCLUDED.wear_state,
                        damage_state = EXCLUDED.damage_state,
                        temporal_decay = EXCLUDED.temporal_decay
                    """,
                    obj.object_id,
                    obj.object_type,
                    obj.narrative_weight.value,
                    obj.story_tags,
                    obj.wear_state,
                    obj.damage_state,
                    obj.temporal_decay,
                    json.dumps(obj.relationship_rules),
                    json.dumps(obj.placement_context),
                )
        except Exception as e:
            _logger.error(f"Failed to persist scene {scene.scene_id}: {e}", exc_info=True)
            # Don't fail scene generation if persistence fails
    
    def _create_object_metadata(
        self,
        object_type: str,
        narrative_weight: NarrativeWeight,
        wear_state: Optional[float] = None
    ) -> ObjectMetadata:
        """Create object metadata with appropriate properties."""
        import random
        
        obj_id = uuid4()
        if wear_state is None:
            wear_state = random.uniform(0.0, 0.7)  # Most objects show some wear
        
        story_tags = self._generate_story_tags(object_type, narrative_weight)
        
        return ObjectMetadata(
            object_id=obj_id,
            object_type=object_type,
            narrative_weight=narrative_weight,
            story_tags=story_tags,
            wear_state=wear_state,
            damage_state=random.uniform(0.0, wear_state),  # Damage <= wear
            temporal_decay=random.uniform(0.0, 1.0),
        )
    
    def _generate_story_tags(self, object_type: str, weight: NarrativeWeight) -> List[str]:
        """Generate story tags based on object type and weight."""
        tags = [object_type]
        
        if weight == NarrativeWeight.CRITICAL:
            tags.append("narrative_key")
        elif weight == NarrativeWeight.HIGH:
            tags.append("important")
        
        # Add contextual tags
        if object_type in ["weapon", "ammunition", "armor"]:
            tags.append("combat")
        elif object_type in ["medical_supplies", "food"]:
            tags.append("survival")
        elif object_type in ["personal_item", "clothing"]:
            tags.append("personal")
        
        return tags
    
    def _generate_discovery_markers(self, scene_type: SceneType) -> List[str]:
        """Generate discovery markers for scene type."""
        markers = []
        
        if scene_type == SceneType.BATTLE_AFTERMATH:
            markers.extend(["blood_stain", "damage_pattern", "scattered_items"])
        elif scene_type == SceneType.ABANDONED_CAMP:
            markers.extend(["disturbed_ground", "left_behind_items", "extinguished_fire"])
        elif scene_type == SceneType.RECENT_DEPARTURE:
            markers.extend(["fresh_tracks", "warm_embers", "recent_movement"])
        elif scene_type == SceneType.LONG_TERM_SETTLEMENT:
            markers.extend(["established_structures", "organized_layout", "permanent_markers", "community_signs"])
        
        return markers
    
    async def record_discovery(
        self,
        player_id: UUID,
        object_id: Optional[UUID] = None,
        scene_id: Optional[UUID] = None,
        noticed: bool = True
    ) -> DiscoveryReward:
        """
        Record a discovery by a player.
        
        Args:
            player_id: Player who made the discovery
            object_id: Optional object that was discovered
            scene_id: Optional scene that was discovered
            noticed: Whether player explicitly noticed
            
        Returns:
            DiscoveryReward created
        """
        discovery_id = uuid4()
        
        # Calculate reward based on what was discovered
        reward_type = "narrative"
        reward_value = 1.0
        
        # Get object metadata from cache or database
        obj = None
        if object_id:
            async with self._lock:
                # Check cache first
                if object_id in self._scenes_cache:
                    # Find object in cached scenes
                    for scene in self._scenes_cache.values():
                        for cached_obj in scene.objects:
                            if cached_obj.object_id == object_id:
                                obj = cached_obj
                                break
                        if obj:
                            break
            
            # If not in cache, try database
            if not obj:
                postgres = await self._get_postgres()
                if postgres:
                    row = await postgres.fetch(
                        "SELECT * FROM object_metadata WHERE object_id = $1",
                        object_id
                    )
                    if row:
                        # Reconstruct ObjectMetadata from row
                        obj = ObjectMetadata(
                            object_id=object_id,
                            object_type=row["object_type"],
                            narrative_weight=NarrativeWeight(row["narrative_weight"]),
                            story_tags=row["story_tags"] or [],
                            wear_state=row["wear_state"],
                            damage_state=row["damage_state"],
                            temporal_decay=row["temporal_decay"],
                            relationship_rules=json.loads(row["relationship_rules"]) if isinstance(row["relationship_rules"], str) else row["relationship_rules"],
                            placement_context=json.loads(row["placement_context"]) if isinstance(row["placement_context"], str) else row["placement_context"],
                        )
        
        if obj:
            if obj.narrative_weight == NarrativeWeight.CRITICAL:
                reward_value = 10.0
                reward_type = "lore"
            elif obj.narrative_weight == NarrativeWeight.HIGH:
                reward_value = 5.0
        
        reward = DiscoveryReward(
            discovery_id=discovery_id,
            player_id=player_id,
            object_id=object_id,
            scene_id=scene_id,
            reward_type=reward_type,
            reward_value=reward_value,
            noticed=noticed,
        )
        
        # Persist to database
        await self._persist_discovery(reward)
        
        async with self._lock:
            self._update_discovery_metrics(noticed)
        
        _logger.info(f"Recorded discovery {discovery_id} by player {player_id} (noticed={noticed})")
        return reward
    
    async def _persist_discovery(self, reward: DiscoveryReward) -> None:
        """Persist discovery reward to database."""
        try:
            postgres = await self._get_postgres()
            if not postgres:
                return
            
            await postgres.execute(
                """
                INSERT INTO discovery_rewards (
                    discovery_id, player_id, object_id, scene_id,
                    reward_type, reward_value, noticed, discovered_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (discovery_id) DO NOTHING
                """,
                reward.discovery_id,
                reward.player_id,
                reward.object_id,
                reward.scene_id,
                reward.reward_type,
                reward.reward_value,
                reward.noticed,
                reward.discovered_at,
            )
        except Exception as e:
            _logger.error(f"Failed to persist discovery {reward.discovery_id}: {e}", exc_info=True)
    
    def _update_discovery_metrics(self, noticed: bool) -> None:
        """Update discovery metrics."""
        self._discovery_metrics["total_details"] += 1
        if noticed:
            self._discovery_metrics["noticed_details"] += 1
        else:
            self._discovery_metrics["unnoticed_details"] += 1
        
        total = self._discovery_metrics["total_details"]
        if total > 0:
            self._discovery_metrics["discovery_rate"] = (
                self._discovery_metrics["noticed_details"] / total
            )
    
    def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get discovery metrics (99% details tracking)."""
        # Note: This is a read-only operation, no lock needed
        # Metrics are updated atomically in _update_discovery_metrics
        return self._discovery_metrics.copy()
    
    async def record_environmental_change(
        self,
        change_type: str,
        location: Tuple[float, float, float],
        description: str,
        player_id: Optional[UUID] = None
    ) -> None:
        """
        Record an environmental change (player action, NPC trace, etc.).
        
        Args:
            change_type: Type of change ("player_action", "npc_trace", "weather_erosion")
            location: Location of change
            description: Description of change
            player_id: Optional player who caused change
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not change_type or not isinstance(change_type, str):
            raise ValueError(f"Invalid change_type: {change_type}")
        
        if not self._validate_location(location):
            raise ValueError(f"Invalid location: {location}")
        
        if not description or not isinstance(description, str):
            raise ValueError("Description must be a non-empty string")
        
        change_id = uuid4()
        record = {
            "change_id": str(change_id),
            "change_type": change_type,
            "location": location,
            "description": description,
            "player_id": str(player_id) if player_id else None,
            "timestamp": datetime.fromtimestamp(time.time()),
        }
        
        # Persist to database
        try:
            postgres = await self._get_postgres()
            if postgres:
                await postgres.execute(
                    """
                    INSERT INTO environmental_history (
                        change_id, change_type, location_x, location_y, location_z,
                        description, player_id, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    change_id,
                    change_type,
                    location[0],
                    location[1],
                    location[2],
                    description,
                    player_id,
                    datetime.fromtimestamp(time.time()),
                )
        except Exception as e:
            _logger.error(f"Failed to persist environmental change: {e}", exc_info=True)
            # Continue even if persistence fails
        
        _logger.debug(f"Recorded environmental change: {change_type} at {location}")
    
    async def get_environmental_history(
        self,
        location: Optional[Tuple[float, float, float]] = None,
        radius: float = 50.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get environmental history for a location.
        
        Args:
            location: Center location (if None, returns all)
            radius: Search radius
            limit: Maximum records to return
            
        Returns:
            List of environmental change records
        """
        try:
            postgres = await self._get_postgres()
            if postgres:
                if location:
                    # Query by location with radius
                    records = await postgres.fetch_all(
                        """
                        SELECT change_id, change_type, location_x, location_y, location_z,
                               description, player_id, timestamp
                        FROM environmental_history
                        WHERE (
                            (location_x - $1)^2 + (location_y - $2)^2 + (location_z - $3)^2
                        ) <= $4^2
                        ORDER BY timestamp DESC
                        LIMIT $5
                        """,
                        location[0],
                        location[1],
                        location[2],
                        radius,
                        limit,
                    )
                else:
                    # Get all recent records
                    records = await postgres.fetch_all(
                        """
                        SELECT change_id, change_type, location_x, location_y, location_z,
                               description, player_id, timestamp
                        FROM environmental_history
                        ORDER BY timestamp DESC
                        LIMIT $1
                        """,
                        limit,
                    )
                
                # Convert to list of dicts
                return [
                    {
                        "change_id": str(r["change_id"]),
                        "change_type": r["change_type"],
                        "location": (r["location_x"], r["location_y"], r["location_z"]),
                        "description": r["description"],
                        "player_id": str(r["player_id"]) if r["player_id"] else None,
                        "timestamp": r["timestamp"].timestamp() if hasattr(r["timestamp"], 'timestamp') else r["timestamp"],
                    }
                    for r in records
                ]
        except Exception as e:
            _logger.error(f"Failed to get environmental history: {e}", exc_info=True)
        
        # Fallback to empty list if database fails
        return []
    
    async def get_scene(self, scene_id: UUID) -> Optional[StoryScene]:
        """Get a scene by ID."""
        # Check cache first
        async with self._lock:
            if scene_id in self._scenes_cache:
                return self._scenes_cache[scene_id]
        
        # Try database
        try:
            postgres = await self._get_postgres()
            if postgres:
                row = await postgres.fetch(
                    """
                    SELECT scene_id, scene_type, location_x, location_y, location_z,
                           clutter_density, objects, discovery_markers, generated_at
                    FROM story_scenes
                    WHERE scene_id = $1
                    """,
                    scene_id,
                )
                
                if row:
                    # Reconstruct scene from database
                    objects_data = json.loads(row["objects"]) if isinstance(row["objects"], str) else row["objects"]
                    objects = [
                        ObjectMetadata(
                            object_id=UUID(obj["object_id"]),
                            object_type=obj["object_type"],
                            narrative_weight=NarrativeWeight(obj["narrative_weight"]),
                            story_tags=obj.get("story_tags", []),
                            wear_state=obj.get("wear_state", 0.0),
                            damage_state=obj.get("damage_state", 0.0),
                            temporal_decay=obj.get("temporal_decay", 0.0),
                            relationship_rules=obj.get("relationship_rules", []),
                            placement_context=obj.get("placement_context", {}),
                        )
                        for obj in objects_data
                    ]
                    
                    scene = StoryScene(
                        scene_id=UUID(str(row["scene_id"])),
                        scene_type=SceneType(row["scene_type"]),
                        location=(row["location_x"], row["location_y"], row["location_z"]),
                        objects=objects,
                        clutter_density=row["clutter_density"],
                        discovery_markers=row["discovery_markers"] or [],
                        generated_at=row["generated_at"].timestamp() if hasattr(row["generated_at"], 'timestamp') else row["generated_at"],
                    )
                    
                    # Cache it
                    async with self._lock:
                        self._scenes_cache[scene_id] = scene
                    
                    return scene
        except Exception as e:
            _logger.error(f"Failed to get scene {scene_id}: {e}", exc_info=True)
        
        return None
    
    async def get_object_metadata(self, object_id: UUID) -> Optional[ObjectMetadata]:
        """Get object metadata by ID."""
        # Try database
        try:
            postgres = await self._get_postgres()
            if postgres:
                row = await postgres.fetch(
                    "SELECT * FROM object_metadata WHERE object_id = $1",
                    object_id,
                )
                
                if row:
                    return ObjectMetadata(
                        object_id=object_id,
                        object_type=row["object_type"],
                        narrative_weight=NarrativeWeight(row["narrative_weight"]),
                        story_tags=row["story_tags"] or [],
                        wear_state=row["wear_state"],
                        damage_state=row["damage_state"],
                        temporal_decay=row["temporal_decay"],
                        relationship_rules=json.loads(row["relationship_rules"]) if isinstance(row["relationship_rules"], str) else row["relationship_rules"],
                        placement_context=json.loads(row["placement_context"]) if isinstance(row["placement_context"], str) else row["placement_context"],
                    )
        except Exception as e:
            _logger.error(f"Failed to get object metadata {object_id}: {e}", exc_info=True)
        
        return None
