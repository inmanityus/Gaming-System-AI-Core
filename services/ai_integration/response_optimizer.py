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

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_redis_pool, RedisPool


class ResponseCache:
    """Response caching with TTL and similarity matching."""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.redis: Optional[RedisPool] = None
        self._key_prefix = "ai_response:"
    
    async def _get_redis(self) -> RedisPool:
        """Get Redis pool instance."""
        if self.redis is None:
            self.redis = await get_redis_pool()
        return self.redis
    
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
        redis = await self._get_redis()
        key = self._generate_cache_key(layer, prompt, context_hash)
        
        cached = await redis.hgetall(key)
        if cached:
            # Parse JSON values and handle special types
            result = {}
            for k, v in cached.items():
                try:
                    # Try JSON parsing first
                    parsed = json.loads(v)
                    # Handle string booleans that were stored
                    if isinstance(parsed, str) and parsed.lower() in ('true', 'false'):
                        result[k] = parsed.lower() == 'true'
                    else:
                        result[k] = parsed
                except (json.JSONDecodeError, TypeError):
                    # Fallback to string value
                    result[k] = v
            
            return result
        
        return None
    
    async def cache_response(
        self, 
        layer: str, 
        prompt: str, 
        context_hash: str,
        response: Dict[str, Any]
    ):
        """Cache response with TTL."""
        redis = await self._get_redis()
        key = self._generate_cache_key(layer, prompt, context_hash)
        
        # Prepare data for Redis hash
        cache_data = {}
        for k, v in response.items():
            if isinstance(v, (dict, list)):
                cache_data[k] = json.dumps(v)
            else:
                cache_data[k] = str(v)
        
        # Store with TTL
        await redis.hset(key, mapping=cache_data)
        await redis.expire(key, self.ttl)
    
    async def invalidate_layer_cache(self, layer: str):
        """Invalidate all cached responses for a layer."""
        redis = await self._get_redis()
        pattern = f"{self._key_prefix}*"
        
        # Get all keys matching pattern
        keys = await redis.keys(pattern)
        
        # Filter keys for specific layer (simplified - in production, use more sophisticated matching)
        layer_keys = [key for key in keys if layer in key.decode()]
        
        if layer_keys:
            await redis.delete(*layer_keys)


class ResponseOptimizer:
    """
    Optimizes AI responses for real-time performance.
    Handles caching, streaming, and performance optimization.
    """
    
    def __init__(self):
        self.cache = ResponseCache()
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
        """Preload common responses for better performance."""
        tasks = []
        
        for layer, prompt, context in common_prompts:
            # Generate response (this would call the actual LLM)
            # For now, just cache placeholder responses
            placeholder_response = {
                "text": f"Preloaded response for {layer}",
                "layer": layer,
                "preloaded": True,
            }
            
            context_hash = self._calculate_context_hash(context)
            tasks.append(
                self.cache.cache_response(layer, prompt, context_hash, placeholder_response)
            )
        
        await asyncio.gather(*tasks)
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "response_times": [],
        }
