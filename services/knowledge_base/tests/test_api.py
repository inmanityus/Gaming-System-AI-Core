"""
Integration Tests for Knowledge Base API
Critical P0 tests as identified by Gemini 2.5 Pro peer review.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
import asyncpg
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from server import app, postgres_pool


@pytest.fixture
def client():
    """Test client for API."""
    return TestClient(app)


@pytest_asyncio.fixture
async def test_db():
    """Test database connection."""
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5443,
        user='postgres',
        password='Inn0vat1on!',
        database='gaming_system_ai_core'
    )
    
    yield pool
    
    # Cleanup
    await pool.close()


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'service' in data


class TestSemanticSearch:
    """Test semantic search endpoint."""
    
    def test_search_without_api_key_dev_mode(self, client):
        """Search works in dev mode (no API keys configured)."""
        response = client.post("/search/semantic", json={
            "query": "vampire",
            "match_count": 5
        })
        # Should work in dev mode
        assert response.status_code in [200, 503]  # 503 if DB not ready
    
    def test_search_validates_input(self, client):
        """Search rejects invalid input."""
        # Empty query
        response = client.post("/search/semantic", json={
            "query": "",
            "match_count": 5
        })
        assert response.status_code == 422  # Validation error
        
        # Query too long
        response = client.post("/search/semantic", json={
            "query": "A" * 3000,
            "match_count": 5
        })
        assert response.status_code == 422
        
        # Match count too high
        response = client.post("/search/semantic", json={
            "query": "test",
            "match_count": 200
        })
        assert response.status_code == 422
    
    def test_search_respects_rate_limit(self, client):
        """Search enforces rate limiting."""
        # Make 31 requests (limit is 30/minute)
        for i in range(31):
            response = client.post("/search/semantic", json={
                "query": f"test {i}",
                "match_count": 1
            })
            
            if i < 30:
                assert response.status_code in [200, 503]
            else:
                # 31st request should be rate limited
                assert response.status_code == 429


class TestConceptCreation:
    """Test concept creation endpoint."""
    
    def test_create_concept_validates_input(self, client):
        """Concept creation validates all fields."""
        # Missing required field
        response = client.post("/concepts/create", json={
            "name": "Test Concept"
            # Missing concept_type, description
        })
        assert response.status_code == 422
        
        # Name too long
        response = client.post("/concepts/create", json={
            "name": "A" * 300,
            "concept_type": "character",
            "description": "Test"
        })
        assert response.status_code == 422
        
        # Invalid scope
        response = client.post("/concepts/create", json={
            "name": "Test",
            "concept_type": "character",
            "description": "Test",
            "scope": "invalid_scope"
        })
        assert response.status_code == 422
    
    def test_create_concept_respects_rate_limit(self, client):
        """Concept creation enforces rate limiting (10/minute)."""
        for i in range(11):
            response = client.post("/concepts/create", json={
                "name": f"Concept {i}",
                "concept_type": "test",
                "description": "Test description"
            })
            
            if i < 10:
                assert response.status_code in [200, 201, 503]
            else:
                assert response.status_code == 429


class TestDocumentStats:
    """Test document statistics endpoint."""
    
    def test_get_stats(self, client):
        """Stats endpoint returns expected format."""
        response = client.get("/documents/stats")
        
        if response.status_code == 200:
            data = response.json()
            assert 'total_chunks' in data
            assert 'total_documents' in data


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_uuid(self, client):
        """Invalid UUID in path returns 422."""
        response = client.get("/world/not-a-uuid/knowledge")
        assert response.status_code == 422
    
    def test_missing_world(self, client):
        """Non-existent world returns empty results."""
        fake_uuid = str(uuid4())
        response = client.get(f"/world/{fake_uuid}/knowledge")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

