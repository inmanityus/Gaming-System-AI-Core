"""
Database integration tests for engagement analytics services.
Tests real PostgreSQL interactions using testcontainers.
"""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.ethelred_engagement.addiction_indicators import (
    AddictionIndicatorAnalyzer, AddictionIndicatorConfig
)
from services.ethelred_engagement.safety_constraints import (
    SafetyConstraintValidator, SafetyConstraintsConfig
)


@pytest.mark.integration
class TestEngagementDatabase:
    """Test engagement analytics with real database."""
    
    async def test_save_engagement_session(self, postgres_pool):
        """Test saving engagement session data."""
        # Create analyzer
        config = AddictionIndicatorConfig()
        analyzer = AddictionIndicatorAnalyzer(
            config=config,
            db_pool=postgres_pool
        )
        
        # Create session data
        session_data = {
            'user_id': 'engagement_test_user',
            'session_start': datetime.now(timezone.utc) - timedelta(hours=3),
            'session_end': datetime.now(timezone.utc),
            'events': [
                {'type': 'game_start', 'timestamp': datetime.now(timezone.utc) - timedelta(hours=3)},
                {'type': 'level_complete', 'timestamp': datetime.now(timezone.utc) - timedelta(hours=2)},
                {'type': 'death', 'timestamp': datetime.now(timezone.utc) - timedelta(hours=1)},
                {'type': 'game_end', 'timestamp': datetime.now(timezone.utc)}
            ]
        }
        
        # Analyze session
        indicators = analyzer.analyze_session(session_data)
        
        # Save to database
        async with postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ethelred.engagement_sessions
                (user_id, session_start, session_end, duration_minutes,
                 is_night_session, is_early_morning, events, addiction_indicators)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            session_data['user_id'],
            session_data['session_start'],
            session_data['session_end'],
            int((session_data['session_end'] - session_data['session_start']).total_seconds() / 60),
            indicators.get('night_session', False),
            indicators.get('early_morning_session', False),
            json.dumps([{**e, 'timestamp': e['timestamp'].isoformat()} for e in session_data['events']]),
            json.dumps(indicators)
            )
        
        # Verify saved
        async with postgres_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM ethelred.engagement_sessions
                WHERE user_id = $1
                ORDER BY session_start DESC
                LIMIT 1
            """, 'engagement_test_user')
        
        assert row is not None
        assert row['duration_minutes'] == 180  # 3 hours
        assert row['addiction_indicators'] is not None
    
    async def test_query_user_engagement_history(self, postgres_pool, sample_engagement_data):
        """Test querying user's engagement history."""
        async with postgres_pool.acquire() as conn:
            # Get recent sessions
            rows = await conn.fetch("""
                SELECT * FROM ethelred.engagement_sessions
                WHERE user_id = $1
                ORDER BY session_start DESC
            """, 'test_user_1')
            
            assert len(rows) > 0
            assert rows[0]['is_night_session'] is True
            assert rows[0]['duration_minutes'] == 240
            
            # Calculate total playtime
            total_minutes = await conn.fetchval("""
                SELECT SUM(duration_minutes) 
                FROM ethelred.engagement_sessions
                WHERE user_id = $1
            """, 'test_user_1')
            
            assert total_minutes == 240
    
    async def test_addiction_pattern_detection(self, postgres_pool):
        """Test detecting addiction patterns from database."""
        # Insert pattern data
        base_time = datetime.now(timezone.utc)
        sessions = []
        
        # Create pattern: daily night sessions for a week
        for day in range(7):
            session_time = base_time - timedelta(days=day, hours=2)  # 10 PM each day
            sessions.append({
                'user_id': 'pattern_test_user',
                'session_start': session_time,
                'session_end': session_time + timedelta(hours=4),
                'duration_minutes': 240,
                'is_night_session': True,
                'is_early_morning': True,  # Extends past 2 AM
                'events': json.dumps([
                    {'type': 'game_start', 'timestamp': session_time.isoformat()},
                    {'type': 'game_end', 'timestamp': (session_time + timedelta(hours=4)).isoformat()}
                ])
            })
        
        # Bulk insert
        async with postgres_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO ethelred.engagement_sessions
                (user_id, session_start, session_end, duration_minutes,
                 is_night_session, is_early_morning, events)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, [
                (s['user_id'], s['session_start'], s['session_end'],
                 s['duration_minutes'], s['is_night_session'],
                 s['is_early_morning'], s['events'])
                for s in sessions
            ])
        
        # Analyze patterns
        async with postgres_pool.acquire() as conn:
            # Consecutive days played
            consecutive_days = await conn.fetchval("""
                WITH daily_sessions AS (
                    SELECT 
                        user_id,
                        DATE(session_start) as play_date,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY DATE(session_start)) as rn
                    FROM ethelred.engagement_sessions
                    WHERE user_id = $1
                    GROUP BY user_id, DATE(session_start)
                )
                SELECT COUNT(*) as consecutive_days
                FROM daily_sessions
                WHERE play_date >= CURRENT_DATE - INTERVAL '7 days'
            """, 'pattern_test_user')
            
            assert consecutive_days >= 7
            
            # Night session ratio
            night_ratio = await conn.fetchval("""
                SELECT 
                    CAST(SUM(CASE WHEN is_night_session THEN 1 ELSE 0 END) AS FLOAT) / 
                    NULLIF(COUNT(*), 0) as night_ratio
                FROM ethelred.engagement_sessions
                WHERE user_id = $1
                AND session_start >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            """, 'pattern_test_user')
            
            assert night_ratio == 1.0  # All sessions are night sessions
    
    async def test_cohort_analysis(self, postgres_pool):
        """Test cohort-based analysis."""
        # Insert cohort data
        users = []
        base_time = datetime.now(timezone.utc)
        
        # Create 150 users with varying patterns
        for i in range(150):
            user_id = f'cohort_user_{i}'
            # Half are night players, half are day players
            is_night = i < 75
            
            session_start = base_time - timedelta(
                hours=3 if is_night else 15,  # Night: 9 PM, Day: 9 AM
                days=i % 7
            )
            
            users.append({
                'user_id': user_id,
                'session_start': session_start,
                'session_end': session_start + timedelta(hours=2),
                'duration_minutes': 120,
                'is_night_session': is_night,
                'is_early_morning': False,
                'events': json.dumps([
                    {'type': 'game_start', 'timestamp': session_start.isoformat()}
                ])
            })
        
        # Bulk insert
        async with postgres_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO ethelred.engagement_sessions
                (user_id, session_start, session_end, duration_minutes,
                 is_night_session, is_early_morning, events)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, [
                (u['user_id'], u['session_start'], u['session_end'],
                 u['duration_minutes'], u['is_night_session'],
                 u['is_early_morning'], u['events'])
                for u in users
            ])
        
        # Analyze cohort
        config = SafetyConstraintsConfig(min_cohort_size=100)
        validator = SafetyConstraintValidator(config, db_pool=postgres_pool)
        
        # Get cohort stats
        async with postgres_pool.acquire() as conn:
            cohort_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT user_id) as cohort_size,
                    AVG(duration_minutes) as avg_duration,
                    SUM(CASE WHEN is_night_session THEN 1 ELSE 0 END) as night_sessions,
                    COUNT(*) as total_sessions
                FROM ethelred.engagement_sessions
                WHERE user_id LIKE 'cohort_user_%'
            """)
        
        assert cohort_stats['cohort_size'] >= config.min_cohort_size
        assert cohort_stats['night_sessions'] == 75  # Half are night sessions
    
    async def test_time_series_queries(self, postgres_pool):
        """Test time-series engagement queries."""
        # Insert time series data
        base_time = datetime.now(timezone.utc)
        
        async with postgres_pool.acquire() as conn:
            for hour in range(24):
                timestamp = base_time - timedelta(hours=hour)
                await conn.execute("""
                    INSERT INTO ethelred.engagement_sessions
                    (user_id, session_start, session_end, duration_minutes)
                    VALUES ($1, $2, $3, $4)
                """,
                f'timeseries_user_{hour % 5}',  # 5 different users
                timestamp,
                timestamp + timedelta(minutes=30),
                30
                )
        
        # Query hourly engagement
        async with postgres_pool.acquire() as conn:
            hourly_stats = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('hour', session_start) as hour,
                    COUNT(*) as sessions,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(duration_minutes) as avg_duration
                FROM ethelred.engagement_sessions
                WHERE session_start >= $1
                GROUP BY DATE_TRUNC('hour', session_start)
                ORDER BY hour DESC
            """, base_time - timedelta(days=1))
        
        assert len(hourly_stats) >= 24
        
        # Peak hours analysis
        peak_hour = await conn.fetchrow("""
            SELECT 
                EXTRACT(HOUR FROM session_start) as hour,
                COUNT(*) as session_count
            FROM ethelred.engagement_sessions
            WHERE session_start >= $1
            GROUP BY EXTRACT(HOUR FROM session_start)
            ORDER BY session_count DESC
            LIMIT 1
        """, base_time - timedelta(days=1))
        
        assert peak_hour is not None
    
    async def test_concurrent_session_updates(self, postgres_pool):
        """Test handling concurrent session updates."""
        user_id = 'concurrent_test_user'
        base_time = datetime.now(timezone.utc)
        
        # Function to insert a session
        async def insert_session(session_num):
            async with postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ethelred.engagement_sessions
                    (user_id, session_start, session_end, duration_minutes)
                    VALUES ($1, $2, $3, $4)
                """,
                user_id,
                base_time - timedelta(hours=session_num),
                base_time - timedelta(hours=session_num - 1),
                60
                )
        
        # Run concurrent inserts
        tasks = [insert_session(i) for i in range(20)]
        await asyncio.gather(*tasks)
        
        # Verify all inserted
        async with postgres_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM ethelred.engagement_sessions
                WHERE user_id = $1
            """, user_id)
        
        assert count == 20
    
    async def test_json_event_queries(self, postgres_pool):
        """Test querying JSON event data."""
        # Insert session with complex events
        events = [
            {'type': 'game_start', 'timestamp': '2024-11-20T10:00:00Z'},
            {'type': 'level_complete', 'level': 1, 'score': 1000, 'timestamp': '2024-11-20T10:30:00Z'},
            {'type': 'achievement_unlock', 'achievement': 'First Blood', 'timestamp': '2024-11-20T10:35:00Z'},
            {'type': 'death', 'cause': 'vampire_bite', 'location': 'dark_alley', 'timestamp': '2024-11-20T10:40:00Z'},
            {'type': 'level_complete', 'level': 2, 'score': 2500, 'timestamp': '2024-11-20T11:00:00Z'},
            {'type': 'game_end', 'reason': 'voluntary', 'timestamp': '2024-11-20T11:30:00Z'}
        ]
        
        async with postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ethelred.engagement_sessions
                (user_id, session_start, session_end, events)
                VALUES ($1, $2, $3, $4)
            """,
            'json_test_user',
            datetime(2024, 11, 20, 10, 0, tzinfo=timezone.utc),
            datetime(2024, 11, 20, 11, 30, tzinfo=timezone.utc),
            json.dumps(events)
            )
            
            # Query specific event types
            death_sessions = await conn.fetch("""
                SELECT user_id, events
                FROM ethelred.engagement_sessions
                WHERE user_id = 'json_test_user'
                AND events @> '[{"type": "death"}]'
            """)
            
            assert len(death_sessions) == 1
            
            # Extract level completions
            level_completions = await conn.fetchval("""
                SELECT jsonb_array_length(
                    jsonb_path_query_array(
                        events::jsonb,
                        '$[*] ? (@.type == "level_complete")'
                    )
                )
                FROM ethelred.engagement_sessions
                WHERE user_id = 'json_test_user'
            """)
            
            assert level_completions == 2


@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraints and data integrity."""
    
    async def test_user_preferences_constraints(self, postgres_pool):
        """Test user preferences table constraints."""
        async with postgres_pool.acquire() as conn:
            # Insert preferences
            await conn.execute("""
                INSERT INTO users.preferences
                (user_id, language_code, audio_settings, accessibility_settings)
                VALUES ($1, $2, $3, $4)
            """,
            'pref_test_user',
            'ja-JP',
            {'volume': 0.8, 'voice_type': 'female'},
            {'subtitles': True, 'high_contrast': False}
            )
            
            # Test unique constraint
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute("""
                    INSERT INTO users.preferences (user_id)
                    VALUES ('pref_test_user')
                """)
            
            # Test update
            await conn.execute("""
                UPDATE users.preferences
                SET language_code = 'en-US',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = 'pref_test_user'
            """)
            
            # Verify update
            row = await conn.fetchrow("""
                SELECT * FROM users.preferences
                WHERE user_id = 'pref_test_user'
            """)
            
            assert row['language_code'] == 'en-US'
            assert row['updated_at'] > row['created_at']
    
    async def test_cascade_deletes(self, postgres_pool):
        """Test cascade delete behavior."""
        # This test would verify cascade deletes if configured
        # For now, we'll test that related data requires proper cleanup
        pass
    
    async def test_timestamp_defaults(self, postgres_pool):
        """Test timestamp default values."""
        async with postgres_pool.acquire() as conn:
            # Insert without timestamps
            await conn.execute("""
                INSERT INTO ethelred.audio_metrics
                (user_id, audio_file_path, intelligibility_score)
                VALUES ('timestamp_test', '/test/time.ogg', 85.0)
            """)
            
            # Check defaults were applied
            row = await conn.fetchrow("""
                SELECT created_at, updated_at, analysis_timestamp
                FROM ethelred.audio_metrics
                WHERE user_id = 'timestamp_test'
            """)
            
            assert row['created_at'] is not None
            assert row['updated_at'] is not None
            assert row['analysis_timestamp'] is not None
            assert row['created_at'] == row['updated_at']
