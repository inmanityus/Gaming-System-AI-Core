"""
LLM Client - Manages connections to hierarchical LLM system.
Handles load balancing, retry logic, and circuit breaker patterns.
Integrated with Model Management System for model selection and tracking.
"""

import asyncio
import json
import sys
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout

# Add parent directory to path for model_management imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from services.model_management.model_registry import ModelRegistry
from services.model_management.historical_log_processor import HistoricalLogProcessor


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class LLMServiceUnavailableError(Exception):
    """Raised when LLM service is unavailable."""
    pass


class LLMClient:
    """
    Manages connections to hierarchical LLM system.
    Implements load balancing, retry logic, and circuit breaker patterns.
    Integrated with Model Management System for model selection and tracking.
    """
    
    def __init__(self, model_registry: Optional[ModelRegistry] = None):
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=30.0)
        
        # Model Management System integration
        self.model_registry = model_registry or ModelRegistry()
        self.historical_log_processor = HistoricalLogProcessor()
        
        # LLM Service endpoints (will be updated from Model Registry)
        self.llm_services = {
            "foundation": {
                "url": "http://localhost:8001/generate",
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
                "model_id": None,  # Will be set from registry
                "use_case": "foundation_layer",
            },
            "customization": {
                "url": "http://localhost:8002/generate", 
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
                "model_id": None,
                "use_case": "customization_layer",
            },
            "interaction": {
                "url": "http://localhost:8003/generate",
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
                "model_id": None,
                "use_case": "interaction_layer",
            },
            "coordination": {
                "url": "http://localhost:8004/generate",
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
                "model_id": None,
                "use_case": "coordination_layer",
            },
        }
        
        # Load balancing
        self.current_weights = {name: 1.0 for name in self.llm_services}
        self.request_counts = {name: 0 for name in self.llm_services}
        
        # Model registry initialized flag (will update on first use)
        self._models_initialized = False
        
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _update_models_from_registry(self):
        """Update service configurations from Model Registry."""
        try:
            for layer_name, service in self.llm_services.items():
                use_case = service["use_case"]
                current_model = await self.model_registry.get_current_model(use_case)
                
                if current_model:
                    service["model_id"] = current_model.get("model_id")
                    # Update URL if model has specific endpoint
                    if current_model.get("configuration", {}).get("endpoint"):
                        service["url"] = current_model["configuration"]["endpoint"]
                    
        except Exception as e:
            print(f"Error updating models from registry: {e}")
    
    def _select_service(self, layer: str) -> str:
        """Select LLM service using weighted round-robin."""
        if layer not in self.llm_services:
            raise ValueError(f"Unknown LLM layer: {layer}")
        
        service = self.llm_services[layer]
        
        # Check circuit breaker
        if not service["circuit_breaker"].can_execute():
            raise CircuitBreakerError(f"Circuit breaker open for {layer}")
        
        # Weighted selection (simplified - in production, use more sophisticated algorithm)
        return layer
    
    async def _make_request(
        self, 
        service_name: str, 
        prompt: str, 
        context: Dict[str, Any],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Make request to LLM service with retry logic."""
        service = self.llm_services[service_name]
        url = service["url"]
        
        payload = {
            "prompt": prompt,
            "context": context,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        session = await self._get_session()
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        service["circuit_breaker"].record_success()
                        service["retry_count"] = 0
                        return result
                    else:
                        service["circuit_breaker"].record_failure()
                        retry_count += 1
                        service["retry_count"] = retry_count
                        
            except asyncio.TimeoutError:
                service["circuit_breaker"].record_failure()
                retry_count += 1
                service["retry_count"] = retry_count
                
            except Exception as e:
                service["circuit_breaker"].record_failure()
                retry_count += 1
                service["retry_count"] = retry_count
                
            if retry_count < max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        
        raise LLMServiceUnavailableError(f"Service {service_name} unavailable after {max_retries} retries")
    
    async def generate_text(
        self,
        layer: str,
        prompt: str,
        context: Dict[str, Any],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate text using specified LLM layer.
        Integrated with Model Management System for model selection and logging.
        
        Args:
            layer: LLM layer (foundation, customization, interaction, coordination)
            prompt: Text prompt for generation
            context: Context data for the request
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
        
        Returns:
            Generated text response
        """
        start_time = time.time()
        model_id = None
        use_case = None
        
        try:
            service_name = self._select_service(layer)
            service = self.llm_services[service_name]
            model_id = service.get("model_id")
            use_case = service.get("use_case")
            
            # Ensure model is up to date from registry (on first use or periodically)
            if not self._models_initialized:
                await self._update_models_from_registry()
                self._models_initialized = True
                # Update model_id and use_case after registry update
                model_id = service.get("model_id")
                use_case = service.get("use_case")
            
            result = await self._make_request(
                service_name, prompt, context, max_tokens, temperature
            )
            
            # Update load balancing weights
            self.request_counts[service_name] += 1
            
            generated_text = result.get("text", "")
            tokens_used = result.get("tokens_used", 0)
            latency = time.time() - start_time
            
            # Log to historical logs for model management
            if model_id:
                try:
                    await self.historical_log_processor.log_inference(
                        model_id=UUID(model_id) if isinstance(model_id, str) else model_id,
                        use_case=use_case,
                        prompt=prompt,
                        context=context,
                        generated_output=generated_text,
                        performance_metrics={
                            "latency_ms": latency * 1000,
                            "tokens_used": tokens_used,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        }
                    )
                except Exception as log_error:
                    print(f"Error logging inference to historical logs: {log_error}")
            
            return {
                "success": True,
                "text": generated_text,
                "tokens_used": tokens_used,
                "service": service_name,
                "layer": layer,
                "model_id": model_id,
                "latency_ms": latency * 1000,
            }
            
        except CircuitBreakerError as e:
            fallback_text = self._get_fallback_response(layer, prompt)
            
            # Log failure
            if model_id:
                try:
                    await self.historical_log_processor.log_inference(
                        model_id=UUID(model_id) if isinstance(model_id, str) else model_id,
                        use_case=use_case or layer,
                        prompt=prompt,
                        context=context,
                        generated_output=fallback_text,
                        performance_metrics={
                            "error": str(e),
                            "fallback_used": True,
                        }
                    )
                except Exception:
                    pass
            
            return {
                "success": False,
                "error": str(e),
                "fallback": True,
                "text": fallback_text,
                "model_id": model_id,
            }
            
        except LLMServiceUnavailableError as e:
            fallback_text = self._get_fallback_response(layer, prompt)
            
            # Log failure
            if model_id:
                try:
                    await self.historical_log_processor.log_inference(
                        model_id=UUID(model_id) if isinstance(model_id, str) else model_id,
                        use_case=use_case or layer,
                        prompt=prompt,
                        context=context,
                        generated_output=fallback_text,
                        performance_metrics={
                            "error": str(e),
                            "fallback_used": True,
                        }
                    )
                except Exception:
                    pass
            
            return {
                "success": False,
                "error": str(e),
                "fallback": True,
                "text": fallback_text,
                "model_id": model_id,
            }
    
    def _get_fallback_response(self, layer: str, prompt: str) -> str:
        """Get fallback response when LLM services are unavailable."""
        fallback_responses = {
            "foundation": "I understand you're looking for information. Let me help you with that.",
            "customization": "Based on your preferences, here's what I recommend.",
            "interaction": "I'm here to help. What would you like to know?",
            "coordination": "Let me coordinate the best response for your situation.",
        }
        
        return fallback_responses.get(layer, "I'm processing your request. Please wait a moment.")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all LLM services."""
        status = {}
        
        for name, service in self.llm_services.items():
            circuit_breaker = service["circuit_breaker"]
            status[name] = {
                "url": service["url"],
                "circuit_breaker_state": circuit_breaker.state,
                "failure_count": circuit_breaker.failure_count,
                "success_count": circuit_breaker.success_count,
                "retry_count": service["retry_count"],
                "weight": self.current_weights[name],
                "request_count": self.request_counts[name],
            }
        
        return status
    
    async def reset_circuit_breaker(self, service_name: str) -> bool:
        """Reset circuit breaker for a specific service."""
        if service_name in self.llm_services:
            self.llm_services[service_name]["circuit_breaker"].reset()
            return True
        return False


class CircuitBreakerState:
    """Circuit breaker state management."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """Record successful request."""
        self.success_count += 1
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def reset(self):
        """Reset circuit breaker state."""
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
