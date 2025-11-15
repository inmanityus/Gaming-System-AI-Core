"""
Story Memory Configuration
==========================

Configuration settings and thresholds for the Story Memory System.
"""

from typing import Dict, Any
from pydantic import BaseSettings


class StoryMemoryConfig(BaseSettings):
    """Configuration for Story Memory System."""
    
    # Service settings
    service_name: str = "story-memory"
    nats_url: str = "nats://localhost:4222"
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql://postgres:password@localhost:5432/gaming_system"
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 10000
    snapshot_cache_prefix: str = "story:snapshot:"
    
    # Drift detection thresholds
    main_arc_stall_hours: float = 2.0  # Hours without main arc progress
    side_content_ratio_threshold: float = 0.7  # 70% time in side content triggers drift
    experience_overindulgence_hours: float = 1.5  # Too long in single experience
    
    # Theme drift thresholds
    theme_coherence_window_minutes: int = 30  # Rolling window for theme analysis
    horror_theme_minimum_ratio: float = 0.4  # 40% horror content minimum
    off_theme_tolerance_ratio: float = 0.2  # 20% off-theme content allowed
    
    # Conflict detection settings
    conflict_check_interval_seconds: int = 300  # 5 minutes
    dead_npc_grace_period_minutes: int = 10  # Allow some narrative flexibility
    timeline_conflict_severity_threshold: float = 0.8  # How severe before alert
    
    # Performance settings
    event_batch_size: int = 100
    event_flush_interval_seconds: int = 5
    max_snapshot_size_kb: int = 100  # Limit snapshot size
    
    # Observability
    metrics_port: int = 8099
    log_level: str = "INFO"
    trace_enabled: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "STORY_"


# Global config instance
story_config = StoryMemoryConfig()


# Drift analyzer configurations
DRIFT_ANALYZERS = {
    "time_allocation": {
        "enabled": True,
        "check_interval_minutes": 15,
        "thresholds": {
            "main_arc_stall": {
                "hours": story_config.main_arc_stall_hours,
                "severity": "high",
                "description": "Player hasn't progressed main story"
            },
            "side_content_overload": {
                "ratio": story_config.side_content_ratio_threshold,
                "severity": "medium",
                "description": "Too much time in side content"
            },
            "experience_marathon": {
                "hours": story_config.experience_overindulgence_hours,
                "severity": "low",
                "description": "Extended time in single experience"
            }
        }
    },
    "theme_coherence": {
        "enabled": True,
        "check_interval_minutes": 10,
        "thresholds": {
            "horror_dilution": {
                "min_ratio": story_config.horror_theme_minimum_ratio,
                "severity": "high",
                "description": "Core horror theme being diluted"
            },
            "genre_drift": {
                "max_off_theme": story_config.off_theme_tolerance_ratio,
                "severity": "medium",
                "description": "Drifting into other genres"
            }
        }
    },
    "narrative_conflicts": {
        "enabled": True,
        "check_interval_minutes": 5,
        "conflict_rules": [
            {
                "type": "dead_npc_interaction",
                "severity": "critical",
                "description": "Player interacting with dead NPC"
            },
            {
                "type": "timeline_paradox",
                "severity": "high",
                "description": "Events happening out of order"
            },
            {
                "type": "faction_contradiction",
                "severity": "medium",
                "description": "Contradictory faction standings"
            },
            {
                "type": "quest_state_mismatch",
                "severity": "high",
                "description": "Quest state conflicts with story"
            }
        ]
    }
}


# Event type mappings
EVENT_TYPE_HANDLERS = {
    # Arc events
    "arc.beat.reached": "handle_arc_beat",
    "arc.started": "handle_arc_started",
    "arc.completed": "handle_arc_completed",
    
    # Quest events
    "quest.started": "handle_quest_started",
    "quest.completed": "handle_quest_completed",
    "quest.failed": "handle_quest_failed",
    
    # Decision events
    "decision.made": "handle_decision",
    "moral.choice": "handle_moral_choice",
    
    # Relationship events
    "relationship.changed": "handle_relationship_change",
    "faction.standing.changed": "handle_faction_change",
    
    # Experience events
    "experience.started": "handle_experience_started",
    "experience.completed": "handle_experience_completed",
    
    # Death/respawn events
    "player.death": "handle_player_death",
    "npc.death": "handle_npc_death",
    "soul.echo.encounter": "handle_soul_echo",
}
