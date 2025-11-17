"""
Comprehensive unit tests for IntelligibilityAnalyzer.
Tests all methods, edge cases, and configurations.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
import asyncio

from services.ethelred_audio_metrics.intelligibility_analyzer import (
    IntelligibilityAnalyzer,
    IntelligibilityConfig
)


class TestIntelligibilityAnalyzer:
    """Test suite for IntelligibilityAnalyzer."""
    
    @pytest.mark.unit
    def test_initialization_default_config(self):
        """Test analyzer initialization with default configuration."""
        analyzer = IntelligibilityAnalyzer()
        
        assert analyzer.sample_rate == 48000
        assert analyzer.config.sample_rate == 48000
        assert analyzer.config.excellent_threshold == 15.0
        assert analyzer.config.good_threshold == 10.0
        assert analyzer.config.fair_threshold == 5.0
    
    @pytest.mark.unit
    def test_initialization_custom_config(self, intelligibility_config):
        """Test analyzer initialization with custom configuration."""
        analyzer = IntelligibilityAnalyzer(
            sample_rate=16000,
            config=intelligibility_config
        )
        
        assert analyzer.sample_rate == 16000
        assert analyzer.config == intelligibility_config
    
    @pytest.mark.unit
    def test_analyze_clean_speech(self, sample_audio_48khz):
        """Test analysis of clean speech signal."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        score, band = analyzer.analyze(audio)
        
        assert isinstance(score, float)
        assert 0 <= score <= 30  # Reasonable range for SNR
        assert band in ['excellent', 'good', 'fair', 'degraded', 'unacceptable']
        
        # Clean speech should have good intelligibility
        assert score > 5.0
        assert band in ['excellent', 'good', 'fair']
    
    @pytest.mark.unit
    def test_analyze_noisy_speech(self, noisy_audio):
        """Test analysis of noisy speech signal."""
        audio, sr = noisy_audio
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        score, band = analyzer.analyze(audio)
        
        # Noisy speech should have lower intelligibility
        assert score < 10.0
        assert band in ['fair', 'degraded', 'unacceptable']
    
    @pytest.mark.unit
    def test_analyze_silent_audio(self, silent_audio):
        """Test analysis of silent audio."""
        audio, sr = silent_audio
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        score, band = analyzer.analyze(audio)
        
        # Silent audio should have very low score
        assert score == 0.0
        assert band == 'unacceptable'
    
    @pytest.mark.unit
    def test_analyze_empty_audio(self):
        """Test analysis of empty audio array."""
        analyzer = IntelligibilityAnalyzer()
        empty_audio = np.array([])
        
        score, band = analyzer.analyze(empty_audio)
        
        assert score == 0.0
        assert band == 'unacceptable'
    
    @pytest.mark.unit
    def test_analyze_very_short_audio(self):
        """Test analysis of very short audio (< 0.1s)."""
        analyzer = IntelligibilityAnalyzer()
        # 0.05 seconds of audio
        short_audio = np.random.randn(int(48000 * 0.05))
        
        score, band = analyzer.analyze(short_audio)
        
        # Should still return valid results
        assert isinstance(score, float)
        assert band in ['excellent', 'good', 'fair', 'degraded', 'unacceptable']
    
    @pytest.mark.unit
    def test_get_detailed_analysis(self, sample_audio_48khz):
        """Test detailed analysis with confidence scores."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        result = analyzer.get_detailed_analysis(audio)
        
        assert 'intelligibility_score' in result
        assert 'intelligibility_band' in result
        assert 'confidence' in result
        assert 'config' in result
        assert 'details' in result
        
        assert 0 <= result['confidence'] <= 1.0
        assert result['config']['sample_rate'] == sr
        
        # Check details
        details = result['details']
        assert 'snr_db' in details
        assert 'spectral_clarity' in details
        assert 'articulation_index' in details
        assert 'duration_seconds' in details
    
    @pytest.mark.unit
    def test_normalize_audio(self):
        """Test audio normalization with factor."""
        analyzer = IntelligibilityAnalyzer()
        
        # Test with various amplitudes
        test_cases = [
            (np.array([1.0, -1.0, 0.5]), 1.0),  # Already normalized
            (np.array([2.0, -2.0, 1.0]), 0.5),   # Needs scaling down
            (np.array([0.1, -0.1, 0.05]), 10.0), # Needs scaling up
            (np.array([0.0, 0.0, 0.0]), 1.0),    # All zeros
        ]
        
        for audio, expected_factor in test_cases:
            normalized, factor = analyzer._normalize_audio_with_factor(audio)
            
            if not np.all(audio == 0):
                assert np.max(np.abs(normalized)) <= 1.0
                assert np.isclose(factor, expected_factor, rtol=0.1)
            else:
                assert np.all(normalized == 0)
                assert factor == 1.0
    
    @pytest.mark.unit
    def test_compute_spectral_features_cached(self, sample_audio_48khz):
        """Test spectral feature computation and caching."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        # First call should compute
        fft1, spec1, freq1 = analyzer._compute_spectral_features_cached(audio)
        
        assert fft1 is not None
        assert spec1 is not None
        assert freq1 is not None
        
        # Second call should use cache
        fft2, spec2, freq2 = analyzer._compute_spectral_features_cached(audio)
        
        # Should be the same objects (cached)
        assert fft1 is fft2
        assert spec1 is spec2
        assert freq1 is freq2
        
        # Different audio should compute new features
        other_audio = audio * 0.5
        fft3, spec3, freq3 = analyzer._compute_spectral_features_cached(other_audio)
        
        assert fft3 is not fft1
        assert spec3 is not spec1
    
    @pytest.mark.unit
    def test_calculate_snr_with_confidence(self, sample_audio_48khz):
        """Test SNR calculation with confidence score."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        normalized, _ = analyzer._normalize_audio_with_factor(audio)
        snr, confidence = analyzer._calculate_snr_with_confidence(normalized)
        
        assert isinstance(snr, float)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1.0
        
        # For good audio, should have high confidence
        assert confidence > 0.5
    
    @pytest.mark.unit
    def test_calculate_spectral_clarity(self, sample_audio_48khz):
        """Test spectral clarity calculation."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        normalized, _ = analyzer._normalize_audio_with_factor(audio)
        clarity = analyzer._calculate_spectral_clarity_cached(normalized)
        
        assert isinstance(clarity, float)
        assert 0 <= clarity <= 1.0
    
    @pytest.mark.unit
    def test_calculate_articulation_index(self, sample_audio_48khz):
        """Test articulation index calculation."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        normalized, _ = analyzer._normalize_audio_with_factor(audio)
        ai = analyzer._calculate_articulation_index_cached(normalized)
        
        assert isinstance(ai, float)
        assert 0 <= ai <= 1.0
    
    @pytest.mark.unit
    def test_calculate_confidence(self):
        """Test confidence score calculation."""
        analyzer = IntelligibilityAnalyzer()
        
        test_cases = [
            # (snr_confidence, duration, norm_factor, expected_range)
            (0.9, 3.0, 1.0, (0.8, 1.0)),    # Good case
            (0.5, 0.3, 10.0, (0.2, 0.5)),   # Poor case
            (0.7, 1.0, 2.0, (0.5, 0.8)),    # Medium case
        ]
        
        for snr_conf, duration, norm_factor, expected_range in test_cases:
            confidence = analyzer._calculate_confidence(snr_conf, duration, norm_factor)
            
            assert expected_range[0] <= confidence <= expected_range[1]
    
    @pytest.mark.unit
    def test_detect_voice_activity(self, sample_audio_48khz):
        """Test voice activity detection."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        normalized, _ = analyzer._normalize_audio_with_factor(audio)
        active_segments = analyzer._detect_voice_activity(normalized)
        
        assert isinstance(active_segments, list)
        
        # Should detect some activity in speech signal
        assert len(active_segments) > 0
        
        # Each segment should be boolean array
        for segment in active_segments:
            assert isinstance(segment, np.ndarray)
            assert segment.dtype == bool
    
    @pytest.mark.unit
    def test_edge_case_single_sample(self):
        """Test with single sample audio."""
        analyzer = IntelligibilityAnalyzer()
        single_sample = np.array([0.5])
        
        score, band = analyzer.analyze(single_sample)
        
        assert score == 0.0
        assert band == 'unacceptable'
    
    @pytest.mark.unit
    def test_edge_case_nan_values(self):
        """Test handling of NaN values in audio."""
        analyzer = IntelligibilityAnalyzer()
        audio_with_nan = np.array([1.0, np.nan, 0.5, -0.5])
        
        # Should handle NaN gracefully
        score, band = analyzer.analyze(audio_with_nan)
        
        assert not np.isnan(score)
        assert band in ['excellent', 'good', 'fair', 'degraded', 'unacceptable']
    
    @pytest.mark.unit
    def test_edge_case_infinite_values(self):
        """Test handling of infinite values in audio."""
        analyzer = IntelligibilityAnalyzer()
        audio_with_inf = np.array([1.0, np.inf, 0.5, -np.inf])
        
        # Should handle infinity gracefully
        score, band = analyzer.analyze(audio_with_inf)
        
        assert not np.isinf(score)
        assert band in ['excellent', 'good', 'fair', 'degraded', 'unacceptable']
    
    @pytest.mark.unit
    def test_deprecated_methods_redirect(self, sample_audio_48khz):
        """Test that old method names still work (redirect to cached versions)."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        normalized, _ = analyzer._normalize_audio_with_factor(audio)
        
        # Old methods should still work
        clarity_old = analyzer._calculate_spectral_clarity(normalized)
        clarity_new = analyzer._calculate_spectral_clarity_cached(normalized)
        
        assert clarity_old == clarity_new
        
        ai_old = analyzer._calculate_articulation_index(normalized)
        ai_new = analyzer._calculate_articulation_index_cached(normalized)
        
        assert ai_old == ai_new
    
    @pytest.mark.unit
    @pytest.mark.parametrize("sample_rate", [8000, 16000, 22050, 44100, 48000])
    def test_different_sample_rates(self, sample_rate):
        """Test analyzer with different sample rates."""
        analyzer = IntelligibilityAnalyzer(sample_rate=sample_rate)
        
        # Generate audio at target sample rate
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 200 * t) + 0.1 * np.random.randn(len(t))
        
        score, band = analyzer.analyze(audio)
        
        assert isinstance(score, float)
        assert band in ['excellent', 'good', 'fair', 'degraded', 'unacceptable']
    
    @pytest.mark.unit
    def test_configuration_validation(self):
        """Test configuration parameter validation."""
        # Test with invalid thresholds
        config = IntelligibilityConfig(
            sample_rate=48000,
            excellent_threshold=5.0,
            good_threshold=10.0,  # Should be less than excellent
            fair_threshold=15.0   # Should be less than good
        )
        
        analyzer = IntelligibilityAnalyzer(config=config)
        
        # Analyzer should still work despite misconfigured thresholds
        audio = np.random.randn(48000)
        score, band = analyzer.analyze(audio)
        
        assert isinstance(score, float)
        assert isinstance(band, str)
    
    @pytest.mark.performance
    def test_performance_large_audio(self, performance_timer):
        """Test performance with large audio files."""
        analyzer = IntelligibilityAnalyzer()
        
        # 60 seconds of audio
        large_audio = np.random.randn(48000 * 60)
        
        with performance_timer as timer:
            score, band = analyzer.analyze(large_audio)
        
        # Should complete within reasonable time
        assert timer.elapsed < 5.0  # 5 seconds max
        
        # Check cache effectiveness
        with performance_timer as timer2:
            # Second analysis of same audio should be faster
            score2, band2 = analyzer.get_detailed_analysis(large_audio)
        
        # Cached operations should be faster
        assert timer2.elapsed < timer.elapsed
    
    @pytest.mark.unit
    def test_concurrent_analysis(self, sample_audio_48khz):
        """Test thread safety with concurrent analysis."""
        audio, sr = sample_audio_48khz
        analyzer = IntelligibilityAnalyzer(sample_rate=sr)
        
        # Generate different audio samples
        audio_samples = [
            audio * (0.5 + i * 0.1) for i in range(5)
        ]
        
        async def analyze_async(audio_data):
            return analyzer.analyze(audio_data)
        
        async def run_concurrent():
            tasks = [analyze_async(a) for a in audio_samples]
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(run_concurrent())
        
        # All results should be valid
        assert len(results) == 5
        for score, band in results:
            assert isinstance(score, float)
            assert band in ['excellent', 'good', 'fair', 'degraded', 'unacceptable']
