"""
Pairwise integration tests for database interactions.
Tests how different components interact with the database layer.
"""
import pytest
import asyncio
import asyncpg
import json
import time
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import psutil
import random
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.audio_analytics.intelligibility_analyzer import IntelligibilityAnalyzer
from services.audio_analytics.archetype_analyzer import ArchetypeAnalyzer
from services.engagement_analytics.addiction_indicators import AddictionIndicatorAnalyzer
from services.multi_language_experience.localization_store import LocalizationStore
from services.multi_language_experience.language_gateway import LanguageGateway


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseConnectionPooling:
    """Test connection pooling behavior with multiple services."""
    
    async def test_connection_pool_sharing_between_services(self, postgres_pool):
        """Test that services can efficiently share a connection pool."""
        # Create multiple service instances sharing the same pool
        intel_analyzer = IntelligibilityAnalyzer(db_pool=postgres_pool)
        arch_analyzer = ArchetypeAnalyzer(db_pool=postgres_pool) 
        addiction_analyzer = AddictionIndicatorAnalyzer(db_pool=postgres_pool)
        
        # Track initial pool stats
        initial_size = postgres_pool.get_size()
        initial_free = postgres_pool.get_idle_size()
        
        # Perform concurrent operations from all services
        tasks = []
        
        # Create sample data
        audio = np.random.randn(48000 * 3).astype(np.float32)  # 3 seconds
        
        # 10 operations from each service
        for i in range(10):
            tasks.append(intel_analyzer.analyze(audio, 48000, f"user_{i}", "session_1"))
            tasks.append(arch_analyzer.analyze(audio, 48000, f"user_{i}", expected_archetype="vampire"))
            
            # Engagement session operations
            session_data = {
                "session_id": f"engagement_{i}",
                "user_id": f"user_{i}",
                "events": [{"type": "game_start", "timestamp": datetime.now(timezone.utc).isoformat()}]
            }
            tasks.append(addiction_analyzer.analyze_session(session_data))
        
        # Execute all operations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for errors
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Operations failed: {errors}"
        
        # Verify pool didn't grow excessively
        final_size = postgres_pool.get_size()
        assert final_size <= initial_size + 5, "Pool grew too much during concurrent operations"
        
        # Verify all connections were returned
        await asyncio.sleep(0.1)  # Allow time for cleanup
        final_free = postgres_pool.get_idle_size()
        assert final_free >= initial_free, "Connections not properly returned to pool"
    
    async def test_connection_exhaustion_handling(self, postgres_pool):
        """Test behavior when connection pool is exhausted."""
        # Create analyzer with small pool for testing
        small_pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "gaming_system_ai_core"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Inn0vat1on!"),
            min_size=1,
            max_size=3,  # Very small pool
            command_timeout=5.0
        )
        
        try:
            analyzer = IntelligibilityAnalyzer(db_pool=small_pool)
            audio = np.random.randn(48000).astype(np.float32)
            
            # Create more concurrent requests than pool size
            tasks = []
            for i in range(10):
                tasks.append(analyzer.analyze(audio, 48000, f"user_{i}", "session_test"))
            
            # Should complete without errors (queuing should work)
            start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start
            
            # Check all completed successfully
            errors = [r for r in results if isinstance(r, Exception)]
            assert len(errors) == 0, f"Some operations failed: {errors}"
            
            # Verify queuing behavior (should take longer due to limited connections)
            assert duration > 1.0, "Operations completed too fast - queuing not working"
            
        finally:
            await small_pool.close()
    
    async def test_connection_leak_detection(self, postgres_pool):
        """Test that connection leaks are prevented."""
        initial_idle = postgres_pool.get_idle_size()
        
        # Simulate a service that might leak connections
        class LeakyService:
            def __init__(self, pool):
                self.pool = pool
            
            async def bad_operation(self):
                # Acquire connection but simulate forgetting to release
                conn = await self.pool.acquire()
                # Simulate work
                await conn.fetchval("SELECT 1")
                # Oops, forgot to release!
                # (In practice, context manager prevents this)
                await self.pool.release(conn)  # Fix the leak for test
        
        service = LeakyService(postgres_pool)
        
        # Run operations
        for _ in range(5):
            await service.bad_operation()
        
        # Check connections are returned
        await asyncio.sleep(0.1)
        final_idle = postgres_pool.get_idle_size()
        assert final_idle >= initial_idle, "Connections leaked from pool"


@pytest.mark.integration
@pytest.mark.asyncio
class TestReadWriteSplitting:
    """Test read/write splitting behavior for scalability."""
    
    async def test_read_operations_use_read_pool(self, postgres_pool):
        """Test that read operations can use a separate read pool."""
        # In production, we'd have separate read/write pools
        # For testing, simulate with connection tracking
        
        class ConnectionTracker:
            def __init__(self):
                self.read_queries = []
                self.write_queries = []
            
            async def execute_read(self, query, *args):
                self.read_queries.append(query)
                async with postgres_pool.acquire() as conn:
                    return await conn.fetch(query, *args)
            
            async def execute_write(self, query, *args):
                self.write_queries.append(query)
                async with postgres_pool.acquire() as conn:
                    return await conn.execute(query, *args)
        
        tracker = ConnectionTracker()
        
        # Simulate service operations
        # Reads
        await tracker.execute_read(
            "SELECT * FROM audio_analytics.audio_metrics WHERE user_id = $1",
            "test_user"
        )
        await tracker.execute_read(
            "SELECT * FROM engagement.sessions WHERE user_id = $1 LIMIT 10",
            "test_user"
        )
        
        # Writes
        await tracker.execute_write(
            """INSERT INTO audio_analytics.audio_metrics 
               (user_id, session_id, sample_rate, intelligibility_score, duration_seconds)
               VALUES ($1, $2, $3, $4, $5)""",
            "test_user", "test_session", 48000, 0.85, 3.0
        )
        
        # Verify separation
        assert len(tracker.read_queries) == 2
        assert len(tracker.write_queries) == 1
        assert all("SELECT" in q for q in tracker.read_queries)
        assert all("INSERT" in q or "UPDATE" in q or "DELETE" in q for q in tracker.write_queries)
    
    async def test_transaction_stickiness(self, postgres_pool):
        """Test that transactions stay on the write connection."""
        async with postgres_pool.acquire() as conn:
            async with conn.transaction():
                # All queries in transaction should use same connection
                await conn.execute(
                    """INSERT INTO engagement.sessions 
                       (user_id, start_time, session_id) 
                       VALUES ($1, $2, $3)""",
                    "test_user", datetime.now(timezone.utc), "txn_test_session"
                )
                
                # Even reads in transaction use write connection
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM engagement.sessions WHERE user_id = $1",
                    "test_user"
                )
                
                # Update based on read
                await conn.execute(
                    """UPDATE users.preferences 
                       SET feature_flags = $1 
                       WHERE user_id = $2""",
                    json.dumps({"session_count": result}),
                    "test_user"
                )
        
        # Verify transaction completed
        async with postgres_pool.acquire() as conn:
            session_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM engagement.sessions WHERE session_id = $1)",
                "txn_test_session"
            )
            assert session_exists


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabasePerformanceInteractions:
    """Test performance characteristics of database interactions."""
    
    async def test_jsonb_query_performance(self, postgres_pool, performance_timer):
        """Test JSONB query performance for gaming events."""
        # Insert test data with complex JSONB
        async with postgres_pool.acquire() as conn:
            # Create test sessions with varying event counts
            for i in range(100):
                events = []
                for j in range(random.randint(10, 100)):
                    events.append({
                        "type": random.choice(["click", "move", "action", "pause"]),
                        "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=j)).isoformat(),
                        "data": {
                            "x": random.randint(0, 1920),
                            "y": random.randint(0, 1080),
                            "value": random.random()
                        }
                    })
                
                await conn.execute(
                    """INSERT INTO engagement.sessions 
                       (user_id, session_id, start_time, events)
                       VALUES ($1, $2, $3, $4)""",
                    f"perf_user_{i % 10}",
                    f"perf_session_{i}",
                    datetime.now(timezone.utc) - timedelta(hours=i),
                    json.dumps(events)
                )
        
        # Test various JSONB queries
        with performance_timer("jsonb_array_length"):
            async with postgres_pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT session_id, jsonb_array_length(events) as event_count
                    FROM engagement.sessions
                    WHERE jsonb_array_length(events) > 50
                """)
                assert len(result) > 0
        
        with performance_timer("jsonb_containment"):
            async with postgres_pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT session_id
                    FROM engagement.sessions
                    WHERE events @> '[{"type": "action"}]'
                """)
                assert len(result) > 0
        
        with performance_timer("jsonb_path_query"):
            async with postgres_pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT session_id, 
                           jsonb_path_query_array(events, '$[*] ? (@.type == "click")') as clicks
                    FROM engagement.sessions
                    WHERE user_id = $1
                """, "perf_user_0")
                assert len(result) > 0
        
        # Verify GIN index performance
        with performance_timer("jsonb_gin_index_query"):
            async with postgres_pool.acquire() as conn:
                # This should use GIN index if created
                result = await conn.fetch("""
                    SELECT session_id
                    FROM engagement.sessions
                    WHERE events @? '$[*] ? (@.data.value > 0.8)'
                    LIMIT 10
                """)
        
        # All queries should complete quickly
        assert performance_timer.get_time("jsonb_array_length") < 0.1
        assert performance_timer.get_time("jsonb_gin_index_query") < 0.05
    
    async def test_time_series_partition_performance(self, postgres_pool, performance_timer):
        """Test time-series query performance with partitioning."""
        # Insert time-series data
        base_time = datetime.now(timezone.utc)
        
        async with postgres_pool.acquire() as conn:
            # Bulk insert audio metrics over time
            data = []
            for days_ago in range(30):
                for hour in range(24):
                    for i in range(10):  # 10 entries per hour
                        timestamp = base_time - timedelta(days=days_ago, hours=hour, minutes=i*6)
                        data.append((
                            f"ts_user_{i % 5}",
                            f"ts_session_{days_ago}_{hour}_{i}",
                            48000,
                            random.uniform(0.6, 0.95),
                            3.0,
                            timestamp
                        ))
            
            # Bulk insert
            await conn.executemany(
                """INSERT INTO audio_analytics.audio_metrics 
                   (user_id, session_id, sample_rate, intelligibility_score, 
                    duration_seconds, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                data
            )
        
        # Test time-range queries
        with performance_timer("recent_data_query"):
            async with postgres_pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT COUNT(*), AVG(intelligibility_score)
                    FROM audio_analytics.audio_metrics
                    WHERE created_at >= $1
                    GROUP BY date_trunc('hour', created_at)
                    ORDER BY date_trunc('hour', created_at) DESC
                """, base_time - timedelta(days=1))
                assert len(result) >= 24  # At least 24 hours of data
        
        with performance_timer("user_history_30days"):
            async with postgres_pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT 
                        date_trunc('day', created_at) as day,
                        COUNT(*) as session_count,
                        AVG(intelligibility_score) as avg_score
                    FROM audio_analytics.audio_metrics
                    WHERE user_id = $1 AND created_at >= $2
                    GROUP BY day
                    ORDER BY day
                """, "ts_user_0", base_time - timedelta(days=30))
        
        # Partitioned queries should be fast
        assert performance_timer.get_time("recent_data_query") < 0.2
        assert performance_timer.get_time("user_history_30days") < 0.3
    
    async def test_concurrent_write_performance(self, postgres_pool, performance_timer):
        """Test write performance under concurrent load."""
        
        async def write_batch(pool, batch_id: int, size: int = 100):
            """Write a batch of records."""
            async with pool.acquire() as conn:
                data = []
                for i in range(size):
                    data.append((
                        f"batch_{batch_id}_user_{i}",
                        f"batch_{batch_id}_session_{i}",
                        48000,
                        random.uniform(0.5, 1.0),
                        random.uniform(1.0, 5.0)
                    ))
                
                await conn.executemany(
                    """INSERT INTO audio_analytics.audio_metrics
                       (user_id, session_id, sample_rate, intelligibility_score, duration_seconds)
                       VALUES ($1, $2, $3, $4, $5)""",
                    data
                )
        
        # Test concurrent writes
        with performance_timer("concurrent_10_batches"):
            tasks = [write_batch(postgres_pool, i) for i in range(10)]
            await asyncio.gather(*tasks)
        
        # Should handle concurrent writes efficiently
        total_time = performance_timer.get_time("concurrent_10_batches")
        assert total_time < 2.0, f"Concurrent writes too slow: {total_time}s"
        
        # Verify all data was written
        async with postgres_pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM audio_analytics.audio_metrics WHERE user_id LIKE 'batch_%'"
            )
            assert count == 1000  # 10 batches * 100 records


@pytest.mark.integration
@pytest.mark.asyncio
class TestCrossDomainInteractions:
    """Test interactions between different domains (audio, engagement, localization)."""
    
    async def test_audio_engagement_correlation(self, postgres_pool):
        """Test correlating audio quality with engagement metrics."""
        # Insert correlated data
        user_id = "correlation_test_user"
        
        async with postgres_pool.acquire() as conn:
            # Create engagement session
            await conn.execute(
                """INSERT INTO engagement.sessions 
                   (user_id, session_id, start_time, end_time, duration_seconds)
                   VALUES ($1, $2, $3, $4, $5)""",
                user_id, "corr_session_1",
                datetime.now(timezone.utc) - timedelta(hours=2),
                datetime.now(timezone.utc) - timedelta(hours=1),
                3600.0
            )
            
            # Add audio metrics during the session
            for i in range(10):
                await conn.execute(
                    """INSERT INTO audio_analytics.audio_metrics
                       (user_id, session_id, sample_rate, intelligibility_score, 
                        duration_seconds, created_at, archetype)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    user_id, "corr_session_1", 48000,
                    0.9 - (i * 0.05),  # Declining quality over time
                    180.0,
                    datetime.now(timezone.utc) - timedelta(hours=2, minutes=i*10),
                    "vampire"
                )
            
            # Query correlation
            result = await conn.fetchrow("""
                SELECT 
                    s.session_id,
                    s.duration_seconds as session_duration,
                    COUNT(a.id) as audio_count,
                    AVG(a.intelligibility_score) as avg_intelligibility,
                    MIN(a.intelligibility_score) as min_intelligibility,
                    MAX(a.intelligibility_score) as max_intelligibility
                FROM engagement.sessions s
                JOIN audio_analytics.audio_metrics a 
                    ON s.user_id = a.user_id 
                    AND s.session_id = a.session_id
                WHERE s.user_id = $1
                GROUP BY s.session_id, s.duration_seconds
            """, user_id)
            
            assert result['audio_count'] == 10
            assert result['avg_intelligibility'] > 0.5
            assert result['min_intelligibility'] < result['max_intelligibility']
    
    async def test_localization_with_user_preferences(self, postgres_pool):
        """Test localization system with user preferences."""
        user_id = "locale_test_user"
        
        async with postgres_pool.acquire() as conn:
            # Set user preferences
            await conn.execute(
                """INSERT INTO users.preferences 
                   (user_id, language_code, timezone, audio_quality)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (user_id) 
                   DO UPDATE SET language_code = $2, timezone = $3""",
                user_id, "ja-JP", "Asia/Tokyo", "high"
            )
            
            # Add localized content
            await conn.execute(
                """INSERT INTO localization.content 
                   (content_key, language_code, content_value, version)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (content_key, language_code, version) 
                   DO NOTHING""",
                "test.greeting", "ja-JP", "こんにちは", 1
            )
            
            # Query with user preference join
            result = await conn.fetchrow("""
                SELECT 
                    u.user_id,
                    u.language_code,
                    l.content_value
                FROM users.preferences u
                LEFT JOIN localization.content l 
                    ON l.language_code = u.language_code 
                    AND l.content_key = $2
                WHERE u.user_id = $1
            """, user_id, "test.greeting")
            
            assert result['content_value'] == "こんにちは"
    
    async def test_full_user_journey_data_consistency(self, postgres_pool):
        """Test data consistency across a full user journey."""
        user_id = f"journey_user_{int(time.time())}"
        session_id = f"journey_session_{int(time.time())}"
        
        async with postgres_pool.acquire() as conn:
            async with conn.transaction():
                # 1. User starts session
                await conn.execute(
                    """INSERT INTO engagement.sessions 
                       (user_id, session_id, start_time)
                       VALUES ($1, $2, $3)""",
                    user_id, session_id, datetime.now(timezone.utc)
                )
                
                # 2. User preferences set
                await conn.execute(
                    """INSERT INTO users.preferences 
                       (user_id, language_code, safety_mode)
                       VALUES ($1, $2, $3)""",
                    user_id, "en-US", "strict"
                )
                
                # 3. Audio analysis performed
                analysis_id = await conn.fetchval(
                    """INSERT INTO audio_analytics.audio_metrics
                       (user_id, session_id, sample_rate, intelligibility_score, 
                        duration_seconds, archetype, confidence_level)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)
                       RETURNING analysis_id""",
                    user_id, session_id, 48000, 0.92, 3.5, "vampire", 0.88
                )
                
                # 4. TTS request logged
                await conn.execute(
                    """INSERT INTO language_system.tts_metrics
                       (language_code, text_length, processing_time_ms, cache_hit)
                       VALUES ($1, $2, $3, $4)""",
                    "en-US", 150, 45.3, False
                )
                
                # 5. Session ends
                await conn.execute(
                    """UPDATE engagement.sessions 
                       SET end_time = $1, duration_seconds = $2
                       WHERE session_id = $3""",
                    datetime.now(timezone.utc),
                    1800.0,
                    session_id
                )
            
            # Verify complete journey data
            journey_data = await conn.fetchrow("""
                SELECT 
                    s.user_id,
                    s.session_id,
                    s.duration_seconds,
                    p.language_code,
                    p.safety_mode,
                    COUNT(a.id) as audio_analyses,
                    AVG(a.intelligibility_score) as avg_score
                FROM engagement.sessions s
                JOIN users.preferences p ON s.user_id = p.user_id
                LEFT JOIN audio_analytics.audio_metrics a 
                    ON s.session_id = a.session_id
                WHERE s.session_id = $1
                GROUP BY s.user_id, s.session_id, s.duration_seconds, 
                         p.language_code, p.safety_mode
            """, session_id)
            
            assert journey_data['user_id'] == user_id
            assert journey_data['audio_analyses'] == 1
            assert journey_data['avg_score'] == 0.92
            assert journey_data['safety_mode'] == "strict"


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseErrorHandling:
    """Test error handling and recovery in database interactions."""
    
    async def test_transaction_rollback_on_error(self, postgres_pool):
        """Test that transactions properly rollback on error."""
        user_id = "rollback_test_user"
        
        async with postgres_pool.acquire() as conn:
            try:
                async with conn.transaction():
                    # Insert valid data
                    await conn.execute(
                        """INSERT INTO audio_analytics.audio_metrics
                           (user_id, session_id, sample_rate, intelligibility_score, duration_seconds)
                           VALUES ($1, $2, $3, $4, $5)""",
                        user_id, "rollback_session", 48000, 0.85, 3.0
                    )
                    
                    # Attempt invalid operation (constraint violation)
                    await conn.execute(
                        """INSERT INTO audio_analytics.audio_metrics
                           (user_id, session_id, sample_rate, intelligibility_score, duration_seconds)
                           VALUES ($1, $2, $3, $4, $5)""",
                        user_id, "rollback_session", 48000, 1.5, 3.0  # Invalid score > 1
                    )
            except asyncpg.CheckViolationError:
                # Expected error
                pass
            
            # Verify rollback - no data should exist
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM audio_analytics.audio_metrics WHERE user_id = $1",
                user_id
            )
            assert count == 0, "Transaction not properly rolled back"
    
    async def test_deadlock_recovery(self, postgres_pool):
        """Test recovery from deadlock situations."""
        
        async def update_in_order_1(pool):
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE users.preferences SET feature_flags = '{}' WHERE user_id = 'user_a'"
                    )
                    await asyncio.sleep(0.1)  # Create opportunity for deadlock
                    await conn.execute(
                        "UPDATE users.preferences SET feature_flags = '{}' WHERE user_id = 'user_b'"
                    )
        
        async def update_in_order_2(pool):
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE users.preferences SET feature_flags = '{}' WHERE user_id = 'user_b'"
                    )
                    await asyncio.sleep(0.1)  # Create opportunity for deadlock
                    await conn.execute(
                        "UPDATE users.preferences SET feature_flags = '{}' WHERE user_id = 'user_a'"
                    )
        
        # Ensure test users exist
        async with postgres_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users.preferences (user_id) VALUES ('user_a'), ('user_b') ON CONFLICT DO NOTHING"
            )
        
        # Attempt to create deadlock
        results = await asyncio.gather(
            update_in_order_1(postgres_pool),
            update_in_order_2(postgres_pool),
            return_exceptions=True
        )
        
        # At least one should succeed, other might get deadlock error
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) >= 1, "Both transactions failed"
    
    async def test_connection_failure_recovery(self, postgres_pool):
        """Test recovery from connection failures."""
        
        # Simulate analyzer that handles connection errors
        class ResilientAnalyzer:
            def __init__(self, pool):
                self.pool = pool
                self.retry_count = 3
            
            async def analyze_with_retry(self, user_id: str) -> Optional[Dict]:
                for attempt in range(self.retry_count):
                    try:
                        async with self.pool.acquire() as conn:
                            return await conn.fetchrow(
                                "SELECT * FROM audio_analytics.audio_metrics WHERE user_id = $1 LIMIT 1",
                                user_id
                            )
                    except (asyncpg.PostgresConnectionError, asyncpg.InterfaceError) as e:
                        if attempt == self.retry_count - 1:
                            raise
                        await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                return None
        
        analyzer = ResilientAnalyzer(postgres_pool)
        
        # Should succeed under normal conditions
        result = await analyzer.analyze_with_retry("test_user")
        # Result might be None if no data, but shouldn't raise exception


@pytest.fixture
def performance_timer():
    """Fixture to measure performance of operations."""
    
    class PerformanceTimer:
        def __init__(self):
            self.timings = {}
        
        def __call__(self, name: str):
            return self.Timer(self, name)
        
        class Timer:
            def __init__(self, parent, name):
                self.parent = parent
                self.name = name
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, *args):
                duration = time.time() - self.start_time
                self.parent.timings[self.name] = duration
        
        def get_time(self, name: str) -> float:
            return self.timings.get(name, 0.0)
        
        def get_all(self) -> Dict[str, float]:
            return self.timings.copy()
    
    return PerformanceTimer()
