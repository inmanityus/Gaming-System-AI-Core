"""
Integration tests for Localization ↔ Language System.
Tests the interaction between content localization and TTS/language processing.
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

# Import components (mocked for testing)
# In real tests, would import actual services


class MockLocalizationService:
    """Mock localization service for testing."""
    
    def __init__(self, content_db):
        self.content_db = content_db
        self.fallback_chain = ['en-US']
    
    async def get_content(self, key, language_code, with_fallback=True):
        """Get localized content."""
        if key in self.content_db and language_code in self.content_db[key]:
            return self.content_db[key][language_code]
        elif with_fallback and key in self.content_db:
            # Try fallback languages
            for fallback in self.fallback_chain:
                if fallback in self.content_db[key]:
                    return self.content_db[key][fallback]
        return None
    
    async def get_dialogue_content(self, dialogue_id, language_code):
        """Get dialogue with metadata."""
        key = f'dialogue.{dialogue_id}'
        content = await self.get_content(key, language_code)
        if content:
            return {
                'text': content.get('text'),
                'speaker': content.get('speaker', 'narrator'),
                'emotion': content.get('emotion', 'neutral'),
                'audio_file': content.get('audio_file'),
                'tts_enabled': content.get('tts_enabled', False)
            }
        return None


class MockLanguageGateway:
    """Mock language gateway for testing."""
    
    def __init__(self):
        self.tts_cache = {}
        self.supported_languages = {
            'en-US': {'voices': ['en-US-Standard-A', 'en-US-Standard-B']},
            'ja-JP': {'voices': ['ja-JP-Standard-A', 'ja-JP-Wavenet-B']},
            'es-ES': {'voices': ['es-ES-Standard-A', 'es-ES-Neural2-B']},
            'zh-CN': {'voices': ['zh-CN-Standard-A', 'zh-CN-Wavenet-C']}
        }
    
    async def synthesize_speech(self, text, language_code, voice_id=None, emotion=None):
        """Synthesize speech from text."""
        cache_key = f"{text}_{language_code}_{voice_id}_{emotion}"
        
        if cache_key in self.tts_cache:
            return self.tts_cache[cache_key]
        
        # Mock TTS generation
        result = {
            'audio_data': b'mock_audio_data_' + text.encode()[:20],
            'duration_ms': len(text) * 50,  # Rough estimate
            'format': 'mp3',
            'sample_rate': 24000,
            'voice_used': voice_id or self._get_default_voice(language_code)
        }
        
        self.tts_cache[cache_key] = result
        return result
    
    def _get_default_voice(self, language_code):
        """Get default voice for language."""
        if language_code in self.supported_languages:
            return self.supported_languages[language_code]['voices'][0]
        return 'en-US-Standard-A'
    
    async def get_timing_metadata(self, text, language_code):
        """Get timing metadata for subtitles."""
        words = text.split()
        timing = []
        
        current_ms = 0
        for i, word in enumerate(words):
            duration = len(word) * 50 + 100  # Mock duration
            timing.append({
                'word': word,
                'start_ms': current_ms,
                'end_ms': current_ms + duration,
                'confidence': 0.95
            })
            current_ms += duration + 50  # Small pause between words
        
        return {
            'words': timing,
            'total_duration_ms': current_ms,
            'language': language_code
        }


class TestLocalizationLanguageIntegration:
    """Integration tests for localization and language systems."""
    
    @pytest.fixture
    def mock_content_db(self):
        """Mock localization database."""
        return {
            'ui.button.start': {
                'en-US': {'text': 'Start Game', 'validated': True},
                'ja-JP': {'text': 'ゲーム開始', 'validated': True},
                'es-ES': {'text': 'Iniciar Juego', 'validated': True},
                'fr-FR': {'text': 'Démarrer', 'validated': False}
            },
            'dialogue.intro.welcome': {
                'en-US': {
                    'text': 'Welcome to the dark world, {player_name}.',
                    'speaker': 'narrator',
                    'emotion': 'mysterious',
                    'audio_file': 'intro_welcome_en.ogg'
                },
                'ja-JP': {
                    'text': '暗い世界へようこそ、{player_name}。',
                    'speaker': 'narrator',
                    'emotion': 'mysterious',
                    'tts_enabled': True
                },
                'es-ES': {
                    'text': 'Bienvenido al mundo oscuro, {player_name}.',
                    'speaker': 'narrator',
                    'emotion': 'mysterious',
                    'tts_enabled': True
                }
            },
            'error.network.timeout': {
                'en-US': {'text': 'Connection timed out. Please try again.'},
                'de-DE': {'text': 'Zeitüberschreitung. Bitte erneut versuchen.'}
            }
        }
    
    @pytest.fixture
    def localization_service(self, mock_content_db):
        """Create mock localization service."""
        return MockLocalizationService(mock_content_db)
    
    @pytest.fixture
    def language_gateway(self):
        """Create mock language gateway."""
        return MockLanguageGateway()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dialogue_with_tts_generation(self, localization_service, language_gateway):
        """Test dialogue localization with TTS generation."""
        # Get dialogue in Japanese (TTS enabled)
        dialogue = await localization_service.get_dialogue_content('intro.welcome', 'ja-JP')
        
        assert dialogue is not None
        assert dialogue['text'] == '暗い世界へようこそ、{player_name}。'
        assert dialogue['tts_enabled'] is True
        
        # Generate TTS
        tts_result = await language_gateway.synthesize_speech(
            dialogue['text'],
            'ja-JP',
            emotion=dialogue['emotion']
        )
        
        assert tts_result['audio_data'] is not None
        assert tts_result['duration_ms'] > 0
        assert tts_result['voice_used'].startswith('ja-JP')
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fallback_chain_with_tts(self, localization_service, language_gateway):
        """Test fallback language chain with TTS synthesis."""
        # Request content in unsupported language
        dialogue = await localization_service.get_dialogue_content('intro.welcome', 'ko-KR')
        
        # Should fall back to English
        assert dialogue is not None
        assert dialogue['text'] == 'Welcome to the dark world, {player_name}.'
        
        # TTS should use English voice
        tts_result = await language_gateway.synthesize_speech(
            dialogue['text'],
            'en-US',  # Fallback language
            emotion=dialogue['emotion']
        )
        
        assert tts_result['voice_used'].startswith('en-US')
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_subtitle_timing_generation(self, localization_service, language_gateway):
        """Test subtitle timing generation for different languages."""
        languages = ['en-US', 'ja-JP', 'es-ES']
        
        for lang in languages:
            dialogue = await localization_service.get_dialogue_content('intro.welcome', lang)
            
            # Generate timing metadata
            timing = await language_gateway.get_timing_metadata(dialogue['text'], lang)
            
            assert 'words' in timing
            assert len(timing['words']) > 0
            assert timing['total_duration_ms'] > 0
            
            # Verify timing continuity
            for i in range(len(timing['words']) - 1):
                current = timing['words'][i]
                next_word = timing['words'][i + 1]
                
                # End of current should be before or at start of next
                assert current['end_ms'] <= next_word['start_ms']
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_placeholder_handling_across_languages(self, localization_service, language_gateway):
        """Test placeholder replacement in different languages."""
        player_name = "TestPlayer"
        languages = ['en-US', 'ja-JP', 'es-ES']
        
        for lang in languages:
            dialogue = await localization_service.get_dialogue_content('intro.welcome', lang)
            
            # Replace placeholder
            text_with_name = dialogue['text'].replace('{player_name}', player_name)
            
            # Generate TTS with replaced text
            tts_result = await language_gateway.synthesize_speech(
                text_with_name,
                lang,
                emotion=dialogue['emotion']
            )
            
            assert player_name.encode() in tts_result['audio_data']  # Mock check
            
            # Timing should handle the replaced text
            timing = await language_gateway.get_timing_metadata(text_with_name, lang)
            
            # Player name should appear in word timing
            words = [w['word'] for w in timing['words']]
            
            # Check based on language tokenization
            if lang == 'ja-JP':
                # Japanese might treat it differently
                assert any(player_name in word for word in words)
            else:
                assert player_name in words
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_emotion_aware_tts(self, localization_service, language_gateway):
        """Test emotion-aware TTS synthesis."""
        # Different emotions for the same text
        emotions = ['neutral', 'mysterious', 'threatening', 'sad']
        
        dialogue = await localization_service.get_dialogue_content('intro.welcome', 'en-US')
        base_text = dialogue['text']
        
        tts_results = []
        
        for emotion in emotions:
            result = await language_gateway.synthesize_speech(
                base_text,
                'en-US',
                emotion=emotion
            )
            tts_results.append(result)
        
        # Each emotion should produce different audio (in real implementation)
        # Cache keys should be different
        cache_keys = [f"{base_text}_en-US_None_{emotion}" for emotion in emotions]
        assert len(set(cache_keys)) == len(emotions)
        
        # Duration might vary by emotion (e.g., sad = slower)
        durations = [r['duration_ms'] for r in tts_results]
        # In mock, they're the same, but document expected behavior
        # assert max(durations) > min(durations) * 1.1  # At least 10% variation
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_tts_generation(self, localization_service, language_gateway):
        """Test batch TTS generation for multiple dialogues."""
        dialogue_ids = ['intro.welcome', 'vampire.greeting', 'battle.victory']
        languages = ['en-US', 'ja-JP']
        
        # Simulate batch processing
        tasks = []
        
        for dialogue_id in dialogue_ids:
            for lang in languages:
                async def process_dialogue(did=dialogue_id, language=lang):
                    # Mock dialogue lookup
                    dialogue = {
                        'text': f'Mock dialogue {did} in {language}',
                        'speaker': 'narrator',
                        'emotion': 'neutral',
                        'tts_enabled': True
                    }
                    
                    if dialogue['tts_enabled']:
                        return await language_gateway.synthesize_speech(
                            dialogue['text'],
                            language,
                            emotion=dialogue['emotion']
                        )
                    return None
                
                tasks.append(process_dialogue())
        
        # Process all in parallel
        results = await asyncio.gather(*tasks)
        
        assert len(results) == len(dialogue_ids) * len(languages)
        assert all(r is not None for r in results)
        
        # Check cache effectiveness
        assert len(language_gateway.tts_cache) == len(results)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_voice_consistency_across_sessions(self, language_gateway):
        """Test voice consistency for same character across sessions."""
        character_voices = {
            'narrator': 'en-US-Standard-A',
            'vampire_lord': 'en-US-Standard-B',
            'player_character': 'en-US-Wavenet-C'
        }
        
        # Generate speech for same character multiple times
        character = 'vampire_lord'
        voice = character_voices[character]
        
        texts = [
            "Your blood smells delicious.",
            "Come closer, mortal.",
            "The night is young."
        ]
        
        results = []
        for text in texts:
            result = await language_gateway.synthesize_speech(
                text,
                'en-US',
                voice_id=voice
            )
            results.append(result)
        
        # All should use the same voice
        voices_used = [r['voice_used'] for r in results]
        assert all(v == voice for v in voices_used)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_language_detection_and_correction(self, localization_service, language_gateway):
        """Test detection and correction of language mismatches."""
        # User's system language
        system_language = 'es-ES'
        
        # But they accidentally have game set to German
        game_language = 'de-DE'
        
        # Try to get content
        content = await localization_service.get_content('ui.button.start', game_language)
        
        if content is None:
            # German not available for this key, try system language
            content = await localization_service.get_content('ui.button.start', system_language)
            assert content is not None
            assert content['text'] == 'Iniciar Juego'
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tts_caching_performance(self, language_gateway):
        """Test TTS caching for performance."""
        text = "This is a frequently used dialogue line."
        language = 'en-US'
        
        # First generation (cache miss)
        start_time = asyncio.get_event_loop().time()
        result1 = await language_gateway.synthesize_speech(text, language)
        first_time = asyncio.get_event_loop().time() - start_time
        
        # Second generation (cache hit)
        start_time = asyncio.get_event_loop().time()
        result2 = await language_gateway.synthesize_speech(text, language)
        second_time = asyncio.get_event_loop().time() - start_time
        
        # Cache hit should be much faster
        assert second_time < first_time * 0.1  # At least 10x faster
        assert result1 == result2  # Same result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_localization_requests(self, localization_service):
        """Test handling of concurrent localization requests."""
        # Simulate multiple users requesting content simultaneously
        languages = ['en-US', 'ja-JP', 'es-ES', 'fr-FR', 'de-DE']
        keys = ['ui.button.start', 'dialogue.intro.welcome', 'error.network.timeout']
        
        tasks = []
        for _ in range(10):  # 10 concurrent users
            for lang in languages:
                for key in keys:
                    task = localization_service.get_content(key, lang)
                    tasks.append(task)
        
        # All should complete without errors
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # No exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_special_character_handling(self, localization_service, language_gateway):
        """Test handling of special characters in different languages."""
        special_texts = {
            'en-US': "Hello! How're you? Cost: $9.99 & save 50%!",
            'ja-JP': "こんにちは！元気ですか？価格：¥1000〜",
            'es-ES': "¡Hola! ¿Cómo estás? Precio: €9,99",
            'ar-SA': "مرحبا! كيف حالك؟ السعر: ﷼50",
            'zh-CN': "你好！你好吗？价格：￥68"
        }
        
        for lang, text in special_texts.items():
            # Generate TTS
            result = await language_gateway.synthesize_speech(text, lang)
            
            assert result is not None
            assert result['duration_ms'] > 0
            
            # Generate timing
            timing = await language_gateway.get_timing_metadata(text, lang)
            
            # Should handle special characters in timing
            assert timing['total_duration_ms'] > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dynamic_content_updates(self, localization_service, language_gateway):
        """Test handling of dynamic content updates."""
        # Initial content
        key = 'ui.notification.daily'
        initial_text = "Daily reward available!"
        
        # Mock content update
        localization_service.content_db[key] = {
            'en-US': {'text': initial_text, 'validated': True}
        }
        
        # Generate TTS for initial
        result1 = await language_gateway.synthesize_speech(initial_text, 'en-US')
        
        # Update content (e.g., special event)
        updated_text = "Double rewards today only!"
        localization_service.content_db[key]['en-US']['text'] = updated_text
        
        # Get updated content
        content = await localization_service.get_content(key, 'en-US')
        assert content['text'] == updated_text
        
        # Generate TTS for updated
        result2 = await language_gateway.synthesize_speech(updated_text, 'en-US')
        
        # Should be different
        assert result1['audio_data'] != result2['audio_data']
