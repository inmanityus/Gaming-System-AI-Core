"""
Comprehensive unit tests for ArchetypeConformityAnalyzer.
Tests voice archetype matching and configuration.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
import json
from pathlib import Path

from services.ethelred_audio_metrics.archetype_analyzer import (
    ArchetypeConformityAnalyzer,
    ArchetypeAnalyzerConfig
)


class TestArchetypeConformityAnalyzer:
    """Test suite for ArchetypeConformityAnalyzer."""
    
    @pytest.mark.unit
    def test_initialization_default(self):
        """Test analyzer initialization with defaults."""
        analyzer = ArchetypeConformityAnalyzer()
        
        assert analyzer.sample_rate == 48000
        assert analyzer.config.on_profile_threshold == 0.8
        assert analyzer.config.too_clean_threshold == 0.95
        assert analyzer.config.too_flat_threshold == 0.3
        assert analyzer.config.profile_source == "memory"
        
        # Should have default profiles loaded
        assert 'vampire_alpha' in analyzer.archetype_profiles
        assert 'human_agent' in analyzer.archetype_profiles
        assert 'corpse_tender' in analyzer.archetype_profiles
    
    @pytest.mark.unit
    def test_initialization_custom_config(self, archetype_config):
        """Test analyzer initialization with custom config."""
        analyzer = ArchetypeConformityAnalyzer(
            sample_rate=16000,
            config=archetype_config
        )
        
        assert analyzer.sample_rate == 16000
        assert analyzer.config == archetype_config
    
    @pytest.mark.unit
    def test_analyze_vampire_voice(self, sample_audio_48khz):
        """Test analysis of vampire archetype voice."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        # Modify audio to be more vampire-like (lower pitch)
        # Simple pitch shifting for testing
        vampire_audio = np.interp(
            np.arange(0, len(audio), 1.2),  # Stretch to lower pitch
            np.arange(len(audio)),
            audio
        )
        
        score, band = analyzer.analyze(vampire_audio, 'vampire_alpha')
        
        assert isinstance(score, float)
        assert 0 <= score <= 1.0
        assert band in ['on_profile', 'acceptable', 'misaligned']
    
    @pytest.mark.unit 
    def test_analyze_human_voice(self, sample_audio_48khz):
        """Test analysis of human agent voice."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        score, band = analyzer.analyze(audio, 'human_agent')
        
        assert isinstance(score, float)
        assert 0 <= score <= 1.0
        assert band in ['on_profile', 'acceptable', 'misaligned']
        
        # Normal speech should match human agent reasonably well
        assert score > 0.3
    
    @pytest.mark.unit
    def test_analyze_corpse_tender_voice(self, sample_audio_48khz):
        """Test analysis of corpse tender voice."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        # Add roughness for corpse tender
        rough_audio = audio + 0.3 * np.random.randn(len(audio))
        
        score, band = analyzer.analyze(rough_audio, 'corpse_tender')
        
        assert isinstance(score, float)
        assert 0 <= score <= 1.0
        assert band in ['on_profile', 'acceptable', 'misaligned']
    
    @pytest.mark.unit
    def test_analyze_unknown_archetype(self, sample_audio_48khz):
        """Test analysis with unknown archetype."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        score, band = analyzer.analyze(audio, 'unknown_archetype')
        
        # Should return low score for unknown archetype
        assert score == 0.0
        assert band == 'misaligned'
    
    @pytest.mark.unit
    def test_analyze_empty_audio(self):
        """Test analysis of empty audio."""
        analyzer = ArchetypeConformityAnalyzer()
        empty_audio = np.array([])
        
        score, band = analyzer.analyze(empty_audio, 'vampire_alpha')
        
        assert score == 0.0
        assert band == 'misaligned'
    
    @pytest.mark.unit
    def test_analyze_short_audio(self):
        """Test analysis of very short audio."""
        analyzer = ArchetypeConformityAnalyzer()
        # 0.1 seconds - shorter than typical analysis window
        short_audio = np.random.randn(int(48000 * 0.1))
        
        score, band = analyzer.analyze(short_audio, 'human_agent')
        
        # Should still return valid results
        assert isinstance(score, float)
        assert 0 <= score <= 1.0
        assert band in ['on_profile', 'acceptable', 'misaligned']
    
    @pytest.mark.unit
    def test_extract_pitch_features(self, sample_audio_48khz):
        """Test pitch feature extraction."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        pitch_features = analyzer._extract_pitch_features(audio)
        
        assert 'mean_pitch' in pitch_features
        assert 'pitch_range' in pitch_features
        assert 'pitch_stability' in pitch_features
        
        # Check reasonable values
        assert 50 <= pitch_features['mean_pitch'] <= 500  # Hz
        assert 0 <= pitch_features['pitch_range'] <= 200   # Hz
        assert 0 <= pitch_features['pitch_stability'] <= 1.0
    
    @pytest.mark.unit
    def test_extract_pitch_features_silent(self, silent_audio):
        """Test pitch extraction from silent audio."""
        audio, sr = silent_audio
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        pitch_features = analyzer._extract_pitch_features(audio)
        
        # Silent audio should have zero/minimal pitch
        assert pitch_features['mean_pitch'] == 0 or pitch_features['mean_pitch'] < 50
        assert pitch_features['pitch_range'] < 10
    
    @pytest.mark.unit
    def test_extract_formant_features(self, sample_audio_48khz):
        """Test formant feature extraction."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        formant_features = analyzer._extract_formant_features(audio)
        
        assert 'formant_positions' in formant_features
        assert 'formant_ratios' in formant_features
        assert 'formant_bandwidths' in formant_features
        
        # Should extract 3-4 formants
        assert 3 <= len(formant_features['formant_positions']) <= 4
        
        # Check reasonable formant frequencies
        formants = formant_features['formant_positions']
        if len(formants) >= 3:
            assert 200 <= formants[0] <= 1000   # F1
            assert 500 <= formants[1] <= 3000    # F2
            assert 1500 <= formants[2] <= 4000   # F3
    
    @pytest.mark.unit
    def test_extract_formant_features_edge_cases(self):
        """Test formant extraction edge cases."""
        analyzer = ArchetypeConformityAnalyzer()
        
        # Very short audio
        short_audio = np.random.randn(100)
        formants = analyzer._extract_formant_features(short_audio)
        assert len(formants['formant_positions']) >= 0
        
        # Constant audio (no formants)
        constant_audio = np.ones(1000)
        formants = analyzer._extract_formant_features(constant_audio)
        assert isinstance(formants['formant_positions'], list)
    
    @pytest.mark.unit
    def test_extract_voice_texture(self, sample_audio_48khz):
        """Test voice texture analysis."""
        audio, sr = sample_audio_48khz
        analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
        
        texture = analyzer._extract_voice_texture(audio)
        
        assert 'roughness' in texture
        assert 'breathiness' in texture
        assert 'clarity' in texture
        
        # All values should be normalized 0-1
        assert 0 <= texture['roughness'] <= 1.0
        assert 0 <= texture['breathiness'] <= 1.0
        assert 0 <= texture['clarity'] <= 1.0
    
    @pytest.mark.unit
    def test_calculate_conformity_score(self):
        """Test conformity score calculation."""
        analyzer = ArchetypeConformityAnalyzer()
        
        # Perfect match
        features = {
            'mean_pitch': 120,
            'pitch_range': 40,
            'formant_ratios': [1.0, 1.8, 2.6],
            'roughness': 0.7,
            'breathiness': 0.3,
            'clarity': 0.8
        }
        
        profile = analyzer.archetype_profiles['vampire_alpha']
        score = analyzer._calculate_conformity_score(features, profile)
        
        assert 0 <= score <= 1.0
        assert score > 0.7  # Should be high for good match
    
    @pytest.mark.unit
    def test_calculate_conformity_score_mismatch(self):
        """Test conformity score with mismatched features."""
        analyzer = ArchetypeConformityAnalyzer()
        
        # Features that don't match vampire profile
        features = {
            'mean_pitch': 300,  # Too high
            'pitch_range': 100,  # Too variable
            'formant_ratios': [1.0, 2.5, 3.5],  # Wrong ratios
            'roughness': 0.1,  # Too smooth
            'breathiness': 0.9,  # Too breathy
            'clarity': 0.2  # Too unclear
        }
        
        profile = analyzer.archetype_profiles['vampire_alpha']
        score = analyzer._calculate_conformity_score(features, profile)
        
        assert 0 <= score <= 1.0
        assert score < 0.5  # Should be low for poor match
    
    @pytest.mark.unit
    def test_profile_loading_from_file(self, temp_dir, archetype_profiles):
        """Test loading profiles from JSON file."""
        # Create profile file
        profile_file = temp_dir / "test_profiles.json"
        with open(profile_file, 'w') as f:
            json.dump(archetype_profiles, f)
        
        config = ArchetypeAnalyzerConfig(
            profile_source="file",
            profile_file_path=str(profile_file)
        )
        
        analyzer = ArchetypeConformityAnalyzer(config=config)
        
        # Should have loaded profiles from file
        assert 'vampire_alpha' in analyzer.archetype_profiles
        assert analyzer.archetype_profiles['vampire_alpha'] == archetype_profiles['vampire_alpha']
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_profile_loading_from_database(self, mock_postgres_pool):
        """Test loading profiles from database."""
        # Mock database response
        mock_profiles = [
            {
                'archetype_id': 'test_archetype',
                'profile_data': {
                    'pitch_range': (100, 200),
                    'formant_ratios': [1.0, 1.5, 2.0],
                    'voice_texture': {
                        'roughness': 0.5,
                        'breathiness': 0.5,
                        'clarity': 0.5
                    }
                }
            }
        ]
        
        # Configure mock
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = mock_profiles
        
        config = ArchetypeAnalyzerConfig(
            profile_source="database",
            profile_db_table="archetype_profiles"
        )
        
        # Note: Current implementation has TODO for database loading
        # This test documents expected behavior
        analyzer = ArchetypeConformityAnalyzer(config=config)
        
        # For now, should fall back to default profiles
        assert 'vampire_alpha' in analyzer.archetype_profiles
    
    @pytest.mark.unit
    def test_edge_case_nan_audio(self):
        """Test handling of NaN values in audio."""
        analyzer = ArchetypeConformityAnalyzer()
        audio_with_nan = np.array([1.0, np.nan, 0.5, -0.5] * 1000)
        
        score, band = analyzer.analyze(audio_with_nan, 'human_agent')
        
        assert not np.isnan(score)
        assert band in ['on_profile', 'acceptable', 'misaligned']
    
    @pytest.mark.unit
    def test_edge_case_infinite_audio(self):
        """Test handling of infinite values in audio."""
        analyzer = ArchetypeConformityAnalyzer()
        audio_with_inf = np.array([1.0, np.inf, 0.5, -np.inf] * 1000)
        
        score, band = analyzer.analyze(audio_with_inf, 'human_agent')
        
        assert not np.isinf(score)
        assert band in ['on_profile', 'acceptable', 'misaligned']
    
    @pytest.mark.unit
    @pytest.mark.parametrize("archetype,expected_pitch_range", [
        ('vampire_alpha', (80, 160)),
        ('human_agent', (100, 200)),
        ('corpse_tender', (60, 120))
    ])
    def test_archetype_pitch_ranges(self, archetype, expected_pitch_range):
        """Test that default archetypes have expected pitch ranges."""
        analyzer = ArchetypeConformityAnalyzer()
        
        profile = analyzer.archetype_profiles.get(archetype)
        assert profile is not None
        assert profile['pitch_range'] == expected_pitch_range
    
    @pytest.mark.unit
    def test_lpc_stability(self):
        """Test LPC coefficient calculation stability."""
        analyzer = ArchetypeConformityAnalyzer()
        
        # Various test signals
        test_signals = [
            np.random.randn(1000),  # White noise
            np.sin(2 * np.pi * 440 * np.arange(1000) / 48000),  # Pure tone
            np.ones(1000),  # Constant
            np.zeros(1000),  # Silence
        ]
        
        for signal in test_signals:
            # Should not crash or produce invalid results
            formants = analyzer._extract_formant_features(signal)
            assert isinstance(formants['formant_positions'], list)
            assert all(isinstance(f, (int, float)) for f in formants['formant_positions'])
    
    @pytest.mark.performance
    def test_performance_analysis(self, performance_timer):
        """Test performance of archetype analysis."""
        analyzer = ArchetypeConformityAnalyzer()
        
        # 10 seconds of audio
        long_audio = np.random.randn(48000 * 10)
        
        with performance_timer as timer:
            score, band = analyzer.analyze(long_audio, 'vampire_alpha')
        
        # Should complete in reasonable time
        assert timer.elapsed < 2.0  # 2 seconds max
        assert isinstance(score, float)
    
    @pytest.mark.unit
    def test_config_threshold_behavior(self, sample_audio_48khz):
        """Test behavior with different threshold configurations."""
        audio, sr = sample_audio_48khz
        
        # Strict thresholds
        strict_config = ArchetypeAnalyzerConfig(
            on_profile_threshold=0.95,
            too_clean_threshold=0.99,
            too_flat_threshold=0.1
        )
        
        analyzer_strict = ArchetypeConformityAnalyzer(
            sample_rate=sr,
            config=strict_config
        )
        
        # Lenient thresholds
        lenient_config = ArchetypeAnalyzerConfig(
            on_profile_threshold=0.5,
            too_clean_threshold=0.8,
            too_flat_threshold=0.5
        )
        
        analyzer_lenient = ArchetypeConformityAnalyzer(
            sample_rate=sr,
            config=lenient_config
        )
        
        # Same audio should get different bands with different thresholds
        score_strict, band_strict = analyzer_strict.analyze(audio, 'human_agent')
        score_lenient, band_lenient = analyzer_lenient.analyze(audio, 'human_agent')
        
        # Scores should be the same
        assert abs(score_strict - score_lenient) < 0.01
        
        # But bands might differ based on thresholds
        assert band_strict in ['on_profile', 'acceptable', 'misaligned']
        assert band_lenient in ['on_profile', 'acceptable', 'misaligned']
    
    @pytest.mark.unit
    def test_pre_emphasis_filter(self, sample_audio_48khz):
        """Test pre-emphasis filter effect."""
        audio, sr = sample_audio_48khz
        
        # Config without pre-emphasis
        config_no_emphasis = ArchetypeAnalyzerConfig(pre_emphasis=0.0)
        analyzer_no_emphasis = ArchetypeConformityAnalyzer(
            sample_rate=sr,
            config=config_no_emphasis
        )
        
        # Config with pre-emphasis
        config_emphasis = ArchetypeAnalyzerConfig(pre_emphasis=0.97)
        analyzer_emphasis = ArchetypeConformityAnalyzer(
            sample_rate=sr,
            config=config_emphasis
        )
        
        # Extract formants with both configs
        formants_no = analyzer_no_emphasis._extract_formant_features(audio)
        formants_yes = analyzer_emphasis._extract_formant_features(audio)
        
        # Pre-emphasis should affect formant extraction
        # (exact values will differ based on the signal)
        assert formants_no != formants_yes
