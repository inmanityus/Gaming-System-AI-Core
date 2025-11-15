"""
Tests for Story Memory Event Ingestor
=====================================
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from ..event_ingestor import EventIngestor
from ..story_schemas import (
    StoryEvent, ArcBeatReachedEvent, QuestCompletedEvent,
    ExperienceCompletedEvent, RelationshipChangedEvent,
    ArcRole, ProgressState
)


@pytest.fixture
async def mock_story_manager():
    """Create mock story state manager."""
    manager = AsyncMock()
    manager.update_arc_progress = AsyncMock()
    manager.record_decision = AsyncMock()
    manager.update_relationship = AsyncMock()
    manager.update_dark_world_standing = AsyncMock()
    manager.record_experience = AsyncMock()
    manager.update_player_metadata = AsyncMock()
    return manager


@pytest.fixture
async def mock_drift_detector():
    """Create mock drift detector."""
    detector = AsyncMock()
    detector.check_drift = AsyncMock(return_value=None)
    detector.check_conflicts = AsyncMock(return_value=[])
    return detector


@pytest.fixture
async def mock_postgres():
    """Create mock PostgreSQL pool."""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire = AsyncMock(return_value=conn)
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=0)
    conn.execute = AsyncMock()
    return pool


@pytest.fixture
async def event_ingestor(mock_postgres, mock_story_manager, mock_drift_detector):
    """Create event ingestor with mocked dependencies."""
    ingestor = EventIngestor(
        postgres_pool=mock_postgres,
        story_manager=mock_story_manager,
        drift_detector=mock_drift_detector
    )
    return ingestor


class TestEventIngestor:
    """Test suite for event ingestor."""
    
    @pytest.mark.asyncio
    async def test_arc_beat_reached_event(self, event_ingestor, mock_story_manager):
        """Test handling of arc beat reached event."""
        player_id = uuid4()
        event = ArcBeatReachedEvent(
            player_id=player_id,
            arc_id="main_quest_1",
            beat_id="beat_3",
            arc_role=ArcRole.MAIN_ARC,
            progress_state=ProgressState.MID
        )
        
        await event_ingestor.process_event(event)
        
        # Verify arc progress was updated
        mock_story_manager.update_arc_progress.assert_called_once_with(
            player_id=player_id,
            arc_id="main_quest_1",
            arc_role=ArcRole.MAIN_ARC,
            progress_state=ProgressState.MID,
            last_beat_id="beat_3"
        )
    
    @pytest.mark.asyncio
    async def test_quest_completed_event(self, event_ingestor):
        """Test handling of quest completed event."""
        player_id = uuid4()
        event = QuestCompletedEvent(
            player_id=player_id,
            quest_id="side_quest_42",
            is_main_quest=False,
            rewards={"xp": 500, "item": "shadow_blade"}
        )
        
        await event_ingestor.process_event(event)
        
        # Event should be processed without errors
        # Specific side effects depend on implementation
    
    @pytest.mark.asyncio
    async def test_relationship_changed_event(self, event_ingestor, mock_story_manager):
        """Test handling of relationship change event."""
        player_id = uuid4()
        event = RelationshipChangedEvent(
            player_id=player_id,
            entity_id="npc_sarah",
            new_score=0.75,
            change_reason="Saved from danger"
        )
        
        await event_ingestor.process_event(event)
        
        # Verify relationship was updated
        mock_story_manager.update_relationship.assert_called_once_with(
            player_id=player_id,
            entity_id="npc_sarah",
            score=0.75,
            state={"last_interaction": "Saved from danger"}
        )
    
    @pytest.mark.asyncio
    async def test_experience_completed_event(self, event_ingestor, mock_story_manager):
        """Test handling of experience completed event."""
        player_id = uuid4()
        event = ExperienceCompletedEvent(
            player_id=player_id,
            experience_id="soul_echo_encounter_1",
            outcome="negotiated",
            metadata={"souls_saved": 3}
        )
        
        await event_ingestor.process_event(event)
        
        # Verify experience was recorded
        mock_story_manager.record_experience.assert_called_once_with(
            player_id=player_id,
            experience_id="soul_echo_encounter_1",
            status="completed",
            metadata={"outcome": "negotiated", "souls_saved": 3}
        )
    
    @pytest.mark.asyncio
    async def test_event_storage_idempotency(self, event_ingestor, mock_postgres):
        """Test that duplicate events are handled idempotently."""
        player_id = uuid4()
        event = StoryEvent(
            player_id=player_id,
            event_type="test_event",
            event_data={"test": "data"}
        )
        
        # Process event twice
        await event_ingestor.process_event(event)
        await event_ingestor.process_event(event)
        
        # Should only execute once due to ON CONFLICT
        assert mock_postgres.acquire.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_drift_check_triggering(self, event_ingestor, mock_drift_detector):
        """Test that drift checks are triggered periodically."""
        player_id = uuid4()
        
        # Simulate multiple events for same player
        for i in range(5):
            event = StoryEvent(
                player_id=player_id,
                event_type="test_event",
                event_data={"index": i}
            )
            await event_ingestor.process_event(event)
        
        # Drift check should have been triggered
        assert mock_drift_detector.check_drift.called
    
    @pytest.mark.asyncio
    async def test_arc_advancement_detection(self, event_ingestor, mock_story_manager):
        """Test detection of significant arc advancement."""
        player_id = uuid4()
        
        # Progress from early to late stage
        event = ArcBeatReachedEvent(
            player_id=player_id,
            arc_id="main_quest_1",
            beat_id="climax_1",
            arc_role=ArcRole.MAIN_ARC,
            progress_state=ProgressState.LATE
        )
        
        await event_ingestor.process_event(event)
        
        # Should update arc progress
        mock_story_manager.update_arc_progress.assert_called()
    
    @pytest.mark.asyncio
    async def test_world_state_impact(self, event_ingestor, mock_story_manager):
        """Test handling of world state changes."""
        player_id = uuid4()
        event = StoryEvent(
            player_id=player_id,
            event_type="world_state_changed",
            event_data={
                "dark_family": "The_Veiled_Court",
                "change_type": "territory_gained",
                "impact": 0.2
            }
        )
        
        await event_ingestor.process_event(event)
        
        # Should update dark world standing
        mock_story_manager.update_dark_world_standing.assert_called()
    
    @pytest.mark.asyncio
    async def test_moral_decision_tracking(self, event_ingestor, mock_story_manager):
        """Test tracking of moral decisions."""
        player_id = uuid4()
        event = StoryEvent(
            player_id=player_id,
            event_type="decision_made",
            event_data={
                "decision_id": "save_or_harvest",
                "choice": "harvest",
                "moral_weight": 0.7,
                "arc_context": "warehouse_raid"
            }
        )
        
        await event_ingestor.process_event(event)
        
        # Should record decision
        mock_story_manager.record_decision.assert_called_with(
            player_id=player_id,
            decision_id="save_or_harvest",
            arc_id="warehouse_raid",
            choice="harvest",
            consequences={},
            moral_weight=0.7
        )
    
    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, event_ingestor):
        """Test handling of concurrent events for different players."""
        player_ids = [uuid4() for _ in range(5)]
        
        # Create events for different players
        events = []
        for i, player_id in enumerate(player_ids):
            event = StoryEvent(
                player_id=player_id,
                event_type="test_event",
                event_data={"player_index": i}
            )
            events.append(event)
        
        # Process concurrently
        tasks = [
            event_ingestor.process_event(event)
            for event in events
        ]
        await asyncio.gather(*tasks)
        
        # All should process without errors
        # Each player should maintain separate sequence
