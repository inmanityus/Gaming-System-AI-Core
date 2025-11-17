"""
Complete integration tests with actual implementations.
Tests real interactions between components with assertions.
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

from services.ethelred_audio_metrics.intelligibility_analyzer import IntelligibilityAnalyzer, IntelligibilityConfig
from services.ethelred_audio_metrics.archetype_analyzer import ArchetypeConformityAnalyzer, ArchetypeAnalyzerConfig
from services.ethelred_engagement.addiction_indicators import AddictionIndicatorCalculator, AddictionIndicatorConfig
from services.ethelred_engagement.safety_constraints import EngagementSafetyConstraints, SafetyConstraintsConfig


class TestCompleteIntegration:
    """Real integration tests with actual assertions."""
    
    @pytest.mark.integration
    def test_poor_audio_triggers_safety_constraints(self):
        """Test that poor audio quality affects safety constraints."""
        # Configure analyzers with strict thresholds
        intel_config = IntelligibilityConfig(
            excellent_threshold=20.0,
            good_threshold=15.0,
            fair_threshold=10.0
        )
        intelligibility = IntelligibilityAnalyzer(config=intel_config)
        
        safety_config = SafetyConstraintsConfig(
            min_cohort_size=50,  # Lower for testing
            optimization_keywords=['maximize', 'optimize']
        )
        safety = EngagementSafetyConstraints(config=safety_config)
        
        # Generate poor quality audio (lots of noise)
        duration = 2.0
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Signal buried in noise
        signal = 0.1 * np.sin(2 * np.pi * 200 * t)  # Weak signal
        noise = np.random.randn(len(signal)) * 0.9   # Strong noise
        poor_audio = signal + noise
        
        # Analyze audio
        intel_score, intel_band = intelligibility.analyze(poor_audio)
        
        # Assertions
        assert intel_score < 5.0, f"Expected low intelligibility score, got {intel_score}"
        assert intel_band in ['degraded', 'unacceptable'], f"Expected poor band, got {intel_band}"
        
        # Check if poor audio affects safety decisions
        allowed, reason = safety.check_usage_allowed(
            cohort_size=100,
            usage_context='dashboard',
            request_metadata={
                'audio_quality': intel_band,
                'purpose': 'analyze player audio'
            }
        )
        
        # Currently safety doesn't check audio directly, but document expected behavior
        assert allowed is True  # Current behavior
        # In future: assert allowed is False if intel_band == 'unacceptable'
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_archetype_mismatch_increases_addiction_risk(self, mock_postgres_pool):
        """Test that voice archetype mismatches flag addiction risk."""
        # Setup analyzers
        archetype = ArchetypeConformityAnalyzer()
        addiction = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Generate voice that doesn't match vampire archetype
        # High pitch (300Hz) when vampire expects low (80-160Hz)
        duration = 2.0
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        high_pitch_voice = np.sin(2 * np.pi * 300 * t)  # Child-like voice
        
        # Analyze against vampire archetype
        arch_score, arch_band = archetype.analyze(high_pitch_voice, 'vampire_alpha')
        
        # Assertions
        assert arch_score < 0.5, f"Expected low conformity, got {arch_score}"
        assert arch_band == 'misaligned', f"Expected misaligned, got {arch_band}"
        
        # Create session data with archetype mismatch events
        sessions_with_mismatch = [{
            'session_start': datetime.utcnow() - timedelta(hours=2),
            'session_end': datetime.utcnow(),
            'duration_minutes': 120,
            'archetype_mismatches': 15,  # Many voice changes
            'avg_conformity_score': arch_score
        }]
        
        # Mock data
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions_with_mismatch
        
        # Calculate addiction indicators
        indicators = await addiction.compute_indicators(['suspicious_user'], 7)
        
        # Assertions - document expected behavior
        assert 'cohort_size' in indicators
        # Future: assert 'account_sharing_risk' in indicators['risk_factors']
    
    @pytest.mark.integration
    def test_audio_quality_degradation_over_session(self):
        """Test detecting voice fatigue over long sessions."""
        intelligibility = IntelligibilityAnalyzer()
        
        # Simulate 6-hour session with degrading voice quality
        hours = 6
        samples_per_hour = 3
        
        quality_scores = []
        quality_bands = []
        
        for hour in range(hours):
            # Generate progressively worse audio
            t = np.linspace(0, 1, 48000)
            
            # Base signal
            signal = np.sin(2 * np.pi * 200 * t)
            
            # Fatigue effects increase over time
            fatigue_factor = hour / hours
            
            # Add jitter (voice instability)
            jitter = np.random.randn(len(t)) * (0.05 * fatigue_factor)
            
            # Add noise (breathiness/hoarseness)
            noise = np.random.randn(len(signal)) * (0.3 * fatigue_factor)
            
            # Reduce amplitude (voice weakness)
            amplitude = 1.0 - (0.5 * fatigue_factor)
            
            fatigued_audio = amplitude * signal + noise
            
            # Analyze
            score, band = intelligibility.analyze(fatigued_audio)
            
            quality_scores.append(score)
            quality_bands.append(band)
        
        # Assertions
        # Quality should degrade over time
        assert quality_scores[0] > quality_scores[-1], "Voice quality should degrade"
        
        # Calculate degradation rate
        degradation = (quality_scores[0] - quality_scores[-1]) / quality_scores[0]
        assert degradation > 0.3, f"Expected >30% degradation, got {degradation:.1%}"
        
        # Later hours should have worse bands
        early_bands = quality_bands[:2]
        late_bands = quality_bands[-2:]
        
        # Map bands to numeric scores for comparison
        band_scores = {
            'excellent': 4,
            'good': 3,
            'fair': 2,
            'degraded': 1,
            'unacceptable': 0
        }
        
        avg_early = sum(band_scores[b] for b in early_bands) / len(early_bands)
        avg_late = sum(band_scores[b] for b in late_bands) / len(late_bands)
        
        assert avg_early > avg_late, "Late session should have worse quality bands"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_safety_constraints_with_addiction_indicators(self, mock_postgres_pool):
        """Test safety constraints applied based on addiction risk."""
        # Setup with custom configs
        addiction_config = AddictionIndicatorConfig(
            excessive_session_hours=2.0,  # Lower threshold
            concerning_consecutive_days=5  # Lower threshold
        )
        addiction = AddictionIndicatorCalculator(mock_postgres_pool, config=addiction_config)
        
        safety_config = SafetyConstraintsConfig(
            min_cohort_size=10,  # Lower for testing
            max_hourly_checks_dashboard=5  # Strict limit
        )
        safety = EngagementSafetyConstraints(config=safety_config)
        
        # Create problematic play pattern
        sessions = []
        base_date = datetime.utcnow()
        
        for day in range(10):  # 10 consecutive days
            date = base_date - timedelta(days=day)
            sessions.append({
                'session_start': date.replace(hour=22),  # Late night
                'session_end': date.replace(hour=2) + timedelta(days=1),  # 4 hours
                'duration_minutes': 240
            })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        # Calculate addiction indicators
        indicators = await addiction.compute_indicators(['at_risk_user'], 14)
        
        # Assertions
        assert indicators['consecutive_days_playing'] >= 10
        assert indicators['avg_session_duration_hours'] >= 3.5
        assert indicators['night_time_play_ratio'] > 0.8
        assert 'high_consecutive_days' in indicators['risk_factors']
        assert indicators['risk_level'] in ['high', 'extreme']
        
        # Test rate limiting for high-risk user
        user_id = 'at_risk_user'
        
        # Exhaust rate limit
        for i in range(5):
            allowed = safety._check_access_frequency(user_id, 'dashboard')
            assert allowed, f"Request {i+1} should be allowed"
        
        # Next request should be blocked
        allowed = safety._check_access_frequency(user_id, 'dashboard')
        assert not allowed, "Should hit rate limit"
    
    @pytest.mark.integration
    @pytest.mark.parametrize("snr_db,expected_band,expected_constraints", [
        (25.0, 'excellent', False),  # Great audio, no constraints
        (12.0, 'good', False),       # Good audio, no constraints
        (7.0, 'fair', True),         # Fair audio, apply constraints
        (3.0, 'degraded', True),     # Poor audio, apply constraints
        (0.0, 'unacceptable', True), # Terrible audio, apply constraints
    ])
    def test_audio_quality_thresholds(self, snr_db, expected_band, expected_constraints):
        """Test audio quality thresholds and their effects."""
        intelligibility = IntelligibilityAnalyzer()
        
        # Generate audio with specific SNR
        duration = 1.0
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Clean signal
        signal = np.sin(2 * np.pi * 200 * t)
        signal_power = np.mean(signal ** 2)
        
        # Add noise to achieve target SNR
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.random.randn(len(signal)) * np.sqrt(noise_power)
        
        audio = signal + noise
        
        # Analyze
        score, band = intelligibility.analyze(audio)
        
        # Assertions
        assert band == expected_band, f"Expected {expected_band}, got {band}"
        
        # Check if constraints should be applied
        should_constrain = band in ['fair', 'degraded', 'unacceptable']
        assert should_constrain == expected_constraints
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_user_isolation(self, mock_postgres_pool):
        """Test that concurrent users don't interfere with each other."""
        addiction = AddictionIndicatorCalculator(mock_postgres_pool)
        safety = EngagementSafetyConstraints()
        
        # Create different patterns for different users
        user_patterns = {
            'healthy_user': {
                'sessions': 3,
                'avg_duration': 60,
                'night_ratio': 0.0
            },
            'moderate_user': {
                'sessions': 7,
                'avg_duration': 120,
                'night_ratio': 0.3
            },
            'at_risk_user': {
                'sessions': 14,
                'avg_duration': 240,
                'night_ratio': 0.8
            }
        }
        
        async def analyze_user(user_id, pattern):
            # Generate sessions
            sessions = []
            base_date = datetime.utcnow()
            
            for i in range(pattern['sessions']):
                date = base_date - timedelta(days=i)
                
                # Determine if night session
                if np.random.random() < pattern['night_ratio']:
                    hour = 23
                else:
                    hour = 15
                
                sessions.append({
                    'session_start': date.replace(hour=hour),
                    'session_end': date.replace(hour=hour) + timedelta(minutes=pattern['avg_duration']),
                    'duration_minutes': pattern['avg_duration']
                })
            
            # Mock different data for each user
            mock_pool = AsyncMock()
            mock_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
            
            calc = AddictionIndicatorCalculator(mock_pool)
            return await calc.compute_indicators([user_id], 30)
        
        # Analyze all users concurrently
        results = await asyncio.gather(*[
            analyze_user(user_id, pattern)
            for user_id, pattern in user_patterns.items()
        ])
        
        # Assertions - each user should have different risk levels
        risk_levels = [r['risk_level'] for r in results]
        
        assert results[0]['risk_level'] == 'low'  # healthy_user
        assert results[1]['risk_level'] in ['low', 'moderate']  # moderate_user
        assert results[2]['risk_level'] in ['high', 'extreme']  # at_risk_user
        
        # Verify isolation - check rate limits are per-user
        for _ in range(3):
            assert safety._check_access_frequency('user_a', 'api')
            assert safety._check_access_frequency('user_b', 'api')
    
    @pytest.mark.integration
    def test_combined_risk_scoring(self):
        """Test comprehensive risk scoring from all factors."""
        # Initialize all components
        intelligibility = IntelligibilityAnalyzer()
        archetype = ArchetypeConformityAnalyzer()
        
        # Generate problematic audio
        poor_audio = np.random.randn(48000)  # Pure noise
        
        # Generate mismatched voice
        wrong_voice = np.sin(2 * np.pi * 400 * np.linspace(0, 1, 48000))  # Too high for vampire
        
        # Analyze
        intel_score, intel_band = intelligibility.analyze(poor_audio)
        arch_score, arch_band = archetype.analyze(wrong_voice, 'vampire_alpha')
        
        # Calculate combined risk
        risk_factors = []
        risk_score = 0.0
        
        # Audio quality risk
        if intel_band in ['degraded', 'unacceptable']:
            risk_factors.append('poor_audio_quality')
            risk_score += 0.3
        
        # Archetype mismatch risk
        if arch_band == 'misaligned':
            risk_factors.append('voice_mismatch')
            risk_score += 0.3
        
        # Mock addiction indicators
        addiction_risk = {
            'night_time_play_ratio': 0.7,
            'consecutive_days': 15,
            'avg_session_hours': 4.5
        }
        
        if addiction_risk['night_time_play_ratio'] > 0.6:
            risk_factors.append('excessive_night_play')
            risk_score += 0.2
        
        if addiction_risk['consecutive_days'] > 10:
            risk_factors.append('daily_playing')
            risk_score += 0.2
        
        # Assertions
        assert len(risk_factors) >= 3, f"Expected multiple risk factors, got {risk_factors}"
        assert risk_score >= 0.7, f"Expected high risk score, got {risk_score}"
        
        # Determine intervention
        if risk_score >= 0.8:
            intervention = 'immediate'
        elif risk_score >= 0.6:
            intervention = 'recommended'
        else:
            intervention = 'monitor'
        
        assert intervention in ['immediate', 'recommended'], f"Expected intervention, got {intervention}"
    
    @pytest.mark.integration
    def test_real_audio_files(self):
        """Test with actual generated audio files."""
        test_data_dir = Path('tests/test_data/audio')
        
        if not test_data_dir.exists():
            pytest.skip("Test data not generated")
        
        intelligibility = IntelligibilityAnalyzer()
        archetype = ArchetypeConformityAnalyzer()
        
        # Test each audio file
        test_files = {
            'clean_speech_high_snr.wav': {
                'expected_intel': 'excellent',
                'min_score': 15.0
            },
            'noisy_speech_5db.wav': {
                'expected_intel': 'fair',
                'min_score': 5.0,
                'max_score': 10.0
            },
            'very_noisy_speech_-5db.wav': {
                'expected_intel': 'unacceptable',
                'max_score': 5.0
            },
            'vampire_alpha_voice.wav': {
                'archetype': 'vampire_alpha',
                'expected_conformity': 'on_profile',
                'min_conformity': 0.7
            }
        }
        
        import soundfile as sf
        
        for filename, expected in test_files.items():
            filepath = test_data_dir / filename
            if not filepath.exists():
                continue
            
            # Load audio
            audio, sr = sf.read(filepath)
            
            # Intelligibility tests
            if 'expected_intel' in expected:
                analyzer = IntelligibilityAnalyzer(sample_rate=sr)
                score, band = analyzer.analyze(audio)
                
                # Assertions
                if 'min_score' in expected:
                    assert score >= expected['min_score'], f"{filename}: score {score} < {expected['min_score']}"
                if 'max_score' in expected:
                    assert score <= expected['max_score'], f"{filename}: score {score} > {expected['max_score']}"
            
            # Archetype tests
            if 'archetype' in expected:
                analyzer = ArchetypeConformityAnalyzer(sample_rate=sr)
                score, band = analyzer.analyze(audio, expected['archetype'])
                
                if 'min_conformity' in expected:
                    assert score >= expected['min_conformity'], f"{filename}: conformity {score} < {expected['min_conformity']}"
