"""
Paid Model Scanner - Scans available paid models from providers.
Scans OpenRouter, Anthropic, OpenAI, Google for available models.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import aiohttp
from aiohttp import ClientSession, ClientTimeout


class PaidModelScanner:
    """
    Scans available paid models from various providers.
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=30.0)
        self.openrouter_api_key: Optional[str] = None  # Should come from config
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def scan_available_models(
        self,
        use_case: str,
        providers: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan available models from paid providers.
        
        Args:
            use_case: Use case identifier (story_generation, narrative_coordination, etc.)
            providers: List of providers to scan (default: all)
        
        Returns:
            List of available models with metadata
        """
        if providers is None:
            providers = ["openrouter", "openai", "anthropic", "google"]
        
        all_models = []
        
        for provider in providers:
            try:
                if provider == "openrouter":
                    models = await self._scan_openrouter(use_case)
                elif provider == "openai":
                    models = await self._scan_openai(use_case)
                elif provider == "anthropic":
                    models = await self._scan_anthropic(use_case)
                elif provider == "google":
                    models = await self._scan_google(use_case)
                else:
                    continue
                
                all_models.extend(models)
            except Exception as e:
                # Log error but continue scanning other providers
                print(f"Error scanning {provider}: {e}")
                continue
        
        # Filter by use case compatibility
        compatible_models = [
            m for m in all_models
            if self._is_compatible_for_use_case(m, use_case)
        ]
        
        return compatible_models
    
    async def _scan_openrouter(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Scan OpenRouter for available models.
        
        OpenRouter provides access to many models across providers.
        """
        session = await self._get_session()
        
        try:
            # Get model list from OpenRouter
            async with session.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.openrouter_api_key}"} if self.openrouter_api_key else {}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    
                    # Convert to our format
                    formatted_models = []
                    for model in models:
                        formatted_models.append({
                            "model_id": model.get("id"),
                            "model_name": model.get("name"),
                            "provider": "openrouter",
                            "model_type": "paid",
                            "use_case": use_case,
                            "context_length": model.get("context_length"),
                            "pricing": model.get("pricing", {}),
                            "architecture": model.get("architecture", {}),
                            "top_provider": model.get("top_provider", {}),
                            "permission": model.get("permission")
                        })
                    
                    return formatted_models
        except Exception as e:
            print(f"Error scanning OpenRouter: {e}")
        
        return []
    
    async def _scan_openai(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Scan OpenAI API for available models.
        
        Note: OpenAI doesn't have a public model listing API,
        so we use known models.
        """
        known_models = [
            {
                "model_id": "gpt-4o",
                "model_name": "GPT-4o",
                "provider": "openai",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 128000,
                "capabilities": ["text", "vision", "tools"]
            },
            {
                "model_id": "gpt-4-turbo",
                "model_name": "GPT-4 Turbo",
                "provider": "openai",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 128000,
                "capabilities": ["text", "vision", "tools"]
            },
            {
                "model_id": "gpt-3.5-turbo",
                "model_name": "GPT-3.5 Turbo",
                "provider": "openai",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 16385,
                "capabilities": ["text", "tools"]
            }
        ]
        
        return known_models
    
    async def _scan_anthropic(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Scan Anthropic API for available models.
        
        Known Anthropic models.
        """
        known_models = [
            {
                "model_id": "claude-3-5-sonnet-20241022",
                "model_name": "Claude 3.5 Sonnet",
                "provider": "anthropic",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 200000,
                "capabilities": ["text", "vision", "tools"]
            },
            {
                "model_id": "claude-3-opus-20240229",
                "model_name": "Claude 3 Opus",
                "provider": "anthropic",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 200000,
                "capabilities": ["text", "vision", "tools"]
            }
        ]
        
        return known_models
    
    async def _scan_google(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Scan Google API for available models.
        
        Known Google models.
        """
        known_models = [
            {
                "model_id": "gemini-2.0-flash-exp",
                "model_name": "Gemini 2.0 Flash",
                "provider": "google",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 1000000,  # 1M tokens
                "capabilities": ["text", "vision", "tools"]
            },
            {
                "model_id": "gemini-pro",
                "model_name": "Gemini Pro",
                "provider": "google",
                "model_type": "paid",
                "use_case": use_case,
                "context_length": 32768,
                "capabilities": ["text", "vision", "tools"]
            }
        ]
        
        return known_models
    
    def _is_compatible_for_use_case(
        self,
        model: Dict[str, Any],
        use_case: str
    ) -> bool:
        """
        Check if model is compatible for use case.
        
        Compatibility rules:
        - Story generation: Needs large context, good coherence
        - NPC dialogue: Needs personality, dialogue capability
        - Narrative coordination: Needs reasoning, coordination capability
        """
        # Basic compatibility check
        # Can be expanded with more sophisticated logic
        
        if use_case == "story_generation":
            # Need large context and good quality
            return model.get("context_length", 0) >= 100000
        
        if use_case == "npc_dialogue":
            # Need reasonable context
            return model.get("context_length", 0) >= 8000
        
        if use_case == "narrative_coordination":
            # Need large context and reasoning
            return model.get("context_length", 0) >= 100000
        
        # Default: compatible
        return True












