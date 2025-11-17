"""
Unit tests for audio protobuf round-trip serialization
"""
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Compile proto if needed
from compile_proto import compile_proto
compile_proto()

# Import generated protobuf classes
from generated import ethelred_audio_pb2 as audio_pb2
from google.protobuf.timestamp_pb2 import Timestamp


def create_test_envelope():
    """Create a test canonical envelope."""
    envelope = audio_pb2.CanonicalEnvelope()
    envelope.trace_id = str(uuid.uuid4())
    envelope.session_id = f"sess-{uuid.uuid4()}"
    envelope.player_id = f"player-{uuid.uuid4()}"
    envelope.build_id = "build-2025-11-15"
    
    # Set timestamp range
    now = datetime.utcnow()
    envelope.timestamp_range.start.FromDatetime(now)
    envelope.timestamp_range.end.FromDatetime(now)
    
    envelope.domain = "Audio"
    envelope.issue_type = "AUDIO.SEGMENT_CREATED"
    envelope.severity = audio_pb2.SEVERITY_INFO
    envelope.confidence = 0.95
    envelope.evidence_refs.extend(["redalert://media/audio/test.ogg"])
    envelope.goal_tags.extend(["G-IMMERSION", "G-HORROR"])
    
    return envelope


def test_segment_created_event():
    """Test SegmentCreatedEvent serialization."""
    event = audio_pb2.SegmentCreatedEvent()
    event.envelope.CopyFrom(create_test_envelope())
    
    # Set segment data
    event.segment_id = "seg-aud-123"
    event.segment_type = audio_pb2.SEGMENT_TYPE_DIALOGUE
    event.speaker.speaker_id = "npc-vampire-01"
    event.speaker.role = audio_pb2.SPEAKER_ROLE_NPC
    event.speaker.archetype_id = "vampire_house_alpha"
    event.language_code = "en-US"
    
    # Context
    event.context.line_id = "line-intro-01"
    event.context.scene_id = "scene-castle-entrance"
    event.context.experience_id = "exp-vampire-mansion"
    event.context.emotional_tag = "menace"
    event.context.environment_type = "gothic_castle"
    
    event.simulator_applied = True
    
    # Technical details
    event.media_uri = "redalert://media/audio/build-2025-11-15/seg-aud-123.ogg"
    event.sample_rate = 48000
    event.bit_depth = 24
    event.channels = 2
    event.duration_seconds = 3.5
    event.bus_name = "dialogue_bus"
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = audio_pb2.SegmentCreatedEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.segment_id == "seg-aud-123"
    assert deserialized.segment_type == audio_pb2.SEGMENT_TYPE_DIALOGUE
    assert deserialized.speaker.archetype_id == "vampire_house_alpha"
    assert deserialized.language_code == "en-US"
    assert deserialized.simulator_applied == True
    assert deserialized.duration_seconds == 3.5
    
    print("✓ SegmentCreatedEvent serialization test passed")


def test_audio_scores_event():
    """Test AudioScoresEvent serialization."""
    event = audio_pb2.AudioScoresEvent()
    event.envelope.CopyFrom(create_test_envelope())
    event.envelope.issue_type = "AUDIO.SCORES"
    
    # Basic fields
    event.segment_id = "seg-aud-123"
    event.segment_type = audio_pb2.SEGMENT_TYPE_DIALOGUE
    event.speaker.speaker_id = "npc-vampire-01"
    event.speaker.role = audio_pb2.SPEAKER_ROLE_NPC
    event.speaker.archetype_id = "vampire_house_alpha"
    event.language_code = "en-US"
    event.simulator_applied = True
    
    # Scores
    event.scores.intelligibility = 0.92
    event.scores.naturalness = 0.88
    event.scores.archetype_conformity = 0.80
    event.scores.simulator_stability = 0.95
    event.scores.mix_quality = 0.84
    
    # Bands
    event.bands.intelligibility = audio_pb2.INTELLIGIBILITY_ACCEPTABLE
    event.bands.naturalness = audio_pb2.NATURALNESS_OK
    event.bands.archetype_conformity = audio_pb2.ARCHETYPE_ON_PROFILE
    event.bands.simulator_stability = audio_pb2.STABILITY_STABLE
    event.bands.mix_quality = audio_pb2.MIX_QUALITY_OK
    
    # Additional metrics
    event.additional_metrics["snr_db"] = 42.5
    event.additional_metrics["pitch_variability"] = 0.75
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = audio_pb2.AudioScoresEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.scores.intelligibility == 0.92
    assert deserialized.bands.naturalness == audio_pb2.NATURALNESS_OK
    assert deserialized.additional_metrics["snr_db"] == 42.5
    
    print("✓ AudioScoresEvent serialization test passed")


def test_audio_report_event():
    """Test AudioReportEvent serialization."""
    event = audio_pb2.AudioReportEvent()
    event.envelope.CopyFrom(create_test_envelope())
    event.envelope.issue_type = "AUDIO.REPORT"
    
    event.report_id = f"report-{uuid.uuid4()}"
    event.build_id = "build-2025-11-15"
    event.archetype_id = "vampire_house_alpha"
    event.language_code = "en-US"
    
    # Summary
    event.summary.num_segments = 320
    event.summary.intelligibility_distribution["acceptable"] = 0.93
    event.summary.intelligibility_distribution["degraded"] = 0.06
    event.summary.intelligibility_distribution["unacceptable"] = 0.01
    event.summary.naturalness_mean = 0.87
    event.summary.archetype_conformity_mean = 0.81
    event.summary.simulator_stability_mean = 0.96
    event.summary.mix_quality_mean = 0.83
    event.summary.common_deviations.extend([
        "lines in hospital wing slightly too clean",
        "occasional clipping on boss intro roars"
    ])
    
    # Comparison
    event.comparison.prev_build_id = "build-2025-11-07"
    event.comparison.archetype_conformity_delta = 0.03
    event.comparison.simulator_stability_delta = -0.01
    event.comparison.intelligibility_delta = 0.02
    event.comparison.notes = "Stability slightly decreased due to new FX"
    
    event.generated_at.FromDatetime(datetime.utcnow())
    event.report_type = "archetype_report"
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = audio_pb2.AudioReportEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.summary.num_segments == 320
    assert deserialized.summary.intelligibility_distribution["acceptable"] == 0.93
    assert deserialized.comparison.archetype_conformity_delta == 0.03
    assert len(deserialized.summary.common_deviations) == 2
    
    print("✓ AudioReportEvent serialization test passed")


def test_audio_feedback_event():
    """Test AudioFeedbackEvent serialization."""
    # Test simulator feedback
    event = audio_pb2.AudioFeedbackEvent()
    event.envelope.CopyFrom(create_test_envelope())
    event.envelope.issue_type = "AUDIO.FEEDBACK"
    
    event.feedback_id = f"feedback-{uuid.uuid4()}"
    event.build_id = "build-2025-11-15"
    
    # Simulator feedback
    sim_feedback = event.simulator_feedback
    sim_feedback.archetype_id = "vampire_house_alpha"
    sim_feedback.simulator_profile_id = "vampire_alpha_v1"
    
    finding = sim_feedback.findings.add()
    finding.dimension = "roughness"
    finding.observed_mean = 0.45
    finding.target_range_min = 0.55
    finding.target_range_max = 0.70
    finding.recommendation = "Increase glottal roughness parameter by 10-15% for ritual scenes"
    
    sim_feedback.notes = "Do not auto-apply; requires sound designer review"
    
    event.generated_at.FromDatetime(datetime.utcnow())
    
    # Serialize and deserialize
    serialized = event.SerializeToString()
    deserialized = audio_pb2.AudioFeedbackEvent()
    deserialized.ParseFromString(serialized)
    
    # Verify
    assert deserialized.WhichOneof("feedback_type") == "simulator_feedback"
    assert deserialized.simulator_feedback.archetype_id == "vampire_house_alpha"
    assert len(deserialized.simulator_feedback.findings) == 1
    assert deserialized.simulator_feedback.findings[0].dimension == "roughness"
    
    print("✓ AudioFeedbackEvent (simulator) serialization test passed")
    
    # Test archetype feedback
    event2 = audio_pb2.AudioFeedbackEvent()
    event2.envelope.CopyFrom(create_test_envelope())
    event2.envelope.issue_type = "AUDIO.FEEDBACK"
    
    event2.feedback_id = f"feedback-{uuid.uuid4()}"
    event2.build_id = "build-2025-11-15"
    
    # Archetype feedback
    arch_feedback = event2.archetype_feedback
    arch_feedback.archetype_id = "zombie_horde"
    arch_feedback.language_code = "en-US"
    arch_feedback.mean_archetype_conformity = 0.78
    arch_feedback.weak_contexts.extend(["hospital", "prison_yard"])
    
    example = arch_feedback.candidate_training_examples.add()
    example.segment_id = "seg-aud-882"
    example.media_uri = "redalert://media/audio/.../seg-aud-882.ogg"
    example.labels.extend(["too_clean", "not_monster_like_enough"])
    
    event2.generated_at.FromDatetime(datetime.utcnow())
    
    # Serialize and deserialize
    serialized2 = event2.SerializeToString()
    deserialized2 = audio_pb2.AudioFeedbackEvent()
    deserialized2.ParseFromString(serialized2)
    
    # Verify
    assert deserialized2.WhichOneof("feedback_type") == "archetype_feedback"
    assert deserialized2.archetype_feedback.archetype_id == "zombie_horde"
    assert len(deserialized2.archetype_feedback.weak_contexts) == 2
    assert len(deserialized2.archetype_feedback.candidate_training_examples) == 1
    
    print("✓ AudioFeedbackEvent (archetype) serialization test passed")


def test_enums():
    """Test enum value handling."""
    # Test all enums have proper values
    assert audio_pb2.SEGMENT_TYPE_DIALOGUE == 1
    assert audio_pb2.SPEAKER_ROLE_NPC == 1
    assert audio_pb2.INTELLIGIBILITY_ACCEPTABLE == 1
    assert audio_pb2.NATURALNESS_OK == 1
    assert audio_pb2.ARCHETYPE_ON_PROFILE == 1
    assert audio_pb2.STABILITY_STABLE == 1
    assert audio_pb2.MIX_QUALITY_OK == 1
    assert audio_pb2.SEVERITY_INFO == 1
    
    print("✓ Enum value tests passed")


if __name__ == "__main__":
    print("Running audio protobuf serialization tests...")
    test_segment_created_event()
    test_audio_scores_event()
    test_audio_report_event()
    test_audio_feedback_event()
    test_enums()
    print("\nAll tests passed! ✅")

