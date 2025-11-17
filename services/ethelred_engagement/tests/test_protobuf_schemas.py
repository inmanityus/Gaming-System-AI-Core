"""
Unit tests for engagement protobuf schemas
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Compile proto if needed
from compile_proto import compile_proto
compile_proto()

# Import generated protobuf classes
from generated import ethelred_engagement_pb2 as engagement_pb2
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.duration_pb2 import Duration


def test_npc_interaction_event():
    """Test NPCInteractionEvent serialization."""
    event = engagement_pb2.NPCInteractionEvent()
    
    # Set metadata
    event.session_id = f"session-{uuid.uuid4()}"
    event.player_id = f"player-{uuid.uuid4()}"
    event.actor_type = engagement_pb2.ACTOR_TYPE_REAL_PLAYER
    
    # Set interaction details
    event.npc_id = "npc-vampire-butler"
    event.interaction_type = engagement_pb2.INTERACTION_TYPE_DIALOGUE
    event.choice_id = "butler-greeting-01"
    event.choice_label = "Ask about the master"
    event.help_harm_flag = engagement_pb2.HELP_HARM_NEUTRAL
    
    # Set context
    event.timestamp.FromDatetime(datetime.utcnow())
    event.location_id = "castle-foyer"
    event.arc_id = "vampire-mansion-main"
    event.experience_id = "castle-exploration"
    event.build_id = "build-2025-11-15"
    
    # Add additional context
    event.additional_context["mood"] = "curious"
    event.additional_context["quest_active"] = "find-the-key"
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = engagement_pb2.NPCInteractionEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.npc_id == "npc-vampire-butler"
    assert deserialized.interaction_type == engagement_pb2.INTERACTION_TYPE_DIALOGUE
    assert deserialized.help_harm_flag == engagement_pb2.HELP_HARM_NEUTRAL
    assert deserialized.additional_context["mood"] == "curious"
    
    print("✓ NPCInteractionEvent serialization test passed")


def test_moral_choice_event():
    """Test MoralChoiceEvent serialization."""
    event = engagement_pb2.MoralChoiceEvent()
    
    # Set metadata
    event.session_id = f"session-{uuid.uuid4()}"
    event.player_id = f"player-{uuid.uuid4()}"
    event.actor_type = engagement_pb2.ACTOR_TYPE_REAL_PLAYER
    
    # Set choice details
    event.choice_id = "bridge-dilemma"
    event.arc_id = "main-quest"
    event.scene_id = "collapsing-bridge"
    
    # Add choice options
    option1 = event.options.add()
    option1.option_id = "save-child"
    option1.option_label = "Save the child"
    option1.tags.extend([engagement_pb2.OPTION_TAG_GOOD, engagement_pb2.OPTION_TAG_SAFE])
    
    option2 = event.options.add()
    option2.option_id = "save-artifact"
    option2.option_label = "Grab the artifact"
    option2.tags.extend([engagement_pb2.OPTION_TAG_EVIL, engagement_pb2.OPTION_TAG_EXTREME])
    
    option3 = event.options.add()
    option3.option_id = "save-both"
    option3.option_label = "Try to save both"
    option3.tags.extend([engagement_pb2.OPTION_TAG_NEUTRAL, engagement_pb2.OPTION_TAG_MODERATE])
    
    event.selected_option_id = "save-child"
    
    # Set decision metrics
    event.decision_latency_ms = 8500  # 8.5 seconds of thinking
    event.num_retries = 0
    event.reloaded_save = False
    
    event.timestamp.FromDatetime(datetime.utcnow())
    event.build_id = "build-2025-11-15"
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = engagement_pb2.MoralChoiceEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.choice_id == "bridge-dilemma"
    assert len(deserialized.options) == 3
    assert deserialized.selected_option_id == "save-child"
    assert deserialized.decision_latency_ms == 8500
    assert engagement_pb2.OPTION_TAG_GOOD in deserialized.options[0].tags
    
    print("✓ MoralChoiceEvent serialization test passed")


def test_session_metrics_event():
    """Test SessionMetricsEvent serialization."""
    event = engagement_pb2.SessionMetricsEvent()
    
    # Set metadata
    event.session_id = f"session-{uuid.uuid4()}"
    event.player_id = f"player-{uuid.uuid4()}"
    event.actor_type = engagement_pb2.ACTOR_TYPE_REAL_PLAYER
    
    # Set session timing
    start_time = datetime.utcnow() - timedelta(minutes=127)
    end_time = datetime.utcnow()
    event.session_start.FromDatetime(start_time)
    event.session_end.FromDatetime(end_time)
    event.total_duration_minutes = 127
    
    # Set patterns
    event.time_of_day_bucket = engagement_pb2.TIME_OF_DAY_LATE_NIGHT
    event.day_of_week = 5  # Friday
    event.num_sessions_last_7_days = 12
    event.num_sessions_last_24_hours = 3
    
    # Set behavior
    event.is_return_session = True
    event.time_since_last_session.seconds = 1800  # 30 minutes
    
    # Set context
    event.build_id = "build-2025-11-15"
    event.platform = "PC"
    event.region = "NA-East"
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = engagement_pb2.SessionMetricsEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.total_duration_minutes == 127
    assert deserialized.time_of_day_bucket == engagement_pb2.TIME_OF_DAY_LATE_NIGHT
    assert deserialized.is_return_session == True
    assert deserialized.num_sessions_last_24_hours == 3
    assert deserialized.platform == "PC"
    
    print("✓ SessionMetricsEvent serialization test passed")


def test_ai_player_run_event():
    """Test AIPlayerRunEvent serialization."""
    event = engagement_pb2.AIPlayerRunEvent()
    
    # Set metadata
    event.ai_run_id = f"ai-run-{uuid.uuid4()}"
    event.personality_profile = engagement_pb2.PERSONALITY_EMPATHETIC
    
    # Set run summary
    event.total_npcs_interacted = 47
    event.moral_choices_made = 12
    event.help_harm_ratio = 3.5  # Mostly helpful
    event.exploration_coverage = 0.82
    
    # Set timing
    run_start = datetime.utcnow() - timedelta(hours=3)
    event.run_start.FromDatetime(run_start)
    event.run_end.FromDatetime(datetime.utcnow())
    event.total_duration_hours = 3
    
    # Set context
    event.build_id = "build-2025-11-15"
    event.scenario_id = "full-game-empathetic-run"
    
    event.additional_context["difficulty"] = "normal"
    event.additional_context["test_variant"] = "A"
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = engagement_pb2.AIPlayerRunEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.personality_profile == engagement_pb2.PERSONALITY_EMPATHETIC
    assert deserialized.total_npcs_interacted == 47
    assert abs(deserialized.help_harm_ratio - 3.5) < 0.01
    assert deserialized.scenario_id == "full-game-empathetic-run"
    
    print("✓ AIPlayerRunEvent serialization test passed")


def test_engagement_metrics_event():
    """Test EngagementMetricsEvent serialization."""
    event = engagement_pb2.EngagementMetricsEvent()
    
    # Set envelope
    event.envelope.trace_id = str(uuid.uuid4())
    event.envelope.domain = "Engagement"
    event.envelope.issue_type = "ENGAGEMENT.METRICS"
    event.envelope.severity = engagement_pb2.SEVERITY_INFO
    event.envelope.confidence = 0.85
    event.envelope.goal_tags.extend(["G-IMMERSION", "G-LONGTERM"])
    
    # Set aggregation context
    event.cohort_id = "NA-18-25-PC"
    event.aggregation_period = "2025-11-15T00:00:00Z/P1D"
    
    # Add NPC attachment metrics
    npc_metric = event.npc_attachments.add()
    npc_metric.npc_id = "npc-vampire-butler"
    npc_metric.protection_harm_ratio = 2.5
    npc_metric.attention_score = 0.73
    npc_metric.abandonment_frequency = 0.15
    npc_metric.total_interactions = 234
    npc_metric.helpful_actions = 156
    npc_metric.harmful_actions = 12
    npc_metric.neutral_actions = 66
    npc_metric.total_proximity_time.seconds = 7200  # 2 hours
    
    # Add moral tension metrics
    moral_metric = event.moral_tensions.add()
    moral_metric.arc_id = "main-quest"
    moral_metric.scene_id = "collapsing-bridge"
    moral_metric.tension_index = 0.78
    moral_metric.choice_distribution_entropy = 1.45
    moral_metric.avg_decision_latency_seconds = 12.3
    moral_metric.total_choices = 89
    moral_metric.reload_count = 7
    moral_metric.option_counts["save-child"] = 45
    moral_metric.option_counts["save-artifact"] = 12
    moral_metric.option_counts["save-both"] = 32
    
    # Add profile distribution
    event.profile_distribution["lore-driven explorer"] = 127
    event.profile_distribution["combat-focused"] = 89
    event.profile_distribution["completionist"] = 203
    
    # Add top profiles
    profile = event.top_profiles.add()
    profile.profile_id = "prof-001"
    profile.profile_name = "lore-driven explorer"
    profile.confidence = 0.82
    profile.characteristic_behaviors.extend([
        "reads all books",
        "exhausts dialogue trees",
        "explores hidden areas"
    ])
    
    # Set summary stats
    event.total_sessions_analyzed = 419
    event.total_players_analyzed = 312
    event.avg_session_duration_minutes = 87.5
    
    event.computed_at.FromDatetime(datetime.utcnow())
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = engagement_pb2.EngagementMetricsEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.cohort_id == "NA-18-25-PC"
    assert len(deserialized.npc_attachments) == 1
    assert deserialized.npc_attachments[0].npc_id == "npc-vampire-butler"
    assert len(deserialized.moral_tensions) == 1
    assert deserialized.moral_tensions[0].tension_index == 0.78
    assert deserialized.profile_distribution["completionist"] == 203
    
    print("✓ EngagementMetricsEvent serialization test passed")


def test_addiction_risk_event():
    """Test AddictionRiskEvent serialization."""
    event = engagement_pb2.AddictionRiskEvent()
    
    # Set envelope
    event.envelope.trace_id = str(uuid.uuid4())
    event.envelope.domain = "Engagement"
    event.envelope.issue_type = "ENGAGEMENT.ADDICTION_RISK"
    event.envelope.severity = engagement_pb2.SEVERITY_WARNING
    event.envelope.confidence = 0.75
    
    # Set cohort identification
    event.cohort.region = "NA-East"
    event.cohort.age_band = "18-25"
    event.cohort.platform = "PC"
    event.cohort.cohort_size = 1247
    
    event.report_period = "2025-11-08/P7D"
    
    # Set risk indicators
    event.avg_daily_session_hours = 4.7
    event.night_time_play_fraction = 0.28
    event.rapid_session_return_rate = 0.15
    event.weekend_spike_ratio = 1.8
    
    # Set pattern detection
    event.high_risk_patterns.extend([
        "3am_regular",
        "rapid_cycling",
        "weekend_binge"
    ])
    event.associated_systems.extend([
        "dark_world_gambling",
        "collection_minigame"
    ])
    
    # Set risk assessment
    event.overall_risk_level = engagement_pb2.RISK_LEVEL_MEDIUM
    event.risk_summary = "Cohort shows elevated late-night play and rapid session cycling"
    event.recommendations.extend([
        "Review dark world gambling reward schedules",
        "Add cooldown to collection minigame rewards",
        "Consider session-end wellness prompts"
    ])
    
    event.computed_at.FromDatetime(datetime.utcnow())
    event.confidence_percentage = 75
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = engagement_pb2.AddictionRiskEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.cohort.age_band == "18-25"
    assert deserialized.avg_daily_session_hours == 4.7
    assert deserialized.overall_risk_level == engagement_pb2.RISK_LEVEL_MEDIUM
    assert "3am_regular" in deserialized.high_risk_patterns
    assert len(deserialized.recommendations) == 3
    
    print("✓ AddictionRiskEvent serialization test passed")


def test_enums():
    """Test enum values."""
    # Actor types
    assert engagement_pb2.ACTOR_TYPE_REAL_PLAYER == 1
    assert engagement_pb2.ACTOR_TYPE_AI_PLAYER == 2
    
    # Interaction types
    assert engagement_pb2.INTERACTION_TYPE_DIALOGUE == 1
    assert engagement_pb2.INTERACTION_TYPE_HARM == 4
    
    # Option tags
    assert engagement_pb2.OPTION_TAG_SAFE == 1
    assert engagement_pb2.OPTION_TAG_EXTREME == 3
    assert engagement_pb2.OPTION_TAG_EVIL == 4
    
    # Time buckets
    assert engagement_pb2.TIME_OF_DAY_LATE_NIGHT == 5
    
    # Personality profiles
    assert engagement_pb2.PERSONALITY_EMPATHETIC == 1
    assert engagement_pb2.PERSONALITY_RUTHLESS == 2
    
    # Risk levels
    assert engagement_pb2.RISK_LEVEL_HIGH == 3
    
    print("✓ Enum value tests passed")


if __name__ == "__main__":
    print("Running engagement protobuf schema tests...")
    
    test_npc_interaction_event()
    test_moral_choice_event()
    test_session_metrics_event()
    test_ai_player_run_event()
    test_engagement_metrics_event()
    test_addiction_risk_event()
    test_enums()
    
    print("\nAll protobuf schema tests passed! ✅")

