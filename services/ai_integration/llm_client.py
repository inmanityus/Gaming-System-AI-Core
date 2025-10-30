"""
LLM Client - Manages connections to hierarchical LLM system.
Handles load balancing, retry logic, and circuit breaker patterns.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout


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
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=30.0)
        
        # LLM Service endpoints
        self.llm_services = {
            "foundation": {
                "url": "http://localhost:8001/generate",
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
            },
            "customization": {
                "url": "http://localhost:8002/generate", 
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
            },
            "interaction": {
                "url": "http://localhost:8003/generate",
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
            },
            "coordination": {
                "url": "http://localhost:8004/generate",
                "weight": 1.0,
                "circuit_breaker": CircuitBreakerState(),
                "retry_count": 0,
            },
        }
        
        # Load balancing
        self.current_weights = {name: 1.0 for name in self.llm_services}
        self.request_counts = {name: 0 for name in self.llm_services}
        
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
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
        
        Args:
            layer: LLM layer (foundation, customization, interaction, coordination)
            prompt: Text prompt for generation
            context: Context data for the request
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
        
        Returns:
            Generated text response
        """
        try:
            service_name = self._select_service(layer)
            result = await self._make_request(
                service_name, prompt, context, max_tokens, temperature
            )
            
            # Update load balancing weights
            self.request_counts[service_name] += 1
            
            return {
                "success": True,
                "text": result.get("text", ""),
                "tokens_used": result.get("tokens_used", 0),
                "service": service_name,
                "layer": layer,
            }
            
        except CircuitBreakerError as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": True,
                "text": self._get_fallback_response(layer, prompt),
            }
            
        except LLMServiceUnavailableError as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": True,
                "text": self._get_fallback_response(layer, prompt),
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
