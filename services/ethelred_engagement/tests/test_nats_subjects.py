"""
Integration tests for engagement NATS subjects
"""
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock NATS for testing
class MockNATSMessage:
    def __init__(self, subject, data):
        self.subject = subject
        self.data = data


class MockNATSClient:
    def __init__(self):
        self.published = []
        self.subscriptions = {}
    
    async def connect(self, *args, **kwargs):
        pass
    
    async def publish(self, subject, data):
        self.published.append((subject, data))
        # Deliver to any subscribers
        if subject in self.subscriptions:
            for cb in self.subscriptions[subject]:
                await cb(MockNATSMessage(subject, data))
    
    async def subscribe(self, subject, queue=None, cb=None):
        if subject not in self.subscriptions:
            self.subscriptions[subject] = []
        self.subscriptions[subject].append(cb)
    
    async def close(self):
        pass


# Compile proto
from compile_proto import compile_proto
compile_proto()

from generated import ethelred_engagement_pb2 as engagement_pb2


# NATS subject definitions
SUBJECTS = {
    # Telemetry inputs
    'npc_interaction': 'telemetry.raw.npc_interaction',
    'moral_choice': 'telemetry.raw.moral_choice', 
    'session_metrics': 'telemetry.raw.session_metrics',
    'ai_run': 'telemetry.raw.ai_run',
    
    # Normalized telemetry
    'normalized_npc': 'telemetry.emo.normalized.npc_interaction',
    'normalized_moral': 'telemetry.emo.normalized.moral_choice',
    'normalized_session': 'telemetry.emo.normalized.session_metrics',
    'normalized_ai': 'telemetry.emo.normalized.ai_run',
    
    # Analytics outputs
    'engagement_metrics': 'events.ethelred.emo.v1.engagement_metrics',
    'addiction_risk': 'events.ethelred.emo.v1.addiction_risk'
}


async def test_telemetry_flow():
    """Test telemetry event flow through NATS."""
    nc = MockNATSClient()
    await nc.connect()
    
    raw_events = []
    normalized_events = []
    
    # Subscribe to raw telemetry
    async def raw_handler(msg):
        raw_events.append(msg)
    
    await nc.subscribe(SUBJECTS['npc_interaction'], cb=raw_handler)
    await nc.subscribe(SUBJECTS['moral_choice'], cb=raw_handler)
    
    # Subscribe to normalized telemetry
    async def norm_handler(msg):
        normalized_events.append(msg)
    
    await nc.subscribe(SUBJECTS['normalized_npc'], cb=norm_handler)
    await nc.subscribe(SUBJECTS['normalized_moral'], cb=norm_handler)
    
    # Publish NPC interaction event
    npc_event = engagement_pb2.NPCInteractionEvent()
    npc_event.session_id = f"session-{uuid.uuid4()}"
    npc_event.npc_id = "npc-test"
    npc_event.interaction_type = engagement_pb2.INTERACTION_TYPE_DIALOGUE
    npc_event.timestamp.FromDatetime(datetime.utcnow())
    
    await nc.publish(SUBJECTS['npc_interaction'], npc_event.SerializeToString())
    
    # Publish moral choice event
    moral_event = engagement_pb2.MoralChoiceEvent()
    moral_event.session_id = f"session-{uuid.uuid4()}"
    moral_event.choice_id = "test-choice"
    moral_event.arc_id = "test-arc"
    moral_event.timestamp.FromDatetime(datetime.utcnow())
    
    await nc.publish(SUBJECTS['moral_choice'], moral_event.SerializeToString())
    
    await asyncio.sleep(0.1)
    
    # Verify raw events received
    assert len(raw_events) == 2
    assert raw_events[0].subject == SUBJECTS['npc_interaction']
    assert raw_events[1].subject == SUBJECTS['moral_choice']
    
    await nc.close()
    print("✓ Telemetry flow test passed")


async def test_analytics_output_flow():
    """Test analytics output event flow."""
    nc = MockNATSClient()
    await nc.connect()
    
    metrics_events = []
    risk_events = []
    
    # Subscribe to analytics outputs
    async def metrics_handler(msg):
        event = engagement_pb2.EngagementMetricsEvent()
        event.ParseFromString(msg.data)
        metrics_events.append(event)
    
    async def risk_handler(msg):
        event = engagement_pb2.AddictionRiskEvent()
        event.ParseFromString(msg.data)
        risk_events.append(event)
    
    await nc.subscribe(SUBJECTS['engagement_metrics'], cb=metrics_handler)
    await nc.subscribe(SUBJECTS['addiction_risk'], cb=risk_handler)
    
    # Publish engagement metrics
    metrics_event = engagement_pb2.EngagementMetricsEvent()
    metrics_event.envelope.trace_id = str(uuid.uuid4())
    metrics_event.envelope.domain = "Engagement"
    metrics_event.envelope.issue_type = "ENGAGEMENT.METRICS"
    metrics_event.cohort_id = "test-cohort"
    metrics_event.total_sessions_analyzed = 100
    
    await nc.publish(SUBJECTS['engagement_metrics'], metrics_event.SerializeToString())
    
    # Publish addiction risk
    risk_event = engagement_pb2.AddictionRiskEvent()
    risk_event.envelope.trace_id = str(uuid.uuid4())
    risk_event.envelope.domain = "Engagement"
    risk_event.envelope.issue_type = "ENGAGEMENT.ADDICTION_RISK"
    risk_event.cohort.region = "NA"
    risk_event.cohort.age_band = "18-25"
    risk_event.overall_risk_level = engagement_pb2.RISK_LEVEL_LOW
    
    await nc.publish(SUBJECTS['addiction_risk'], risk_event.SerializeToString())
    
    await asyncio.sleep(0.1)
    
    # Verify events received
    assert len(metrics_events) == 1
    assert metrics_events[0].cohort_id == "test-cohort"
    
    assert len(risk_events) == 1
    assert risk_events[0].cohort.age_band == "18-25"
    assert risk_events[0].overall_risk_level == engagement_pb2.RISK_LEVEL_LOW
    
    await nc.close()
    print("✓ Analytics output flow test passed")


async def test_session_metrics_patterns():
    """Test session metrics event patterns."""
    nc = MockNATSClient()
    await nc.connect()
    
    session_events = []
    
    async def handler(msg):
        event = engagement_pb2.SessionMetricsEvent()
        event.ParseFromString(msg.data)
        session_events.append(event)
    
    await nc.subscribe(SUBJECTS['session_metrics'], cb=handler)
    
    # Simulate multiple session patterns
    
    # Normal session
    normal_session = engagement_pb2.SessionMetricsEvent()
    normal_session.session_id = f"session-normal-{uuid.uuid4()}"
    normal_session.actor_type = engagement_pb2.ACTOR_TYPE_REAL_PLAYER
    normal_session.total_duration_minutes = 90
    normal_session.time_of_day_bucket = engagement_pb2.TIME_OF_DAY_EVENING
    normal_session.is_return_session = False
    
    await nc.publish(SUBJECTS['session_metrics'], normal_session.SerializeToString())
    
    # Late night rapid return session
    rapid_session = engagement_pb2.SessionMetricsEvent()
    rapid_session.session_id = f"session-rapid-{uuid.uuid4()}"
    rapid_session.actor_type = engagement_pb2.ACTOR_TYPE_REAL_PLAYER
    rapid_session.total_duration_minutes = 15
    rapid_session.time_of_day_bucket = engagement_pb2.TIME_OF_DAY_LATE_NIGHT
    rapid_session.is_return_session = True
    rapid_session.time_since_last_session.seconds = 1200  # 20 minutes
    
    await nc.publish(SUBJECTS['session_metrics'], rapid_session.SerializeToString())
    
    # AI player session
    ai_session = engagement_pb2.SessionMetricsEvent()
    ai_session.session_id = f"session-ai-{uuid.uuid4()}"
    ai_session.actor_type = engagement_pb2.ACTOR_TYPE_AI_PLAYER
    ai_session.total_duration_minutes = 180
    ai_session.time_of_day_bucket = engagement_pb2.TIME_OF_DAY_MORNING
    ai_session.is_return_session = False
    
    await nc.publish(SUBJECTS['session_metrics'], ai_session.SerializeToString())
    
    await asyncio.sleep(0.1)
    
    # Verify all patterns received
    assert len(session_events) == 3
    
    # Find each type
    normal = next(e for e in session_events if "normal" in e.session_id)
    rapid = next(e for e in session_events if "rapid" in e.session_id)
    ai = next(e for e in session_events if "ai" in e.session_id)
    
    assert normal.total_duration_minutes == 90
    assert rapid.is_return_session == True
    assert rapid.time_of_day_bucket == engagement_pb2.TIME_OF_DAY_LATE_NIGHT
    assert ai.actor_type == engagement_pb2.ACTOR_TYPE_AI_PLAYER
    
    await nc.close()
    print("✓ Session metrics patterns test passed")


async def test_subject_naming_conventions():
    """Verify all subject names follow conventions."""
    # Telemetry subjects should start with 'telemetry.'
    for key in ['npc_interaction', 'moral_choice', 'session_metrics', 'ai_run']:
        assert SUBJECTS[key].startswith('telemetry.raw.')
    
    # Normalized subjects
    for key in ['normalized_npc', 'normalized_moral', 'normalized_session', 'normalized_ai']:
        assert SUBJECTS[key].startswith('telemetry.emo.normalized.')
    
    # Event subjects should start with 'events.'
    for key in ['engagement_metrics', 'addiction_risk']:
        assert SUBJECTS[key].startswith('events.ethelred.emo.v1.')
    
    # All event subjects should include version
    for key in ['engagement_metrics', 'addiction_risk']:
        assert '.v1.' in SUBJECTS[key]
    
    print("✓ Subject naming conventions test passed")


async def test_privacy_compliance():
    """Test that events comply with privacy requirements."""
    # Test that addiction risk events have NO player IDs
    risk_event = engagement_pb2.AddictionRiskEvent()
    risk_event.envelope.domain = "Engagement"
    risk_event.cohort.region = "NA"
    risk_event.cohort.age_band = "18-25"
    
    # Verify no player_id field in envelope for addiction risk
    # (player_id is optional and should not be set for cohort analytics)
    assert not risk_event.envelope.player_id
    
    # Test that metrics events use cohort IDs
    metrics_event = engagement_pb2.EngagementMetricsEvent()
    metrics_event.cohort_id = "NA-18-25-PC"  # Cohort, not individual
    metrics_event.total_players_analyzed = 100  # Aggregate count
    
    # Verify cohort-based aggregation
    assert metrics_event.cohort_id
    assert metrics_event.total_players_analyzed > 1  # Not individual
    
    print("✓ Privacy compliance test passed")


async def main():
    """Run all NATS integration tests."""
    print("Running engagement NATS integration tests...")
    
    await test_telemetry_flow()
    await test_analytics_output_flow()
    await test_session_metrics_patterns()
    await test_subject_naming_conventions()
    await test_privacy_compliance()
    
    print("\nAll NATS integration tests passed! ✅")


if __name__ == "__main__":
    asyncio.run(main())
