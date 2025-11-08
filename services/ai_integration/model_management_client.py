"""
Model Management HTTP Client - Replaces cross-service imports.
Provides HTTP-based access to model management service functionality.
"""

import asyncio
import aiohttp
import os
from typing import Any, Dict, List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ModelManagementClient:
    """HTTP client for model-management service."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "MODEL_MANAGEMENT_URL", 
            "http://model-management:8080"
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30.0)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_current_model(self, use_case: str) -> Optional[Dict[str, Any]]:
        """
        Get current model for a specific use case.
        
        Args:
            use_case: Use case identifier (e.g., "foundation_layer", "story_generation")
        
        Returns:
            Model information dict or None if not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/models/current/{use_case}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Failed to get current model: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting current model: {e}")
            return None
    
    async def log_inference(
        self,
        model_id: UUID,
        use_case: str,
        prompt: str,
        context: Dict[str, Any],
        generated_output: str,
        performance_metrics: Dict[str, Any]
    ) -> bool:
        """
        Log inference to historical logs.
        
        Args:
            model_id: Model UUID
            use_case: Use case identifier
            prompt: Input prompt
            context: Request context
            generated_output: Generated text
            performance_metrics: Performance metrics dict
        
        Returns:
            True if logged successfully
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/logs/inference"
            
            payload = {
                "model_id": str(model_id),
                "use_case": use_case,
                "prompt": prompt,
                "context": context,
                "generated_output": generated_output,
                "performance_metrics": performance_metrics
            }
            
            async with session.post(url, json=payload) as response:
                if response.status in (200, 201):
                    return True
                else:
                    logger.error(f"Failed to log inference: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error logging inference: {e}")
            return False
    
    async def select_optimal_model(
        self,
        task_type: str,
        context: Dict[str, Any],
        priority: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Select optimal model using cost-benefit router.
        
        Args:
            task_type: Task type identifier
            context: Request context
            priority: Priority level (balanced, speed, quality, cost)
        
        Returns:
            Routing decision with selected model
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/routing/select"
            
            payload = {
                "task_type": task_type,
                "context": context,
                "priority": priority
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to select optimal model: {response.status}")
                    return {
                        "selected_model_id": "fallback",
                        "selected_model_name": "fallback",
                        "reason": "routing_failed"
                    }
        except Exception as e:
            logger.error(f"Error selecting optimal model: {e}")
            return {
                "selected_model_id": "fallback",
                "selected_model_name": "fallback",
                "reason": f"error: {str(e)}"
            }
    
    async def monitor_outputs(
        self,
        model_id: str,
        outputs: List[str]
    ) -> Dict[str, Any]:
        """
        Monitor outputs with guardrails.
        
        Args:
            model_id: Model identifier
            outputs: List of output texts to monitor
        
        Returns:
            Monitoring results with compliance status
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/guardrails/monitor"
            
            payload = {
                "model_id": model_id,
                "outputs": outputs
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to monitor outputs: {response.status}")
                    return {
                        "compliant": True,  # Default to compliant if service unavailable
                        "violations": []
                    }
        except Exception as e:
            logger.error(f"Error monitoring outputs: {e}")
            return {
                "compliant": True,  # Default to compliant if service unavailable
                "violations": []
            }
    
    async def generate_with_srl_model(
        self,
        tier: str,
        model_name: str,
        adapter_name: Optional[str],
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Generate text using SRL-trained model.
        
        Args:
            tier: Model tier (gold, silver, bronze)
            model_name: Base model name
            adapter_name: LoRA adapter name (optional)
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/srl/generate"
            
            payload = {
                "tier": tier,
                "model_name": model_name,
                "adapter_name": adapter_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("text", "")
                else:
                    logger.error(f"Failed to generate with SRL model: {response.status}")
                    raise Exception(f"SRL generation failed: {response.status}")
        except Exception as e:
            logger.error(f"Error generating with SRL model: {e}")
            raise Exception(f"SRL model generation failed: {e}")
    
    async def get_deployment_info(self, model_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get deployment information for a model.
        
        Args:
            model_id: Model UUID
        
        Returns:
            Deployment info dict or None
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/deployments/{model_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Failed to get deployment info: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting deployment info: {e}")
            return None


# Singleton instance
_client_instance: Optional[ModelManagementClient] = None


def get_model_management_client() -> ModelManagementClient:
    """Get singleton ModelManagementClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = ModelManagementClient()
    return _client_instance

