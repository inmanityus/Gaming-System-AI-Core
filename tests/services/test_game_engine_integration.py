"""
Real tests for UE5 Game Engine Integration.
Created via pairwise testing protocol.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.language_system.integration.game_engine_integration import (
    UE5GameEngineIntegration,
    UE5DialogueRequest,
    UE5DialogueResponse
)


class TestUE5GameEngineIntegration:
    """Real tests for UE5 integration."""
    
    def test_initialization_with_api_url(self):
        """Test initialization with API URL."""
        integration = UE5GameEngineIntegration(ue5_api_url="http://test:8080")
        assert integration.ue5_api_url == "http://test:8080"
    
    def test_initialization_without_api_url(self):
        """Test initialization without API URL (uses environment or default)."""
        integration = UE5GameEngineIntegration()
        assert integration.ue5_api_url is not None
    
    @patch('services.language_system.integration.game_engine_integration.HTTPX_AVAILABLE', True)
    @patch('services.language_system.integration.game_engine_integration.httpx')
    def test_generate_dialogue_with_api_success(self, mock_httpx):
        """Test dialogue generation with successful API call."""
        # Setup mock HTTP client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "text": "Hello, traveler!",
            "audio_file": "/path/to/audio.wav",
            "subtitle": "Hello, traveler!",
            "language": "en"
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client
        
        integration = UE5GameEngineIntegration(ue5_api_url="http://test:8080")
        integration.http_client = mock_client
        
        request = UE5DialogueRequest(
            npc_id="test_npc",
            language="en",
            intent="greeting",
            context={}
        )
        
        result = integration.generate_dialogue(request)
        
        assert isinstance(result, UE5DialogueResponse)
        assert result.text == "Hello, traveler!"
        assert result.audio_file == "/path/to/audio.wav"
        assert result.language == "en"
        mock_client.post.assert_called_once()
    
    def test_generate_dialogue_fallback(self):
        """Test dialogue generation with fallback (no HTTP client)."""
        integration = UE5GameEngineIntegration()
        integration.http_client = None
        
        request = UE5DialogueRequest(
            npc_id="test_npc",
            language="en",
            intent="greeting",
            context={}
        )
        
        result = integration.generate_dialogue(request)
        
        assert isinstance(result, UE5DialogueResponse)
        assert "test_npc" in result.text or "Hello" in result.text
        assert result.language == "en"
    
    def test_generate_fallback_dialogue_intents(self):
        """Test fallback dialogue generation for different intents."""
        integration = UE5GameEngineIntegration()
        
        intents = ["greeting", "question", "trade", "quest", "unknown"]
        for intent in intents:
            request = UE5DialogueRequest(
                npc_id="test_npc",
                language="en",
                intent=intent,
                context={}
            )
            dialogue = integration._generate_fallback_dialogue(request)
            assert isinstance(dialogue, str)
            assert len(dialogue) > 0
    
    @patch('services.language_system.integration.game_engine_integration.HTTPX_AVAILABLE', True)
    @patch('services.language_system.integration.game_engine_integration.httpx')
    def test_apply_settings_success(self, mock_httpx):
        """Test applying settings with successful API call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client
        
        integration = UE5GameEngineIntegration()
        integration.http_client = mock_client
        
        settings = {"language": "en", "subtitle_enabled": True}
        result = integration.apply_settings(settings)
        
        assert result is True
        mock_client.post.assert_called_once()
    
    def test_apply_settings_fallback(self):
        """Test applying settings with fallback (no HTTP client)."""
        integration = UE5GameEngineIntegration()
        integration.http_client = None
        
        settings = {"language": "en", "subtitle_enabled": True}
        result = integration.apply_settings(settings)
        
        assert result is True
    
    @patch('services.language_system.integration.game_engine_integration.HTTPX_AVAILABLE', True)
    @patch('services.language_system.integration.game_engine_integration.httpx')
    def test_sync_audio_success(self, mock_httpx):
        """Test audio sync with successful API call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client
        
        integration = UE5GameEngineIntegration()
        integration.http_client = mock_client
        
        result = integration.sync_audio("/path/to/audio.wav", "Subtitle text")
        
        assert result is True
        mock_client.post.assert_called_once()
    
    def test_sync_audio_fallback(self):
        """Test audio sync with fallback (no HTTP client)."""
        integration = UE5GameEngineIntegration()
        integration.http_client = None
        
        result = integration.sync_audio("/path/to/audio.wav", "Subtitle text")
        
        assert result is True
    
    def test_close_cleans_up_client(self):
        """Test that close() cleans up HTTP client."""
        integration = UE5GameEngineIntegration()
        mock_client = MagicMock()
        integration.http_client = mock_client
        
        integration.close()
        
        assert integration.http_client is None
        mock_client.close.assert_called_once()

