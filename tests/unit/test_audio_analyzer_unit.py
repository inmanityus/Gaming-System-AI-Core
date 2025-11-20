"""
Unit tests for audio analyzer components.
Tests individual components in isolation.
"""
import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.ethelred_audio_metrics.intelligibility_analyzer import (
    IntelligibilityAnalyzer,
    IntelligibilityConfig
)


class TestIntelligibilityAnalyzer:
    """Unit tests for IntelligibilityAnalyzer."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return IntelligibilityConfig(
            sample_rate=48000,
            vad_energy_threshold=0.01,
            vad_frequency_threshold=0.1,
            fft_size=2048,
            hop_length=512,
            n_fft_intelligibility=4096
        )
    
    @pytest.fixture
    def analyzer(self, config):
        """Create analyzer instance."""
        return IntelligibilityAnalyzer(config=config)
    
    def test_analyzer_initialization(self, analyzer, config):
        """Test analyzer initializes correctly."""
        assert analyzer.config == config
        assert analyzer.sample_rate == config.sample_rate
        assert analyzer.fft_size == config.fft_size
    
    def test_normalize_audio(self, analyzer):
        """Test audio normalization."""
        # Test with various input types
        audio = np.array([0.5, -0.5, 1.0, -1.0])
        normalized = analyzer._normalize_audio(audio)
        
        assert np.max(np.abs(normalized)) <= 1.0
        assert normalized.dtype == np.float32
    
    def test_normalize_audio_silence(self, analyzer):
        """Test normalization of silent audio."""
        audio = np.zeros(1000)
        normalized = analyzer._normalize_audio(audio)
        
        assert np.all(normalized == 0)
        assert normalized.dtype == np.float32
    
    @pytest.mark.asyncio
    async def test_analyze_pure_tone(self, analyzer):
        """Test analysis of pure tone."""
        # Generate 1 second of 440Hz tone
        duration = 1.0
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        
        result = await analyzer.analyze(audio, sample_rate, user_id="test_user")
        
        assert "score" in result
        assert "confidence" in result
        assert "metrics" in result
        assert 0 <= result["score"] <= 100
        assert 0 <= result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_with_db_pool(self, analyzer):
        """Test analysis with database pool."""
        # Mock database pool
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.__aenter__.return_value = mock_conn
        
        analyzer.db_pool = mock_pool
        
        # Generate test audio
        audio = np.random.randn(48000)  # 1 second of noise
        
        result = await analyzer.analyze(
            audio,
            48000,
            user_id="test_user",
            audio_file_path="/test/audio.wav"
        )
        
        # Verify database interaction
        mock_pool.acquire.assert_called_once()
        mock_conn.execute.assert_called_once()
    
    def test_spectral_clarity_calculation(self, analyzer):
        """Test spectral clarity calculation."""
        # Create spectrum with clear peaks
        spectrum = np.zeros(1000)
        spectrum[100] = 1.0  # Peak at bin 100
        spectrum[200] = 0.8  # Peak at bin 200
        spectrum[300] = 0.6  # Peak at bin 300
        
        clarity = analyzer._calculate_spectral_clarity(spectrum)
        
        assert isinstance(clarity, float)
        assert 0 <= clarity <= 100
    
    def test_snr_estimation(self, analyzer):
        """Test SNR estimation."""
        # Generate signal with known SNR
        signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 48000))
        noise = np.random.normal(0, 0.1, 48000)
        mixed = signal + noise
        
        estimated_snr = analyzer._estimate_snr(mixed)
        
        assert isinstance(estimated_snr, float)
        # Should be positive for this signal
        assert estimated_snr > 0
    
    def test_vad_detection(self, analyzer):
        """Test voice activity detection."""
        # Generate audio with speech and silence
        duration = 2.0
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # First half: speech-like signal
        speech = np.sin(2 * np.pi * 150 * t[:len(t)//2])
        # Second half: silence
        silence = np.zeros(len(t)//2)
        
        audio = np.concatenate([speech, silence])
        
        vad_frames = analyzer._detect_voice_activity(audio)
        
        assert isinstance(vad_frames, np.ndarray)
        assert vad_frames.dtype == bool
        # Should detect more activity in first half
        assert np.sum(vad_frames[:len(vad_frames)//2]) > np.sum(vad_frames[len(vad_frames)//2:])
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_sample_rate(self, analyzer):
        """Test error handling for invalid sample rate."""
        audio = np.random.randn(1000)
        
        with pytest.raises(ValueError):
            await analyzer.analyze(audio, sample_rate=0, user_id="test")
    
    @pytest.mark.asyncio
    async def test_error_handling_empty_audio(self, analyzer):
        """Test error handling for empty audio."""
        audio = np.array([])
        
        result = await analyzer.analyze(audio, 48000, user_id="test")
        
        # Should handle gracefully
        assert result["score"] == 0
        assert result["confidence"] == 0


class TestIntelligibilityConfig:
    """Test configuration validation."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = IntelligibilityConfig()
        
        assert config.sample_rate == 48000
        assert config.vad_energy_threshold > 0
        assert config.fft_size > 0
        assert config.hop_length > 0
        assert config.hop_length < config.fft_size
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = IntelligibilityConfig(
            sample_rate=16000,
            fft_size=1024,
            hop_length=256,
            excellent_threshold=20.0
        )
        
        assert config.sample_rate == 16000
        assert config.fft_size == 1024
        assert config.hop_length == 256
        assert config.excellent_threshold == 20.0
    
    def test_config_validation(self):
        """Test configuration validation."""
        # This would test any validation logic in the config class
        pass


class TestAudioUtilities:
    """Test audio utility functions."""
    
    def test_compute_spectral_features(self):
        """Test spectral feature computation."""
        # This would test any utility functions
        pass
    
    def test_frame_audio(self):
        """Test audio framing."""
        # This would test frame extraction
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
