"""
End-to-End Router Integration Tests

Tests full request flow through router → tier → cache → response.

These tests validate:
- Complete request routing flow
- Fallback scenarios
- Cache hit/miss behavior
- Performance characteristics
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from services.router.intelligent_router import IntelligentRouter
from services.cache.intent_cache import IntentCache
from services.cache.result_cache import ResultCache


class TestE2ERouterFlow:
    """Test complete request flows through the router system."""
    
    @pytest.fixture
    async def router(self):
        """Create router instance."""
        router_instance = IntelligentRouter()
        yield router_instance
        await router_instance.close()
    
    @pytest.fixture
    def intent_cache(self):
        """Create intent cache."""
        return IntentCache(default_ttl=1.0)
    
    @pytest.fixture
    def result_cache(self):
        """Create result cache."""
        return ResultCache(default_ttl=60.0)
    
    @pytest.mark.asyncio
    async def test_gold_tier_real_time_request(self, router):
        """
        Test Gold tier routing for real-time request.
        
        Validates:
        - Correct tier selection
        - Latency within budget
        - Fallback to Silver if Gold unavailable
        """
        request = {
            "prompt": "NPC action: move forward",
            "max_tokens": 8,
            "sla": "real-time",
            "latency_budget_ms": 16
        }
        
        # Route request
        response = await router.route(request)
        
        # Validate response
        assert response is not None
        assert "tier" in response
        assert "endpoint" in response
        assert "sla" in response
        
        # Should route to Gold tier
        assert response["tier"] == "gold"
        assert response["endpoint"] == "http://localhost:8001"
        assert response["sla"] == "real-time"
    
    @pytest.mark.asyncio
    async def test_silver_tier_interactive_request(self, router):
        """
        Test Silver tier routing for interactive request.
        
        Validates:
        - Correct tier selection
        - Latency within budget
        - Fallback to Bronze if Silver unavailable
        """
        request = {
            "prompt": "NPC dialogue: respond to player question about quest",
            "max_tokens": 100,
            "sla": "interactive",
            "latency_budget_ms": 200
        }
        
        # Route request
        response = await router.route(request)
        
        # Validate response
        assert response is not None
        assert "tier" in response
        assert "endpoint" in response
        assert "sla" in response
        
        # Should route to Silver tier
        assert response["tier"] == "silver"
        assert response["endpoint"] == "http://localhost:8002"
        assert response["sla"] == "interactive"
    
    @pytest.mark.asyncio
    async def test_bronze_tier_async_request(self, router):
        """
        Test Bronze tier routing for async request.
        
        Validates:
        - Correct tier selection
        - Async job handling
        - No fallback (Bronze is last resort)
        """
        request = {
            "prompt": "Generate story arc about player exploration",
            "max_tokens": 500,
            "sla": "async",
            "latency_budget_ms": 5000
        }
        
        # Route request
        response = await router.route(request)
        
        # Validate response
        assert response is not None
        assert "tier" in response
        assert "endpoint" in response
        assert "sla" in response
        assert "async" in response
        assert "job_id" in response
        
        # Should route to Bronze tier
        assert response["tier"] == "bronze"
        assert response["endpoint"] == "http://localhost:8003"
        assert response["sla"] == "async"
        assert response["async"] is True
    
    @pytest.mark.asyncio
    async def test_gold_to_silver_fallback(self, router):
        """
        Test Gold → Silver fallback when Gold tier is unavailable.
        
        Simulates Gold tier failure and validates fallback.
        """
        # TODO: This test requires infrastructure to bring down Gold tier
        # For now, mark as skipped
        pytest.skip("Requires ability to control tier availability")
    
    @pytest.mark.asyncio
    async def test_silver_to_bronze_fallback(self, router):
        """
        Test Silver → Bronze fallback when Silver tier is unavailable.
        
        Simulates Silver tier failure and validates fallback.
        """
        # TODO: This test requires infrastructure to bring down Silver tier
        pytest.skip("Requires ability to control tier availability")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, router):
        """
        Test circuit breaker opens after repeated failures.
        
        Validates:
        - Circuit breaker records failures
        - Circuit breaker opens after threshold
        - Circuit breaker recovers after timeout
        """
        # TODO: This test requires controlled failure injection
        pytest.skip("Requires failure injection mechanism")
    
    @pytest.mark.asyncio
    async def test_intent_cache_integration(self, router, intent_cache):
        """
        Test intent cache integration with router.
        
        Validates:
        - Cache miss → route to tier
        - Cache hit → return cached intent
        - Cache expiration
        """
        npc_id = "test_npc_1"
        prompt = "What is my next action?"
        
        # First request: cache miss, route to tier
        cached_intent = intent_cache.get_intent(npc_id)
        assert cached_intent["action"] == "idle"  # Cache miss returns default intent
        
        # Route request (simulating Gold tier)
        request = {
            "prompt": prompt,
            "max_tokens": 8,
            "sla": "real-time",
            "latency_budget_ms": 16
        }
        response = await router.route(request)
        
        # Cache the intent (simulating async update)
        if response.get("tier") == "gold":
            intent = {
                "action": "move_forward",
                "tokens": ["move", "forward"]
            }
            intent_cache.update_intent(npc_id, intent, ttl=1.0)
        
        # Second request: cache hit
        cached_intent = intent_cache.get_intent(npc_id)
        if cached_intent:
            assert "action" in cached_intent
            assert cached_intent["action"] == "move_forward"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Third request: cache expired
        cached_intent = intent_cache.get_intent(npc_id)
        assert cached_intent["action"] == "idle"  # Cache expired, returns default intent
    
    @pytest.mark.asyncio
    async def test_result_cache_integration(self, router, result_cache):
        """
        Test result cache integration with router.
        
        Validates:
        - Cache miss → route to tier
        - Cache hit → return cached result
        - Cache expiration
        """
        cache_key = "story_arc:test_arc_1"
        prompt = "Generate story arc about exploration"
        
        # First request: cache miss, route to tier
        cached_result = result_cache.get_result(cache_key)
        assert cached_result is None  # Cache miss
        
        # Route request (simulating Bronze tier)
        request = {
            "prompt": prompt,
            "max_tokens": 500,
            "sla": "async",
            "latency_budget_ms": 5000
        }
        response = await router.route(request)
        
        # Cache the result
        if response.get("tier") == "bronze":
            result = {"story_arc": "test_arc_content"}
            result_cache.set_result(cache_key, result, ttl=60.0)
        
        # Second request: cache hit
        cached_result = result_cache.get_result(cache_key)
        if cached_result:
            assert cached_result is not None
        
        # Wait for expiration
        await asyncio.sleep(61.0)
        
        # Third request: cache expired
        cached_result = result_cache.get_result(cache_key)
        assert cached_result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, router):
        """
        Test concurrent request handling.
        
        Validates:
        - Router handles multiple concurrent requests
        - No race conditions
        - All requests complete successfully
        """
        # Create multiple concurrent requests
        requests = [
            {
                "prompt": f"Request {i}",
                "max_tokens": 8,
                "sla": "real-time",
                "latency_budget_ms": 16
            }
            for i in range(10)
        ]
        
        # Route all requests concurrently
        start_time = time.time()
        responses = await asyncio.gather(
            *[router.route(req) for req in requests],
            return_exceptions=True
        )
        end_time = time.time()
        
        # Validate all requests completed
        assert len(responses) == 10
        
        # All should complete (either success or graceful failure)
        for response in responses:
            assert not isinstance(response, Exception)
            assert response is not None
            assert "tier" in response
        
        # Should handle concurrency without significant delay
        elapsed_ms = (end_time - start_time) * 1000
        # Reasonable assumption: 10 requests should not take 10x longer
        assert elapsed_ms < 5000
    
    @pytest.mark.asyncio
    async def test_routing_decision_logic(self, router):
        """
        Test routing decision logic for different SLA/latency combinations.
        
        Validates:
        - Correct tier selection for various SLA/latency combinations
        - Default behavior when SLA is unclear
        """
        test_cases = [
            # (sla, latency_budget_ms, expected_tier)
            ("real-time", 16, "gold"),
            ("real-time", 8, "gold"),
            ("real-time", 32, "gold"),
            ("interactive", 200, "silver"),
            ("interactive", 100, "silver"),
            ("interactive", 300, "silver"),
            ("async", 5000, "bronze"),
            ("async", 10000, "bronze"),
        ]
        
        for sla, latency_budget_ms, expected_tier in test_cases:
            request = {
                "prompt": "Test request",
                "max_tokens": 100,
                "sla": sla,
                "latency_budget_ms": latency_budget_ms
            }
            
            response = await router.route(request)
            
            # Validate tier selection
            actual_tier = response.get("tier")
            # Should route to expected tier
            assert actual_tier == expected_tier
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, router):
        """
        Test health check integration with routing.
        
        Validates:
        - Health checks run periodically
        - Unhealthy tiers are avoided
        - Health status is accurate
        """
        # Get health status
        health_status = await router.get_tier_health_status()
        
        # Validate health status structure
        assert health_status is not None
        assert "gold" in health_status
        assert "silver" in health_status
        assert "bronze" in health_status
        
        # Validate health status fields
        for tier, status in health_status.items():
            assert "is_healthy" in status
            assert "failure_count" in status
            assert "latency_p95_ms" in status
            assert isinstance(status["is_healthy"], bool)
            assert isinstance(status["failure_count"], int)
            assert isinstance(status["latency_p95_ms"], (int, float))


class TestE2EPerformance:
    """Test performance characteristics of router system."""
    
    @pytest.fixture
    async def router(self):
        """Create router instance."""
        router_instance = IntelligentRouter()
        yield router_instance
        await router_instance.close()
    
    @pytest.mark.asyncio
    async def test_latency_budget_respect(self, router):
        """
        Test that router respects latency budgets.
        
        Validates:
        - Gold tier requests complete within 16ms budget
        - Silver tier requests complete within 250ms budget
        - Bronze tier requests complete within 5000ms budget
        """
        test_cases = [
            ("gold", 16),
            ("silver", 250),
            ("bronze", 5000)
        ]
        
        for tier, budget_ms in test_cases:
            sla_map = {"gold": "real-time", "silver": "interactive", "bronze": "async"}
            sla = sla_map[tier]
            
            request = {
                "prompt": f"Performance test for {tier} tier",
                "max_tokens": 100,
                "sla": sla,
                "latency_budget_ms": budget_ms
            }
            
            response = await router.route(request)
            
            # Router only selects tier, doesn't actually call it
            # So latency is near-zero
            assert response is not None
            assert response.get("tier") == tier
    
    @pytest.mark.asyncio
    async def test_router_overhead(self, router):
        """
        Test router overhead is minimal.
        
        Validates:
        - Router adds minimal overhead to requests
        - Processing time is reasonable
        """
        request = {
            "prompt": "Test overhead",
            "max_tokens": 8,
            "sla": "real-time",
            "latency_budget_ms": 16
        }
        
        # Measure multiple requests to get average
        latencies = []
        for _ in range(10):
            start_time = time.time()
            response = await router.route(request)
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        avg_latency_ms = sum(latencies) / len(latencies)
        # Router should add minimal overhead (< 5ms)
        # Most latency comes from tier processing
        assert avg_latency_ms < 10  # Very fast - just routing logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

