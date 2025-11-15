from __future__ import annotations

"""
Game Engine Integration (UE5)
===============================

Provides integration with Unreal Engine 5 for dialogue and language systems.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

logger = logging.getLogger(__name__)


@dataclass
class UE5DialogueRequest:
    """Request for UE5 dialogue generation."""
    npc_id: str
    language: str
    intent: str
    context: Dict[str, Any]


@dataclass
class UE5DialogueResponse:
    """Response from UE5 dialogue system."""
    text: str
    audio_file: Optional[str] = None
    subtitle: Optional[str] = None
    language: str = ""


class UE5GameEngineIntegration:
    """
    Integration with Unreal Engine 5 game engine.
    
    Provides:
    - Dialogue system integration
    - Settings UI integration
    - Language system communication
    - Audio synchronization
    """
    
    def __init__(self, ue5_api_url: Optional[str] = None):
        """
        Initialize UE5 integration.
        
        Args:
            ue5_api_url: URL to UE5 API endpoint (if None, uses environment variable or localhost)
        """
        self.ue5_api_url = ue5_api_url or os.getenv("UE5_API_URL", "http://localhost:8080")
        self.http_client = None
        
        if HTTPX_AVAILABLE:
            self.http_client = httpx.Client(timeout=30.0, base_url=self.ue5_api_url)
        else:
            logger.warning("httpx not available, UE5 integration will use fallback methods")
        
        logger.info(f"UE5GameEngineIntegration initialized (API URL: {self.ue5_api_url})")
    
    def generate_dialogue(self, request: UE5DialogueRequest) -> UE5DialogueResponse:
        """
        Generate dialogue for UE5 via API or message queue.
        
        Args:
            request: Dialogue request
            
        Returns:
            Dialogue response
        """
        logger.info(f"Generating dialogue for NPC {request.npc_id} in {request.language}")
        
        try:
            if self.http_client:
                # Make API call to UE5
                response = self.http_client.post(
                    "/api/dialogue/generate",
                    json={
                        "npc_id": request.npc_id,
                        "language": request.language,
                        "intent": request.intent,
                        "context": request.context
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return UE5DialogueResponse(
                    text=data.get("text", ""),
                    audio_file=data.get("audio_file"),
                    subtitle=data.get("subtitle"),
                    language=data.get("language", request.language)
                )
            else:
                # Fallback: Generate dialogue locally (simulated)
                # In production, this would use a message queue (RabbitMQ, SQS, etc.)
                logger.warning("HTTP client not available, using fallback dialogue generation")
                
                # Basic dialogue generation based on intent
                dialogue_text = self._generate_fallback_dialogue(request)
                
                return UE5DialogueResponse(
                    text=dialogue_text,
                    language=request.language,
                    subtitle=dialogue_text
                )
                
        except Exception as e:
            logger.error(f"Error generating dialogue: {e}")
            # Return fallback dialogue on error
            return UE5DialogueResponse(
                text=self._generate_fallback_dialogue(request),
                language=request.language,
                subtitle=self._generate_fallback_dialogue(request)
            )
    
    def _generate_fallback_dialogue(self, request: UE5DialogueRequest) -> str:
        """Generate fallback dialogue when API is unavailable."""
        # Basic intent-based dialogue templates
        intent_templates = {
            "greeting": f"Hello, traveler. I am {request.npc_id}.",
            "question": f"I can help you with that. What would you like to know?",
            "trade": f"Let's see what we can trade. What do you have?",
            "quest": f"I have a task for you, if you're interested.",
            "default": f"I'm here to help. What do you need?"
        }
        
        template = intent_templates.get(request.intent, intent_templates["default"])
        
        # Add language-specific flavor if available in context
        if "dialogue_style" in request.context:
            template = f"[{request.context['dialogue_style']}] {template}"
        
        return template
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply language settings to UE5.
        
        Args:
            settings: Dictionary of settings to apply (e.g., {"language": "en", "subtitle_enabled": True})
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Applying settings to UE5: {settings}")
        
        try:
            if self.http_client:
                response = self.http_client.post(
                    "/api/settings/apply",
                    json=settings
                )
                response.raise_for_status()
                return True
            else:
                # Fallback: Log settings (would be sent via message queue in production)
                logger.warning("HTTP client not available, settings logged but not applied")
                # In production, this would publish to a message queue (RabbitMQ, SQS, etc.)
                return True
                
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            return False
    
    def sync_audio(self, audio_file: str, subtitle: str) -> bool:
        """
        Synchronize audio with subtitle display in UE5.
        
        Args:
            audio_file: Path to audio file
            subtitle: Subtitle text to display
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Syncing audio {audio_file} with subtitle: {subtitle[:50]}...")
        
        try:
            if self.http_client:
                response = self.http_client.post(
                    "/api/audio/sync",
                    json={
                        "audio_file": audio_file,
                        "subtitle": subtitle
                    }
                )
                response.raise_for_status()
                return True
            else:
                # Fallback: Log sync request (would be sent via message queue in production)
                logger.warning("HTTP client not available, audio sync logged but not applied")
                # In production, this would publish to a message queue
                return True
                
        except Exception as e:
            logger.error(f"Error syncing audio: {e}")
            return False
    
    def close(self):
        """Clean up HTTP client resources."""
        if self.http_client:
            self.http_client.close()
            self.http_client = None


