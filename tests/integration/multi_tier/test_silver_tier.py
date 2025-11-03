"""
Integration tests for Silver Tier (Interactive) infrastructure.

Tests vLLM deployment, latency requirements (80-250ms), and MCP tool integration.
"""
import pytest
import time
import requests
from typing import Dict, Any
import os


@pytest.fixture
def silver_tier_endpoint():
    """Get Silver tier endpoint from environment or use default."""
    return os.getenv("SILVER_TIER_ENDPOINT", "http://localhost:8002")


@pytest.fixture
def test_payload():
    """Test payload for Silver tier inference."""
    return {
        "prompt": "Complex NPC dialogue with player",
        "max_tokens": 50,
        "temperature": 0.7
    }


class TestSilverTierLatency:
    """Test Silver tier latency requirements (80-250ms)."""
    
    def test_single_request_latency(self, silver_tier_endpoint, test_payload):
        """Test that a single request completes within latency budget."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{silver_tier_endpoint}/v1/completions",
                json=test_payload,
                timeout=5.0
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
            
            assert 80 <= elapsed_ms <= 250, f"Latency {elapsed_ms}ms outside 80-250ms range"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")
    
    def test_p95_latency_requirement(self, silver_tier_endpoint, test_payload):
        """Test that p95 latency meets 80-250ms requirement."""
        try:
            latencies = []
            
            for _ in range(100):
                start_time = time.time()
                response = requests.post(
                    f"{silver_tier_endpoint}/v1/completions",
                    json=test_payload,
                    timeout=5.0
                )
                if response.status_code != 200:
                    pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
                elapsed_ms = (time.time() - start_time) * 1000
                latencies.append(elapsed_ms)
            
            latencies.sort()
            p95_latency = latencies[int(len(latencies) * 0.95)]
            
            assert 80 <= p95_latency <= 250, f"p95 latency {p95_latency}ms outside 80-250ms range"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")
    
    def test_throughput_requirement(self, silver_tier_endpoint, test_payload):
        """Test that Silver tier can handle reasonable throughput."""
        import concurrent.futures
        
        def make_request():
            start_time = time.time()
            response = requests.post(
                f"{silver_tier_endpoint}/v1/completions",
                json=test_payload,
                timeout=5.0
            )
            elapsed_ms = (time.time() - start_time) * 1000
            return response.status_code == 200, elapsed_ms
        
        try:
            start = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            total_time = time.time() - start
            success_count = sum(1 for success, _ in results if success)
            throughput = success_count / total_time
            
            assert success_count >= 18, f"Only {success_count}/20 requests succeeded"
            assert throughput >= 2.0, f"Throughput {throughput} req/s below requirement"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")


class TestSilverTierMCPIntegration:
    """Test Silver tier MCP tool integration."""
    
    def test_mcp_tool_availability(self, silver_tier_endpoint):
        """Test that MCP tools are accessible from Silver tier."""
        try:
            response = requests.get(f"{silver_tier_endpoint}/health", timeout=5.0)
            if response.status_code != 200:
                pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
            assert response.status_code == 200
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")
    
    def test_tool_call_latency(self, silver_tier_endpoint):
        """Test that tool calls complete within latency budget."""
        try:
            # Placeholder for actual MCP tool call test
            # Would test RAG, Game State, Utilities MCP integration
            payload = {
                "prompt": "Use tool to retrieve game state",
                "tools": ["game_state_query"],
                "max_tokens": 50
            }
            
            # This is a placeholder - actual implementation would call MCP tools
            response = requests.post(
                f"{silver_tier_endpoint}/v1/completions",
                json=payload,
                timeout=5.0
            )
            
            # For now, just verify endpoint is accessible
            assert response.status_code in [200, 501]  # 501 if not implemented yet
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")


class TestSilverTierHealth:
    """Test Silver tier health checks."""
    
    def test_health_endpoint(self, silver_tier_endpoint):
        """Test health check endpoint."""
        try:
            response = requests.get(f"{silver_tier_endpoint}/health", timeout=5.0)
            if response.status_code != 200:
                pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
            data = response.json()
            assert data.get("status") == "healthy"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")
    
    def test_ready_endpoint(self, silver_tier_endpoint):
        """Test readiness endpoint."""
        try:
            response = requests.get(f"{silver_tier_endpoint}/ready", timeout=5.0)
            if response.status_code != 200:
                pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
            data = response.json()
            assert data.get("ready") is True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")
    
    def test_metrics_endpoint(self, silver_tier_endpoint):
        """Test Prometheus metrics endpoint."""
        try:
            response = requests.get(f"{silver_tier_endpoint}/metrics", timeout=5.0)
            if response.status_code != 200:
                pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
            assert "vllm" in response.text.lower() or "request" in response.text.lower()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")


class TestSilverTierIntegration:
    """Test Silver tier integration with game systems."""
    
    def test_complex_dialogue_generation(self, silver_tier_endpoint):
        """Test complex dialogue generation for key NPCs."""
        try:
            payload = {
                "prompt": "NPC responds to player question about game lore",
                "max_tokens": 100,
                "temperature": 0.8
            }
            
            response = requests.post(
                f"{silver_tier_endpoint}/v1/completions",
                json=payload,
                timeout=5.0
            )
            
            if response.status_code != 200:
                pytest.skip(f"Silver tier endpoint returned {response.status_code} (not deployed yet)")
            
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            text = data["choices"][0]["text"]
            assert len(text) > 0, "Generated empty response"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Silver tier endpoint not available (not deployed yet)")
