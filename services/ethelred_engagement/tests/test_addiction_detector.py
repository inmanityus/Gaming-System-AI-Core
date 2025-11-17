"""
Unit tests for addiction risk detector.
Tests TEMO-07, TEMO-08 implementation.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from ..engagement_schemas import (
    AddictionRiskIndicators,
    AddictionRiskReport,
    RiskLevel,
    CohortDefinition
)
from ..addiction_detector import AddictionDetector


class MockPostgresPool:
    """Mock PostgreSQL pool for testing."""
    
    def __init__(self):
        self.test_scenario = 'normal'  # Can be 'normal', 'high_risk', 'critical_risk'
    
    async def acquire(self):
        return MockConnection(self)


class MockConnection:
    """Mock PostgreSQL connection."""
    
    def __init__(self, pool):
        self.pool = pool
    
    async def fetchval(self, query, *args):
        # Mock cohort size
        if "COUNT(DISTINCT e.session_id)" in query and "FROM engagement_events" in query:
            return 150  # Large enough for privacy
        
        # Mock 3 AM session count
        elif "EXTRACT(HOUR FROM e.session_start) BETWEEN 3 AND 5" in query:
            if self.pool.test_scenario == 'critical_risk':
                return 40
            elif self.pool.test_scenario == 'high_risk':
                return 15
            return 5
        
        # Mock total session count
        elif "e.event_type = 'session_metrics'" in query and "COUNT(*)" in query:
            return 100
        
        # Mock long session count (12+ hours)
        elif "e.total_duration_minutes >= 720" in query:
            if self.pool.test_scenario == 'critical_risk':
                return 5
            elif self.pool.test_scenario == 'high_risk':
                return 2
            return 0
        
        return 0
    
    async def fetch(self, query, *args):
        # Mock session data
        if "FROM engagement_events e" in query and "e.event_type = 'session_metrics'" in query:
            if self.pool.test_scenario == 'critical_risk':
                return self._generate_critical_risk_sessions()
            elif self.pool.test_scenario == 'high_risk':
                return self._generate_high_risk_sessions()
            else:
                return self._generate_normal_sessions()
        
        # Mock high reload scenes
        elif "FROM engagement_aggregates" in query and "aggregate_type = 'moral_tension'" in query:
            if self.pool.test_scenario in ['high_risk', 'critical_risk']:
                return [
                    {'scene_id': 'scene-001', 'avg_reloads': 3.5},
                    {'scene_id': 'scene-002', 'avg_reloads': 2.8},
                    {'scene_id': 'scene-003', 'avg_reloads': 2.2}
                ]
            return []
        
        # Mock top NPCs
        elif "FROM engagement_events e" in query and "e.event_type = 'npc_interaction'" in query:
            return [
                {'npc_id': 'npc-romance-001', 'interaction_count': 50},
                {'npc_id': 'npc-quest-001', 'interaction_count': 30},
                {'npc_id': 'npc-merchant-001', 'interaction_count': 20}
            ]
        
        # Mock arc engagement
        elif "e.arc_id IS NOT NULL" in query:
            return [
                {'arc_id': 'arc_vampire', 'event_count': 80},
                {'arc_id': 'arc_flesh_debt', 'event_count': 60}
            ]
        
        return []
    
    def _generate_normal_sessions(self):
        """Generate normal play pattern sessions."""
        sessions = []
        base_time = datetime.now(timezone.utc).replace(hour=19, minute=0)
        
        for i in range(10):
            start = base_time - timedelta(days=i, hours=2)
            end = start + timedelta(hours=2, minutes=30)
            
            sessions.append({
                'total_duration_minutes': 150,
                'time_of_day_bucket': 'evening',
                'day_of_week': (i + 3) % 7,
                'session_start': start,
                'session_end': end,
                'is_return_session': i > 0,
                'time_since_last_session_seconds': 86400 if i > 0 else None
            })
        
        return sessions
    
    def _generate_high_risk_sessions(self):
        """Generate high-risk play pattern sessions."""
        sessions = []
        
        # Late night sessions
        for i in range(5):
            start = datetime.now(timezone.utc).replace(hour=23, minute=0) - timedelta(days=i)
            end = start + timedelta(hours=4)
            
            sessions.append({
                'total_duration_minutes': 240,
                'time_of_day_bucket': 'late_night',
                'day_of_week': (i + 1) % 7,
                'session_start': start,
                'session_end': end,
                'is_return_session': True,
                'time_since_last_session_seconds': 1200  # 20 minutes
            })
        
        # Weekend binges
        for i in range(2):
            start = datetime.now(timezone.utc).replace(hour=10, minute=0) - timedelta(days=i*7)
            end = start + timedelta(hours=8)
            
            sessions.append({
                'total_duration_minutes': 480,
                'time_of_day_bucket': 'morning',
                'day_of_week': 6,  # Saturday
                'session_start': start,
                'session_end': end,
                'is_return_session': False,
                'time_since_last_session_seconds': None
            })
        
        return sessions
    
    def _generate_critical_risk_sessions(self):
        """Generate critical risk play pattern sessions."""
        sessions = []
        
        # 3 AM regular sessions
        for i in range(10):
            start = datetime.now(timezone.utc).replace(hour=3, minute=0) - timedelta(days=i)
            end = start + timedelta(hours=6)
            
            sessions.append({
                'total_duration_minutes': 360,
                'time_of_day_bucket': 'early_morning',
                'day_of_week': i % 7,
                'session_start': start,
                'session_end': end,
                'is_return_session': True,
                'time_since_last_session_seconds': 600  # 10 minutes
            })
        
        # 12+ hour marathon
        start = datetime.now(timezone.utc).replace(hour=18, minute=0) - timedelta(days=2)
        end = start + timedelta(hours=14)
        
        sessions.append({
            'total_duration_minutes': 840,
            'time_of_day_bucket': 'evening',
            'day_of_week': 5,  # Friday
            'session_start': start,
            'session_end': end,
            'is_return_session': False,
            'time_since_last_session_seconds': None
        })
        
        return sessions


@pytest.fixture
def mock_postgres():
    """Create mock PostgreSQL pool."""
    return MockPostgresPool()


@pytest.fixture
def detector(mock_postgres):
    """Create addiction detector with mock database."""
    return AddictionDetector(mock_postgres)


@pytest.mark.asyncio
async def test_assess_normal_cohort(detector, mock_postgres):
    """Test assessment of cohort with normal play patterns."""
    mock_postgres.test_scenario = 'normal'
    
    cohort_def = CohortDefinition(
        cohort_id="NA-18-25-PC",
        region="NA",
        age_band="18-25",
        platform="PC"
    )
    
    report = await detector.assess_cohort_risk(cohort_def, "test-build-001", period_days=7)
    
    assert isinstance(report, AddictionRiskReport)
    assert report.cohort_size == 150
    assert report.overall_risk_level == RiskLevel.LOW
    assert report.risk_indicators.avg_daily_session_hours < 4.0
    assert report.risk_indicators.night_time_play_fraction < 0.2
    assert len(report.risk_indicators.high_risk_patterns) == 0
    assert report.confidence_percentage > 50


@pytest.mark.asyncio
async def test_assess_high_risk_cohort(detector, mock_postgres):
    """Test assessment of cohort with high-risk patterns."""
    mock_postgres.test_scenario = 'high_risk'
    
    cohort_def = CohortDefinition(
        cohort_id="EU-26-35-Console",
        region="EU",
        age_band="26-35",
        platform="Console"
    )
    
    report = await detector.assess_cohort_risk(cohort_def, "test-build-001", period_days=7)
    
    assert report.overall_risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]
    assert report.risk_indicators.avg_daily_session_hours > 4.0
    assert report.risk_indicators.night_time_play_fraction > 0.3
    assert 'compulsive_restart' in report.risk_indicators.high_risk_patterns
    assert len(report.recommendations) > 0
    assert any('break' in rec.lower() for rec in report.recommendations)


@pytest.mark.asyncio
async def test_assess_critical_risk_cohort(detector, mock_postgres):
    """Test assessment of cohort with critical risk patterns."""
    mock_postgres.test_scenario = 'critical_risk'
    
    cohort_def = CohortDefinition(
        cohort_id="APAC-18-25-PC",
        region="APAC",
        age_band="18-25",
        platform="PC"
    )
    
    report = await detector.assess_cohort_risk(cohort_def, "test-build-001", period_days=7)
    
    assert report.overall_risk_level == RiskLevel.CRITICAL
    assert report.risk_indicators.avg_daily_session_hours > 6.0
    assert report.risk_indicators.rapid_session_return_rate > 0.5
    assert '3am_regular' in report.risk_indicators.high_risk_patterns
    assert '12hr_binge' in report.risk_indicators.high_risk_patterns
    assert 'URGENT' in report.recommendations[0]


@pytest.mark.asyncio
async def test_insufficient_cohort_size(detector, mock_postgres):
    """Test handling of cohort too small for privacy protection."""
    # Mock small cohort
    async def mock_fetchval(query, *args):
        if "COUNT(DISTINCT e.session_id)" in query:
            return 50  # Below threshold
        return 0
    
    conn = await mock_postgres.acquire()
    conn.fetchval = mock_fetchval
    
    cohort_def = CohortDefinition(cohort_id="small-cohort")
    report = await detector.assess_cohort_risk(cohort_def, "test-build-001")
    
    assert report.cohort_size == 50
    assert report.overall_risk_level == RiskLevel.LOW
    assert report.confidence_percentage == 0
    assert "Insufficient data" in report.risk_summary
    assert "privacy threshold" in report.notes


@pytest.mark.asyncio
async def test_risk_indicators_calculation(detector):
    """Test calculation of specific risk indicators."""
    indicators = AddictionRiskIndicators(
        avg_daily_session_hours=5.5,
        night_time_play_fraction=0.45,
        rapid_session_return_rate=0.6,
        weekend_spike_ratio=3.5,
        high_risk_patterns=['3am_regular', '12hr_binge'],
        associated_systems=['romance_system']
    )
    
    risk_level = detector._calculate_overall_risk(indicators, ['3am_regular', '12hr_binge'])
    
    assert risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


@pytest.mark.asyncio
async def test_associated_systems_detection(detector, mock_postgres):
    """Test detection of game systems associated with extended play."""
    mock_postgres.test_scenario = 'high_risk'
    
    conn = await mock_postgres.acquire()
    systems = await detector._identify_associated_systems(
        conn, "cohort-001", "build-001",
        datetime.now(timezone.utc), datetime.now(timezone.utc)
    )
    
    assert 'vampire_politics' in systems
    assert 'debt_collection' in systems
    assert len(systems) >= 2


@pytest.mark.asyncio
async def test_risk_summary_generation(detector):
    """Test generation of human-readable risk summaries."""
    indicators = AddictionRiskIndicators(
        avg_daily_session_hours=7.2,
        night_time_play_fraction=0.35,
        rapid_session_return_rate=0.4,
        weekend_spike_ratio=2.5,
        high_risk_patterns=['3am_regular'],
        associated_systems=[]
    )
    
    summary = detector._generate_risk_summary(
        indicators, ['3am_regular'], RiskLevel.HIGH
    )
    
    assert "HIGH" in summary
    assert "7.2 hours daily" in summary
    assert "35% of sessions" in summary
    assert "Regular play during 3-5 AM" in summary

