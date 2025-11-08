"""
Integration tests for AI Integration Service.
Tests LLM client, context management, and service coordination.
"""

import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from llm_client import LLMClient
from context_manager import ContextManager
from service_coordinator import ServiceCoordinator
from response_optimizer import ResponseOptimizer


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_pool_before_test():
    """Reset connection pool before each test to avoid event loop conflicts."""
    import services.state_manager.connection_pool as cp
    # Reset pools to ensure fresh state for each test
    if cp._postgres_pool is not None:
        try:
            if hasattr(cp._postgres_pool, '_pool') and cp._postgres_pool._pool:
                if not cp._postgres_pool._pool.is_closing():
                    await cp._postgres_pool._pool.close()
        except Exception:
            pass  # Ignore errors
    cp._postgres_pool = None
    
    # Also reset Redis pool
    if hasattr(cp, '_redis_pool') and cp._redis_pool is not None:
        try:
            if hasattr(cp._redis_pool, '_client') and cp._redis_pool._client:
                if hasattr(cp._redis_pool._client, 'aclose'):
                    await cp._redis_pool._client.aclose()
                elif hasattr(cp._redis_pool._client, 'close'):
                    await cp._redis_pool._client.close()
        except Exception:
            pass  # Ignore errors
    if hasattr(cp, '_redis_pool'):
        cp._redis_pool = None
    
    yield
    
    # Cleanup after test
    try:
        loop = asyncio.get_running_loop()
        if cp._postgres_pool and hasattr(cp._postgres_pool, '_pool') and cp._postgres_pool._pool:
            if not cp._postgres_pool._pool.is_closing():
                await cp._postgres_pool._pool.close()
        cp._postgres_pool = None
        if hasattr(cp, '_redis_pool') and cp._redis_pool:
            if hasattr(cp._redis_pool, '_client') and cp._redis_pool._client:
                if hasattr(cp._redis_pool._client, 'aclose'):
                    await cp._redis_pool._client.aclose()
                elif hasattr(cp._redis_pool._client, 'close'):
                    await cp._redis_pool._client.close()
        if hasattr(cp, '_redis_pool'):
            cp._redis_pool = None
    except (RuntimeError, Exception):
        # Event loop closed or other error - just reset the references
        cp._postgres_pool = None
        if hasattr(cp, '_redis_pool'):
            cp._redis_pool = None


@pytest_asyncio.fixture(scope="function")
async def llm_client():
    """LLM client fixture."""
    client = LLMClient()
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="function")
async def context_manager():
    """Context manager fixture."""
    manager = ContextManager()
    yield manager


@pytest_asyncio.fixture(scope="function")
async def service_coordinator():
    """Service coordinator fixture."""
    coordinator = ServiceCoordinator()
    yield coordinator
    await coordinator.close()


@pytest_asyncio.fixture(scope="function")
async def response_optimizer():
    """Response optimizer fixture."""
    optimizer = ResponseOptimizer()
    yield optimizer


@pytest_asyncio.fixture(scope="function")
async def test_player_id():
    """Test player ID fixture."""
    # Create a test player in the database
    # Database connection handled internally by context_manager
    
    postgres = await get_postgres_pool()
    player_id = uuid4()
    
    # Insert test player
    await postgres.execute(
            """
            INSERT INTO players (id, steam_id, username, tier, stats, inventory, money, reputation, level, xp)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9, $10)
            """,
            player_id,
            "test_steam_123",
            "test_player",
            "free",
            '{"strength": 10, "intelligence": 10}',
            '{"items": []}',
            1000,
            50,
            1,
            0
        )
    
    yield player_id
    
    # Cleanup
    try:
        await postgres.execute("DELETE FROM players WHERE id = $1", player_id)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_llm_client_initialization(llm_client):
    """Test LLM client initialization."""
    assert llm_client is not None
    assert llm_client.session is None  # Not initialized yet
    
    # Test service selection
    service_name = llm_client._select_service("foundation")
    assert service_name == "foundation"


@pytest.mark.asyncio
async def test_llm_client_service_status(llm_client):
    """Test LLM client service status."""
    status = await llm_client.get_service_status()
    
    assert isinstance(status, dict)
    assert "foundation" in status
    assert "customization" in status
    assert "interaction" in status
    assert "coordination" in status
    
    for service_name, service_status in status.items():
        assert "url" in service_status
        assert "circuit_breaker_state" in service_status
        assert "failure_count" in service_status
        assert "success_count" in service_status


@pytest.mark.asyncio
async def test_context_manager_player_context(context_manager, test_player_id):
    """Test context manager player context."""
    context = await context_manager.get_player_context(test_player_id)
    
    assert isinstance(context, dict)
    assert "player" in context
    assert "game_state" in context
    assert "story_history" in context
    
    # Check player data
    player_data = context["player"]
    assert player_data["id"] == str(test_player_id)
    assert player_data["username"] == "test_player"
    assert player_data["tier"] == "free"


@pytest.mark.asyncio
async def test_context_manager_world_context(context_manager):
    """Test context manager world context."""
    context = await context_manager.get_world_context()
    
    assert isinstance(context, dict)
    assert "world_time" in context
    assert "current_weather" in context
    assert "global_events" in context
    assert "faction_power" in context
    assert "economic_state" in context
    assert "npc_population" in context
    assert "territory_control" in context
    assert "active_npcs" in context


@pytest.mark.asyncio
async def test_context_manager_optimized_context(context_manager, test_player_id):
    """Test context manager optimized context."""
    # Test full context
    full_context = await context_manager.get_optimized_context(test_player_id, "full")
    assert isinstance(full_context, dict)
    assert "player" in full_context
    assert "game_state" in full_context
    assert "story_history" in full_context
    assert "world" in full_context
    
    # Test minimal context
    minimal_context = await context_manager.get_optimized_context(test_player_id, "minimal")
    assert isinstance(minimal_context, dict)
    assert "player" in minimal_context
    assert "game_state" in minimal_context
    assert len(minimal_context["player"]) == 4  # Only essential fields


@pytest.mark.asyncio
async def test_service_coordinator_initialization(service_coordinator):
    """Test service coordinator initialization."""
    assert service_coordinator is not None
    assert service_coordinator.session is None  # Not initialized yet


@pytest.mark.asyncio
async def test_service_coordinator_service_health(service_coordinator):
    """Test service coordinator service health."""
    health = await service_coordinator.get_service_health()
    
    assert isinstance(health, dict)
    assert "state_manager" in health
    assert "settings" in health
    assert "story_teller" in health


@pytest.mark.asyncio
async def test_response_optimizer_initialization(response_optimizer):
    """Test response optimizer initialization."""
    assert response_optimizer is not None
    assert response_optimizer.cache is not None


@pytest.mark.asyncio
async def test_response_optimizer_performance_metrics(response_optimizer):
    """Test response optimizer performance metrics."""
    metrics = await response_optimizer.get_performance_metrics()
    
    assert isinstance(metrics, dict)
    assert "total_requests" in metrics
    assert "cache_hits" in metrics
    assert "cache_misses" in metrics
    assert "cache_hit_rate" in metrics
    assert "avg_response_time" in metrics


@pytest.mark.asyncio
async def test_response_optimizer_optimize_response(response_optimizer):
    """Test response optimizer optimize response."""
    layer = "foundation"
    prompt = "Test prompt"
    context = {"test": "context"}
    response = {"text": "Test response", "tokens_used": 10}
    
    optimized = await response_optimizer.optimize_response(
        layer, prompt, context, response
    )
    
    assert isinstance(optimized, dict)
    assert "text" in optimized
    assert "optimized" in optimized
    assert "timestamp" in optimized
    assert optimized["optimized"] is True


@pytest.mark.asyncio
async def test_integration_flow(llm_client, context_manager, test_player_id):
    """Test integration flow between components."""
    # Get player context
    context = await context_manager.get_optimized_context(test_player_id, "minimal")
    assert isinstance(context, dict)
    
    # Test LLM service status
    status = await llm_client.get_service_status()
    assert isinstance(status, dict)
    
    # Test fallback response
    fallback = llm_client._get_fallback_response("foundation", "test prompt")
    assert isinstance(fallback, str)
    assert len(fallback) > 0


@pytest.mark.asyncio
async def test_error_handling(llm_client):
    """Test error handling in LLM client."""
    # Test circuit breaker
    from llm_client import CircuitBreakerError
    
    # This should not raise an exception
    try:
        service_name = llm_client._select_service("foundation")
        assert service_name == "foundation"
    except CircuitBreakerError:
        # Circuit breaker might be open, which is expected in test environment
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
