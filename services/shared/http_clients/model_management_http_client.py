"""
HTTP Client for Model Management Service
Replaces direct imports from services.model_management
"""

import aiohttp
from typing import Dict, Any, List, Optional
from uuid import UUID


class ModelManagementHTTPClient:
    """HTTP client for model-management service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "http://model-management:8000"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def register_model(
        self,
        model_name: str,
        model_type: str,
        provider: str,
        use_case: str,
        version: str,
        model_path: Optional[str] = None,
        configuration: Dict[str, Any] = None,
        performance_metrics: Dict[str, Any] = None,
        resource_requirements: Dict[str, Any] = None,
        api_key: str = None
    ) -> Dict[str, Any]:
        """Register a new model."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/model-management/register"
        headers = {"x-api-key": api_key} if api_key else {}
        
        payload = {
            "model_name": model_name,
            "model_type": model_type,
            "provider": provider,
            "use_case": use_case,
            "version": version,
            "model_path": model_path,
            "configuration": configuration or {},
            "performance_metrics": performance_metrics or {},
            "resource_requirements": resource_requirements or {}
        }
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get model information by ID."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/model-management/models/{model_id}"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    
    async def list_models(
        self,
        model_type: Optional[str] = None,
        use_case: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all models with optional filtering."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/model-management/models"
        params = {}
        if model_type:
            params["model_type"] = model_type
        if use_case:
            params["use_case"] = use_case
        
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/health"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()


# Global singleton instance
_client_instance: Optional[ModelManagementHTTPClient] = None


def get_model_management_client(base_url: str = None) -> ModelManagementHTTPClient:
    """Get or create ModelManagementHTTPClient singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = ModelManagementHTTPClient(base_url)
    return _client_instance

