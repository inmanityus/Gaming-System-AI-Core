"""
Shared test fixtures and configuration for all tests.
Provides common test data, mocks, and utilities.
"""
import pytest
import asyncio
import os
import tempfile
import numpy as np
from unittest.mock import Mock, AsyncMock, MagicMock
from pathlib import Path
import json
import asyncpg

# Test data directories
TEST_DATA_DIR = Path(__file__).parent / "test_data"
AUDIO_DATA_DIR = TEST_DATA_DIR / "audio"
LOCALIZATION_DATA_DIR = TEST_DATA_DIR / "localization"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def postgres_pool():
    """Create a test PostgreSQL connection pool."""
    # Use test database
    pool = await asyncpg.create_pool(
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=os.getenv("TEST_DB_PORT", 5443),
        database=os.getenv("TEST_DB_NAME", "gaming_test"),
        user=os.getenv("TEST_DB_USER", "postgres"),
        password=os.getenv("TEST_DB_PASSWORD", "postgres"),
        min_size=1,
        max_size=5
    )
    
    yield pool
    
    await pool.close()


@pytest.fixture
def mock_postgres_pool():
    """Mock PostgreSQL pool for unit tests."""
    pool = AsyncMock()
    
    # Mock connection
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    
    # Mock transaction
    conn.transaction = MagicMock()
    conn.transaction.__aenter__ = AsyncMock(return_value=None)
    conn.transaction.__aexit__ = AsyncMock(return_value=None)
    
    # Pool acquire returns connection
    pool.acquire = MagicMock()
    pool.acquire.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.__aexit__ = AsyncMock(return_value=None)
    
    return pool


# Audio test data generators
@pytest.fixture
def sample_audio_48khz():
    """Generate sample audio at 48kHz."""
    duration = 3.0  # seconds
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate speech-like signal
    # Fundamental frequency (varies like speech)
    f0 = 150 + 50 * np.sin(2 * np.pi * 0.5 * t)  # Varying pitch
    
    # Add harmonics
    signal = np.zeros_like(t)
    for harmonic in range(1, 5):
        signal += (1.0 / harmonic) * np.sin(2 * np.pi * f0 * harmonic * t)
    
    # Add formants (resonances)
    # F1 around 700 Hz, F2 around 1220 Hz, F3 around 2600 Hz
    formants = [700, 1220, 2600]
    for f in formants:
        resonance = np.sin(2 * np.pi * f * t) * np.exp(-t * 0.5)
        signal += 0.3 * resonance
    
    # Add some noise
    noise = np.random.normal(0, 0.1, signal.shape)
    signal += noise
    
    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.8
    
    return signal, sample_rate


@pytest.fixture
def sample_audio_16khz():
    """Generate sample audio at 16kHz."""
    signal_48k, _ = sample_audio_48khz()
    # Simple downsampling (production would use proper resampling)
    signal_16k = signal_48k[::3]  # 48k / 3 = 16k
    return signal_16k, 16000


@pytest.fixture
def noisy_audio():
    """Generate noisy audio for testing."""
    duration = 2.0
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Speech signal
    speech = np.sin(2 * np.pi * 200 * t) * 0.5
    
    # Heavy noise
    noise = np.random.normal(0, 0.8, speech.shape)
    
    return speech + noise, sample_rate


@pytest.fixture
def silent_audio():
    """Generate silent audio."""
    duration = 1.0
    sample_rate = 48000
    return np.zeros(int(sample_rate * duration)), sample_rate


# Localization test data
@pytest.fixture
def sample_localization_content():
    """Sample localization content for testing."""
    return {
        'ui.button.start': {
            'en-US': {'text': 'Start Game', 'validated': True},
            'ja-JP': {'text': 'ゲーム開始', 'validated': True},
            'es-ES': {'text': 'Iniciar Juego', 'validated': True},
            'zh-CN': {'text': '开始游戏', 'validated': True}
        },
        'dialogue.intro.greeting': {
            'en-US': {
                'text': 'Welcome, {player_name}!',
                'audio_file': 'intro_greeting_en.ogg',
                'speaker': 'narrator'
            },
            'ja-JP': {
                'text': 'ようこそ、{player_name}さん！',
                'tts_enabled': True,
                'speaker': 'narrator'
            }
        },
        'error.network.timeout': {
            'en-US': {'text': 'Network connection timed out. Please try again.'},
            'fr-FR': {'text': 'Connexion réseau expirée. Veuillez réessayer.'},
            'de-DE': {'text': 'Netzwerkverbindung abgelaufen. Bitte versuchen Sie es erneut.'}
        }
    }


@pytest.fixture
def archetype_profiles():
    """Sample archetype profiles for testing."""
    return {
        'vampire_alpha': {
            'pitch_range': (80, 160),
            'formant_ratios': [1.0, 1.8, 2.6],
            'voice_texture': {
                'roughness': 0.7,
                'breathiness': 0.3,
                'clarity': 0.8
            }
        },
        'human_agent': {
            'pitch_range': (100, 200),
            'formant_ratios': [1.0, 1.6, 2.4],
            'voice_texture': {
                'roughness': 0.3,
                'breathiness': 0.2,
                'clarity': 0.9
            }
        },
        'corpse_tender': {
            'pitch_range': (60, 120),
            'formant_ratios': [1.0, 1.4, 2.2],
            'voice_texture': {
                'roughness': 0.9,
                'breathiness': 0.6,
                'clarity': 0.4
            }
        }
    }


@pytest.fixture
def engagement_session_data():
    """Sample engagement session data."""
    return [
        {
            'user_id': 'test_user_1',
            'session_start': '2024-11-15T22:30:00Z',
            'session_end': '2024-11-16T02:45:00Z',
            'events': [
                {'type': 'game_start', 'timestamp': '2024-11-15T22:30:00Z'},
                {'type': 'level_complete', 'timestamp': '2024-11-15T23:15:00Z'},
                {'type': 'death', 'timestamp': '2024-11-15T23:45:00Z'},
                {'type': 'restart', 'timestamp': '2024-11-15T23:46:00Z'},
                {'type': 'game_end', 'timestamp': '2024-11-16T02:45:00Z'}
            ]
        },
        {
            'user_id': 'test_user_2',
            'session_start': '2024-11-15T14:00:00Z',
            'session_end': '2024-11-15T14:45:00Z',
            'events': [
                {'type': 'game_start', 'timestamp': '2024-11-15T14:00:00Z'},
                {'type': 'level_complete', 'timestamp': '2024-11-15T14:30:00Z'},
                {'type': 'game_end', 'timestamp': '2024-11-15T14:45:00Z'}
            ]
        }
    ]


# Configuration fixtures
@pytest.fixture
def intelligibility_config():
    """Test configuration for intelligibility analyzer."""
    from services.ethelred_audio_metrics.intelligibility_analyzer import IntelligibilityConfig
    return IntelligibilityConfig(
        sample_rate=48000,
        vad_energy_threshold=0.01,
        vad_frequency_threshold=0.1,
        fft_size=2048,
        hop_length=512,
        n_fft_intelligibility=4096,
        excellent_threshold=15.0,
        good_threshold=10.0,
        fair_threshold=5.0,
        min_confidence_duration=0.5,
        confidence_snr_weight=0.6
    )


@pytest.fixture
def archetype_config():
    """Test configuration for archetype analyzer."""
    from services.ethelred_audio_metrics.archetype_analyzer import ArchetypeAnalyzerConfig
    return ArchetypeAnalyzerConfig(
        on_profile_threshold=0.8,
        too_clean_threshold=0.95,
        too_flat_threshold=0.3,
        profile_source="memory",
        profile_file_path=None,
        profile_db_table=None,
        min_pitch_values=10,
        pitch_range_tolerance=0.2,
        formant_range_tolerance=0.15,
        lpc_order=16,
        pre_emphasis=0.97
    )


@pytest.fixture
def addiction_config():
    """Test configuration for addiction indicators."""
    from services.ethelred_engagement.addiction_indicators import AddictionIndicatorConfig
    return AddictionIndicatorConfig(
        night_time_start=22,
        night_time_end=6,
        early_morning_start=2,
        early_morning_end=6,
        excessive_session_hours=3.0,
        one_more_run_window_minutes=5,
        high_night_ratio=0.3,
        concerning_night_ratio=0.5,
        high_one_more_ratio=0.2,
        extreme_one_more_ratio=0.4,
        concerning_session_hours=4.0,
        extreme_session_hours=6.0,
        concerning_consecutive_days=7,
        high_consecutive_days=14,
        concerning_daily_hours=4.0,
        extreme_daily_hours=8.0
    )


@pytest.fixture
def safety_config():
    """Test configuration for safety constraints."""
    from services.ethelred_engagement.safety_constraints import SafetyConstraintsConfig
    return SafetyConstraintsConfig(
        min_cohort_size=100,
        max_hourly_checks_dashboard=10,
        max_daily_checks_report=5,
        max_hourly_checks_api=60,
        max_checks_real_time=0,
        real_time_latency_threshold_ms=100,
        optimization_keywords=[
            'maximize', 'optimize', 'increase', 'boost',
            'enhance', 'improve', 'growth'
        ]
    )


# Mock services
@pytest.fixture
def mock_localization_service():
    """Mock localization service."""
    service = AsyncMock()
    service.get_content = AsyncMock(return_value={
        'text': 'Test content',
        'validated': True
    })
    service.get_supported_languages = AsyncMock(return_value=[
        'en-US', 'ja-JP', 'es-ES', 'zh-CN', 'ko-KR'
    ])
    service.get_language_statistics = AsyncMock(return_value={
        'total_keys': 1000,
        'translated_keys': 980,
        'missing_keys': 20,
        'validated_keys': 950
    })
    return service


@pytest.fixture
def mock_language_gateway():
    """Mock language gateway."""
    gateway = AsyncMock()
    gateway.synthesize_speech = AsyncMock(return_value={
        'audio_data': b'mock_audio_data',
        'duration_ms': 2500,
        'format': 'mp3'
    })
    gateway.get_tts_metrics = AsyncMock(return_value={
        'avg_generation_time_ms': 150,
        'cache_hit_rate': 0.85,
        'total_requests': 1000
    })
    return gateway


# Test data creation utilities
@pytest.fixture(autouse=True)
def ensure_test_directories():
    """Ensure test data directories exist."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    AUDIO_DATA_DIR.mkdir(exist_ok=True)
    LOCALIZATION_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# Performance measurement utilities
@pytest.fixture
def performance_timer():
    """Timer for performance measurements."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None
        
        def start(self):
            self.start_time = time.perf_counter()
            return self
        
        def stop(self):
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed
        
        def __enter__(self):
            self.start()
            return self
        
        def __exit__(self, *args):
            self.stop()
    
    return Timer


# Async utilities
@pytest.fixture
def async_timeout():
    """Async timeout context manager."""
    async def _timeout(seconds):
        async with asyncio.timeout(seconds):
            yield
    return _timeout


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        'TESTING': 'true',
        'LOG_LEVEL': 'DEBUG',
        'DB_HOST': 'localhost',
        'DB_PORT': '5443',
        'DB_NAME': 'gaming_test',
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'postgres',
        'ETHELRED_SAMPLE_RATE': '48000',
        'MIN_COHORT_SIZE': '10',  # Lower for testing
        'ADDICTION_NIGHT_START': '22',
        'ADDICTION_NIGHT_END': '6'
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
