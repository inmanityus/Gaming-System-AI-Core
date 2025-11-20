"""
Smoke tests for API endpoints.
Quick tests to verify basic functionality after deployment.
"""
import os
import sys
import requests
import pytest
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture
def api_endpoint():
    """Get API endpoint from environment or command line."""
    # From pytest command line: --api-endpoint=https://api.example.com
    endpoint = pytest.config.getoption("--api-endpoint", default=None)
    if not endpoint:
        # From environment variable
        endpoint = os.getenv("API_ENDPOINT", "http://localhost:8000")
    return endpoint.rstrip("/")


@pytest.fixture
def api_headers():
    """Common headers for API requests."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.mark.smoke
class TestAPISmokeTests:
    """Basic smoke tests for all API endpoints."""
    
    def test_health_check(self, api_endpoint, api_headers):
        """Test health check endpoint."""
        response = requests.get(
            f"{api_endpoint}/health",
            headers=api_headers,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "version" in data
    
    def test_api_documentation(self, api_endpoint):
        """Test OpenAPI documentation is available."""
        response = requests.get(
            f"{api_endpoint}/docs",
            timeout=10
        )
        
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_audio_analysis_endpoint(self, api_endpoint, api_headers):
        """Test audio analysis endpoint is responding."""
        # Test with minimal valid payload
        response = requests.post(
            f"{api_endpoint}/api/v1/audio/analyze/intelligibility",
            headers=api_headers,
            json={
                "audio_data": "base64_encoded_audio_here",
                "sample_rate": 48000,
                "user_id": "smoke_test_user"
            },
            timeout=10
        )
        
        # Should either process or return validation error
        assert response.status_code in [200, 400, 422]
    
    def test_engagement_session_endpoint(self, api_endpoint, api_headers):
        """Test engagement session endpoint is responding."""
        import datetime
        
        response = requests.post(
            f"{api_endpoint}/api/v1/engagement/session/start",
            headers=api_headers,
            json={
                "user_id": "smoke_test_user",
                "timestamp": datetime.datetime.utcnow().isoformat()
            },
            timeout=10
        )
        
        # Should either create session or return error
        assert response.status_code in [200, 201, 400, 422]
    
    def test_localization_endpoint(self, api_endpoint, api_headers):
        """Test localization endpoint is responding."""
        response = requests.get(
            f"{api_endpoint}/api/v1/localization/content",
            headers=api_headers,
            params={
                "key": "ui.test.smoke",
                "language": "en-US"
            },
            timeout=10
        )
        
        # Should either return content or 404
        assert response.status_code in [200, 404]
    
    def test_tts_endpoint(self, api_endpoint, api_headers):
        """Test TTS endpoint is responding."""
        response = requests.post(
            f"{api_endpoint}/api/v1/tts/synthesize",
            headers=api_headers,
            json={
                "text": "Smoke test",
                "language": "en-US"
            },
            timeout=10
        )
        
        # Should either synthesize or return error
        assert response.status_code in [200, 400, 422, 503]
    
    def test_metrics_endpoint(self, api_endpoint, api_headers):
        """Test Prometheus metrics endpoint."""
        response = requests.get(
            f"{api_endpoint}/metrics",
            headers=api_headers,
            timeout=10
        )
        
        # Metrics endpoint might not be exposed publicly
        if response.status_code == 200:
            assert "http_requests_total" in response.text
    
    def test_service_discovery(self, api_endpoint, api_headers):
        """Test service discovery/status endpoint."""
        response = requests.get(
            f"{api_endpoint}/api/v1/services/status",
            headers=api_headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "services" in data
            
            # Check expected services
            expected_services = [
                "ethelred-audio",
                "ethelred-engagement",
                "multi-language",
                "api-gateway"
            ]
            
            for service in expected_services:
                assert any(service in s for s in data["services"])


@pytest.mark.smoke
class TestDatabaseConnectivity:
    """Test database connectivity from services."""
    
    def test_database_health(self, api_endpoint, api_headers):
        """Test database health check endpoint."""
        response = requests.get(
            f"{api_endpoint}/api/v1/health/database",
            headers=api_headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("database") == "connected"
            assert "latency_ms" in data


@pytest.mark.smoke
class TestSecurityHeaders:
    """Test security headers are present."""
    
    def test_security_headers(self, api_endpoint):
        """Test that security headers are set."""
        response = requests.get(
            f"{api_endpoint}/health",
            timeout=10
        )
        
        # Check security headers
        headers = response.headers
        
        # These should be present
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        missing_headers = []
        for header in security_headers:
            if header not in headers:
                missing_headers.append(header)
        
        # Some headers might not be set in development
        if api_endpoint.startswith("https://"):
            assert len(missing_headers) == 0, f"Missing security headers: {missing_headers}"


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--api-endpoint",
        action="store",
        default=None,
        help="API endpoint to test against"
    )


if __name__ == "__main__":
    # Can run directly with: python test_api_smoke.py
    pytest.main([__file__, "-v", "--api-endpoint=http://localhost:8000"])
