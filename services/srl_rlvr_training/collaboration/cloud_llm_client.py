"""
Cloud LLM Client
================

HTTP client for communicating with cloud LLMs via OpenRouter API.
Supports GPT-5 Pro, Claude 4.5 Sonnet, Gemini 2.5 Pro, and other models.
"""

import logging
import os
from typing import Dict, List, Optional, Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from .base_http_client import BaseHttpClient

logger = logging.getLogger(__name__)


class CloudLLMClient(BaseHttpClient):
    """
    Client for calling cloud LLMs via OpenRouter API.
    
    Supports multiple models:
    - GPT-5 Pro: openai/gpt-5-pro
    - Claude 4.5 Sonnet: anthropic/claude-sonnet-4.5
    - Gemini 2.5 Pro: google/gemini-2.5-pro
    """
    
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 60.0):
        """
        Initialize Cloud LLM Client.
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            timeout: Request timeout in seconds
        """
        super().__init__(self.OPENROUTER_API_URL, timeout)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set - API calls will fail")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-5-pro",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Generate text using cloud LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., 'openai/gpt-5-pro')
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenRouter API parameters
        
        Returns:
            Generated text, or None if request failed
        """
        if not self.api_key:
            logger.error("API key not set - cannot generate")
            return None
        
        logger.info(f"Generating with {model} (temp={temperature})")
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add any additional parameters
        payload.update(kwargs)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://gaming-system-ai-core",  # Optional
            "X-Title": "Gaming System AI Core",  # Optional
        }
        
        # Make request using base class
        session = await self._get_session()
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with session.post(
                    self.OPENROUTER_API_URL,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._record_success()
                        
                        # Extract generated text
                        if "choices" in data and len(data["choices"]) > 0:
                            generated_text = data["choices"][0]["message"]["content"]
                            logger.debug(f"Generated {len(generated_text)} characters")
                            return generated_text
                        else:
                            logger.warning("No choices in response")
                            return None
                    
                    elif response.status == 401:
                        logger.error("Authentication failed - check API key")
                        await self._record_success()  # Not a retriable service failure
                        return None
                    
                    elif 400 <= response.status < 500:
                        error_text = await response.text()
                        logger.error(f"Client error {response.status}: {error_text}")
                        await self._record_success()  # Not a retriable service failure
                        return None
                    
                    else:
                        logger.warning(f"Server returned status {response.status}")
                        await self._record_failure()
                        retry_count += 1
                        
            except Exception as e:
                logger.error(f"Error calling OpenRouter API: {e}")
                await self._record_failure()
                retry_count += 1
            
            if retry_count < max_retries:
                wait_time = 2 ** retry_count
                logger.info(f"Retrying in {wait_time} seconds...")
                import asyncio
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to generate after {max_retries} attempts")
        return None
    
    def _make_request(self, *args, **kwargs):
        """
        Override base class _make_request - not used for OpenRouter API.
        OpenRouter uses POST with JSON body, not GET with params.
        """
        raise NotImplementedError("Use generate() method instead")

