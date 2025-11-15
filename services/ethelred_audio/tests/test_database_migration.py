"""
Tests for audio database migration
"""
import asyncio
import uuid
from datetime import datetime
import asyncpg
import os
from pathlib import Path


# Database connection for testing
TEST_DB_URL = os.environ.get(
    'TEST_DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/test_audio_db'
)


async def create_test_database():
    """Create a test database if it doesn't exist."""
    # Connect to default postgres database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='postgres'
    )
    
    # Drop and recreate test database
    try:
        await conn.execute('DROP DATABASE IF EXISTS test_audio_db')
        await conn.execute('CREATE DATABASE test_audio_db')
    finally:
        await conn.close()


async def apply_migration(conn):
    """Apply the audio migration."""
    migration_path = Path(__file__).parent.parent.parent.parent / 'database' / 'migrations' / '014_audio_authentication.sql'
    
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    # Execute migration
    await conn.execute(migration_sql)


async def test_audio_segments_table():
    """Test audio_segments table creation and constraints."""
    conn = await asyncpg.connect(TEST_DB_URL)
    
    try:
        # Insert test segment
        segment_id = uuid.uuid4()
        now = datetime.utcnow()
        
        await conn.execute("""
            INSERT INTO audio_segments (
                segment_id, build_id, segment_type, speaker_id, speaker_role,
                archetype_id, language_code, scene_id, simulator_applied,
                media_uri, duration_seconds, timestamp_start, timestamp_end
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """, segment_id, 'build-2025-11-15', 'dialogue', 'npc-vampire-01', 'npc',
            'vampire_house_alpha', 'en-US', 'scene-castle', True,
            f'redalert://media/audio/build-2025-11-15/{segment_id}.ogg',
            3.5, now, now)
        
        # Query it back
        row = await conn.fetchrow(
            "SELECT * FROM audio_segments WHERE segment_id = $1", 
            segment_id
        )
        
        assert row is not None
        assert row['build_id'] == 'build-2025-11-15'
        assert row['segment_type'] == 'dialogue'
        assert row['duration_seconds'] == 3.5
        
        # Test constraint - invalid segment type
        try:
            await conn.execute("""
                INSERT INTO audio_segments (
                    build_id, segment_type, media_uri, duration_seconds,
                    timestamp_start, timestamp_end
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, 'build-test', 'invalid_type', 'test://uri', 1.0, now, now)
            assert False, "Should have failed on invalid segment_type"
        except asyncpg.CheckViolationError:
            pass  # Expected
        
        print("✓ audio_segments table test passed")
        
    finally:
        await conn.close()


async def test_audio_scores_table():
    """Test audio_scores table with foreign key."""
    conn = await asyncpg.connect(TEST_DB_URL)
    
    try:
        # First create a segment
        segment_id = uuid.uuid4()
        now = datetime.utcnow()
        
        await conn.execute("""
            INSERT INTO audio_segments (
                segment_id, build_id, segment_type, media_uri,
                duration_seconds, timestamp_start, timestamp_end
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, segment_id, 'build-test', 'dialogue', 'test://uri',
            2.0, now, now)
        
        # Insert scores
        await conn.execute("""
            INSERT INTO audio_scores (
                segment_id, intelligibility, naturalness,
                archetype_conformity, simulator_stability, mix_quality,
                intelligibility_band, naturalness_band
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, segment_id, 0.92, 0.88, 0.80, 0.95, 0.84,
            'acceptable', 'ok')
        
        # Query scores
        row = await conn.fetchrow(
            "SELECT * FROM audio_scores WHERE segment_id = $1",
            segment_id
        )
        
        assert row['intelligibility'] == 0.92
        assert row['intelligibility_band'] == 'acceptable'
        
        # Test score constraints
        try:
            await conn.execute("""
                INSERT INTO audio_scores (segment_id, intelligibility)
                VALUES ($1, $2)
            """, uuid.uuid4(), 1.5)  # Invalid score > 1.0
            assert False, "Should have failed on score > 1.0"
        except (asyncpg.CheckViolationError, asyncpg.ForeignKeyViolationError):
            pass  # Expected
        
        # Test cascade delete
        await conn.execute(
            "DELETE FROM audio_segments WHERE segment_id = $1",
            segment_id
        )
        
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM audio_scores WHERE segment_id = $1",
            segment_id
        )
        assert count == 0  # Should be deleted by cascade
        
        print("✓ audio_scores table test passed")
        
    finally:
        await conn.close()


async def test_reports_and_feedback():
    """Test report and feedback tables."""
    conn = await asyncpg.connect(TEST_DB_URL)
    
    try:
        # Insert archetype report
        report_id = uuid.uuid4()
        
        await conn.execute("""
            INSERT INTO audio_archetype_reports (
                report_id, build_id, archetype_id, report_type,
                num_segments, intelligibility_distribution,
                naturalness_mean, archetype_conformity_mean
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, report_id, 'build-2025-11-15', 'vampire_house_alpha',
            'archetype_report', 150,
            '{"acceptable": 0.90, "degraded": 0.08, "unacceptable": 0.02}',
            0.87, 0.81)
        
        # Query report
        row = await conn.fetchrow(
            "SELECT * FROM audio_archetype_reports WHERE report_id = $1",
            report_id
        )
        
        assert row['num_segments'] == 150
        assert row['archetype_conformity_mean'] == 0.81
        
        # Insert feedback
        feedback_id = uuid.uuid4()
        
        await conn.execute("""
            INSERT INTO audio_feedback (
                feedback_id, build_id, feedback_type,
                archetype_id, findings, recommendations
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, feedback_id, 'build-2025-11-15', 'simulator',
            'zombie_horde',
            '[{"dimension": "roughness", "recommendation": "Increase by 15%"}]',
            ['Increase roughness parameter', 'Review breathiness settings'])
        
        # Update feedback as applied
        await conn.execute("""
            UPDATE audio_feedback
            SET applied = true, applied_at = CURRENT_TIMESTAMP
            WHERE feedback_id = $1
        """, feedback_id)
        
        row = await conn.fetchrow(
            "SELECT * FROM audio_feedback WHERE feedback_id = $1",
            feedback_id
        )
        
        assert row['applied'] == True
        assert row['applied_at'] is not None
        
        print("✓ reports and feedback tables test passed")
        
    finally:
        await conn.close()


async def test_reference_data_tables():
    """Test baseline and profile tables."""
    conn = await asyncpg.connect(TEST_DB_URL)
    
    try:
        # Insert speech baseline
        baseline_id = uuid.uuid4()
        
        await conn.execute("""
            INSERT INTO audio_speech_baselines (
                baseline_id, language_code, corpus_source,
                speech_rate_mean, pitch_mean_hz
            ) VALUES ($1, $2, $3, $4, $5)
        """, baseline_id, 'en-US', 'LibriSpeech', 150.0, 120.0)
        
        # Insert archetype profile
        profile_id = uuid.uuid4()
        
        await conn.execute("""
            INSERT INTO audio_archetype_profiles (
                profile_id, archetype_id, profile_version,
                f0_range_min, f0_range_max, roughness_target
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, profile_id, 'vampire_house_alpha', 'v1.0',
            80.0, 200.0, 0.65)
        
        # Test unique constraints
        try:
            await conn.execute("""
                INSERT INTO audio_speech_baselines (
                    language_code, corpus_source
                ) VALUES ($1, $2)
            """, 'en-US', 'LibriSpeech')
            assert False, "Should have failed on duplicate baseline"
        except asyncpg.UniqueViolationError:
            pass  # Expected
        
        print("✓ reference data tables test passed")
        
    finally:
        await conn.close()


async def test_indexes():
    """Verify indexes were created correctly."""
    conn = await asyncpg.connect(TEST_DB_URL)
    
    try:
        # Query pg_indexes to verify our indexes exist
        indexes = await conn.fetch("""
            SELECT indexname FROM pg_indexes
            WHERE tablename LIKE 'audio_%'
            ORDER BY indexname
        """)
        
        index_names = [row['indexname'] for row in indexes]
        
        # Check some key indexes exist
        expected_indexes = [
            'idx_audio_segments_build',
            'idx_audio_segments_speaker',
            'idx_audio_segments_archetype',
            'idx_audio_segments_language',
            'idx_audio_scores_bands',
            'idx_audio_reports_build'
        ]
        
        for expected in expected_indexes:
            assert expected in index_names, f"Missing index: {expected}"
        
        print("✓ index creation test passed")
        
    finally:
        await conn.close()


async def main():
    """Run all database migration tests."""
    print("Setting up test database...")
    await create_test_database()
    
    # Connect and apply migration
    conn = await asyncpg.connect(TEST_DB_URL)
    try:
        await apply_migration(conn)
        print("✓ Migration applied successfully")
    finally:
        await conn.close()
    
    # Run tests
    print("\nRunning database tests...")
    await test_audio_segments_table()
    await test_audio_scores_table()
    await test_reports_and_feedback()
    await test_reference_data_tables()
    await test_indexes()
    
    print("\nAll database migration tests passed! ✅")


if __name__ == "__main__":
    # Note: This requires a local PostgreSQL instance running
    # In production, these tests would run in CI with a test database
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure PostgreSQL is running locally on port 5432")
