"""
Integration tests for AI Inference Service ↔ Model Registry integration.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from services.ai_integration.llm_client import LLMClient
from services.model_management.model_registry import ModelRegistry


@pytest.fixture
def model_registry():
    """Create ModelRegistry instance with mocked database."""
    registry = ModelRegistry()
    # Mock the database pool to avoid async issues
    with patch.object(registry, '_get_postgres') as mock_postgres:
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_pool.fetch = AsyncMock(return_value={
            "model_id": uuid4(),
            "model_name": "test-model",
            "model_type": "self_hosted",
            "provider": "ollama",
            "use_case": "foundation_layer",
            "version": "1.0",
            "status": "current",
            "configuration": {"endpoint": "http://localhost:8001/generate"}
        })
        mock_postgres.return_value = mock_pool
        yield registry


@pytest.fixture
def llm_client():
    """Create LLMClient with ModelRegistry integration."""
    # Mock the registry to avoid database calls
    mock_registry = MagicMock()
    mock_registry.get_current_model = AsyncMock(return_value={
        "model_id": str(uuid4()),
        "use_case": "foundation_layer",
        "configuration": {"endpoint": "http://localhost:8001/generate"}
    })
    return LLMClient(model_registry=mock_registry)


@pytest.mark.asyncio
async def test_model_registry_integration(llm_client):
    """Test that LLMClient uses ModelRegistry for model selection."""
    # Mock registry to return test models
    test_model_id = uuid4()
    with patch.object(llm_client.model_registry, 'get_current_model') as mock_get_model:
        mock_get_model.side_effect = [
            {"model_id": str(test_model_id), "use_case": "foundation_layer", "configuration": {"endpoint": "http://localhost:8001/generate"}},
            {"model_id": str(uuid4()), "use_case": "customization_layer", "configuration": {"endpoint": "http://localhost:8002/generate"}},
            {"model_id": str(uuid4()), "use_case": "interaction_layer", "configuration": {"endpoint": "http://localhost:8003/generate"}},
            {"model_id": str(uuid4()), "use_case": "coordination_layer", "configuration": {"endpoint": "http://localhost:8004/generate"}},
        ]
        
        # Ensure models are initialized
        await llm_client._update_models_from_registry()
        
        # Verify models are set from registry
        foundation_service = llm_client.llm_services["foundation"]
        assert foundation_service.get("model_id") == str(test_model_id)
        assert foundation_service.get("use_case") == "foundation_layer"
        
        customization_service = llm_client.llm_services["customization"]
        assert customization_service.get("model_id") is not None
        assert customization_service.get("use_case") == "customization_layer"


@pytest.mark.asyncio
async def test_historical_logging_integration(llm_client):
    """Test that historical logging happens automatically."""
    # Mock the historical log processor
    with patch.object(llm_client.historical_log_processor, 'log_inference') as mock_log:
        mock_log.return_value = uuid4()
        
        # Mock the LLM service call
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "text": "Test response",
                "tokens_used": 100
            }
            
            # Generate text (should trigger logging)
            result = await llm_client.generate_text(
                layer="foundation",
                prompt="Test prompt",
                context={"test": "context"},
                max_tokens=1000,
                temperature=0.7
            )
            
            # Verify logging was called
            assert mock_log.called
            call_args = mock_log.call_args
            assert call_args[1]["use_case"] == "foundation_layer"
            assert call_args[1]["prompt"] == "Test prompt"
            assert call_args[1]["generated_output"] == "Test response"


@pytest.mark.asyncio
async def test_error_handling_registry_unavailable():
    """Test that LLMClient handles registry unavailability gracefully."""
    # Create client without registry (should create default)
    client = LLMClient()
    
    # Mock registry to raise exception
    with patch.object(client.model_registry, 'get_current_model', side_effect=Exception("Registry unavailable")):
        # Should not raise exception, should handle gracefully
        await client._update_models_from_registry()
        
        # Service should still work (fallback to defaults)
        assert client.llm_services["foundation"]["url"] is not None


@pytest.mark.asyncio
async def test_error_handling_logging_failure(llm_client):
    """Test that logging failures don't block inference."""
    # Mock logging to fail
    with patch.object(llm_client.historical_log_processor, 'log_inference', side_effect=Exception("Logging failed")):
        # Mock successful LLM call
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "text": "Test response",
                "tokens_used": 100
            }
            
            # Should still succeed even if logging fails
            result = await llm_client.generate_text(
                layer="foundation",
                prompt="Test prompt",
                context={},
                max_tokens=1000,
                temperature=0.7
            )
            
            # Verify response is returned
            assert result["success"] is True
            assert result["text"] == "Test response"


@pytest.mark.asyncio
async def test_performance_metrics_tracking(llm_client):
    """Test that performance metrics are captured in logs."""
    with patch.object(llm_client.historical_log_processor, 'log_inference') as mock_log:
        mock_log.return_value = uuid4()
        
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "text": "Test response",
                "tokens_used": 150
            }
            
            await llm_client.generate_text(
                layer="foundation",
                prompt="Test prompt",
                context={},
                max_tokens=2000,
                temperature=0.8
            )
            
            # Verify performance metrics in log call
            call_args = mock_log.call_args
            metrics = call_args[1]["performance_metrics"]
            assert "latency_ms" in metrics
            assert "tokens_used" in metrics
            assert metrics["tokens_used"] == 150
            assert "temperature" in metrics
            assert metrics["temperature"] == 0.8

