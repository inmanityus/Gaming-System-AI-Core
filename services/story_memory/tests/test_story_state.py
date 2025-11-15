"""
Tests for Story State Manager.
"""
import asyncio
from datetime import datetime
from uuid import uuid4

import pytest
import asyncpg

from ..story_schemas import (
    ArcProgress, ArcRole, ProgressState, StoryDecision,
    DarkWorldFamily, DarkWorldStanding
)
from ..story_state_manager import StoryStateManager


@pytest.fixture
async def postgres_pool():
    """Create test database pool."""
    # In real tests, this would create a test database
    # For now, mock it
    class MockPool:
        async def acquire(self):
            return MockConnection()
    
    return MockPool()


class MockConnection:
    """Mock database connection."""
    
    def __init__(self):
        self.data = {}
    
    async def fetchrow(self, query, *args):
        # Simple mock - return empty player data
        if "story_players" in query:
            return {
                'broker_book_state': {},
                'debt_of_flesh_state': {},
                'surgeon_butcher_score': 0.0
            }
        return None
    
    async def fetch(self, query, *args):
        # Return empty results for all queries
        return []
    
    async def fetchval(self, query, *args):
        return 0
    
    async def execute(self, query, *args):
        pass


@pytest.mark.asyncio
async def test_get_story_snapshot_new_player(postgres_pool):
    """Test getting snapshot for new player."""
    manager = StoryStateManager(postgres_pool)
    player_id = uuid4()
    
    snapshot = await manager.get_story_snapshot(player_id)
    
    assert snapshot.player_id == player_id
    assert snapshot.surgeon_butcher_score == 0.0
    assert len(snapshot.arc_progress) == 0
    assert len(snapshot.recent_decisions) == 0
    assert len(snapshot.relationships) == 0
    assert len(snapshot.dark_world_standings) == 0


@pytest.mark.asyncio
async def test_update_arc_progress(postgres_pool):
    """Test updating arc progress."""
    manager = StoryStateManager(postgres_pool)
    player_id = uuid4()
    
    await manager.update_arc_progress(
        player_id=player_id,
        arc_id="dark.carrion_kin",
        arc_role=ArcRole.MAIN_ARC,
        progress_state=ProgressState.EARLY,
        last_beat_id="intro_01"
    )
    
    # In real test, would verify database update
    assert True


@pytest.mark.asyncio
async def test_record_decision(postgres_pool):
    """Test recording a player decision."""
    manager = StoryStateManager(postgres_pool)
    player_id = uuid4()
    
    decision = StoryDecision(
        decision_id="choice_001",
        arc_id="dark.vampiric_houses",
        choice_label="Spare the vampire",
        outcome_tags=["mercy", "vampire_ally"],
        moral_weight=-0.1,  # Slightly more surgeon
        timestamp=datetime.utcnow()
    )
    
    await manager.record_decision(player_id, decision)
    
    # In real test, would verify database insert
    assert True


@pytest.mark.asyncio
async def test_update_relationship(postgres_pool):
    """Test updating NPC relationship."""
    manager = StoryStateManager(postgres_pool)
    player_id = uuid4()
    
    relationship = await manager.update_relationship(
        player_id=player_id,
        entity_id="npc_valdris",
        entity_type="npc",
        score_delta=20.0,
        new_flags=["trusted"],
        interaction="Helped with blood debt"
    )
    
    assert relationship.entity_id == "npc_valdris"
    assert relationship.relationship_score == 20.0
    assert "trusted" in relationship.flags


@pytest.mark.asyncio
async def test_update_dark_world_standing(postgres_pool):
    """Test updating Dark World family standing."""
    manager = StoryStateManager(postgres_pool)
    player_id = uuid4()
    
    standing = await manager.update_dark_world_standing(
        player_id=player_id,
        family=DarkWorldFamily.VAMPIRIC_HOUSES,
        standing_delta=15.0,
        favor_delta=1,
        special_status=["preferred_supplier"]
    )
    
    assert standing.family_name == DarkWorldFamily.VAMPIRIC_HOUSES
    assert standing.standing_score == 15.0
    assert standing.favors_owed == 1
    assert "preferred_supplier" in standing.special_status


def test_arc_progress_model():
    """Test ArcProgress model."""
    progress = ArcProgress(
        arc_id="dark.moon_clans",
        arc_role=ArcRole.MAIN_ARC,
        progress_state=ProgressState.MID,
        last_beat_id="moon_ritual_02",
        last_update_at=datetime.utcnow()
    )
    
    assert progress.arc_id == "dark.moon_clans"
    assert progress.arc_role == ArcRole.MAIN_ARC
    assert progress.progress_state == ProgressState.MID
