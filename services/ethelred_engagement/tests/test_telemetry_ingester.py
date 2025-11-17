"""
Unit tests for telemetry ingester.
Tests TEMO-03 implementation.
"""
import pytest
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from ..engagement_schemas import (
    NPCInteractionEvent,
    MoralChoiceEvent,
    MoralChoiceOption,
    SessionMetricsEvent,
    ActorType,
    EventType,
    InteractionType,
    HelpHarmFlag,
    TimeOfDayBucket
)
from ..telemetry_ingester import TelemetryIngester


class MockPostgresPool:
    """Mock PostgreSQL pool for testing."""
    
    def __init__(self):
        self.events = []
        self.cohorts = {}
    
    async def acquire(self):
        return MockConnection(self)


class MockConnection:
    """Mock PostgreSQL connection."""
    
    def __init__(self, pool):
        self.pool = pool
        self._transaction = None
    
    async def execute(self, query, *args):
        # Store events for verification
        if "INSERT INTO engagement_events" in query:
            event_data = {
                'session_id': args[0],
                'player_id': args[1],
                'actor_type': args[2],
                'event_type': args[3],
                'timestamp': args[4]
            }
            if args[3] == 'npc_interaction':
                event_data['npc_id'] = args[7]
                event_data['interaction_type'] = args[8]
            elif args[3] == 'moral_choice':
                event_data['scene_id'] = args[7]
                event_data['selected_option_id'] = args[9]
            self.pool.events.append(event_data)
        
        # Store cohort assignments
        elif "INSERT INTO session_cohorts" in query:
            self.pool.cohorts[str(args[0])] = {
                'cohort_id': args[1],
                'region': args[2],
                'age_band': args[3],
                'platform': args[4]
            }
    
    def transaction(self):
        return MockTransaction()


class MockTransaction:
    """Mock transaction context manager."""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.fixture
def mock_postgres():
    """Create mock PostgreSQL pool."""
    return MockPostgresPool()


@pytest.fixture  
def ingester(mock_postgres):
    """Create telemetry ingester with mock database."""
    return TelemetryIngester(mock_postgres)


@pytest.mark.asyncio
async def test_ingest_npc_interaction_event(ingester, mock_postgres):
    """Test ingesting an NPC interaction event."""
    event_data = {
        'event_type': 'npc_interaction',
        'session_id': str(uuid4()),
        'player_id': str(uuid4()),
        'actor_type': 'real_player',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'build_id': 'test-build-001',
        'npc_id': 'npc-vampire-001',
        'interaction_type': 'dialogue',
        'choice_id': 'choice-001',
        'choice_label': 'Ask about the blood debt',
        'help_harm_flag': 'neutral'
    }
    
    success = await ingester.ingest_event(event_data)
    
    assert success is True
    assert len(ingester._event_buffer) == 1
    
    # Verify parsed event
    event = ingester._event_buffer[0]
    assert isinstance(event, NPCInteractionEvent)
    assert event.npc_id == 'npc-vampire-001'
    assert event.interaction_type == InteractionType.DIALOGUE
    assert event.help_harm_flag == HelpHarmFlag.NEUTRAL


@pytest.mark.asyncio
async def test_ingest_moral_choice_event(ingester):
    """Test ingesting a moral choice event."""
    event_data = {
        'event_type': 'moral_choice',
        'session_id': str(uuid4()),
        'player_id': str(uuid4()),
        'actor_type': 'real_player',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'build_id': 'test-build-001',
        'scene_id': 'scene-moral-001',
        'options': [
            {'option_id': 'save', 'option_label': 'Save the child', 'tags': ['good', 'selfless']},
            {'option_id': 'ignore', 'option_label': 'Walk away', 'tags': ['neutral', 'pragmatic']},
            {'option_id': 'exploit', 'option_label': 'Use the situation', 'tags': ['evil', 'selfish']}
        ],
        'selected_option_id': 'save',
        'decision_latency_ms': 8500,
        'num_retries': 0,
        'reloaded_save': False
    }
    
    success = await ingester.ingest_event(event_data)
    
    assert success is True
    assert len(ingester._event_buffer) == 1
    
    event = ingester._event_buffer[0]
    assert isinstance(event, MoralChoiceEvent)
    assert event.scene_id == 'scene-moral-001'
    assert len(event.options) == 3
    assert event.selected_option_id == 'save'
    assert event.decision_latency_ms == 8500


@pytest.mark.asyncio
async def test_ingest_session_metrics_event(ingester):
    """Test ingesting a session metrics event."""
    session_start = datetime.now(timezone.utc).replace(hour=14, minute=0)
    session_end = session_start.replace(hour=16, minute=30)
    
    event_data = {
        'event_type': 'session_metrics',
        'session_id': str(uuid4()),
        'player_id': str(uuid4()),
        'actor_type': 'real_player',
        'timestamp': session_end.isoformat(),
        'build_id': 'test-build-001',
        'session_start': session_start.isoformat(),
        'session_end': session_end.isoformat(),
        'total_duration_minutes': 150,
        'day_of_week': 3,  # Wednesday
        'num_sessions_last_7_days': 12,
        'num_sessions_last_24_hours': 2,
        'is_return_session': True,
        'time_since_last_session_seconds': 7200,
        'platform': 'PC',
        'region': 'NA'
    }
    
    success = await ingester.ingest_event(event_data)
    
    assert success is True
    assert len(ingester._event_buffer) == 1
    
    event = ingester._event_buffer[0]
    assert isinstance(event, SessionMetricsEvent)
    assert event.total_duration_minutes == 150
    assert event.time_of_day_bucket == TimeOfDayBucket.AFTERNOON
    assert event.is_return_session is True


@pytest.mark.asyncio
async def test_calculate_time_bucket(ingester):
    """Test time of day bucket calculation."""
    
    # Test early morning (2 AM)
    timestamp = datetime.now(timezone.utc).replace(hour=2, minute=0)
    bucket = ingester._calculate_time_bucket(timestamp)
    assert bucket == TimeOfDayBucket.EARLY_MORNING.value
    
    # Test morning (8 AM)
    timestamp = datetime.now(timezone.utc).replace(hour=8, minute=0)
    bucket = ingester._calculate_time_bucket(timestamp)
    assert bucket == TimeOfDayBucket.MORNING.value
    
    # Test afternoon (3 PM)
    timestamp = datetime.now(timezone.utc).replace(hour=15, minute=0)
    bucket = ingester._calculate_time_bucket(timestamp)
    assert bucket == TimeOfDayBucket.AFTERNOON.value
    
    # Test evening (8 PM)
    timestamp = datetime.now(timezone.utc).replace(hour=20, minute=0)
    bucket = ingester._calculate_time_bucket(timestamp)
    assert bucket == TimeOfDayBucket.EVENING.value
    
    # Test late night (11 PM)
    timestamp = datetime.now(timezone.utc).replace(hour=23, minute=0)
    bucket = ingester._calculate_time_bucket(timestamp)
    assert bucket == TimeOfDayBucket.LATE_NIGHT.value


@pytest.mark.asyncio
async def test_buffer_flush(ingester, mock_postgres):
    """Test event buffer flushing."""
    # Add events to fill buffer
    for i in range(5):
        event_data = {
            'event_type': 'npc_interaction',
            'session_id': str(uuid4()),
            'actor_type': 'real_player',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'build_id': 'test-build-001',
            'npc_id': f'npc-{i}',
            'interaction_type': 'dialogue',
            'help_harm_flag': 'neutral'
        }
        await ingester.ingest_event(event_data)
    
    assert len(ingester._event_buffer) == 5
    
    # Flush buffer
    await ingester._flush_buffer()
    
    # Verify buffer is empty and events were stored
    assert len(ingester._event_buffer) == 0
    assert len(mock_postgres.events) == 5
    
    # Verify event counts
    assert ingester._event_counts['npc_interaction'] == 5


@pytest.mark.asyncio
async def test_invalid_event_handling(ingester):
    """Test handling of invalid events."""
    # Missing required field
    event_data = {
        'event_type': 'npc_interaction',
        'session_id': str(uuid4()),
        'actor_type': 'real_player',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'build_id': 'test-build-001'
        # Missing npc_id
    }
    
    success = await ingester.ingest_event(event_data)
    assert success is False
    assert len(ingester._event_buffer) == 0
    
    # Invalid event type
    event_data = {
        'event_type': 'unknown_type',
        'session_id': str(uuid4()),
        'actor_type': 'real_player',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'build_id': 'test-build-001'
    }
    
    success = await ingester.ingest_event(event_data)
    assert success is False
    
    # Invalid moral choice (only 1 option)
    event_data = {
        'event_type': 'moral_choice',
        'session_id': str(uuid4()),
        'actor_type': 'real_player',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'build_id': 'test-build-001',
        'scene_id': 'scene-001',
        'options': [
            {'option_id': 'only', 'option_label': 'Only choice', 'tags': []}
        ],
        'selected_option_id': 'only',
        'decision_latency_ms': 1000
    }
    
    success = await ingester.ingest_event(event_data)
    assert success is False

