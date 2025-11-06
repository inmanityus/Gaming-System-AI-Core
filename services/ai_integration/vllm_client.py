"""
vLLM Server Integration - AI-002
Production LLM model serving using vLLM.
AI-005: Continuous batching support added.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
from aiohttp import ClientSession, ClientTimeout


class VLLMClient:
    """
    Client for vLLM inference server.
    Supports GPU-accelerated model serving with LoRA adapters.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000")
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=60.0)
        self._models_loaded: Dict[str, bool] = {}
        
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vLLM server health."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                return {"status": "unhealthy", "code": response.status}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["id"] for model in data.get("data", [])]
                return []
        except Exception:
            return []
    
    async def generate(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 1.0,
        lora_request: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text using vLLM.
        
        Args:
            model: Model name
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            lora_request: LoRA adapter name (optional)
            stream: Whether to stream response
        
        Returns:
            Generation result
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
        }
        
        if lora_request:
            payload["lora_request"] = lora_request
        
        try:
            async with session.post(
                f"{self.base_url}/v1/completions",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}: {error_text}",
                        "success": False
                    }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        lora_request: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat completion using vLLM.
        
        Args:
            model: Model name
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            lora_request: LoRA adapter name (optional)
        
        Returns:
            Chat completion result
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if lora_request:
            payload["lora_request"] = lora_request
        
        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}: {error_text}",
                        "success": False
                    }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

