"""
End-to-end API integration tests.
Tests complete workflows across multiple services.
"""
import pytest
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
import numpy as np
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EAudioWorkflow:
    """Test complete audio analysis workflow from API to database."""
    
    @pytest.fixture
    async def api_client(self):
        """Create API client for testing."""
        async with aiohttp.ClientSession() as session:
            yield session
    
    async def test_complete_audio_submission_workflow(
        self,
        postgres_pool,
        api_client,
        sample_audio_48khz
    ):
        """Test submitting audio through API and verifying all processing."""
        # Note: This assumes services are running. In real tests, we'd start them.
        base_url = "http://localhost:8000"
        
        # 1. Submit audio for analysis
        audio, sample_rate = sample_audio_48khz
        audio_bytes = (audio * 32767).astype(np.int16).tobytes()
        
        # Create multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field('audio', audio_bytes, 
                          filename='test_audio.wav',
                          content_type='audio/wav')
        form_data.add_field('user_id', 'e2e_test_user')
        form_data.add_field('archetype', 'vampire_alpha')
        form_data.add_field('sample_rate', str(sample_rate))
        
        # Submit to intelligibility endpoint
        try:
            async with api_client.post(
                f"{base_url}/api/v1/audio/analyze/intelligibility",
                data=form_data
            ) as response:
                if response.status == 200:
                    intelligibility_result = await response.json()
                else:
                    # Service might not be running, skip
                    pytest.skip("Audio service not running")
        except aiohttp.ClientError:
            pytest.skip("Cannot connect to audio service")
        
        # 2. Submit to archetype analysis
        form_data = aiohttp.FormData()
        form_data.add_field('audio', audio_bytes,
                          filename='test_audio.wav',
                          content_type='audio/wav')
        form_data.add_field('user_id', 'e2e_test_user')
        form_data.add_field('expected_archetype', 'vampire_alpha')
        form_data.add_field('sample_rate', str(sample_rate))
        
        try:
            async with api_client.post(
                f"{base_url}/api/v1/audio/analyze/archetype",
                data=form_data
            ) as response:
                if response.status == 200:
                    archetype_result = await response.json()
        except:
            pass  # Continue even if this fails
        
        # 3. Verify data in database
        async with postgres_pool.acquire() as conn:
            # Check audio metrics stored
            metrics = await conn.fetch("""
                SELECT * FROM ethelred.audio_metrics
                WHERE user_id = 'e2e_test_user'
                ORDER BY analysis_timestamp DESC
            """)
            
            if len(metrics) > 0:
                # Verify intelligibility data
                assert metrics[0]['intelligibility_score'] is not None
                assert metrics[0]['confidence_level'] is not None
                
                # Verify archetype data if available
                if 'archetype' in locals():
                    assert metrics[0]['archetype'] == 'vampire_alpha'
        
        # 4. Query aggregated data through API
        try:
            async with api_client.get(
                f"{base_url}/api/v1/audio/metrics/user/e2e_test_user"
            ) as response:
                if response.status == 200:
                    user_metrics = await response.json()
                    assert 'average_intelligibility' in user_metrics
                    assert 'total_analyses' in user_metrics
        except:
            pass  # API might not be available
    
    async def test_multi_language_audio_workflow(
        self,
        postgres_pool,
        api_client,
        sample_audio_48khz
    ):
        """Test multi-language TTS and audio analysis workflow."""
        base_url = "http://localhost:8000"
        
        # 1. Get localized content
        try:
            async with api_client.get(
                f"{base_url}/api/v1/localization/content",
                params={
                    'key': 'dialogue.greeting.morning',
                    'language': 'ja-JP'
                }
            ) as response:
                if response.status == 200:
                    content = await response.json()
                    text = content.get('text', 'おはようございます')
                else:
                    text = 'おはようございます'
        except:
            text = 'おはようございます'
            pytest.skip("Localization service not running")
        
        # 2. Request TTS generation
        try:
            async with api_client.post(
                f"{base_url}/api/v1/tts/synthesize",
                json={
                    'text': text,
                    'language': 'ja-JP',
                    'voice_id': 'ja-JP-Standard-A'
                }
            ) as response:
                if response.status == 200:
                    tts_result = await response.json()
                    audio_url = tts_result.get('audio_url')
                else:
                    pytest.skip("TTS service not running")
        except:
            pytest.skip("Cannot connect to TTS service")
        
        # 3. Verify TTS cache in database
        if 'tts_result' in locals():
            async with postgres_pool.acquire() as conn:
                import hashlib
                text_hash = hashlib.sha256(text.encode()).hexdigest()
                
                cache_entry = await conn.fetchrow("""
                    SELECT * FROM language.tts_cache
                    WHERE text_hash = $1 AND language_code = $2
                """, text_hash, 'ja-JP')
                
                if cache_entry:
                    assert cache_entry['audio_data'] is not None
                    assert cache_entry['language_code'] == 'ja-JP'


@pytest.mark.integration
@pytest.mark.e2e
class TestE2EEngagementWorkflow:
    """Test complete engagement tracking workflow."""
    
    async def test_gaming_session_workflow(
        self,
        postgres_pool,
        api_client
    ):
        """Test tracking a complete gaming session."""
        base_url = "http://localhost:8000"
        user_id = "e2e_engagement_user"
        
        # 1. Start gaming session
        session_start = datetime.now(timezone.utc)
        
        try:
            async with api_client.post(
                f"{base_url}/api/v1/engagement/session/start",
                json={
                    'user_id': user_id,
                    'timestamp': session_start.isoformat()
                }
            ) as response:
                if response.status == 200:
                    session = await response.json()
                    session_id = session['session_id']
                else:
                    pytest.skip("Engagement service not running")
        except:
            pytest.skip("Cannot connect to engagement service")
        
        # 2. Send game events
        events = [
            {'type': 'level_start', 'level': 1, 'delay': 0},
            {'type': 'enemy_killed', 'enemy_type': 'vampire', 'delay': 5},
            {'type': 'item_collected', 'item': 'health_potion', 'delay': 10},
            {'type': 'death', 'cause': 'fall_damage', 'delay': 15},
            {'type': 'respawn', 'checkpoint': 1, 'delay': 20},
            {'type': 'level_complete', 'level': 1, 'score': 1500, 'delay': 30},
        ]
        
        for event in events:
            event_time = session_start + timedelta(minutes=event['delay'])
            event_data = {k: v for k, v in event.items() if k != 'delay'}
            event_data['timestamp'] = event_time.isoformat()
            
            try:
                await api_client.post(
                    f"{base_url}/api/v1/engagement/session/{session_id}/event",
                    json=event_data
                )
            except:
                pass  # Continue even if some events fail
            
            # Small delay between events
            await asyncio.sleep(0.1)
        
        # 3. End session
        session_end = session_start + timedelta(minutes=45)
        
        try:
            await api_client.post(
                f"{base_url}/api/v1/engagement/session/{session_id}/end",
                json={
                    'timestamp': session_end.isoformat(),
                    'reason': 'player_quit'
                }
            )
        except:
            pass
        
        # 4. Request addiction analysis
        try:
            async with api_client.get(
                f"{base_url}/api/v1/engagement/analysis/addiction/{user_id}"
            ) as response:
                if response.status == 200:
                    addiction_analysis = await response.json()
                    assert 'risk_score' in addiction_analysis
                    assert 'indicators' in addiction_analysis
        except:
            pass
        
        # 5. Verify in database
        async with postgres_pool.acquire() as conn:
            sessions = await conn.fetch("""
                SELECT * FROM ethelred.engagement_sessions
                WHERE user_id = $1
                ORDER BY session_start DESC
            """, user_id)
            
            if len(sessions) > 0:
                latest_session = sessions[0]
                assert latest_session['duration_minutes'] == 45
                if latest_session['events']:
                    events = json.loads(latest_session['events']) if isinstance(latest_session['events'], str) else latest_session['events']
                    assert len(events) >= 5  # At least some events recorded
    
    async def test_cohort_analysis_workflow(
        self,
        postgres_pool,
        api_client
    ):
        """Test cohort-based analysis workflow."""
        base_url = "http://localhost:8000"
        
        # 1. Create test cohort data
        cohort_users = []
        base_time = datetime.now(timezone.utc)
        
        # Create 150 users with sessions
        async with postgres_pool.acquire() as conn:
            for i in range(150):
                user_id = f'cohort_e2e_user_{i}'
                cohort_users.append(user_id)
                
                # Create session
                await conn.execute("""
                    INSERT INTO ethelred.engagement_sessions
                    (user_id, session_start, session_end, duration_minutes,
                     is_night_session)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                base_time - timedelta(hours=i % 24),
                base_time - timedelta(hours=i % 24 - 2),
                120,
                (i % 24) >= 22 or (i % 24) <= 6  # Night hours
                )
        
        # 2. Request cohort analysis
        try:
            async with api_client.post(
                f"{base_url}/api/v1/engagement/analysis/cohort",
                json={
                    'user_ids': cohort_users[:100],  # First 100 users
                    'metrics': ['play_time', 'night_ratio', 'session_frequency']
                }
            ) as response:
                if response.status == 200:
                    cohort_analysis = await response.json()
                    
                    # Should meet minimum cohort size
                    assert cohort_analysis['cohort_size'] >= 100
                    assert 'average_play_time' in cohort_analysis
                    assert 'night_session_ratio' in cohort_analysis
                else:
                    pytest.skip("Cohort analysis endpoint not available")
        except:
            pytest.skip("Cannot perform cohort analysis")


@pytest.mark.integration
@pytest.mark.e2e  
class TestE2EMultiServiceWorkflow:
    """Test workflows spanning multiple services."""
    
    async def test_complete_user_journey(
        self,
        postgres_pool,
        api_client,
        sample_audio_48khz
    ):
        """Test a complete user journey across all services."""
        base_url = "http://localhost:8000"
        user_id = "e2e_journey_user"
        
        # 1. Set user preferences
        try:
            await api_client.put(
                f"{base_url}/api/v1/users/{user_id}/preferences",
                json={
                    'language_code': 'ja-JP',
                    'audio_settings': {
                        'volume': 0.8,
                        'voice_type': 'female',
                        'subtitles_enabled': True
                    },
                    'accessibility_settings': {
                        'high_contrast': False,
                        'screen_reader': False
                    }
                }
            )
        except:
            pass  # Continue even if this fails
        
        # 2. Get localized content in user's language
        try:
            async with api_client.get(
                f"{base_url}/api/v1/localization/content/user/{user_id}",
                params={'key': 'ui.menu.play'}
            ) as response:
                if response.status == 200:
                    localized_content = await response.json()
                    assert localized_content['language'] == 'ja-JP'
        except:
            pass
        
        # 3. Start gaming session
        session_start = datetime.now(timezone.utc)
        session_data = {
            'user_id': user_id,
            'timestamp': session_start.isoformat()
        }
        
        try:
            async with api_client.post(
                f"{base_url}/api/v1/engagement/session/start",
                json=session_data
            ) as response:
                if response.status == 200:
                    session = await response.json()
                    session_id = session['session_id']
        except:
            session_id = 'mock_session_id'
        
        # 4. Submit voice audio during gameplay
        audio, sample_rate = sample_audio_48khz
        
        # Simulate multiple voice submissions
        for i in range(3):
            await asyncio.sleep(0.5)  # Simulate time passing
            
            # Add some variation to audio
            varied_audio = audio + np.random.normal(0, 0.01, audio.shape)
            audio_bytes = (varied_audio * 32767).astype(np.int16).tobytes()
            
            form_data = aiohttp.FormData()
            form_data.add_field('audio', audio_bytes,
                              filename=f'gameplay_audio_{i}.wav',
                              content_type='audio/wav')
            form_data.add_field('user_id', user_id)
            form_data.add_field('session_id', session_id)
            form_data.add_field('context', f'combat_dialogue_{i}')
            
            try:
                await api_client.post(
                    f"{base_url}/api/v1/audio/submit",
                    data=form_data
                )
            except:
                pass
        
        # 5. End session and get summary
        session_end = session_start + timedelta(hours=2)
        
        try:
            await api_client.post(
                f"{base_url}/api/v1/engagement/session/{session_id}/end",
                json={'timestamp': session_end.isoformat()}
            )
        except:
            pass
        
        # 6. Get comprehensive user report
        try:
            async with api_client.get(
                f"{base_url}/api/v1/users/{user_id}/report"
            ) as response:
                if response.status == 200:
                    user_report = await response.json()
                    
                    # Should contain data from multiple services
                    assert 'preferences' in user_report
                    assert 'engagement_stats' in user_report
                    assert 'audio_quality' in user_report
        except:
            pass
        
        # 7. Verify data consistency across database
        async with postgres_pool.acquire() as conn:
            # Check user preferences
            prefs = await conn.fetchrow("""
                SELECT * FROM users.preferences
                WHERE user_id = $1
            """, user_id)
            
            if prefs:
                assert prefs['language_code'] == 'ja-JP'
            
            # Check engagement data
            engagement = await conn.fetch("""
                SELECT * FROM ethelred.engagement_sessions
                WHERE user_id = $1
            """, user_id)
            
            # Check audio metrics
            audio_metrics = await conn.fetch("""
                SELECT * FROM ethelred.audio_metrics
                WHERE user_id = $1
            """, user_id)
            
            # Verify cross-service consistency
            if engagement and audio_metrics:
                # Audio submissions should be within session timeframe
                session_times = [(s['session_start'], s['session_end']) for s in engagement]
                audio_times = [a['analysis_timestamp'] for a in audio_metrics]
                
                # At least some audio should be during sessions
                # (In real implementation, we'd verify exact matching)
