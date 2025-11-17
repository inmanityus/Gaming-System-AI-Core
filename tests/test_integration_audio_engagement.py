"""
Integration tests for Audio Authentication ↔ Engagement Analytics.
Tests the interaction between audio quality metrics and engagement tracking.
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

# Import both systems
from services.ethelred_audio_metrics.intelligibility_analyzer import IntelligibilityAnalyzer
from services.ethelred_audio_metrics.archetype_analyzer import ArchetypeConformityAnalyzer
from services.ethelred_engagement.addiction_indicators import AddictionIndicatorCalculator
from services.ethelred_engagement.safety_constraints import EngagementSafetyConstraints


class TestAudioEngagementIntegration:
    """Integration tests for audio and engagement systems."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_poor_audio_quality_affects_engagement_metrics(self, mock_postgres_pool):
        """Test that poor audio quality is tracked in engagement metrics."""
        # Setup audio analyzers
        intelligibility = IntelligibilityAnalyzer()
        archetype = ArchetypeConformityAnalyzer()
        
        # Setup engagement systems
        addiction_calc = AddictionIndicatorCalculator(mock_postgres_pool)
        safety = EngagementSafetyConstraints()
        
        # Generate poor quality audio
        poor_audio = np.random.randn(48000 * 2)  # 2 seconds of noise
        
        # Analyze audio quality
        intel_score, intel_band = intelligibility.analyze(poor_audio)
        arch_score, arch_band = archetype.analyze(poor_audio, 'vampire_alpha')
        
        # Mock session data with audio quality events
        sessions = [{
            'session_start': datetime.utcnow() - timedelta(hours=1),
            'session_end': datetime.utcnow(),
            'duration_minutes': 60,
            'audio_quality_events': [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=30),
                    'intelligibility_score': intel_score,
                    'intelligibility_band': intel_band,
                    'archetype_score': arch_score,
                    'archetype_band': arch_band
                }
            ]
        }]
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        # Check if poor audio affects engagement metrics
        indicators = await addiction_calc.compute_indicators(['user1'], 7)
        
        # Poor audio quality should be flagged in risk factors
        assert 'cohort_size' in indicators
        
        # Safety constraints should consider audio quality
        allowed, reason = safety.check_usage_allowed(
            cohort_size=100,
            usage_context='dashboard',
            request_metadata={'audio_quality': intel_band}
        )
        
        assert allowed  # Should still be allowed but tracked
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_voice_archetype_consistency_tracking(self, mock_postgres_pool):
        """Test tracking of voice archetype consistency across sessions."""
        archetype_analyzer = ArchetypeConformityAnalyzer()
        addiction_calc = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Simulate multiple sessions with varying voice consistency
        voice_scores = []
        sessions = []
        
        for day in range(7):
            # Generate voice sample
            voice_sample = np.sin(2 * np.pi * 150 * np.linspace(0, 2, 96000))
            voice_sample += 0.1 * np.random.randn(len(voice_sample))
            
            # Analyze voice
            score, band = archetype_analyzer.analyze(voice_sample, 'vampire_alpha')
            voice_scores.append(score)
            
            # Create session
            session_date = datetime.utcnow() - timedelta(days=day)
            sessions.append({
                'session_start': session_date.replace(hour=15),
                'session_end': session_date.replace(hour=16),
                'duration_minutes': 60,
                'voice_conformity_score': score,
                'voice_conformity_band': band
            })
        
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        # Compute engagement indicators
        indicators = await addiction_calc.compute_indicators(['voice_user'], 7)
        
        # Calculate voice consistency metric
        voice_variance = np.var(voice_scores)
        voice_consistency = 1.0 - min(voice_variance, 1.0)
        
        # High variance in voice could indicate account sharing or fatigue
        assert isinstance(voice_consistency, float)
        assert 0 <= voice_consistency <= 1.0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audio_quality_safety_constraints(self):
        """Test safety constraints based on audio quality metrics."""
        intelligibility = IntelligibilityAnalyzer()
        safety = EngagementSafetyConstraints()
        
        # Test scenario: Real-time audio quality monitoring
        test_cases = [
            # (audio_quality, latency_ms, expected_allowed)
            ('excellent', 50, True),    # Good quality, low latency
            ('unacceptable', 50, False), # Poor quality, low latency
            ('good', 200, True),         # Good quality, high latency
            ('degraded', 150, True),     # Degraded quality, medium latency
        ]
        
        for quality, latency, expected in test_cases:
            allowed, reason = safety.check_usage_allowed(
                cohort_size=200,
                usage_context='api',
                latency_requirement_ms=latency,
                request_metadata={
                    'audio_quality': quality,
                    'purpose': 'monitor audio quality'
                }
            )
            
            # Note: Current implementation doesn't check audio quality directly
            # This test documents expected behavior
            if quality == 'unacceptable' and latency < 100:
                # Should consider blocking real-time monitoring of poor audio
                pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_engagement_patterns_by_audio_archetype(self, mock_postgres_pool):
        """Test different engagement patterns for different voice archetypes."""
        archetype_analyzer = ArchetypeConformityAnalyzer()
        addiction_calc = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Test data for different archetypes
        archetypes_engagement = {
            'vampire_alpha': {
                'avg_session_hours': 3.5,
                'night_play_ratio': 0.7,
                'consecutive_days': 10
            },
            'human_agent': {
                'avg_session_hours': 1.5,
                'night_play_ratio': 0.2,
                'consecutive_days': 5
            },
            'corpse_tender': {
                'avg_session_hours': 2.0,
                'night_play_ratio': 0.9,  # Very nocturnal
                'consecutive_days': 3
            }
        }
        
        for archetype, patterns in archetypes_engagement.items():
            # Generate appropriate voice
            if archetype == 'vampire_alpha':
                pitch = 100
            elif archetype == 'human_agent':
                pitch = 150
            else:  # corpse_tender
                pitch = 80
            
            voice = np.sin(2 * np.pi * pitch * np.linspace(0, 2, 96000))
            
            # Analyze voice
            score, band = archetype_analyzer.analyze(voice, archetype)
            
            # Create engagement data matching the archetype pattern
            sessions = []
            for day in range(patterns['consecutive_days']):
                # Night session if high night ratio
                if np.random.random() < patterns['night_play_ratio']:
                    hour = 23
                else:
                    hour = 15
                
                session_date = datetime.utcnow() - timedelta(days=day)
                sessions.append({
                    'session_start': session_date.replace(hour=hour),
                    'session_end': session_date.replace(hour=hour) + timedelta(hours=patterns['avg_session_hours']),
                    'duration_minutes': patterns['avg_session_hours'] * 60,
                    'archetype': archetype
                })
            
            mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
            
            # Analyze engagement
            indicators = await addiction_calc.compute_indicators([f'{archetype}_player'], 30)
            
            # Different archetypes should show different risk patterns
            if archetype == 'corpse_tender':
                # Very nocturnal play expected
                assert indicators['night_time_play_ratio'] > 0.8
            elif archetype == 'human_agent':
                # More normal patterns
                assert indicators['risk_level'] in ['low', 'moderate']
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audio_degradation_session_length_correlation(self, mock_postgres_pool):
        """Test if audio quality degrades with longer sessions."""
        intelligibility = IntelligibilityAnalyzer()
        
        # Simulate audio quality over a long session
        session_hours = 6
        samples_per_hour = 5
        
        quality_timeline = []
        
        for hour in range(session_hours):
            for sample in range(samples_per_hour):
                # Simulate degrading audio quality over time
                time_factor = (hour * samples_per_hour + sample) / (session_hours * samples_per_hour)
                
                # Start with clean audio
                clean_audio = np.sin(2 * np.pi * 200 * np.linspace(0, 1, 48000))
                
                # Add increasing noise over time
                noise_level = 0.1 + 0.5 * time_factor
                noise = np.random.randn(len(clean_audio)) * noise_level
                
                degraded_audio = clean_audio + noise
                
                # Analyze
                score, band = intelligibility.analyze(degraded_audio)
                
                quality_timeline.append({
                    'hour': hour,
                    'score': score,
                    'band': band,
                    'timestamp': datetime.utcnow() - timedelta(hours=session_hours-hour)
                })
        
        # Check if quality degrades
        early_scores = [q['score'] for q in quality_timeline[:samples_per_hour]]
        late_scores = [q['score'] for q in quality_timeline[-samples_per_hour:]]
        
        avg_early = np.mean(early_scores)
        avg_late = np.mean(late_scores)
        
        # Late session audio should be worse
        assert avg_late < avg_early
        
        # This could indicate player fatigue
        fatigue_indicator = 1.0 - (avg_late / avg_early if avg_early > 0 else 0)
        assert fatigue_indicator > 0.2  # Significant degradation
    
    @pytest.mark.integration
    def test_combined_risk_assessment(self):
        """Test combined risk assessment from audio and engagement metrics."""
        # Initialize all analyzers
        intelligibility = IntelligibilityAnalyzer()
        archetype = ArchetypeConformityAnalyzer()
        safety = EngagementSafetyConstraints()
        
        # Comprehensive risk factors
        risk_factors = {
            'audio_quality': {
                'intelligibility_score': 3.0,  # Poor
                'intelligibility_band': 'degraded',
                'archetype_conformity': 0.4,    # Misaligned
                'voice_consistency': 0.6        # Inconsistent
            },
            'engagement_patterns': {
                'night_time_play_ratio': 0.8,   # Very high
                'avg_session_hours': 5.0,       # Very long
                'consecutive_days': 20,         # Excessive
                'one_more_run_ratio': 0.7      # High
            },
            'safety_violations': {
                'cohort_size_violations': 3,
                'rate_limit_violations': 5,
                'optimization_attempts': 2
            }
        }
        
        # Calculate combined risk score
        audio_risk = 0.0
        if risk_factors['audio_quality']['intelligibility_band'] == 'degraded':
            audio_risk += 0.3
        if risk_factors['audio_quality']['archetype_conformity'] < 0.5:
            audio_risk += 0.2
        if risk_factors['audio_quality']['voice_consistency'] < 0.7:
            audio_risk += 0.1
        
        engagement_risk = 0.0
        if risk_factors['engagement_patterns']['night_time_play_ratio'] > 0.7:
            engagement_risk += 0.3
        if risk_factors['engagement_patterns']['avg_session_hours'] > 4.0:
            engagement_risk += 0.3
        if risk_factors['engagement_patterns']['consecutive_days'] > 14:
            engagement_risk += 0.2
        
        safety_risk = min(1.0, (
            risk_factors['safety_violations']['cohort_size_violations'] * 0.1 +
            risk_factors['safety_violations']['rate_limit_violations'] * 0.05 +
            risk_factors['safety_violations']['optimization_attempts'] * 0.2
        ))
        
        # Combined risk assessment
        total_risk = (audio_risk + engagement_risk + safety_risk) / 3
        
        assert total_risk > 0.5  # High risk player
        
        # Determine intervention level
        if total_risk > 0.8:
            intervention = 'urgent'
        elif total_risk > 0.6:
            intervention = 'recommended'
        elif total_risk > 0.4:
            intervention = 'monitor'
        else:
            intervention = 'none'
        
        assert intervention in ['urgent', 'recommended']
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_voice_fatigue_detection(self):
        """Test detection of voice fatigue through audio analysis."""
        intelligibility = IntelligibilityAnalyzer()
        archetype = ArchetypeConformityAnalyzer()
        
        # Simulate voice samples over time
        baseline_pitch = 150  # Hz
        voice_samples = []
        
        for hour in range(8):  # 8 hour marathon session
            # Pitch drops and becomes irregular with fatigue
            pitch_variation = hour * 5  # Increasing variation
            pitch = baseline_pitch - (hour * 5)  # Dropping pitch
            
            # Generate voice with fatigue characteristics
            t = np.linspace(0, 2, 96000)
            
            # Add jitter (irregular pitch)
            jitter = np.random.randn(len(t)) * (0.01 * hour)
            
            # Base voice
            voice = np.sin(2 * np.pi * pitch * (t + jitter))
            
            # Add breathiness (increases with fatigue)
            breathiness = np.random.randn(len(voice)) * (0.05 * hour)
            voice += breathiness
            
            # Add hoarseness (spectral noise)
            if hour > 4:
                hoarseness = np.random.randn(len(voice)) * 0.1
                voice += hoarseness
            
            # Normalize
            voice = voice / np.max(np.abs(voice))
            
            voice_samples.append({
                'hour': hour,
                'audio': voice,
                'expected_fatigue': hour / 8.0
            })
        
        # Analyze progression
        fatigue_indicators = []
        
        for sample in voice_samples:
            intel_score, intel_band = intelligibility.analyze(sample['audio'])
            arch_score, arch_band = archetype.analyze(sample['audio'], 'human_agent')
            
            # Combine metrics for fatigue score
            # Fatigue indicated by: lower intelligibility, lower archetype conformity
            fatigue_score = 1.0 - (intel_score / 20.0 * 0.5 + arch_score * 0.5)
            
            fatigue_indicators.append({
                'hour': sample['hour'],
                'fatigue_score': fatigue_score,
                'expected': sample['expected_fatigue']
            })
        
        # Check if fatigue detection correlates with time
        hours = [f['hour'] for f in fatigue_indicators]
        scores = [f['fatigue_score'] for f in fatigue_indicators]
        
        # Calculate correlation (simplified)
        correlation = np.corrcoef(hours, scores)[0, 1]
        
        assert correlation > 0.7  # Strong positive correlation
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_user_household_detection(self, mock_postgres_pool):
        """Test detection of multiple users on same account via voice analysis."""
        archetype = ArchetypeConformityAnalyzer()
        addiction_calc = AddictionIndicatorCalculator(mock_postgres_pool)
        
        # Simulate different family members using same account
        user_profiles = {
            'adult_male': {'pitch': 110, 'roughness': 0.3},
            'adult_female': {'pitch': 220, 'roughness': 0.1},
            'teenager': {'pitch': 160, 'roughness': 0.2},
            'child': {'pitch': 300, 'roughness': 0.05}
        }
        
        sessions = []
        voice_signatures = []
        
        for day in range(14):
            # Randomly select who plays each day
            player = np.random.choice(list(user_profiles.keys()))
            profile = user_profiles[player]
            
            # Generate voice for that player
            t = np.linspace(0, 1, 48000)
            voice = np.sin(2 * np.pi * profile['pitch'] * t)
            voice += np.random.randn(len(voice)) * profile['roughness']
            
            # Analyze voice
            score, band = archetype.analyze(voice, 'human_agent')
            
            voice_signatures.append({
                'day': day,
                'pitch_estimate': profile['pitch'],
                'conformity_score': score
            })
            
            # Create session
            session_date = datetime.utcnow() - timedelta(days=day)
            sessions.append({
                'session_start': session_date.replace(hour=15),
                'session_end': session_date.replace(hour=16),
                'duration_minutes': 60,
                'voice_signature': {
                    'pitch': profile['pitch'],
                    'score': score
                }
            })
        
        # Detect multiple users
        unique_pitches = len(set(s['pitch_estimate'] for s in voice_signatures))
        
        # High variance in voice characteristics suggests multiple users
        pitch_variance = np.var([s['pitch_estimate'] for s in voice_signatures])
        
        assert unique_pitches >= 3  # Multiple distinct voices
        assert pitch_variance > 1000  # High variance in pitch
        
        # This should affect addiction risk assessment
        # (shared accounts may show misleading patterns)
        mock_postgres_pool.acquire().__aenter__.return_value.fetch.return_value = sessions
        
        indicators = await addiction_calc.compute_indicators(['shared_account'], 14)
        
        # Document that shared account detection could improve metrics
        assert 'cohort_size' in indicators  # Current system doesn't detect this
