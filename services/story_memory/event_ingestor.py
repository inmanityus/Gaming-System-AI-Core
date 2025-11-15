"""
Event Ingestor - Consumes story events and updates story state.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Any
from uuid import UUID

import asyncpg
from loguru import logger
from nats.aio.client import Client as NATS

from .story_schemas import (
    StoryEvent, ArcBeatReachedEvent, QuestCompletedEvent,
    ExperienceCompletedEvent, RelationshipChangedEvent,
    ArcRole, ProgressState
)
from .story_state_manager import StoryStateManager


class EventIngestor:
    """Ingests story events from various sources and updates story state."""
    
    def __init__(
        self, 
        nats_client: NATS,
        story_state_manager: StoryStateManager,
        postgres_pool: asyncpg.Pool
    ):
        self.nc = nats_client
        self.story_manager = story_state_manager
        self.postgres = postgres_pool
        self._sequence_counters: Dict[str, int] = {}
        
    async def start(self):
        """Start listening for story events."""
        # Subscribe to story event subjects
        await self.nc.subscribe("story.events.arc_beat_reached", self._handle_arc_beat)
        await self.nc.subscribe("story.events.quest_completed", self._handle_quest_completed)
        await self.nc.subscribe("story.events.experience_completed", self._handle_experience_completed)
        await self.nc.subscribe("story.events.relationship_changed", self._handle_relationship_changed)
        await self.nc.subscribe("story.events.decision_made", self._handle_decision_made)
        await self.nc.subscribe("story.events.world_state_changed", self._handle_world_state_changed)
        
        logger.info("Story event ingestor started")
    
    async def _handle_arc_beat(self, msg):
        """Handle arc beat reached events."""
        try:
            data = json.loads(msg.data.decode())
            event = ArcBeatReachedEvent(**data)
            
            # Update arc progress
            await self.story_manager.update_arc_progress(
                player_id=event.player_id,
                arc_id=event.arc_id,
                arc_role=event.arc_role,
                progress_state=self._determine_progress_state(event.beat_id),
                last_beat_id=event.beat_id
            )
            
            # Store event for audit
            await self._store_event(event)
            
            logger.info(f"Processed arc beat: {event.arc_id}/{event.beat_id} for player {event.player_id}")
            
        except Exception as e:
            logger.error(f"Error processing arc beat event: {e}")
    
    async def _handle_quest_completed(self, msg):
        """Handle quest completion events."""
        try:
            data = json.loads(msg.data.decode())
            event = QuestCompletedEvent(**data)
            
            # Store event
            await self._store_event(event)
            
            # Update arc progress if quest is part of an arc
            if event.arc_id:
                # Check if this quest completion advances the arc
                arc_advanced = await self._check_arc_advancement(
                    event.player_id, event.arc_id, event.quest_id
                )
                if arc_advanced:
                    logger.info(f"Quest {event.quest_id} advanced arc {event.arc_id}")
            
            # Track for drift detection
            await self._update_quest_allocation_metrics(
                event.player_id, event.quest_type
            )
            
            logger.info(f"Processed quest completion: {event.quest_id} for player {event.player_id}")
            
        except Exception as e:
            logger.error(f"Error processing quest completed event: {e}")
    
    async def _handle_experience_completed(self, msg):
        """Handle experience completion events."""
        try:
            data = json.loads(msg.data.decode())
            event = ExperienceCompletedEvent(**data)
            
            async with self.postgres.acquire() as conn:
                # Update experience status
                await conn.execute(
                    """
                    UPDATE story_experiences
                    SET status = 'completed',
                        completed_at = $1,
                        emotional_impact = $2
                    WHERE player_id = $3 AND experience_id = $4
                    """,
                    event.timestamp, json.dumps(event.emotional_impact),
                    event.player_id, event.experience_id
                )
            
            await self._store_event(event)
            
            logger.info(f"Processed experience completion: {event.experience_id} for player {event.player_id}")
            
        except Exception as e:
            logger.error(f"Error processing experience completed event: {e}")
    
    async def _handle_relationship_changed(self, msg):
        """Handle relationship change events."""
        try:
            data = json.loads(msg.data.decode())
            event = RelationshipChangedEvent(**data)
            
            # Calculate score delta
            score_delta = event.new_score - event.old_score
            
            # Update relationship
            await self.story_manager.update_relationship(
                player_id=event.player_id,
                entity_id=event.entity_id,
                entity_type=event.entity_type,
                score_delta=score_delta,
                interaction=event.reason
            )
            
            await self._store_event(event)
            
            # Check for significant changes that might trigger story events
            if abs(score_delta) > 20:
                logger.warning(
                    f"Significant relationship change: {event.entity_id} "
                    f"({event.old_score} -> {event.new_score}) for player {event.player_id}"
                )
            
        except Exception as e:
            logger.error(f"Error processing relationship changed event: {e}")
    
    async def _handle_decision_made(self, msg):
        """Handle player decision events."""
        try:
            data = json.loads(msg.data.decode())
            
            # Extract decision data and create StoryDecision
            from .story_schemas import StoryDecision
            
            decision = StoryDecision(
                decision_id=data['decision_id'],
                arc_id=data.get('arc_id'),
                npc_id=data.get('npc_id'),
                choice_label=data['choice_label'],
                outcome_tags=data.get('outcome_tags', []),
                moral_weight=data.get('moral_weight', 0.0),
                timestamp=datetime.fromisoformat(data['timestamp'])
            )
            
            # Record the decision
            await self.story_manager.record_decision(
                player_id=UUID(data['player_id']),
                decision=decision,
                session_id=UUID(data['session_id']) if data.get('session_id') else None
            )
            
            logger.info(f"Processed decision: {decision.decision_id} for player {data['player_id']}")
            
        except Exception as e:
            logger.error(f"Error processing decision made event: {e}")
    
    async def _handle_world_state_changed(self, msg):
        """Handle world state change events for conflict detection."""
        try:
            data = json.loads(msg.data.decode())
            
            # Store for conflict detection
            await self._check_world_story_conflicts(
                player_id=UUID(data['player_id']),
                world_changes=data['changes']
            )
            
        except Exception as e:
            logger.error(f"Error processing world state changed event: {e}")
    
    async def _store_event(self, event: StoryEvent) -> None:
        """Store event for audit and analysis."""
        player_key = str(event.player_id)
        
        # Get next sequence number for this player
        if player_key not in self._sequence_counters:
            # Get max sequence from DB
            async with self.postgres.acquire() as conn:
                max_seq = await conn.fetchval(
                    """
                    SELECT COALESCE(MAX(sequence_num), 0)
                    FROM story_events
                    WHERE player_id = $1
                    """,
                    event.player_id
                )
                self._sequence_counters[player_key] = max_seq
        
        self._sequence_counters[player_key] += 1
        sequence_num = self._sequence_counters[player_key]
        
        async with self.postgres.acquire() as conn:
            # Use ON CONFLICT to handle duplicate events
            await conn.execute(
                """
                INSERT INTO story_events
                    (player_id, session_id, event_type, event_data, 
                     sequence_num, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (player_id, sequence_num) DO NOTHING
                """,
                event.player_id, event.session_id, event.event_type,
                json.dumps(event.event_data), sequence_num, event.timestamp
            )
    
    def _determine_progress_state(self, beat_id: str) -> ProgressState:
        """Determine progress state from beat ID."""
        # Simple heuristic - should be replaced with actual beat mapping
        if 'intro' in beat_id.lower() or 'start' in beat_id.lower():
            return ProgressState.EARLY
        elif 'climax' in beat_id.lower() or 'finale' in beat_id.lower():
            return ProgressState.LATE
        elif 'complete' in beat_id.lower() or 'end' in beat_id.lower():
            return ProgressState.COMPLETED
        else:
            return ProgressState.MID
    
    async def _check_arc_advancement(
        self, 
        player_id: UUID, 
        arc_id: str, 
        quest_id: str
    ) -> bool:
        """Check if quest completion advances an arc."""
        # This would check quest metadata to see if it's a key arc quest
        # For now, simple placeholder
        return 'main' in quest_id.lower() or 'arc' in quest_id.lower()
    
    async def _update_quest_allocation_metrics(
        self,
        player_id: UUID,
        quest_type: str
    ) -> None:
        """Update quest allocation metrics for drift detection."""
        # This would update time-windowed metrics
        # Used by drift detector to identify off-theme content
        pass
    
    async def _check_world_story_conflicts(
        self,
        player_id: UUID,
        world_changes: Dict[str, Any]
    ) -> None:
        """Check for conflicts between world state and story memory."""
        # This would cross-check world changes against story memory
        # e.g., NPC marked dead in world but alive in story
        pass
