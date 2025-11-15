"""
Engagement telemetry ingester for consuming and storing engagement events.
Implements TEMO-03.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from uuid import UUID

import asyncpg
from pydantic import ValidationError

from .engagement_schemas import (
    NPCInteractionEvent,
    MoralChoiceEvent, 
    SessionMetricsEvent,
    AIRunEvent,
    EventType,
    TimeOfDayBucket,
    CohortDefinition
)

logger = logging.getLogger(__name__)


class TelemetryIngester:
    """Ingests and stores engagement telemetry events."""
    
    def __init__(self, postgres_pool: asyncpg.Pool, redis_client: Any = None):
        self.postgres = postgres_pool
        self.redis = redis_client
        self._event_buffer = []
        self._buffer_size = 100  # Batch size for DB writes
        self._flush_interval = 5  # Seconds
        self._last_flush = datetime.now(timezone.utc)
        self._event_counts = {}  # Track event counts by type
        
    async def ingest_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Ingest a single engagement event.
        Returns True if successful, False otherwise.
        """
        try:
            # Parse event type and create appropriate model
            event = self._parse_event(event_data)
            if not event:
                logger.warning(f"Failed to parse event: {event_data}")
                return False
                
            # Validate privacy requirements
            if not self._validate_privacy(event):
                logger.warning(f"Event failed privacy validation: {event.event_type}")
                return False
                
            # Add to buffer
            self._event_buffer.append(event)
            
            # Flush if buffer is full
            if len(self._event_buffer) >= self._buffer_size:
                await self._flush_buffer()
                
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting event: {e}", exc_info=True)
            return False
    
    def _parse_event(self, event_data: Dict[str, Any]) -> Optional[Union[NPCInteractionEvent, MoralChoiceEvent, SessionMetricsEvent, AIRunEvent]]:
        """Parse raw event data into typed event model."""
        try:
            event_type = event_data.get('event_type')
            
            # Convert string timestamps to datetime objects if needed
            if 'timestamp' in event_data and isinstance(event_data['timestamp'], str):
                event_data['timestamp'] = datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00'))
            if 'session_start' in event_data and isinstance(event_data['session_start'], str):
                event_data['session_start'] = datetime.fromisoformat(event_data['session_start'].replace('Z', '+00:00'))
            if 'session_end' in event_data and isinstance(event_data['session_end'], str):
                event_data['session_end'] = datetime.fromisoformat(event_data['session_end'].replace('Z', '+00:00'))
            if 'run_start' in event_data and isinstance(event_data['run_start'], str):
                event_data['run_start'] = datetime.fromisoformat(event_data['run_start'].replace('Z', '+00:00'))
            if 'run_end' in event_data and isinstance(event_data['run_end'], str):
                event_data['run_end'] = datetime.fromisoformat(event_data['run_end'].replace('Z', '+00:00'))
                
            # Parse based on event type
            if event_type == EventType.NPC_INTERACTION.value:
                return NPCInteractionEvent(**event_data)
            elif event_type == EventType.MORAL_CHOICE.value:
                return MoralChoiceEvent(**event_data)
            elif event_type == EventType.SESSION_METRICS.value:
                # Calculate time of day bucket if not provided
                if 'time_of_day_bucket' not in event_data and 'session_start' in event_data:
                    event_data['time_of_day_bucket'] = self._calculate_time_bucket(event_data['session_start'])
                return SessionMetricsEvent(**event_data)
            elif event_type == EventType.AI_RUN.value:
                return AIRunEvent(**event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None
                
        except ValidationError as e:
            logger.error(f"Validation error parsing event: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing event: {e}", exc_info=True)
            return None
    
    def _calculate_time_bucket(self, timestamp: datetime) -> str:
        """Calculate time of day bucket from timestamp."""
        hour = timestamp.hour
        if 0 <= hour < 6:
            return TimeOfDayBucket.EARLY_MORNING.value
        elif 6 <= hour < 12:
            return TimeOfDayBucket.MORNING.value
        elif 12 <= hour < 18:
            return TimeOfDayBucket.AFTERNOON.value
        elif 18 <= hour < 22:
            return TimeOfDayBucket.EVENING.value
        else:
            return TimeOfDayBucket.LATE_NIGHT.value
    
    def _validate_privacy(self, event: Union[NPCInteractionEvent, MoralChoiceEvent, SessionMetricsEvent, AIRunEvent]) -> bool:
        """
        Validate event meets privacy requirements.
        R-EMO-ADD-002: No individual player tracking in addiction analytics.
        """
        # For now, all events are allowed as they use pseudonymized IDs
        # In production, would add more checks here
        return True
    
    async def _flush_buffer(self) -> None:
        """Flush event buffer to database."""
        if not self._event_buffer:
            return
            
        events_to_store = self._event_buffer.copy()
        self._event_buffer.clear()
        
        try:
            async with self.postgres.acquire() as conn:
                # Use transaction for atomicity
                async with conn.transaction():
                    for event in events_to_store:
                        await self._store_event(conn, event)
                        
            logger.info(f"Flushed {len(events_to_store)} events to database")
            self._last_flush = datetime.now(timezone.utc)
            
        except Exception as e:
            # On error, add events back to buffer
            self._event_buffer.extend(events_to_store)
            logger.error(f"Error flushing buffer: {e}", exc_info=True)
            raise
    
    async def _store_event(self, conn: asyncpg.Connection, event: Union[NPCInteractionEvent, MoralChoiceEvent, SessionMetricsEvent, AIRunEvent]) -> None:
        """Store a single event to database."""
        # Common fields
        base_values = [
            event.session_id,
            event.player_id,
            event.actor_type.value,
            event.event_type.value,
            event.timestamp,
            event.build_id,
            event.environment
        ]
        
        # Type-specific fields
        if isinstance(event, NPCInteractionEvent):
            query = """
                INSERT INTO engagement_events (
                    session_id, player_id, actor_type, event_type, timestamp, build_id, environment,
                    npc_id, interaction_type, choice_id, choice_label, help_harm_flag,
                    location_id, arc_id, experience_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """
            values = base_values + [
                event.npc_id,
                event.interaction_type.value,
                event.choice_id,
                event.choice_label,
                event.help_harm_flag.value,
                event.location_id,
                event.arc_id,
                event.experience_id
            ]
            
        elif isinstance(event, MoralChoiceEvent):
            query = """
                INSERT INTO engagement_events (
                    session_id, player_id, actor_type, event_type, timestamp, build_id, environment,
                    scene_id, options, selected_option_id, decision_latency_ms, num_retries,
                    reloaded_save, arc_id, experience_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """
            # Convert options to JSON
            options_json = json.dumps([opt.model_dump() for opt in event.options])
            values = base_values + [
                event.scene_id,
                options_json,
                event.selected_option_id,
                event.decision_latency_ms,
                event.num_retries,
                event.reloaded_save,
                event.arc_id,
                event.experience_id
            ]
            
        elif isinstance(event, SessionMetricsEvent):
            query = """
                INSERT INTO engagement_events (
                    session_id, player_id, actor_type, event_type, timestamp, build_id, environment,
                    session_start, session_end, total_duration_minutes, time_of_day_bucket,
                    day_of_week, num_sessions_last_7_days, num_sessions_last_24_hours,
                    is_return_session, time_since_last_session_seconds, platform, region
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            """
            values = base_values + [
                event.session_start,
                event.session_end,
                event.total_duration_minutes,
                event.time_of_day_bucket.value,
                event.day_of_week,
                event.num_sessions_last_7_days,
                event.num_sessions_last_24_hours,
                event.is_return_session,
                event.time_since_last_session_seconds,
                event.platform,
                event.region
            ]
            
        elif isinstance(event, AIRunEvent):
            query = """
                INSERT INTO engagement_events (
                    session_id, player_id, actor_type, event_type, timestamp, build_id, environment,
                    ai_run_id, personality_profile, total_npcs_interacted, moral_choices_made,
                    help_harm_ratio, exploration_coverage, run_start, run_end,
                    total_duration_hours, scenario_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """
            values = base_values + [
                event.ai_run_id,
                event.personality_profile,
                event.total_npcs_interacted,
                event.moral_choices_made,
                event.help_harm_ratio,
                event.exploration_coverage,
                event.run_start,
                event.run_end,
                event.total_duration_hours,
                event.scenario_id
            ]
        else:
            raise ValueError(f"Unknown event type: {type(event)}")
            
        await conn.execute(query, *values)
        
        # Track event count
        event_type_str = event.event_type.value
        self._event_counts[event_type_str] = self._event_counts.get(event_type_str, 0) + 1
    
    async def assign_session_cohort(self, session_id: UUID, cohort_def: CohortDefinition) -> None:
        """Assign a session to a cohort for privacy-preserving analytics."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO session_cohorts (session_id, cohort_id, region, age_band, platform)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (session_id) DO UPDATE SET
                    cohort_id = EXCLUDED.cohort_id,
                    region = EXCLUDED.region,
                    age_band = EXCLUDED.age_band,
                    platform = EXCLUDED.platform
                """,
                session_id, cohort_def.cohort_id, cohort_def.region,
                cohort_def.age_band, cohort_def.platform
            )
    
    async def periodic_flush(self) -> None:
        """Periodically flush buffer to database."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                
                # Check if flush is needed
                time_since_flush = (datetime.now(timezone.utc) - self._last_flush).total_seconds()
                if self._event_buffer and time_since_flush >= self._flush_interval:
                    await self._flush_buffer()
                    
            except asyncio.CancelledError:
                # Final flush on shutdown
                await self._flush_buffer()
                raise
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        return {
            "buffer_size": len(self._event_buffer),
            "event_counts": self._event_counts.copy(),
            "last_flush": self._last_flush.isoformat()
        }
