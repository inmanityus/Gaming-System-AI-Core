"""
Simplified test configuration without external database dependencies.
Used for basic verification tests.
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
import asyncio

# Test data directories
TEST_DATA_DIR = Path(__file__).parent / "test_data"
AUDIO_DATA_DIR = TEST_DATA_DIR / "audio"


@pytest.fixture
def sample_audio_48khz():
    """Generate sample audio at 48kHz."""
    duration = 3.0
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate speech-like signal
    f0 = 150 + 50 * np.sin(2 * np.pi * 0.5 * t)
    signal = np.zeros_like(t)
    
    for harmonic in range(1, 5):
        signal += (1.0 / harmonic) * np.sin(2 * np.pi * f0 * harmonic * t)
    
    # Add formants
    formants = [700, 1220, 2600]
    for f in formants:
        resonance = np.sin(2 * np.pi * f * t) * np.exp(-t * 0.5)
        signal += 0.3 * resonance
    
    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.8
    
    return signal, sample_rate


@pytest.fixture
def mock_postgres_pool():
    """Simple mock for PostgreSQL pool."""
    pool = AsyncMock()
    conn = AsyncMock()
    
    # Setup basic mock behavior
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    
    pool.acquire = MagicMock()
    pool.acquire.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.__aexit__ = AsyncMock(return_value=None)
    
    return pool
