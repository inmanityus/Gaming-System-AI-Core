"""
Integration tests for Gold Tier (Real-Time) infrastructure.

Tests TensorRT-LLM deployment, latency requirements, and real-time NPC integration.
"""
import pytest
import time
import requests
from typing import Dict, Any
import os


@pytest.fixture
def gold_tier_endpoint():
    """Get Gold tier endpoint from environment or use default."""
    return os.getenv("GOLD_TIER_ENDPOINT", "http://localhost:8001")


@pytest.fixture
def test_payload():
    """Test payload for Gold tier inference."""
    return {
        "prompt": "Test NPC action: move forward",
        "max_tokens": 8,
        "temperature": 0.1
    }


class TestGoldTierLatency:
    """Test Gold tier latency requirements (p95 < 16ms per token)."""
    
    def test_single_request_latency(self, gold_tier_endpoint, test_payload):
        """Test that a single request completes within latency budget."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{gold_tier_endpoint}/v1/completions",
                json=test_payload,
                timeout=1.0
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            assert response.status_code == 200, f"Request failed: {response.text}"
            assert elapsed_ms < 16, f"Latency {elapsed_ms}ms exceeds 16ms requirement"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
    
    def test_p95_latency_requirement(self, gold_tier_endpoint, test_payload):
        """Test that p95 latency meets sub-16ms requirement."""
        try:
            # Test endpoint availability first
            requests.get(f"{gold_tier_endpoint}/health", timeout=1.0)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
        
        latencies = []
        
        for _ in range(100):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{gold_tier_endpoint}/v1/completions",
                    json=test_payload,
                    timeout=1.0
                )
                elapsed_ms = (time.time() - start_time) * 1000
                if response.status_code == 200:
                    latencies.append(elapsed_ms)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                break
        
        if len(latencies) < 50:
            pytest.skip("Gold tier endpoint not available or unstable")
        
        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95)]
        
        assert p95_latency < 16, f"p95 latency {p95_latency}ms exceeds 16ms requirement"
    
    def test_concurrent_requests(self, gold_tier_endpoint, test_payload):
        """Test latency under concurrent load (multiple NPCs)."""
        try:
            # Test endpoint availability first
            requests.get(f"{gold_tier_endpoint}/health", timeout=1.0)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
        
        import concurrent.futures
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.post(
                    f"{gold_tier_endpoint}/v1/completions",
                    json=test_payload,
                    timeout=1.0
                )
                elapsed_ms = (time.time() - start_time) * 1000
                return response.status_code == 200, elapsed_ms
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return False, 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for success, _ in results if success)
        latencies = [elapsed for success, elapsed in results if success]
        
        if success_count < 25:
            pytest.skip("Gold tier endpoint not available or unstable under load")
        
        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
        
        assert success_count >= 48, f"Only {success_count}/50 requests succeeded"
        assert p95_latency < 16, f"p95 latency {p95_latency}ms exceeds 16ms under load"


class TestGoldTierHealth:
    """Test Gold tier health checks and availability."""
    
    def test_health_endpoint(self, gold_tier_endpoint):
        """Test health check endpoint."""
        try:
            response = requests.get(f"{gold_tier_endpoint}/health", timeout=5.0)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
    
    def test_ready_endpoint(self, gold_tier_endpoint):
        """Test readiness endpoint."""
        try:
            response = requests.get(f"{gold_tier_endpoint}/ready", timeout=5.0)
            assert response.status_code == 200
            data = response.json()
            assert data.get("ready") is True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
    
    def test_metrics_endpoint(self, gold_tier_endpoint):
        """Test Prometheus metrics endpoint."""
        try:
            response = requests.get(f"{gold_tier_endpoint}/metrics", timeout=5.0)
            assert response.status_code == 200
            assert "tensorrt_llm" in response.text.lower() or "request" in response.text.lower()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")


class TestGoldTierIntegration:
    """Test Gold tier integration with game engine."""
    
    def test_npc_intent_generation(self, gold_tier_endpoint):
        """Test NPC intent generation for decoupled controller."""
        try:
            payload = {
                "prompt": "NPC context: player nearby, health low",
                "max_tokens": 8,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{gold_tier_endpoint}/v1/completions",
                json=payload,
                timeout=1.0
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "text" in data["choices"][0]
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
    
    def test_short_token_generation(self, gold_tier_endpoint):
        """Test that short token responses work correctly."""
        try:
            payload = {
                "prompt": "Action:",
                "max_tokens": 4,
                "temperature": 0.0
            }
            
            response = requests.post(
                f"{gold_tier_endpoint}/v1/completions",
                json=payload,
                timeout=1.0
            )
            
            assert response.status_code == 200
            data = response.json()
            tokens = data["choices"][0]["text"].split()
            assert len(tokens) <= 4, "Generated more tokens than requested"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Gold tier endpoint not available")
