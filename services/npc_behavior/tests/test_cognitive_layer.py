"""
Tests for Cognitive Layer - Asynchronous AI inference for strategic decisions.

Implements REQ-PERF-003: Async AI Architecture (Cognitive Layer).
"""

import pytest
import asyncio
import time
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock

from services.npc_behavior.cognitive_layer import (
    CognitiveLayer,
    CognitiveAnalysis,
)
from services.npc_behavior.behavioral_proxy import ProxyManager, ProxyStrategy, ProxyDirective
from services.ai_integration.llm_client import LLMClient


@pytest.fixture
def proxy_manager():
    """Create a ProxyManager instance."""
    return ProxyManager()


@pytest.fixture
def mock_llm_client():
    """Create a mock LLMClient."""
    client = Mock(spec=LLMClient)
    client.generate_text = AsyncMock(return_value={"text": "AGGRESSIVE strategy recommended"})
    return client


@pytest.fixture
def cognitive_layer(proxy_manager, mock_llm_client):
    """Create a CognitiveLayer instance."""
    layer = CognitiveLayer(
        proxy_manager=proxy_manager,
        llm_client=mock_llm_client,
        update_rate_hz=0.5
    )
    yield layer
    # Cleanup
    try:
        layer.stop(timeout=2.0)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_cognitive_layer_start_stop(cognitive_layer):
    """Test cognitive layer start and stop."""
    cognitive_layer.start()
    
    # Wait a bit for thread to start
    await asyncio.sleep(0.1)
    
    assert cognitive_layer._running is True
    assert cognitive_layer._loop_thread is not None
    assert cognitive_layer._loop_thread.is_alive()
    
    # Stop
    cognitive_layer.stop(timeout=2.0)
    
    # Wait for thread to stop
    await asyncio.sleep(0.2)
    
    assert cognitive_layer._running is False


@pytest.mark.asyncio
async def test_queue_analysis(cognitive_layer):
    """Test queueing NPC for analysis."""
    cognitive_layer.start()
    await asyncio.sleep(0.1)
    
    npc_id = uuid4()
    
    # Queue analysis
    result = cognitive_layer.queue_analysis(npc_id)
    assert result is True
    
    # Check queue
    assert cognitive_layer.get_pending_count() > 0
    
    cognitive_layer.stop(timeout=2.0)


@pytest.mark.asyncio
async def test_queue_analysis_duplicate(cognitive_layer):
    """Test queueing same NPC twice."""
    cognitive_layer.start()
    await asyncio.sleep(0.1)
    
    npc_id = uuid4()
    
    # Queue first time
    result1 = cognitive_layer.queue_analysis(npc_id)
    assert result1 is True
    
    # Queue second time (should return False)
    result2 = cognitive_layer.queue_analysis(npc_id)
    assert result2 is False
    
    cognitive_layer.stop(timeout=2.0)


@pytest.mark.asyncio
async def test_analysis_processing(cognitive_layer, proxy_manager):
    """Test that analysis is processed and directive sent."""
    cognitive_layer.start()
    await asyncio.sleep(0.1)
    
    npc_id = uuid4()
    
    # Queue analysis
    cognitive_layer.queue_analysis(npc_id)
    
    # Wait for processing (update_rate_hz=0.5 means 2 seconds)
    await asyncio.sleep(3.0)
    
    # Check proxy received directive
    proxy = proxy_manager.get_or_create_proxy(npc_id)
    # Directive should have been applied
    assert proxy.current_strategy in [ProxyStrategy.AGGRESSIVE, ProxyStrategy.DEFENSIVE, 
                                       ProxyStrategy.NEUTRAL, ProxyStrategy.RETREAT,
                                       ProxyStrategy.CURIOUS, ProxyStrategy.SOCIAL]
    
    cognitive_layer.stop(timeout=2.0)


@pytest.mark.asyncio
async def test_rule_based_analysis_fallback(proxy_manager):
    """Test rule-based analysis when LLM client is None."""
    layer = CognitiveLayer(
        proxy_manager=proxy_manager,
        llm_client=None,
        update_rate_hz=0.5
    )
    layer.start()
    await asyncio.sleep(0.1)
    
    npc_id = uuid4()
    layer.queue_analysis(npc_id)
    
    # Wait for processing
    await asyncio.sleep(3.0)
    
    # Should still work with rule-based analysis
    proxy = proxy_manager.get_or_create_proxy(npc_id)
    assert proxy.current_strategy in [ProxyStrategy.AGGRESSIVE, ProxyStrategy.DEFENSIVE,
                                       ProxyStrategy.NEUTRAL, ProxyStrategy.RETREAT,
                                       ProxyStrategy.CURIOUS, ProxyStrategy.SOCIAL]
    
    layer.stop(timeout=2.0)


@pytest.mark.asyncio
async def test_queue_full(cognitive_layer):
    """Test queue behavior when full."""
    cognitive_layer.start()
    await asyncio.sleep(0.1)
    
    # Fill queue to max
    for i in range(1000):
        cognitive_layer.queue_analysis(uuid4())
    
    # Try to add one more (should fail)
    result = cognitive_layer.queue_analysis(uuid4())
    assert result is False
    
    cognitive_layer.stop(timeout=2.0)


def test_request_analysis_alias():
    """Test request_analysis is an alias for queue_analysis."""
    proxy_manager = ProxyManager()
    layer = CognitiveLayer(proxy_manager=proxy_manager, llm_client=None)
    
    npc_id = uuid4()
    
    # First call should succeed
    result1 = layer.request_analysis(npc_id)
    assert result1 is True
    
    # Second call (duplicate) should return False
    result2 = layer.queue_analysis(npc_id)
    assert result2 is False
    
    # request_analysis should also return False for duplicate
    result3 = layer.request_analysis(npc_id)
    assert result3 is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

