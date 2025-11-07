"""
Tests for Social Memory & Relationship Graph System.

Implements REQ-NPC-003: Social Memory & Relationship Graph.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, MagicMock

from services.npc_behavior.social_memory import (
    SocialMemoryGraph,
    Relationship,
    MemoryEvent,
    SentimentType,
)


@pytest_asyncio.fixture
async def social_memory():
    """Create a SocialMemoryGraph instance with mocked databases."""
    memory = SocialMemoryGraph()
    
    # Mock postgres
    mock_postgres = AsyncMock()
    mock_postgres.fetch = AsyncMock(return_value=None)
    memory.postgres = mock_postgres
    
    # Mock redis
    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()
    memory.redis = mock_redis
    
    return memory


@pytest.mark.asyncio
async def test_get_relationship_new(social_memory):
    """Test getting a new relationship."""
    npc_id = uuid4()
    target_id = uuid4()
    
    # Mock no existing relationship
    social_memory.postgres.fetch.return_value = None
    
    relationship = await social_memory.get_relationship(npc_id, target_id)
    
    assert relationship is not None
    assert relationship.npc_id == npc_id
    assert relationship.target_id == target_id
    assert relationship.target_type == "player"
    assert relationship.interaction_count == 0


@pytest.mark.asyncio
async def test_get_relationship_existing(social_memory):
    """Test getting existing relationship from database."""
    npc_id = uuid4()
    target_id = uuid4()
    
    # Mock existing relationship
    mock_result = {
        "npc_id": npc_id,
        "target_id": target_id,
        "target_type": "player",
        "sentiments": {"trust": 0.7, "respect": 0.5},
        "relationship_score": 0.6,
        "interaction_count": 5,
        "first_interaction_time": 1000.0,
        "last_interaction_time": 2000.0,
        "notable_events": [],
        "metadata": {},
    }
    social_memory.postgres.fetch.return_value = mock_result
    
    relationship = await social_memory.get_relationship(npc_id, target_id)
    
    assert relationship is not None
    assert relationship.interaction_count == 5
    assert relationship.relationship_score == 0.6
    assert relationship.sentiments["trust"] == 0.7


@pytest.mark.asyncio
async def test_get_relationship_validation(social_memory):
    """Test input validation in get_relationship."""
    # Invalid npc_id
    with pytest.raises(TypeError):
        await social_memory.get_relationship("not-uuid", uuid4())
    
    # Invalid target_id
    with pytest.raises(TypeError):
        await social_memory.get_relationship(uuid4(), "not-uuid")


@pytest.mark.asyncio
async def test_record_interaction(social_memory):
    """Test recording an interaction."""
    npc_id = uuid4()
    target_id = uuid4()
    
    # Mock relationship
    social_memory.postgres.fetch.return_value = None
    
    # Mock save
    social_memory.postgres.execute = AsyncMock()
    
    await social_memory.record_interaction(
        npc_id=npc_id,
        target_id=target_id,
        interaction_type="dialogue",
        description="Had a conversation",
        sentiment_impact={"trust": 0.1},
        importance=0.6
    )
    
    # Verify save was called
    assert social_memory.postgres.execute.called


@pytest.mark.asyncio
async def test_record_interaction_validation(social_memory):
    """Test input validation in record_interaction."""
    npc_id = uuid4()
    target_id = uuid4()
    
    # Invalid interaction_type
    with pytest.raises(ValueError):
        await social_memory.record_interaction(
            npc_id, target_id, "", "description"
        )
    
    # Invalid importance
    with pytest.raises(ValueError):
        await social_memory.record_interaction(
            npc_id, target_id, "dialogue", "description", importance=1.5
        )
    
    # Invalid sentiment_impact
    with pytest.raises(TypeError):
        await social_memory.record_interaction(
            npc_id, target_id, "dialogue", "description",
            sentiment_impact="not-dict"
        )


@pytest.mark.asyncio
async def test_calculate_relationship_score():
    """Test relationship score calculation."""
    memory = SocialMemoryGraph()
    
    # Positive sentiments
    sentiments = {
        "trust": 0.8,
        "respect": 0.7,
        "affection": 0.6,
    }
    score = memory._calculate_relationship_score(sentiments)
    assert score > 0
    
    # Negative sentiments
    sentiments = {
        "fear": 0.8,
        "anger": 0.7,
        "disgust": 0.6,
    }
    score = memory._calculate_relationship_score(sentiments)
    assert score < 0
    
    # Mixed sentiments
    sentiments = {
        "trust": 0.5,
        "anger": 0.5,
    }
    score = memory._calculate_relationship_score(sentiments)
    assert -1.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_get_memorable_events(social_memory):
    """Test getting memorable events."""
    npc_id = uuid4()
    target_id = uuid4()
    
    # Mock relationship with events
    relationship = Relationship(npc_id=npc_id, target_id=target_id, target_type="player")
    relationship.notable_events = [
        {
            "event_id": "event1",
            "npc_id": str(npc_id),
            "target_id": str(target_id),
            "event_type": "dialogue",
            "description": "Important conversation",
            "sentiment_impact": {},
            "timestamp": 1000.0,
            "importance": 0.8,
            "context": {},
        }
    ]
    social_memory._relationships[(npc_id, target_id)] = relationship
    
    events = await social_memory.get_memorable_events(npc_id, target_id)
    
    assert len(events) == 1
    assert events[0].event_type == "dialogue"


@pytest.mark.asyncio
async def test_get_memorable_events_validation(social_memory):
    """Test input validation in get_memorable_events."""
    npc_id = uuid4()
    
    # Invalid limit
    with pytest.raises(ValueError):
        await social_memory.get_memorable_events(npc_id, limit=0)
    
    with pytest.raises(ValueError):
        await social_memory.get_memorable_events(npc_id, limit=2000)


@pytest.mark.asyncio
async def test_get_dialogue_context(social_memory):
    """Test getting dialogue context."""
    npc_id = uuid4()
    target_id = uuid4()
    
    # Mock relationship
    relationship = Relationship(npc_id=npc_id, target_id=target_id, target_type="player")
    relationship.relationship_score = 0.7
    relationship.sentiments = {"trust": 0.8}
    relationship.interaction_count = 10
    social_memory._relationships[(npc_id, target_id)] = relationship
    
    context = await social_memory.get_dialogue_context(npc_id, target_id)
    
    assert context["relationship_score"] == 0.7
    assert context["sentiments"]["trust"] == 0.8
    assert context["interaction_count"] == 10
    assert "recent_events" in context


@pytest.mark.asyncio
async def test_get_all_relationships(social_memory):
    """Test getting all relationships for an NPC."""
    npc_id = uuid4()
    
    # Mock database results
    mock_results = [
        {
            "npc_id": npc_id,
            "target_id": uuid4(),
            "target_type": "player",
            "sentiments": {},
            "relationship_score": 0.5,
            "interaction_count": 3,
            "first_interaction_time": 1000.0,
            "last_interaction_time": 2000.0,
            "notable_events": [],
            "metadata": {},
        }
    ]
    social_memory.postgres.fetch.return_value = mock_results
    
    relationships = await social_memory.get_all_relationships(npc_id)
    
    assert len(relationships) == 1
    assert relationships[0].npc_id == npc_id


@pytest.mark.asyncio
async def test_get_all_relationships_validation(social_memory):
    """Test input validation in get_all_relationships."""
    # Invalid npc_id
    with pytest.raises(TypeError):
        await social_memory.get_all_relationships("not-uuid")


@pytest.mark.asyncio
async def test_relationship_sentiment_clamping(social_memory):
    """Test that sentiments are clamped to 0.0-1.0 range."""
    npc_id = uuid4()
    target_id = uuid4()
    
    social_memory.postgres.fetch.return_value = None
    social_memory.postgres.execute = AsyncMock()
    
    # Record interaction with high sentiment impact
    await social_memory.record_interaction(
        npc_id=npc_id,
        target_id=target_id,
        interaction_type="dialogue",
        description="Very positive interaction",
        sentiment_impact={"trust": 10.0},  # Should be clamped
        importance=0.8
    )
    
    relationship = await social_memory.get_relationship(npc_id, target_id)
    assert relationship.sentiments["trust"] <= 1.0


def test_relationship_to_dict():
    """Test converting relationship to dictionary."""
    npc_id = uuid4()
    target_id = uuid4()
    
    relationship = Relationship(
        npc_id=npc_id,
        target_id=target_id,
        target_type="player"
    )
    relationship.sentiments = {"trust": 0.7}
    relationship.relationship_score = 0.6
    relationship.interaction_count = 5
    
    data = relationship.to_dict()
    
    assert data["npc_id"] == str(npc_id)
    assert data["target_id"] == str(target_id)
    assert data["sentiments"]["trust"] == 0.7
    assert data["relationship_score"] == 0.6
    assert data["interaction_count"] == 5


def test_relationship_from_dict():
    """Test creating relationship from dictionary."""
    npc_id = uuid4()
    target_id = uuid4()
    
    data = {
        "npc_id": str(npc_id),
        "target_id": str(target_id),
        "target_type": "player",
        "sentiments": {"trust": 0.7},
        "relationship_score": 0.6,
        "interaction_count": 5,
        "first_interaction_time": 1000.0,
        "last_interaction_time": 2000.0,
        "notable_events": [],
        "metadata": {},
    }
    
    relationship = Relationship.from_dict(data)
    
    assert relationship.npc_id == npc_id
    assert relationship.target_id == target_id
    assert relationship.sentiments["trust"] == 0.7


def test_memory_event_to_dict():
    """Test converting memory event to dictionary."""
    npc_id = uuid4()
    target_id = uuid4()
    
    event = MemoryEvent(
        event_id="event1",
        npc_id=npc_id,
        target_id=target_id,
        event_type="dialogue",
        description="Test event",
        sentiment_impact={"trust": 0.1},
        importance=0.7
    )
    
    data = event.to_dict()
    
    assert data["event_id"] == "event1"
    assert data["npc_id"] == str(npc_id)
    assert data["event_type"] == "dialogue"
    assert data["importance"] == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



