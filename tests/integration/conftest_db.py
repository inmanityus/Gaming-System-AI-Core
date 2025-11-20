"""
Database integration test configuration using testcontainers.
Provides real PostgreSQL instances for testing.
"""
import pytest
import pytest_asyncio
import asyncpg
import asyncio
import os
from testcontainers.postgres import PostgresContainer
from typing import AsyncGenerator, Dict, Any
import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def postgres_container():
    """
    Create a PostgreSQL container for the test session.
    This runs once per test session and is shared across all tests.
    """
    container = PostgresContainer(
        image="postgres:15-alpine",
        user="postgres",
        password="postgres",
        dbname="gaming_test"
    )
    
    # Start container
    container.start()
    
    # Log connection details
    logger.info(f"PostgreSQL container started on {container.get_connection_url()}")
    
    yield container
    
    # Cleanup
    container.stop()


@pytest.fixture(scope="session")
def postgres_connection_params(postgres_container) -> Dict[str, Any]:
    """Get connection parameters from the running container."""
    return {
        "host": postgres_container.get_container_host_ip(),
        "port": postgres_container.get_exposed_port(5432),
        "database": postgres_container.dbname,
        "user": postgres_container.user,
        "password": postgres_container.password
    }


@pytest_asyncio.fixture(scope="session")
async def postgres_pool_session(postgres_connection_params):
    """
    Create a session-scoped PostgreSQL connection pool.
    This pool persists for the entire test session.
    """
    pool = await asyncpg.create_pool(
        **postgres_connection_params,
        min_size=1,
        max_size=10,
        command_timeout=60
    )
    
    # Initialize database schema
    async with pool.acquire() as conn:
        # Run migrations or schema setup here
        await _initialize_database_schema(conn)
    
    yield pool
    
    await pool.close()


@pytest_asyncio.fixture
async def postgres_pool(postgres_pool_session):
    """
    Function-scoped pool that resets the database for each test.
    Uses the session pool but cleans data between tests.
    """
    # Clean all tables before each test
    async with postgres_pool_session.acquire() as conn:
        await _clean_database(conn)
    
    yield postgres_pool_session
    
    # Clean again after test to ensure no state leakage
    async with postgres_pool_session.acquire() as conn:
        await _clean_database(conn)


@pytest_asyncio.fixture
async def postgres_connection(postgres_pool):
    """Get a dedicated connection from the pool."""
    async with postgres_pool.acquire() as conn:
        # Begin transaction that will be rolled back
        tx = conn.transaction()
        await tx.start()
        
        yield conn
        
        # Rollback to keep tests isolated
        await tx.rollback()


async def _initialize_database_schema(conn: asyncpg.Connection):
    """Initialize the database schema for tests."""
    
    # Create extensions
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")
    
    # Create schemas
    await conn.execute("CREATE SCHEMA IF NOT EXISTS ethelred")
    await conn.execute("CREATE SCHEMA IF NOT EXISTS localization")
    await conn.execute("CREATE SCHEMA IF NOT EXISTS language")
    await conn.execute("CREATE SCHEMA IF NOT EXISTS users")
    
    # Audio metrics tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS ethelred.audio_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            audio_file_path TEXT NOT NULL,
            archetype VARCHAR(100),
            intelligibility_score NUMERIC(5,2),
            confidence_level NUMERIC(3,2),
            is_on_profile BOOLEAN,
            spectral_clarity NUMERIC(5,2),
            pitch_range_match NUMERIC(3,2),
            formant_accuracy NUMERIC(3,2),
            voice_texture JSONB,
            analysis_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Engagement metrics tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS ethelred.engagement_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            session_start TIMESTAMPTZ NOT NULL,
            session_end TIMESTAMPTZ,
            duration_minutes INTEGER,
            is_night_session BOOLEAN DEFAULT FALSE,
            is_early_morning BOOLEAN DEFAULT FALSE,
            events JSONB,
            addiction_indicators JSONB,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Localization tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS localization.content (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key VARCHAR(500) UNIQUE NOT NULL,
            category VARCHAR(100),
            content JSONB NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS localization.language_stats (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            language_code VARCHAR(10) NOT NULL,
            total_keys INTEGER DEFAULT 0,
            translated_keys INTEGER DEFAULT 0,
            validated_keys INTEGER DEFAULT 0,
            missing_keys INTEGER DEFAULT 0,
            last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(language_code)
        )
    """)
    
    # Language system tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS language.tts_cache (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            text_hash VARCHAR(64) UNIQUE NOT NULL,
            language_code VARCHAR(10) NOT NULL,
            voice_id VARCHAR(100),
            audio_data BYTEA,
            audio_format VARCHAR(20),
            duration_ms INTEGER,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            accessed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 1
        )
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS language.tts_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            language_code VARCHAR(10) NOT NULL,
            voice_id VARCHAR(100),
            generation_time_ms INTEGER,
            cache_hit BOOLEAN DEFAULT FALSE,
            text_length INTEGER,
            audio_duration_ms INTEGER,
            error_code VARCHAR(100),
            metadata JSONB
        )
    """)
    
    # User preferences table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users.preferences (
            user_id VARCHAR(255) PRIMARY KEY,
            language_code VARCHAR(10) DEFAULT 'en-US',
            audio_settings JSONB,
            accessibility_settings JSONB,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audio_metrics_user_timestamp 
        ON ethelred.audio_metrics(user_id, analysis_timestamp DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_engagement_sessions_user_start 
        ON ethelred.engagement_sessions(user_id, session_start DESC)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_localization_content_key 
        ON localization.content(key)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tts_cache_hash_lang 
        ON language.tts_cache(text_hash, language_code)
    """)
    
    logger.info("Database schema initialized successfully")


async def _clean_database(conn: asyncpg.Connection):
    """Clean all test data from database."""
    tables = [
        "ethelred.audio_metrics",
        "ethelred.engagement_sessions", 
        "localization.content",
        "localization.language_stats",
        "language.tts_cache",
        "language.tts_metrics",
        "users.preferences"
    ]
    
    for table in tables:
        await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
    
    logger.info("Database cleaned for next test")


# Test data fixtures
@pytest.fixture
async def sample_audio_metrics(postgres_connection):
    """Insert sample audio metrics data."""
    data = [
        {
            'user_id': 'test_user_1',
            'audio_file_path': '/audio/test1.ogg',
            'archetype': 'vampire_alpha',
            'intelligibility_score': 85.5,
            'confidence_level': 0.92,
            'is_on_profile': True,
            'spectral_clarity': 78.3,
            'pitch_range_match': 0.88,
            'formant_accuracy': 0.91,
            'voice_texture': {
                'roughness': 0.7,
                'breathiness': 0.3,
                'clarity': 0.8
            }
        },
        {
            'user_id': 'test_user_2',
            'audio_file_path': '/audio/test2.ogg',
            'archetype': 'human_agent',
            'intelligibility_score': 92.0,
            'confidence_level': 0.95,
            'is_on_profile': True,
            'spectral_clarity': 88.5,
            'pitch_range_match': 0.93,
            'formant_accuracy': 0.94,
            'voice_texture': {
                'roughness': 0.3,
                'breathiness': 0.2,
                'clarity': 0.9
            }
        }
    ]
    
    for record in data:
        await postgres_connection.execute("""
            INSERT INTO ethelred.audio_metrics 
            (user_id, audio_file_path, archetype, intelligibility_score, 
             confidence_level, is_on_profile, spectral_clarity, 
             pitch_range_match, formant_accuracy, voice_texture)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, 
        record['user_id'], record['audio_file_path'], record['archetype'],
        record['intelligibility_score'], record['confidence_level'],
        record['is_on_profile'], record['spectral_clarity'],
        record['pitch_range_match'], record['formant_accuracy'],
        record['voice_texture']
        )
    
    return data


@pytest.fixture  
async def sample_engagement_data(postgres_connection):
    """Insert sample engagement session data."""
    import datetime
    
    data = [
        {
            'user_id': 'test_user_1',
            'session_start': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4),
            'session_end': datetime.datetime.now(datetime.timezone.utc),
            'duration_minutes': 240,
            'is_night_session': True,
            'is_early_morning': False,
            'events': {
                'level_completes': 5,
                'deaths': 12,
                'restarts': 8
            },
            'addiction_indicators': {
                'consecutive_days': 5,
                'one_more_runs': 3
            }
        }
    ]
    
    for record in data:
        await postgres_connection.execute("""
            INSERT INTO ethelred.engagement_sessions
            (user_id, session_start, session_end, duration_minutes,
             is_night_session, is_early_morning, events, addiction_indicators)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        record['user_id'], record['session_start'], record['session_end'],
        record['duration_minutes'], record['is_night_session'],
        record['is_early_morning'], record['events'], record['addiction_indicators']
        )
    
    return data


@pytest.fixture
async def sample_localization_data(postgres_connection):
    """Insert sample localization data."""
    content = {
        'ui.button.start': {
            'en-US': {'text': 'Start Game', 'validated': True},
            'ja-JP': {'text': 'ゲーム開始', 'validated': True},
            'es-ES': {'text': 'Iniciar Juego', 'validated': True}
        },
        'dialogue.intro.greeting': {
            'en-US': {
                'text': 'Welcome, {player_name}!',
                'audio_file': 'intro_greeting_en.ogg'
            },
            'ja-JP': {
                'text': 'ようこそ、{player_name}さん！',
                'tts_enabled': True
            }
        }
    }
    
    for key, translations in content.items():
        await postgres_connection.execute("""
            INSERT INTO localization.content (key, category, content)
            VALUES ($1, $2, $3)
        """, key, key.split('.')[0], translations)
    
    # Insert language stats
    stats = [
        ('en-US', 100, 100, 100, 0),
        ('ja-JP', 100, 98, 95, 2),
        ('es-ES', 100, 90, 85, 10)
    ]
    
    for lang, total, trans, valid, missing in stats:
        await postgres_connection.execute("""
            INSERT INTO localization.language_stats
            (language_code, total_keys, translated_keys, validated_keys, missing_keys)
            VALUES ($1, $2, $3, $4, $5)
        """, lang, total, trans, valid, missing)
    
    return content
