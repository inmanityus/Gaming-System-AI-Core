"""
Tests for Drift Detection.
"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from ..story_schemas import DriftType, DriftSeverity, DriftMetrics
from ..drift_detector import DriftDetector
from ..story_state_manager import StoryStateManager


class MockNATSClient:
    """Mock NATS client."""
    
    def __init__(self):
        self.published = []
    
    async def publish(self, subject, data):
        self.published.append((subject, data))
    
    async def subscribe(self, subject, callback):
        pass


class MockPostgresPool:
    """Mock PostgreSQL pool."""
    
    def __init__(self):
        self.data = {}
    
    async def acquire(self):
        return MockConnection()


class MockConnection:
    """Mock database connection."""
    
    async def fetch(self, query, *args):
        # Return mock quest data showing too many tangential quests
        if "quest_completed" in query:
            return [
                {'quest_type': 'main_story', 'count': 2},
                {'quest_type': 'side_quest', 'count': 3},
                {'quest_type': 'tangential', 'count': 5}  # 50% tangential!
            ]
        # Return mock activity data showing too much racing
        elif "activity_logged" in query:
            return [
                {'activity': 'body_harvesting', 'count': 2},
                {'activity': 'negotiation', 'count': 1},
                {'activity': 'racing', 'count': 4},  # 57% racing!
                {'activity': 'combat', 'count': 0}
            ]
        return []
    
    async def execute(self, query, *args):
        pass


@pytest.mark.asyncio
async def test_quest_allocation_drift():
    """Test detection of quest allocation drift."""
    nats = MockNATSClient()
    pool = MockPostgresPool()
    manager = StoryStateManager(pool)
    detector = DriftDetector(nats, manager, pool)
    
    player_id = uuid4()
    metrics = await detector.check_drift(player_id, window_hours=3)
    
    assert metrics is not None
    assert metrics.drift_score > 0.3  # Tangential threshold
    assert metrics.severity in [DriftSeverity.MODERATE, DriftSeverity.MAJOR]
    assert metrics.quest_allocation is not None
    assert metrics.quest_allocation['tangential'] == 0.5  # 50% tangential
    assert "main story quest" in metrics.recommended_correction


@pytest.mark.asyncio
async def test_time_allocation_drift():
    """Test detection of time allocation drift."""
    nats = MockNATSClient()
    pool = MockPostgresPool()
    manager = StoryStateManager(pool)
    detector = DriftDetector(nats, manager, pool)
    
    player_id = uuid4()
    metrics = await detector.check_drift(player_id, window_hours=3)
    
    assert metrics is not None
    assert metrics.time_allocation is not None
    assert metrics.time_allocation['racing'] > 0.5  # Too much racing
    assert "racing" in metrics.recommended_correction.lower()


@pytest.mark.asyncio
async def test_no_drift_detected():
    """Test when no drift is detected."""
    # Mock pool that returns balanced activities
    class BalancedPool(MockPostgresPool):
        async def acquire(self):
            class BalancedConnection(MockConnection):
                async def fetch(self, query, *args):
                    if "quest_completed" in query:
                        return [
                            {'quest_type': 'main_story', 'count': 5},
                            {'quest_type': 'side_quest', 'count': 3},
                            {'quest_type': 'tangential', 'count': 1}
                        ]
                    return []
            return BalancedConnection()
    
    nats = MockNATSClient()
    pool = BalancedPool()
    manager = StoryStateManager(pool)
    detector = DriftDetector(nats, manager, pool)
    
    player_id = uuid4()
    metrics = await detector.check_drift(player_id, window_hours=3)
    
    assert metrics is None


def test_drift_severity_calculation():
    """Test severity calculation based on threshold exceedance."""
    detector = DriftDetector(None, None, None)
    
    # Just over threshold = minor
    assert detector._calculate_severity(0.35, 0.3) == DriftSeverity.MINOR
    
    # 1.5x threshold = moderate  
    assert detector._calculate_severity(0.45, 0.3) == DriftSeverity.MODERATE
    
    # 2x threshold = major
    assert detector._calculate_severity(0.6, 0.3) == DriftSeverity.MAJOR


def test_drift_metrics_model():
    """Test DriftMetrics model."""
    metrics = DriftMetrics(
        drift_type=DriftType.QUEST_ALLOCATION,
        severity=DriftSeverity.MODERATE,
        drift_score=0.45,
        quest_allocation={
            'main_story': 0.2,
            'side_quest': 0.35,
            'tangential': 0.45
        }
    )
    
    assert metrics.drift_type == DriftType.QUEST_ALLOCATION
    assert metrics.severity == DriftSeverity.MODERATE
    assert 0.0 <= metrics.drift_score <= 1.0
