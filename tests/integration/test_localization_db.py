"""
Database integration tests for localization services.
Tests real PostgreSQL interactions using testcontainers.
"""
import pytest
import asyncio
from datetime import datetime, timezone
import json
import hashlib
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.multi_language.localization_store import LocalizationStore
from services.multi_language.language_gateway import LanguageGateway
from services.multi_language.quality_assurance import QASystem


@pytest.mark.integration
class TestLocalizationDatabase:
    """Test localization services with real database."""
    
    async def test_store_and_retrieve_content(self, postgres_pool):
        """Test storing and retrieving localized content."""
        store = LocalizationStore(db_pool=postgres_pool)
        
        # Store content
        content = {
            'en-US': {
                'text': 'Welcome to the game!',
                'validated': True,
                'audio_file': 'welcome_en.ogg'
            },
            'ja-JP': {
                'text': 'ゲームへようこそ！',
                'validated': True,
                'tts_enabled': True
            },
            'es-ES': {
                'text': '¡Bienvenido al juego!',
                'validated': False
            }
        }
        
        await store.set_content('ui.welcome.message', content, 'ui')
        
        # Retrieve content
        retrieved = await store.get_content('ui.welcome.message', 'en-US')
        assert retrieved['text'] == 'Welcome to the game!'
        assert retrieved['validated'] is True
        assert retrieved['audio_file'] == 'welcome_en.ogg'
        
        # Retrieve all languages
        all_content = await store.get_all_languages('ui.welcome.message')
        assert len(all_content) == 3
        assert 'ja-JP' in all_content
        assert all_content['ja-JP']['tts_enabled'] is True
    
    async def test_fallback_chain(self, postgres_pool):
        """Test language fallback chain functionality."""
        store = LocalizationStore(db_pool=postgres_pool)
        
        # Set up fallback configuration
        store.fallback_chains = {
            'en-GB': ['en-US'],
            'es-MX': ['es-ES', 'en-US'],
            'zh-TW': ['zh-CN', 'en-US']
        }
        
        # Store content only in some languages
        content = {
            'en-US': {'text': 'Color', 'validated': True},
            'es-ES': {'text': 'Color', 'validated': True},
            'zh-CN': {'text': '颜色', 'validated': True}
        }
        
        await store.set_content('ui.settings.color', content, 'ui')
        
        # Test fallbacks
        # en-GB should fall back to en-US
        result = await store.get_content('ui.settings.color', 'en-GB')
        assert result['text'] == 'Color'
        assert result.get('_fallback_used') == 'en-US'
        
        # es-MX should fall back to es-ES
        result = await store.get_content('ui.settings.color', 'es-MX')
        assert result['text'] == 'Color'
        assert result.get('_fallback_used') == 'es-ES'
        
        # zh-TW should fall back to zh-CN
        result = await store.get_content('ui.settings.color', 'zh-TW')
        assert result['text'] == '颜色'
        assert result.get('_fallback_used') == 'zh-CN'
    
    async def test_batch_operations(self, postgres_pool):
        """Test batch content operations."""
        store = LocalizationStore(db_pool=postgres_pool)
        
        # Prepare batch content
        batch_content = {}
        for i in range(50):
            key = f'dialogue.npc.greeting_{i}'
            batch_content[key] = {
                'en-US': {'text': f'Hello, traveler {i}!', 'validated': True},
                'ja-JP': {'text': f'こんにちは、旅人{i}！', 'validated': True}
            }
        
        # Batch insert
        async with postgres_pool.acquire() as conn:
            async with conn.transaction():
                for key, content in batch_content.items():
                    await store.set_content(key, content, 'dialogue')
        
        # Verify all inserted
        keys = await store.get_keys_by_category('dialogue')
        dialogue_keys = [k for k in keys if k.startswith('dialogue.npc.greeting_')]
        assert len(dialogue_keys) == 50
    
    async def test_versioning(self, postgres_pool):
        """Test content versioning."""
        store = LocalizationStore(db_pool=postgres_pool)
        
        key = 'ui.button.submit'
        
        # Version 1
        content_v1 = {
            'en-US': {'text': 'Submit', 'validated': True}
        }
        await store.set_content(key, content_v1, 'ui')
        
        # Get version 1
        async with postgres_pool.acquire() as conn:
            v1 = await conn.fetchrow("""
                SELECT version, content FROM localization.content
                WHERE key = $1
            """, key)
        
        assert v1['version'] == 1
        
        # Version 2 - update
        content_v2 = {
            'en-US': {'text': 'Submit Form', 'validated': True},
            'ja-JP': {'text': '送信', 'validated': True}
        }
        await store.set_content(key, content_v2, 'ui')
        
        # Get version 2
        async with postgres_pool.acquire() as conn:
            v2 = await conn.fetchrow("""
                SELECT version, content FROM localization.content
                WHERE key = $1
            """, key)
        
        assert v2['version'] == 2
        assert v2['content']['en-US']['text'] == 'Submit Form'
        assert 'ja-JP' in v2['content']
    
    async def test_language_statistics(self, postgres_pool):
        """Test language statistics tracking."""
        store = LocalizationStore(db_pool=postgres_pool)
        
        # Insert various content
        test_content = {
            'complete.key.1': {
                'en-US': {'text': 'Text 1', 'validated': True},
                'ja-JP': {'text': 'テキスト1', 'validated': True},
                'es-ES': {'text': 'Texto 1', 'validated': True}
            },
            'partial.key.1': {
                'en-US': {'text': 'Text 2', 'validated': True},
                'ja-JP': {'text': 'テキスト2', 'validated': False}
            },
            'english.only.1': {
                'en-US': {'text': 'Text 3', 'validated': True}
            }
        }
        
        for key, content in test_content.items():
            await store.set_content(key, content, 'test')
        
        # Update statistics
        await store.update_language_statistics()
        
        # Check statistics
        stats = await store.get_language_statistics()
        
        # en-US should have all 3 keys
        en_stats = next(s for s in stats if s['language_code'] == 'en-US')
        assert en_stats['total_keys'] == 3
        assert en_stats['translated_keys'] == 3
        assert en_stats['validated_keys'] == 3
        assert en_stats['missing_keys'] == 0
        
        # ja-JP should have 2 keys, 1 validated
        ja_stats = next(s for s in stats if s['language_code'] == 'ja-JP')
        assert ja_stats['translated_keys'] == 2
        assert ja_stats['validated_keys'] == 1
        assert ja_stats['missing_keys'] == 1
    
    async def test_concurrent_updates(self, postgres_pool):
        """Test handling concurrent content updates."""
        store = LocalizationStore(db_pool=postgres_pool)
        key = 'concurrent.test.key'
        
        # Initial content
        await store.set_content(key, {
            'en-US': {'text': 'Initial', 'validated': True}
        }, 'test')
        
        # Concurrent updates
        async def update_content(lang, text):
            content = await store.get_all_languages(key)
            content[lang] = {'text': text, 'validated': True}
            await store.set_content(key, content, 'test')
        
        # Run updates concurrently
        tasks = [
            update_content('ja-JP', '日本語'),
            update_content('es-ES', 'Español'),
            update_content('fr-FR', 'Français'),
            update_content('de-DE', 'Deutsch'),
            update_content('ko-KR', '한국어')
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify final state
        final_content = await store.get_all_languages(key)
        
        # Should have at least the initial language
        assert 'en-US' in final_content
        
        # Some updates may have succeeded
        assert len(final_content) >= 2


@pytest.mark.integration
class TestLanguageSystemDatabase:
    """Test language system TTS with database."""
    
    async def test_tts_cache(self, postgres_pool):
        """Test TTS result caching in database."""
        gateway = LanguageGateway(
            localization_store=LocalizationStore(db_pool=postgres_pool),
            db_pool=postgres_pool
        )
        
        # Mock TTS provider
        gateway._providers['mock'] = type('MockProvider', (), {
            'synthesize': lambda self, text, lang, voice: {
                'audio_data': b'mock_audio_' + text.encode(),
                'format': 'mp3',
                'duration_ms': len(text) * 100
            }
        })()
        gateway._default_voices['en-US'] = ('mock', 'mock_voice')
        
        # First request - should generate and cache
        result1 = await gateway.synthesize_speech(
            'Hello, world!',
            'en-US'
        )
        
        # Check cache entry
        text_hash = hashlib.sha256('Hello, world!'.encode()).hexdigest()
        async with postgres_pool.acquire() as conn:
            cache_entry = await conn.fetchrow("""
                SELECT * FROM language.tts_cache
                WHERE text_hash = $1 AND language_code = $2
            """, text_hash, 'en-US')
        
        assert cache_entry is not None
        assert cache_entry['audio_data'] == result1['audio_data']
        assert cache_entry['access_count'] == 1
        
        # Second request - should use cache
        result2 = await gateway.synthesize_speech(
            'Hello, world!',
            'en-US'
        )
        
        assert result2['audio_data'] == result1['audio_data']
        assert result2.get('cached') is True
        
        # Check access count increased
        async with postgres_pool.acquire() as conn:
            access_count = await conn.fetchval("""
                SELECT access_count FROM language.tts_cache
                WHERE text_hash = $1 AND language_code = $2
            """, text_hash, 'en-US')
        
        assert access_count == 2
    
    async def test_tts_metrics(self, postgres_pool):
        """Test TTS metrics collection."""
        gateway = LanguageGateway(
            localization_store=LocalizationStore(db_pool=postgres_pool),
            db_pool=postgres_pool
        )
        
        # Mock provider
        call_count = 0
        def mock_synthesize(text, lang, voice):
            nonlocal call_count
            call_count += 1
            return {
                'audio_data': f'audio_{call_count}'.encode(),
                'format': 'mp3',
                'duration_ms': 1000
            }
        
        gateway._providers['mock'] = type('MockProvider', (), {
            'synthesize': lambda self, text, lang, voice: mock_synthesize(text, lang, voice)
        })()
        gateway._default_voices['en-US'] = ('mock', 'mock_voice')
        
        # Generate multiple TTS requests
        texts = ['Hello', 'World', 'Testing', 'Hello']  # 'Hello' repeated for cache test
        
        for text in texts:
            await gateway.synthesize_speech(text, 'en-US')
        
        # Check metrics
        async with postgres_pool.acquire() as conn:
            metrics = await conn.fetch("""
                SELECT * FROM language.tts_metrics
                WHERE language_code = 'en-US'
                ORDER BY timestamp
            """)
        
        assert len(metrics) == 4
        
        # First 3 should be cache misses
        for i in range(3):
            assert metrics[i]['cache_hit'] is False
        
        # Last one should be cache hit (repeated 'Hello')
        assert metrics[3]['cache_hit'] is True
        
        # Check aggregate stats
        cache_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                AVG(generation_time_ms) as avg_generation_time
            FROM language.tts_metrics
            WHERE language_code = 'en-US'
        """)
        
        assert cache_stats['total_requests'] == 4
        assert cache_stats['cache_hits'] == 1
        assert cache_stats['avg_generation_time'] is not None
    
    async def test_cache_eviction(self, postgres_pool):
        """Test TTS cache eviction for old entries."""
        # This would test cache eviction policies
        # For now, we'll test manual cleanup
        
        async with postgres_pool.acquire() as conn:
            # Insert old cache entry
            await conn.execute("""
                INSERT INTO language.tts_cache
                (text_hash, language_code, audio_data, audio_format,
                 created_at, accessed_at)
                VALUES ($1, $2, $3, $4, $5, $5)
            """,
            'old_hash_12345',
            'en-US',
            b'old_audio_data',
            'mp3',
            datetime.now(timezone.utc) - timedelta(days=60)
            )
            
            # Cleanup old entries (older than 30 days)
            deleted = await conn.fetchval("""
                DELETE FROM language.tts_cache
                WHERE accessed_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
                RETURNING COUNT(*)
            """)
            
            # Our old entry should be deleted
            remaining = await conn.fetchval("""
                SELECT COUNT(*) FROM language.tts_cache
                WHERE text_hash = 'old_hash_12345'
            """)
            
            assert remaining == 0


@pytest.mark.integration
class TestQASystemDatabase:
    """Test QA system with database storage."""
    
    async def test_qa_report_storage(self, postgres_pool):
        """Test storing QA validation reports."""
        qa_system = QASystem(db_pool=postgres_pool)
        
        # Create mock localization store
        store = LocalizationStore(db_pool=postgres_pool)
        qa_system.localization_store = store
        
        # Add test content
        await store.set_content('test.qa.message', {
            'en-US': {'text': 'Test message', 'validated': True},
            'ja-JP': {'text': 'テストメッセージ', 'validated': False}
        }, 'test')
        
        # Run QA validation
        report = await qa_system.validate_all_content()
        
        # Store report in database (extend schema if needed)
        async with postgres_pool.acquire() as conn:
            # Create QA reports table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS localization.qa_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    total_keys INTEGER,
                    validated_keys INTEGER,
                    issues JSONB,
                    language_coverage JSONB,
                    report_data JSONB
                )
            """)
            
            # Store report
            await conn.execute("""
                INSERT INTO localization.qa_reports
                (total_keys, validated_keys, issues, language_coverage, report_data)
                VALUES ($1, $2, $3, $4, $5)
            """,
            report['total_keys'],
            report['validated_keys'],
            json.dumps(report['issues']),
            json.dumps(report['coverage_by_language']),
            json.dumps(report)
            )
            
            # Verify stored
            stored_report = await conn.fetchrow("""
                SELECT * FROM localization.qa_reports
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            assert stored_report is not None
            assert stored_report['total_keys'] == report['total_keys']
