# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Tests for Lore Retriever (Model A)
===================================

Tests the lore retrieval functionality including:
- HTTP client integration
- Circuit breaker behavior
- Retry logic
- Error handling
- Concurrent data fetching
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from services.srl_rlvr_training.collaboration.lore_retriever import LoreRetriever, LoreContext
from services.srl_rlvr_training.collaboration.rules_engine_client import RulesEngineClient
from services.srl_rlvr_training.collaboration.lore_database_client import LoreDatabaseClient


@pytest.fixture
def mock_rules_client():
    """Mock RulesEngineClient."""
    client = MagicMock(spec=RulesEngineClient)
    client.get_rules = AsyncMock(return_value={"rules": {"test": "rule"}})
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_lore_client():
    """Mock LoreDatabaseClient."""
    client = MagicMock(spec=LoreDatabaseClient)
    client.get_lore = AsyncMock(return_value=["lore1", "lore2"])
    client.get_historical_examples = AsyncMock(return_value=[{"example": 1}])
    client.close = AsyncMock()
    return client


@pytest.fixture
def lore_retriever(mock_rules_client, mock_lore_client):
    """Create LoreRetriever with mocked clients."""
    retriever = LoreRetriever.__new__(LoreRetriever)
    retriever.rules_engine_client = mock_rules_client
    retriever.lore_db_client = mock_lore_client
    return retriever


@pytest.mark.asyncio
async def test_retrieve_lore_success(lore_retriever):
    """Test successful lore retrieval."""
    context = await lore_retriever.retrieve_lore("Vampire", "personality")
    
    assert isinstance(context, LoreContext)
    assert context.monster_species == "Vampire"
    assert context.game_rules == {"rules": {"test": "rule"}}
    assert len(context.historical_examples) == 1
    assert len(context.related_lore) == 2


@pytest.mark.asyncio
async def test_retrieve_lore_with_errors(lore_retriever):
    """Test lore retrieval when some sources fail."""
    lore_retriever.rules_engine_client.get_rules = AsyncMock(side_effect=Exception("Network error"))
    lore_retriever.lore_db_client.get_lore = AsyncMock(return_value=["lore1"])
    lore_retriever.lore_db_client.get_historical_examples = AsyncMock(return_value=[])
    
    context = await lore_retriever.retrieve_lore("Vampire", "personality")
    
    # Should still return context with available data
    assert isinstance(context, LoreContext)
    assert context.game_rules == {}
    assert len(context.related_lore) == 1


@pytest.mark.asyncio
async def test_close_closes_all_clients(lore_retriever):
    """Test that close() closes all client sessions."""
    await lore_retriever.close()
    
    lore_retriever.rules_engine_client.close.assert_called_once()
    lore_retriever.lore_db_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_fetching(lore_retriever):
    """Test that all fetches happen concurrently."""
    import time
    
    async def slow_get_rules(*args, **kwargs):
        await asyncio.sleep(0.1)
        return {"rules": {}}
    
    async def slow_get_lore(*args, **kwargs):
        await asyncio.sleep(0.1)
        return []
    
    async def slow_get_examples(*args, **kwargs):
        await asyncio.sleep(0.1)
        return []
    
    lore_retriever.rules_engine_client.get_rules = slow_get_rules
    lore_retriever.lore_db_client.get_lore = slow_get_lore
    lore_retriever.lore_db_client.get_historical_examples = slow_get_examples
    
    start = time.time()
    await lore_retriever.retrieve_lore("Vampire", "personality")
    elapsed = time.time() - start
    
    # Should take ~0.1s (concurrent) not ~0.3s (serial)
    assert elapsed < 0.15

