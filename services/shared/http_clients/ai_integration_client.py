"""
HTTP Client for AI Integration Service
"""

from typing import Dict, Any, Optional
from .base_client import BaseHTTPClient


class AIIntegrationClient(BaseHTTPClient):
    """HTTP client for ai-integration service."""
    
    def __init__(self, base_url: str = None):
        super().__init__(base_url or "http://ai-integration:8000")
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate text using LLM."""
        return await self.post(
            "/api/v1/ai/generate",
            json={
                "prompt": prompt,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )
    
    async def get_active_model(self) -> Dict[str, Any]:
        """Get currently active model info."""
        return await self.get("/api/v1/ai/active-model")
    
    async def switch_model(self, model_id: str, api_key: str) -> Dict[str, Any]:
        """Switch to different model."""
        return await self.post(
            "/api/v1/ai/switch-model",
            json={"model_id": model_id},
            headers={"x-api-key": api_key}
        )

