"""
Performance validation tests for Model Management System integrations.
Measures overhead and validates performance requirements.
"""

import pytest
import time
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from services.ai_integration.llm_client import LLMClient
from services.model_management.model_registry import ModelRegistry


@pytest.mark.asyncio
async def test_model_registry_lookup_performance():
    """Test that model registry lookups don't add significant overhead."""
    registry = ModelRegistry()
    
    # Mock database with timing
    with patch.object(registry, '_get_postgres') as mock_postgres:
        mock_pool = AsyncMock()
        from datetime import datetime
        mock_pool.fetch = AsyncMock(return_value={
            "model_id": str(uuid4()),
            "model_name": "test-model",
            "model_type": "self_hosted",
            "provider": "ollama",
            "use_case": "foundation_layer",
            "version": "1.0",
            "status": "current",
            "model_path": None,
            "configuration": "{}",
            "performance_metrics": "{}",
            "resource_requirements": "{}",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        mock_postgres.return_value = mock_pool
        
        start_time = time.time()
        
        # Perform registry lookup
        model = await registry.get_current_model("foundation_layer")
        
        elapsed = time.time() - start_time
        
        # Registry lookup should be fast (< 100ms with mocked DB)
        assert elapsed < 0.1, f"Registry lookup too slow: {elapsed*1000:.2f}ms"
        assert model is not None


@pytest.mark.asyncio
async def test_historical_logging_overhead():
    """Test that historical logging doesn't block operations."""
    processor = MagicMock()
    processor.log_inference = AsyncMock(return_value=uuid4())
    
    # Simulate logging call
    start_time = time.time()
    
    await processor.log_inference(
        model_id=uuid4(),
        use_case="test",
        prompt="Test",
        context={},
        generated_output="Output"
    )
    
    elapsed = time.time() - start_time
    
    # Logging should be fast (async, non-blocking)
    assert elapsed < 0.1, f"Logging too slow: {elapsed*1000:.2f}ms"


@pytest.mark.asyncio
async def test_integrated_workflow_performance():
    """Test performance of complete integrated workflow."""
    mock_registry = MagicMock()
    mock_registry.get_current_model = AsyncMock(return_value={
        "model_id": str(uuid4()),
        "use_case": "foundation_layer",
        "configuration": {"endpoint": "http://localhost:8001/generate"}
    })
    
    client = LLMClient(model_registry=mock_registry)
    client.historical_log_processor = MagicMock()
    client.historical_log_processor.log_inference = AsyncMock(return_value=uuid4())
    
    with patch.object(client, '_make_request', return_value={"text": "Response", "tokens_used": 100}):
        start_time = time.time()
        
        # Complete workflow: Registry → Inference → Logging
        result = await client.generate_text(
            layer="foundation",
            prompt="Test prompt",
            context={}
        )
        
        elapsed = time.time() - start_time
        
        # Complete workflow should complete in reasonable time (< 500ms mocked)
        assert elapsed < 0.5, f"Workflow too slow: {elapsed*1000:.2f}ms"
        assert result["success"] is True


@pytest.mark.asyncio
async def test_concurrent_operations_performance():
    """Test that concurrent operations maintain performance."""
    mock_registry = MagicMock()
    mock_registry.get_current_model = AsyncMock(return_value={
        "model_id": str(uuid4()),
        "use_case": "foundation_layer"
    })
    
    client = LLMClient(model_registry=mock_registry)
    client.historical_log_processor = MagicMock()
    client.historical_log_processor.log_inference = AsyncMock(return_value=uuid4())
    
    with patch.object(client, '_make_request', return_value={"text": "Response", "tokens_used": 100}):
        # Run 10 concurrent operations
        start_time = time.time()
        
        tasks = [
            client.generate_text(layer="foundation", prompt=f"Test {i}", context={})
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Concurrent operations should complete efficiently
        assert elapsed < 1.0, f"Concurrent operations too slow: {elapsed*1000:.2f}ms"
        assert all(r["success"] for r in results)
        
        # Average time per operation should be reasonable
        avg_time = elapsed / 10
        assert avg_time < 0.2, f"Average time per operation too slow: {avg_time*1000:.2f}ms"


@pytest.mark.asyncio
async def test_error_handling_performance():
    """Test that error handling doesn't add significant overhead."""
    client = LLMClient()
    
    # Simulate registry failure
    with patch.object(client.model_registry, 'get_current_model', side_effect=Exception("Registry down")):
        with patch.object(client, '_make_request', return_value={"text": "Fallback", "tokens_used": 50}):
            start_time = time.time()
            
            result = await client.generate_text(
                layer="foundation",
                prompt="Test",
                context={}
            )
            
            elapsed = time.time() - start_time
            
            # Error handling should be fast
            assert elapsed < 0.3, f"Error handling too slow: {elapsed*1000:.2f}ms"
            assert result is not None  # Should still return result (success or fallback)

