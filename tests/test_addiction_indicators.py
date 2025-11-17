"""
Comprehensive unit tests for AddictionIndicatorCalculator.
Tests addiction risk indicators and configurations.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
import asyncio

from services.ethelred_engagement.addiction_indicators import (
    AddictionIndicatorCalculator,
    AddictionIndicatorConfig
)


class TestAddictionIndicatorCalculator:
    """Test suite for AddictionIndicatorCalculator."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization_default(self, mock_postgres_pool):
        """Test calculator initialization with defaults."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        assert calculator.postgres_pool == mock_postgres_pool
        assert calculator.config.night_time_start == 22
        assert calculator.config.night_time_end == 6
        assert calculator.config.excessive_session_hours == 3.0
        assert calculator.config.one_more_run_window_minutes == 5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization_custom_config(self, mock_postgres_pool, addiction_config):
        """Test calculator initialization with custom config."""
        calculator = AddictionIndicatorCalculator(
            mock_postgres_pool,
            config=addiction_config
        )
        
        assert calculator.config == addiction_config
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_night_owl(self, mock_postgres_pool):
        """Test computation for night owl player."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Mock session data - playing from 11 PM to 3 AM
        night_sessions = []
        for i in range(7):  # 7 days
            date = datetime.utcnow() - timedelta(days=i)
            night_sessions.extend([
                {
                    'session_start': date.replace(hour=23, minute=0),
                    'session_end': (date + timedelta(hours=4)).replace(hour=3, minute=0),
                    'duration_minutes': 240
                }
            ])
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = night_sessions
        
        indicators = await calculator.compute_indicators(
            user_ids=['night_owl_1'],
            time_window_days=7
        )
        
        assert 'cohort_size' in indicators
        assert 'night_time_play_ratio' in indicators
        assert 'risk_factors' in indicators
        
        # Should have high night time ratio
        assert indicators['night_time_play_ratio'] > 0.7
        assert 'high_night_play' in indicators['risk_factors']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_one_more_run(self, mock_postgres_pool):
        """Test computation for 'one more run' behavior."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Create session with many quick restarts
        session_start = datetime.utcnow().replace(hour=14, minute=0)
        events = []
        
        # 10 deaths and restarts within 5-minute windows
        for i in range(10):
            death_time = session_start + timedelta(minutes=i*6)
            restart_time = death_time + timedelta(seconds=30)
            
            events.extend([
                {'event_type': 'player_death', 'timestamp': death_time},
                {'event_type': 'game_restart', 'timestamp': restart_time}
            ])
        
        # Mock data
        sessions = [{
            'session_start': session_start,
            'session_end': session_start + timedelta(hours=1),
            'duration_minutes': 60
        }]
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.side_effect = [
            sessions,  # First fetch for sessions
            events     # Second fetch for events
        ]
        
        indicators = await calculator.compute_indicators(
            user_ids=['one_more_player'],
            time_window_days=1
        )
        
        assert 'one_more_run_ratio' in indicators
        assert indicators['one_more_run_ratio'] > 0.5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_excessive_duration(self, mock_postgres_pool):
        """Test computation for excessive session duration."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Create very long sessions
        long_sessions = [
            {
                'session_start': datetime.utcnow().replace(hour=10),
                'session_end': datetime.utcnow().replace(hour=16),  # 6 hours
                'duration_minutes': 360
            },
            {
                'session_start': datetime.utcnow().replace(hour=18),
                'session_end': datetime.utcnow().replace(hour=23),  # 5 hours
                'duration_minutes': 300
            }
        ]
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = long_sessions
        
        indicators = await calculator.compute_indicators(
            user_ids=['marathon_player'],
            time_window_days=1
        )
        
        assert 'avg_session_duration_hours' in indicators
        assert indicators['avg_session_duration_hours'] > 5.0
        assert 'extreme_session_duration' in indicators['risk_factors']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_consecutive_days(self, mock_postgres_pool):
        """Test computation for consecutive days playing."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Create sessions for many consecutive days
        sessions = []
        base_date = datetime.utcnow()
        
        for day in range(20):  # 20 consecutive days
            date = base_date - timedelta(days=day)
            sessions.append({
                'session_start': date.replace(hour=15),
                'session_end': date.replace(hour=17),
                'duration_minutes': 120,
                'date': date.date()
            })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        indicators = await calculator.compute_indicators(
            user_ids=['daily_player'],
            time_window_days=30
        )
        
        assert 'consecutive_days_playing' in indicators
        assert indicators['consecutive_days_playing'] >= 20
        assert 'high_consecutive_days' in indicators['risk_factors']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_healthy_player(self, mock_postgres_pool):
        """Test computation for healthy play patterns."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Moderate sessions every other day
        sessions = []
        base_date = datetime.utcnow()
        
        for day in [0, 2, 4, 6]:  # Every other day
            date = base_date - timedelta(days=day)
            sessions.append({
                'session_start': date.replace(hour=15),
                'session_end': date.replace(hour=16, minute=30),
                'duration_minutes': 90
            })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        indicators = await calculator.compute_indicators(
            user_ids=['healthy_player'],
            time_window_days=7
        )
        
        assert indicators['risk_level'] == 'low'
        assert indicators['night_time_play_ratio'] < 0.1
        assert indicators['avg_session_duration_hours'] < 2.0
        assert len(indicators['risk_factors']) == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_empty_data(self, mock_postgres_pool):
        """Test computation with no session data."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = []
        
        indicators = await calculator.compute_indicators(
            user_ids=['no_data_player'],
            time_window_days=7
        )
        
        assert indicators['cohort_size'] == 0
        assert indicators['night_time_play_ratio'] == 0
        assert indicators['risk_level'] == 'insufficient_data'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_night_time_ratio(self, mock_postgres_pool):
        """Test night time play ratio calculation."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        sessions = [
            # Day session
            {
                'session_start': datetime(2024, 1, 1, 14, 0),
                'session_end': datetime(2024, 1, 1, 16, 0),
                'duration_minutes': 120
            },
            # Night session (10 PM to 2 AM)
            {
                'session_start': datetime(2024, 1, 1, 22, 0),
                'session_end': datetime(2024, 1, 2, 2, 0),
                'duration_minutes': 240
            },
            # Early morning session (4 AM to 6 AM)
            {
                'session_start': datetime(2024, 1, 2, 4, 0),
                'session_end': datetime(2024, 1, 2, 6, 0),
                'duration_minutes': 120
            }
        ]
        
        ratio = calculator._calculate_night_time_ratio(sessions)
        
        # Total: 480 minutes, Night: 360 minutes
        expected_ratio = 360 / 480
        assert abs(ratio - expected_ratio) < 0.01
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calculate_one_more_run_ratio(self, mock_postgres_pool):
        """Test 'one more run' ratio calculation."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Create events with deaths and restarts
        base_time = datetime.utcnow()
        events = [
            # Quick restart (within window)
            {'event_type': 'player_death', 'timestamp': base_time},
            {'event_type': 'game_restart', 'timestamp': base_time + timedelta(minutes=2)},
            
            # Slow restart (outside window)
            {'event_type': 'player_death', 'timestamp': base_time + timedelta(minutes=10)},
            {'event_type': 'game_restart', 'timestamp': base_time + timedelta(minutes=20)},
            
            # Another quick restart
            {'event_type': 'player_death', 'timestamp': base_time + timedelta(minutes=30)},
            {'event_type': 'game_restart', 'timestamp': base_time + timedelta(minutes=31)},
        ]
        
        # Mock the event fetch
        async def mock_fetch_events(user_ids, time_window_days):
            return events
        
        calculator._fetch_session_events = mock_fetch_events
        
        ratio = await calculator._calculate_one_more_run_ratio(['user'], 7)
        
        # 2 quick restarts out of 3 deaths
        expected_ratio = 2 / 3
        assert abs(ratio - expected_ratio) < 0.01
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_determine_risk_level(self, mock_postgres_pool):
        """Test risk level determination."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        test_cases = [
            # (risk_factors, expected_level)
            ([], 'low'),
            (['mild_factor'], 'moderate'),
            (['high_night_play'], 'high'),
            (['extreme_session_duration'], 'high'),
            (['concerning_night_play', 'extreme_one_more_run'], 'extreme'),
            (['extreme_daily_hours', 'high_consecutive_days'], 'extreme'),
        ]
        
        for risk_factors, expected_level in test_cases:
            indicators = {'risk_factors': risk_factors}
            risk_level = calculator._determine_risk_level(indicators)
            assert risk_level == expected_level
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compute_indicators_time_windows(self, mock_postgres_pool):
        """Test computation with different time windows."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Create sessions over 30 days
        sessions = []
        base_date = datetime.utcnow()
        
        for day in range(30):
            date = base_date - timedelta(days=day)
            sessions.append({
                'session_start': date.replace(hour=15),
                'session_end': date.replace(hour=16),
                'duration_minutes': 60
            })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        # Test different windows
        for window_days in [7, 14, 30]:
            indicators = await calculator.compute_indicators(
                user_ids=['test_user'],
                time_window_days=window_days
            )
            
            # Recent sessions should be included based on window
            assert 'total_sessions' in indicators
            # Can't assert exact count without proper date filtering in mock
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_config_threshold_effects(self, mock_postgres_pool):
        """Test how configuration thresholds affect risk assessment."""
        # Strict config
        strict_config = AddictionIndicatorConfig(
            high_night_ratio=0.2,  # Lower threshold
            excessive_session_hours=2.0,  # Lower threshold
            concerning_consecutive_days=5  # Lower threshold
        )
        
        calculator_strict = AddictionIndicatorCalculator(
            mock_postgres_pool,
            config=strict_config
        )
        
        # Lenient config  
        lenient_config = AddictionIndicatorConfig(
            high_night_ratio=0.5,  # Higher threshold
            excessive_session_hours=5.0,  # Higher threshold
            concerning_consecutive_days=14  # Higher threshold
        )
        
        calculator_lenient = AddictionIndicatorCalculator(
            mock_postgres_pool,
            config=lenient_config
        )
        
        # Moderate play data
        sessions = [{
            'session_start': datetime.utcnow().replace(hour=21),
            'session_end': datetime.utcnow().replace(hour=23, minute=30),
            'duration_minutes': 150
        }]
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        # Same data, different risk assessment
        indicators_strict = await calculator_strict.compute_indicators(['user'], 1)
        indicators_lenient = await calculator_lenient.compute_indicators(['user'], 1)
        
        # Strict config should flag more risk factors
        assert len(indicators_strict['risk_factors']) >= len(indicators_lenient['risk_factors'])
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_weekend_ratio_calculation(self, mock_postgres_pool):
        """Test weekend vs weekday ratio calculation."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Create sessions - more on weekends
        sessions = []
        base_date = datetime(2024, 1, 1)  # Monday
        
        for day in range(14):  # 2 weeks
            date = base_date + timedelta(days=day)
            
            # Longer sessions on weekends
            if date.weekday() in [5, 6]:  # Saturday, Sunday
                duration = 180
            else:
                duration = 60
                
            sessions.append({
                'session_start': date.replace(hour=15),
                'session_end': date.replace(hour=15) + timedelta(minutes=duration),
                'duration_minutes': duration
            })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        indicators = await calculator.compute_indicators(['user'], 14)
        
        assert 'weekend_vs_weekday_ratio' in indicators
        # Should show more play on weekends
        assert indicators['weekend_vs_weekday_ratio'] > 1.5
    
    @pytest.mark.unit  
    @pytest.mark.asyncio
    async def test_time_between_sessions(self, mock_postgres_pool):
        """Test calculation of time between sessions."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Sessions with varying gaps
        base_date = datetime.utcnow()
        sessions = [
            {
                'session_start': base_date,
                'session_end': base_date + timedelta(hours=1),
                'duration_minutes': 60
            },
            {
                'session_start': base_date + timedelta(hours=2),  # 1 hour gap
                'session_end': base_date + timedelta(hours=3),
                'duration_minutes': 60
            },
            {
                'session_start': base_date + timedelta(days=1),  # 21 hour gap
                'session_end': base_date + timedelta(days=1, hours=1),
                'duration_minutes': 60
            }
        ]
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        indicators = await calculator.compute_indicators(['user'], 7)
        
        assert 'min_time_between_sessions_hours' in indicators
        assert indicators['min_time_between_sessions_hours'] < 2.0  # 1 hour gap
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_postgres_pool):
        """Test handling of database errors."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Mock database error
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.side_effect = Exception("DB Error")
        
        indicators = await calculator.compute_indicators(['user'], 7)
        
        # Should return safe defaults
        assert indicators['cohort_size'] == 0
        assert indicators['risk_level'] == 'error'
        assert 'error' in indicators
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_large_cohort(self, mock_postgres_pool, performance_timer):
        """Test performance with large user cohort."""
        calculator = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Generate large dataset
        large_sessions = []
        num_users = 1000
        sessions_per_user = 50
        
        for user_id in range(num_users):
            for session in range(sessions_per_user):
                large_sessions.append({
                    'user_id': f'user_{user_id}',
                    'session_start': datetime.utcnow() - timedelta(days=session),
                    'session_end': datetime.utcnow() - timedelta(days=session, hours=-2),
                    'duration_minutes': 120
                })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = large_sessions
        
        user_ids = [f'user_{i}' for i in range(num_users)]
        
        with performance_timer as timer:
            indicators = await calculator.compute_indicators(user_ids, 30)
        
        # Should complete in reasonable time even with large dataset
        assert timer.elapsed < 5.0  # 5 seconds max
        assert indicators['cohort_size'] == num_users
