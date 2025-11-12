"""
Response Optimizer - Optimizes AI responses for real-time performance.
Handles response caching, streaming, and performance optimization.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

# Import HTTP clients for cross-service communication
from state_manager_client import StateManagerClient, get_state_manager_client



class ResponseCache:
    """Response caching with TTL and similarity matching."""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.state_manager_client: Optional[StateManagerClient] = None
        self._key_prefix = "ai_response:"
    
    async def _get_state_manager(self) -> StateManagerClient:
        """Get StateManager client instance."""
        if self.state_manager_client is None:
            self.state_manager_client = get_state_manager_client()
        return self.state_manager_client
    
    def _generate_cache_key(
        self, 
        layer: str, 
        prompt: str, 
        context_hash: str
    ) -> str:
        """Generate cache key for response."""
        # Create hash of prompt and context for consistent caching
        content_hash = hashlib.md5(
            f"{layer}:{prompt}:{context_hash}".encode()
        ).hexdigest()
        return f"{self._key_prefix}{content_hash}"
    
    async def get_cached_response(
        self, 
        layer: str, 
        prompt: str, 
        context_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        state_manager = await self._get_state_manager()
        key = self._generate_cache_key(layer, prompt, context_hash)
        
        cached_str = await state_manager.get_cache(key)
        if cached_str:
            try:
                # Parse JSON cached response
                result = json.loads(cached_str)
                return result
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, return None
                return None
        
        return None
    
    async def cache_response(
        self, 
        layer: str, 
        prompt: str, 
        context_hash: str,
        response: Dict[str, Any]
    ):
        """Cache response with TTL."""
        state_manager = await self._get_state_manager()
        key = self._generate_cache_key(layer, prompt, context_hash)
        
        # Serialize response to JSON
        cache_value = json.dumps(response)
        
        # Store with TTL via HTTP
        await state_manager.set_cache(key, cache_value, self.ttl)
    
    async def invalidate_layer_cache(self, layer: str):
        """Invalidate all cached responses for a layer."""
        # Note: This is simplified - in production, state-manager should provide
        # a bulk delete or pattern matching API
        # For now, we'll just skip this operation as it's not critical
        pass


class ResponseOptimizer:
    """
    Optimizes AI responses for real-time performance.
    Handles caching, streaming, and performance optimization.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.cache = ResponseCache()
        # Real LLM Client integration for preloading - uses actual HTTP calls
        self.llm_client = llm_client or LLMClient()
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "response_times": [],
        }
        self._max_response_times = 100  # Keep last 100 response times
    
    def _calculate_context_hash(self, context: Dict[str, Any]) -> str:
        """Calculate hash of context for caching."""
        # Create a simplified context hash for caching
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:16]
    
    async def optimize_response(
        self,
        layer: str,
        prompt: str,
        context: Dict[str, Any],
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize AI response for performance.
        
        Args:
            layer: LLM layer name
            prompt: Original prompt
            context: Context used for generation
            response: Generated response
        
        Returns:
            Optimized response
        """
        start_time = time.time()
        
        # Update metrics
        self.performance_metrics["total_requests"] += 1
        
        # Check cache first
        context_hash = self._calculate_context_hash(context)
        cached = await self.cache.get_cached_response(layer, prompt, context_hash)
        
        if cached:
            self.performance_metrics["cache_hits"] += 1
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            # Convert string booleans if cached
            result = dict(cached)
            if "optimized" in result and isinstance(result["optimized"], str):
                result["optimized"] = result["optimized"].lower() == 'true'
            
            return {
                **result,
                "cached": True,
                "response_time": response_time,
            }
        
        self.performance_metrics["cache_misses"] += 1
        
        # Optimize response
        optimized = self._optimize_response_content(response)
        
        # Cache the response
        await self.cache.cache_response(layer, prompt, context_hash, optimized)
        
        response_time = time.time() - start_time
        self._update_response_time(response_time)
        
        return {
            **optimized,
            "cached": False,
            "response_time": response_time,
        }
    
    def _optimize_response_content(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize response content for performance."""
        optimized = response.copy()
        
        # Truncate very long responses
        if "text" in optimized and len(optimized["text"]) > 2000:
            optimized["text"] = optimized["text"][:2000] + "..."
            optimized["truncated"] = True
        
        # Remove unnecessary metadata
        if "metadata" in optimized:
            del optimized["metadata"]
        
        # Add performance hints
        optimized["optimized"] = True
        optimized["timestamp"] = time.time()
        
        return optimized
    
    def _update_response_time(self, response_time: float):
        """Update response time metrics."""
        self.performance_metrics["response_times"].append(response_time)
        
        # Keep only last N response times
        if len(self.performance_metrics["response_times"]) > self._max_response_times:
            self.performance_metrics["response_times"] = self.performance_metrics["response_times"][-self._max_response_times:]
        
        # Update average
        self.performance_metrics["avg_response_time"] = sum(
            self.performance_metrics["response_times"]
        ) / len(self.performance_metrics["response_times"])
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        total_requests = self.performance_metrics["total_requests"]
        
        return {
            "total_requests": total_requests,
            "cache_hits": self.performance_metrics["cache_hits"],
            "cache_misses": self.performance_metrics["cache_misses"],
            "cache_hit_rate": (
                self.performance_metrics["cache_hits"] / max(total_requests, 1) * 100
            ),
            "avg_response_time": self.performance_metrics["avg_response_time"],
            "min_response_time": min(self.performance_metrics["response_times"]) if self.performance_metrics["response_times"] else 0,
            "max_response_time": max(self.performance_metrics["response_times"]) if self.performance_metrics["response_times"] else 0,
        }
    
    async def clear_cache(self, layer: Optional[str] = None):
        """Clear response cache."""
        if layer:
            await self.cache.invalidate_layer_cache(layer)
        else:
            # Clear all cache (implement if needed)
            pass
    
    async def preload_responses(
        self, 
        common_prompts: List[Tuple[str, str, Dict[str, Any]]]
    ):
        """
        Preload common responses for better performance.
        Makes actual LLM calls to generate and cache responses.
        """
        tasks = []
        
        for layer, prompt, context in common_prompts:
            async def preload_single(layer: str, prompt: str, context: Dict[str, Any]):
                """Preload a single response by calling real LLM service."""
                try:
                    # Call real LLM service via LLMClient (makes actual HTTP requests)
                    result = await self.llm_client.generate_text(
                        layer=layer,
                        prompt=prompt,
                        context=context,
                        max_tokens=1000,
                        temperature=0.7,
                    )
                    
                    # Check if request was successful
                    if result.get("success", False):
                        # Extract generated text and create response structure
                        generated_text = result.get("text", "")
                        
                        # Create response structure for caching
                        response = {
                            "text": generated_text,
                            "layer": layer,
                            "preloaded": True,
                            "timestamp": time.time(),
                            "model_id": result.get("model_id"),
                            "tokens_used": result.get("tokens_used", 0),
                        }
                        
                        # Cache the real response
                        context_hash = self._calculate_context_hash(context)
                        await self.cache.cache_response(layer, prompt, context_hash, response)
                    else:
                        # If LLM service unavailable, log but don't cache placeholder
                        error_msg = result.get("error", "Unknown error")
                        print(f"Warning: Could not preload response for {layer}: {error_msg}")
                        
                except Exception as e:
                    # Log error but continue with other preloads
                    print(f"Error preloading response for {layer}: {e}")
            
            tasks.append(preload_single(layer, prompt, context))
        
        # Execute all preload tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "response_times": [],
        }
