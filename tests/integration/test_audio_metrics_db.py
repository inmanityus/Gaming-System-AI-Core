"""
Database integration tests for audio metrics services.
Tests real PostgreSQL interactions using testcontainers.
"""
import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.ethelred_audio_metrics.intelligibility_analyzer import (
    IntelligibilityAnalyzer, IntelligibilityConfig
)
from services.ethelred_audio_metrics.archetype_analyzer import (
    ArchetypeAnalyzer, ArchetypeAnalyzerConfig
)


@pytest.mark.integration
class TestAudioMetricsDatabase:
    """Test audio metrics services with real database."""
    
    async def test_intelligibility_save_and_retrieve(
        self,
        postgres_pool,
        sample_audio_48khz,
        intelligibility_config
    ):
        """Test saving and retrieving intelligibility results."""
        analyzer = IntelligibilityAnalyzer(
            config=intelligibility_config,
            db_pool=postgres_pool
        )
        
        # Analyze audio
        audio, sample_rate = sample_audio_48khz
        result = await analyzer.analyze(
            audio,
            sample_rate,
            user_id="test_user_db_1",
            audio_file_path="/test/audio1.ogg"
        )
        
        # Verify saved to database
        async with postgres_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM ethelred.audio_metrics
                WHERE user_id = $1 AND audio_file_path = $2
            """, "test_user_db_1", "/test/audio1.ogg")
        
        assert row is not None
        assert float(row['intelligibility_score']) == pytest.approx(result['score'], rel=0.01)
        assert float(row['confidence_level']) == pytest.approx(result['confidence'], rel=0.01)
        assert float(row['spectral_clarity']) == pytest.approx(result['metrics']['spectral_clarity'], rel=0.01)
    
    async def test_archetype_save_and_retrieve(
        self,
        postgres_pool,
        sample_audio_48khz,
        archetype_config,
        archetype_profiles
    ):
        """Test saving and retrieving archetype analysis results."""
        # Store profiles in database first
        async with postgres_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ethelred.archetype_profiles (
                    archetype VARCHAR(100) PRIMARY KEY,
                    profile JSONB NOT NULL
                )
            """)
            
            for archetype, profile in archetype_profiles.items():
                await conn.execute("""
                    INSERT INTO ethelred.archetype_profiles (archetype, profile)
                    VALUES ($1, $2)
                    ON CONFLICT (archetype) DO UPDATE SET profile = $2
                """, archetype, profile)
        
        # Configure analyzer to use database profiles
        config = ArchetypeAnalyzerConfig(
            profile_source="database",
            profile_db_table="ethelred.archetype_profiles"
        )
        
        analyzer = ArchetypeAnalyzer(
            config=config,
            db_pool=postgres_pool
        )
        
        # Analyze audio
        audio, sample_rate = sample_audio_48khz
        result = await analyzer.analyze(
            audio,
            sample_rate,
            expected_archetype="vampire_alpha",
            user_id="test_user_db_2",
            audio_file_path="/test/audio2.ogg"
        )
        
        # Verify saved to database
        async with postgres_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM ethelred.audio_metrics
                WHERE user_id = $1 AND audio_file_path = $2
            """, "test_user_db_2", "/test/audio2.ogg")
        
        assert row is not None
        assert row['archetype'] == "vampire_alpha"
        assert row['is_on_profile'] == result['is_on_profile']
        assert float(row['pitch_range_match']) == pytest.approx(result['metrics']['pitch_range_match'], rel=0.01)
    
    async def test_concurrent_saves(self, postgres_pool, sample_audio_48khz, intelligibility_config):
        """Test concurrent database saves don't conflict."""
        analyzer = IntelligibilityAnalyzer(
            config=intelligibility_config,
            db_pool=postgres_pool
        )
        
        audio, sample_rate = sample_audio_48khz
        
        # Run 10 concurrent analyses
        tasks = []
        for i in range(10):
            task = analyzer.analyze(
                audio,
                sample_rate,
                user_id=f"concurrent_user_{i}",
                audio_file_path=f"/test/concurrent_{i}.ogg"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all saved
        async with postgres_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM ethelred.audio_metrics
                WHERE user_id LIKE 'concurrent_user_%'
            """)
        
        assert count == 10
    
    async def test_query_user_history(self, postgres_pool, sample_audio_metrics):
        """Test querying user's audio history."""
        # Query user history
        async with postgres_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM ethelred.audio_metrics
                WHERE user_id = $1
                ORDER BY analysis_timestamp DESC
            """, "test_user_1")
        
        assert len(rows) > 0
        assert rows[0]['archetype'] == 'vampire_alpha'
        assert float(rows[0]['intelligibility_score']) == 85.5
    
    async def test_aggregation_queries(self, postgres_pool, sample_audio_metrics):
        """Test aggregation queries for analytics."""
        async with postgres_pool.acquire() as conn:
            # Average intelligibility by archetype
            avg_results = await conn.fetch("""
                SELECT 
                    archetype,
                    AVG(intelligibility_score) as avg_score,
                    COUNT(*) as count
                FROM ethelred.audio_metrics
                GROUP BY archetype
            """)
            
            archetype_map = {row['archetype']: row for row in avg_results}
            assert 'vampire_alpha' in archetype_map
            assert 'human_agent' in archetype_map
            
            # Time-based analysis
            recent = await conn.fetchval("""
                SELECT COUNT(*) FROM ethelred.audio_metrics
                WHERE analysis_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
            """)
            assert recent == 2  # Our sample data
    
    async def test_database_connection_pooling(self, postgres_pool, intelligibility_config):
        """Test database connection pool behavior."""
        analyzer = IntelligibilityAnalyzer(
            config=intelligibility_config,
            db_pool=postgres_pool
        )
        
        # Get pool stats before
        pool_size_before = postgres_pool.get_size()
        
        # Run multiple analyses
        audio = np.random.randn(48000)  # 1 second of noise
        tasks = []
        for i in range(20):
            task = analyzer.analyze(
                audio,
                48000,
                user_id=f"pool_test_{i}",
                audio_file_path=f"/test/pool_{i}.ogg"
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Pool should handle concurrent access efficiently
        pool_size_after = postgres_pool.get_size()
        assert pool_size_after <= 10  # Max pool size from conftest
    
    async def test_transaction_rollback_on_error(self, postgres_pool):
        """Test that transactions rollback properly on error."""
        async with postgres_pool.acquire() as conn:
            try:
                async with conn.transaction():
                    # Insert valid data
                    await conn.execute("""
                        INSERT INTO ethelred.audio_metrics
                        (user_id, audio_file_path, intelligibility_score)
                        VALUES ('rollback_test', '/test/rollback.ogg', 85.0)
                    """)
                    
                    # Force an error (duplicate key)
                    await conn.execute("""
                        INSERT INTO ethelred.audio_metrics
                        (id, user_id, audio_file_path)
                        VALUES 
                        ('00000000-0000-0000-0000-000000000001', 'test1', '/test1.ogg'),
                        ('00000000-0000-0000-0000-000000000001', 'test2', '/test2.ogg')
                    """)
            except:
                pass  # Expected to fail
        
        # Verify rollback - should not find the record
        async with postgres_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM ethelred.audio_metrics
                WHERE user_id = 'rollback_test'
            """)
        
        assert count == 0
    
    async def test_metadata_storage(self, postgres_pool, intelligibility_config):
        """Test storing and retrieving JSON metadata."""
        analyzer = IntelligibilityAnalyzer(
            config=intelligibility_config,
            db_pool=postgres_pool
        )
        
        # Create metadata
        metadata = {
            "session_id": "test_session_123",
            "client_version": "1.2.3",
            "recording_device": "Microphone (USB Audio Device)",
            "processing_flags": ["noise_reduction", "echo_cancellation"],
            "custom_data": {
                "experiment_id": 42,
                "conditions": ["control", "high_noise"]
            }
        }
        
        # Analyze with metadata
        audio = np.random.randn(48000)
        result = await analyzer.analyze(
            audio,
            48000,
            user_id="metadata_test",
            audio_file_path="/test/metadata.ogg",
            metadata=metadata
        )
        
        # Retrieve and verify
        async with postgres_pool.acquire() as conn:
            stored_metadata = await conn.fetchval("""
                SELECT metadata FROM ethelred.audio_metrics
                WHERE user_id = 'metadata_test'
            """)
        
        assert stored_metadata is not None
        assert stored_metadata['session_id'] == "test_session_123"
        assert stored_metadata['processing_flags'] == ["noise_reduction", "echo_cancellation"]
        assert stored_metadata['custom_data']['experiment_id'] == 42


@pytest.mark.integration 
class TestDatabasePerformance:
    """Performance tests for database operations."""
    
    async def test_bulk_insert_performance(self, postgres_pool, performance_timer):
        """Test bulk insert performance."""
        timer = performance_timer()
        
        # Prepare bulk data
        data = []
        for i in range(1000):
            data.append((
                f"bulk_user_{i}",
                f"/test/bulk_{i}.ogg",
                85.0 + (i % 15),  # Vary scores
                0.8 + (i % 20) * 0.01,  # Vary confidence
                bool(i % 2),  # Alternate profile match
                f"archetype_{i % 5}"  # 5 different archetypes
            ))
        
        # Bulk insert
        with timer:
            async with postgres_pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO ethelred.audio_metrics
                    (user_id, audio_file_path, intelligibility_score,
                     confidence_level, is_on_profile, archetype)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, data)
        
        # Should complete in reasonable time
        assert timer.elapsed < 2.0  # 2 seconds for 1000 records
        
        # Verify all inserted
        async with postgres_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM ethelred.audio_metrics
                WHERE user_id LIKE 'bulk_user_%'
            """)
        
        assert count == 1000
    
    async def test_query_performance_with_index(self, postgres_pool, performance_timer):
        """Test query performance with proper indexes."""
        # Insert test data first
        async with postgres_pool.acquire() as conn:
            for i in range(100):
                await conn.execute("""
                    INSERT INTO ethelred.audio_metrics
                    (user_id, audio_file_path, intelligibility_score, 
                     analysis_timestamp)
                    VALUES ($1, $2, $3, $4)
                """, 
                "perf_test_user",
                f"/test/perf_{i}.ogg", 
                85.0 + (i % 15),
                datetime.now(timezone.utc) - timedelta(hours=i)
                )
        
        timer = performance_timer()
        
        # Query with index (user_id, timestamp)
        with timer:
            async with postgres_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM ethelred.audio_metrics
                    WHERE user_id = $1
                    AND analysis_timestamp > $2
                    ORDER BY analysis_timestamp DESC
                    LIMIT 10
                """, 
                "perf_test_user",
                datetime.now(timezone.utc) - timedelta(days=1)
                )
        
        # Should be fast with index
        assert timer.elapsed < 0.1  # 100ms
        assert len(rows) <= 10
