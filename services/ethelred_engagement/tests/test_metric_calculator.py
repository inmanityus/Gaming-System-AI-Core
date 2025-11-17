"""
Unit tests for engagement metric calculator.
Tests TEMO-04, TEMO-05, TEMO-06 implementation.
"""
import pytest
import json
from datetime import datetime, timezone
from uuid import uuid4

from ..engagement_schemas import (
    NPCAttachmentMetrics,
    MoralTensionMetrics,
    EngagementProfile,
    InteractionType,
    HelpHarmFlag
)
from ..metric_calculator import MetricCalculator


class MockPostgresPool:
    """Mock PostgreSQL pool for testing."""
    
    def __init__(self):
        self.test_data = {
            'npc_interactions': [],
            'moral_choices': [],
            'engagement_profiles': [
                {
                    'profile_id': 'prof-001',
                    'profile_name': 'lore-driven explorer',
                    'example_behaviors': ['reads all books', 'exhausts dialogue trees']
                }
            ]
        }
    
    async def acquire(self):
        return MockConnection(self)


class MockConnection:
    """Mock PostgreSQL connection."""
    
    def __init__(self, pool):
        self.pool = pool
    
    async def fetch(self, query, *args):
        # Mock NPC interaction queries
        if "e.event_type = 'npc_interaction'" in query and "GROUP BY e.interaction_type" in query:
            return [
                {'interaction_type': 'dialogue', 'help_harm_flag': 'neutral', 'count': 25},
                {'interaction_type': 'gift', 'help_harm_flag': 'helpful', 'count': 10},
                {'interaction_type': 'assist', 'help_harm_flag': 'helpful', 'count': 5},
                {'interaction_type': 'ignore', 'help_harm_flag': 'neutral', 'count': 2}
            ]
        
        # Mock moral choice queries  
        elif "e.event_type = 'moral_choice'" in query:
            return [
                {
                    'selected_option_id': 'save',
                    'decision_latency_ms': 12000,
                    'num_retries': 0,
                    'reloaded_save': False,
                    'options': json.dumps([
                        {'option_id': 'save', 'option_label': 'Save', 'tags': ['good']},
                        {'option_id': 'ignore', 'option_label': 'Ignore', 'tags': ['neutral']},
                        {'option_id': 'exploit', 'option_label': 'Exploit', 'tags': ['evil']}
                    ])
                },
                {
                    'selected_option_id': 'save',
                    'decision_latency_ms': 8000,
                    'num_retries': 1,
                    'reloaded_save': True,
                    'options': json.dumps([
                        {'option_id': 'save', 'option_label': 'Save', 'tags': ['good']},
                        {'option_id': 'ignore', 'option_label': 'Ignore', 'tags': ['neutral']},
                        {'option_id': 'exploit', 'option_label': 'Exploit', 'tags': ['evil']}
                    ])
                },
                {
                    'selected_option_id': 'ignore',
                    'decision_latency_ms': 5000,
                    'num_retries': 0,
                    'reloaded_save': False,
                    'options': json.dumps([
                        {'option_id': 'save', 'option_label': 'Save', 'tags': ['good']},
                        {'option_id': 'ignore', 'option_label': 'Ignore', 'tags': ['neutral']},
                        {'option_id': 'exploit', 'option_label': 'Exploit', 'tags': ['evil']}
                    ])
                }
            ]
        
        # Mock dialogue stats for behavioral metrics
        elif "COUNT(DISTINCT npc_id) as npcs_talked_to" in query:
            return [{
                'npcs_talked_to': 15,
                'dialogue_count': 120,
                'ignore_count': 10
            }]
        
        # Mock session count
        elif "COUNT(DISTINCT e.session_id)" in query:
            return [{'count': 10}]
        
        # Mock gift count
        elif "e.interaction_type = 'gift'" in query:
            return [{'count': 8}]
        
        # Mock profile definition
        elif "FROM engagement_profile_definitions" in query:
            return [{
                'profile_id': 'prof-001',
                'profile_name': 'lore-driven explorer',
                'example_behaviors': ['reads all books', 'exhausts dialogue trees']
            }]
        
        return []
    
    async def fetchrow(self, query, *args):
        # Mock proximity time calculation
        if "SUM(" in query and "total_proximity_seconds" in query:
            return {'total_proximity_seconds': 4200}  # 70 minutes total
        
        # Mock profile definition
        elif "FROM engagement_profile_definitions" in query:
            return {
                'profile_id': 'prof-001',
                'profile_name': 'lore-driven explorer',
                'example_behaviors': ['reads all books', 'exhausts dialogue trees']
            }
        
        # Mock dialogue stats
        elif "COUNT(DISTINCT npc_id) as npcs_talked_to" in query:
            return {
                'npcs_talked_to': 15,
                'dialogue_count': 120,
                'ignore_count': 10
            }
        
        return None
    
    async def fetchval(self, query, *args):
        # Mock session count
        if "COUNT(DISTINCT e.session_id)" in query:
            return 10
            
        # Mock gift count
        elif "COUNT(*)" in query and "e.interaction_type = 'gift'" in query:
            return 8
            
        # Mock moral choices with extreme tags
        elif "e.event_type = 'moral_choice'" in query:
            return 25
            
        return 0
    
    async def execute(self, query, *args):
        # Mock storing aggregates
        pass


@pytest.fixture
def mock_postgres():
    """Create mock PostgreSQL pool."""
    return MockPostgresPool()


@pytest.fixture
def calculator(mock_postgres):
    """Create metric calculator with mock database."""
    return MetricCalculator(mock_postgres)


@pytest.mark.asyncio
async def test_calculate_npc_attachment(calculator):
    """Test NPC attachment metric calculation."""
    cohort_id = "NA-18-25-PC"
    npc_id = "npc-vampire-001"
    build_id = "test-build-001"
    period_start = datetime.now(timezone.utc)
    period_end = datetime.now(timezone.utc)
    
    metrics = await calculator.calculate_npc_attachment(
        cohort_id, npc_id, build_id, period_start, period_end
    )
    
    assert isinstance(metrics, NPCAttachmentMetrics)
    assert metrics.npc_id == npc_id
    assert metrics.total_interactions == 42  # 25+10+5+2
    assert metrics.helpful_actions == 15  # 10+5
    assert metrics.harmful_actions == 0
    assert metrics.neutral_actions == 27  # 25+2
    assert metrics.protection_harm_ratio == 15.0  # No harm, so just helpful count
    assert metrics.abandonment_frequency == pytest.approx(0.048, rel=1e-2)  # 2/42
    assert metrics.attention_score > 0.5  # Good diversity and frequency
    assert metrics.total_proximity_time_seconds == 4200


@pytest.mark.asyncio
async def test_calculate_npc_attachment_no_interactions(calculator):
    """Test NPC attachment with no interactions."""
    # Mock empty results
    async def mock_fetch_empty(query, *args):
        return []
    
    async def mock_fetchrow_empty(query, *args):
        if "total_proximity_seconds" in query:
            return {'total_proximity_seconds': 0}
        return None
    
    # Patch the connection
    conn = await calculator.postgres.acquire()
    conn.fetch = mock_fetch_empty
    conn.fetchrow = mock_fetchrow_empty
    
    metrics = await calculator.calculate_npc_attachment(
        "cohort-001", "npc-001", "build-001",
        datetime.now(timezone.utc), datetime.now(timezone.utc)
    )
    
    assert metrics.total_interactions == 0
    assert metrics.protection_harm_ratio == 0.0
    assert metrics.attention_score == 0.0


@pytest.mark.asyncio
async def test_calculate_moral_tension(calculator):
    """Test moral tension metric calculation."""
    cohort_id = "NA-18-25-PC"
    scene_id = "scene-moral-crossroads"
    build_id = "test-build-001"
    period_start = datetime.now(timezone.utc)
    period_end = datetime.now(timezone.utc)
    
    metrics = await calculator.calculate_moral_tension(
        cohort_id, scene_id, build_id, period_start, period_end
    )
    
    assert isinstance(metrics, MoralTensionMetrics)
    assert metrics.scene_id == scene_id
    assert metrics.total_choices == 3
    assert metrics.avg_decision_latency_seconds == pytest.approx(8.33, rel=0.1)  # (12+8+5)/3
    assert metrics.reload_count == 1
    assert metrics.option_counts['save'] == 2
    assert metrics.option_counts['ignore'] == 1
    
    # Check tension index calculation
    assert 0 <= metrics.tension_index <= 1
    assert metrics.choice_distribution_entropy > 0  # Some entropy due to split choices


@pytest.mark.asyncio 
async def test_detect_engagement_profile(calculator):
    """Test engagement profile detection."""
    cohort_id = "NA-18-25-PC"
    build_id = "test-build-001"
    period_start = datetime.now(timezone.utc)
    period_end = datetime.now(timezone.utc)
    
    profile = await calculator.detect_engagement_profile(
        cohort_id, build_id, period_start, period_end
    )
    
    assert isinstance(profile, EngagementProfile)
    assert profile.profile_name == 'lore-driven explorer'
    assert profile.profile_id == 'prof-001'
    assert profile.profile_confidence > 0.5
    assert len(profile.characteristic_behaviors) == 2


@pytest.mark.asyncio
async def test_behavioral_metrics_calculation(calculator):
    """Test calculation of behavioral metrics for profile detection."""
    conn = await calculator.postgres.acquire()
    
    metrics = await calculator._calculate_behavioral_metrics(
        conn, "cohort-001", "build-001",
        datetime.now(timezone.utc), datetime.now(timezone.utc)
    )
    
    assert 'dialogue_completion' in metrics
    assert metrics['dialogue_completion'] == pytest.approx(0.923, rel=0.01)  # 120/(120+10)
    assert metrics['dialogue_skip_rate'] == pytest.approx(0.077, rel=0.01)
    assert metrics['npc_interaction_rate'] == 1.5  # 15 NPCs / 10 sessions
    assert metrics['gift_giving_rate'] == pytest.approx(0.533, rel=0.01)  # 8/15


@pytest.mark.asyncio
async def test_moral_tension_no_choices(calculator):
    """Test moral tension with no choices made."""
    # Mock empty results
    async def mock_fetch_empty(query, *args):
        if "e.event_type = 'moral_choice'" in query:
            return []
        return []
    
    conn = await calculator.postgres.acquire()
    conn.fetch = mock_fetch_empty
    
    metrics = await calculator.calculate_moral_tension(
        "cohort-001", "scene-001", "build-001",
        datetime.now(timezone.utc), datetime.now(timezone.utc)
    )
    
    assert metrics.total_choices == 0
    assert metrics.tension_index == 0.0
    assert metrics.choice_distribution_entropy == 0.0
    assert len(metrics.option_counts) == 0

