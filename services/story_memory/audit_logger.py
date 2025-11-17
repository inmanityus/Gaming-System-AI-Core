"""
Story Memory Audit Logger
========================

Provides comprehensive audit logging for all story-related operations.
Ensures compliance and traceability for narrative decisions.
"""

from __future__ import annotations

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
from enum import Enum
import asyncpg
from loguru import logger


class AuditEventType(str, Enum):
    """Types of auditable events in Story Memory."""
    
    # Arc events
    ARC_PROGRESS_UPDATED = "arc_progress_updated"
    ARC_COMPLETED = "arc_completed"
    ARC_ABANDONED = "arc_abandoned"
    
    # Decision events
    DECISION_MADE = "decision_made"
    DECISION_CONSEQUENCE_APPLIED = "decision_consequence_applied"
    
    # Relationship events
    RELATIONSHIP_CHANGED = "relationship_changed"
    RELATIONSHIP_TERMINATED = "relationship_terminated"
    
    # Drift events
    DRIFT_DETECTED = "drift_detected"
    DRIFT_CORRECTED = "drift_corrected"
    
    # Conflict events
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    
    # World state events
    WORLD_STATE_CHANGED = "world_state_changed"
    DARK_WORLD_STANDING_CHANGED = "dark_world_standing_changed"
    
    # Meta events
    STORY_RESET = "story_reset"
    SNAPSHOT_ACCESSED = "snapshot_accessed"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class AuditLogger:
    """
    Handles audit logging for Story Memory System.
    Stores structured audit trail in database.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres = postgres_pool
        self._batch_queue: List[Dict[str, Any]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the audit logger with batch processing."""
        await self._ensure_audit_table()
        self._batch_task = asyncio.create_task(self._batch_processor())
        logger.info("Story Memory Audit Logger started")
    
    async def stop(self):
        """Stop the audit logger, flushing any pending logs."""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining logs
        await self._flush_batch()
        logger.info("Story Memory Audit Logger stopped")
    
    async def log_arc_progress(
        self,
        player_id: UUID,
        arc_id: str,
        old_state: str,
        new_state: str,
        session_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log arc progress change."""
        await self._log_event(
            event_type=AuditEventType.ARC_PROGRESS_UPDATED,
            player_id=player_id,
            session_id=session_id,
            details={
                "arc_id": arc_id,
                "old_state": old_state,
                "new_state": new_state,
                "metadata": metadata or {}
            }
        )
    
    async def log_decision(
        self,
        player_id: UUID,
        decision_id: str,
        choice: str,
        moral_weight: float,
        arc_context: Optional[str] = None,
        session_id: Optional[UUID] = None
    ) -> None:
        """Log a story decision."""
        await self._log_event(
            event_type=AuditEventType.DECISION_MADE,
            player_id=player_id,
            session_id=session_id,
            details={
                "decision_id": decision_id,
                "choice": choice,
                "moral_weight": moral_weight,
                "arc_context": arc_context
            }
        )
    
    async def log_drift_detection(
        self,
        player_id: UUID,
        drift_type: str,
        severity: str,
        metrics: Dict[str, Any],
        correction: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log narrative drift detection."""
        await self._log_event(
            event_type=AuditEventType.DRIFT_DETECTED,
            player_id=player_id,
            details={
                "drift_type": drift_type,
                "severity": severity,
                "metrics": metrics,
                "correction_suggested": correction
            }
        )
    
    async def log_conflict(
        self,
        player_id: UUID,
        conflict_type: str,
        entities_involved: List[str],
        severity: str,
        resolution: Optional[str] = None
    ) -> None:
        """Log narrative conflict."""
        event_type = (
            AuditEventType.CONFLICT_RESOLVED 
            if resolution else 
            AuditEventType.CONFLICT_DETECTED
        )
        
        await self._log_event(
            event_type=event_type,
            player_id=player_id,
            details={
                "conflict_type": conflict_type,
                "entities_involved": entities_involved,
                "severity": severity,
                "resolution": resolution
            }
        )
    
    async def log_relationship_change(
        self,
        player_id: UUID,
        entity_id: str,
        old_score: float,
        new_score: float,
        reason: str,
        session_id: Optional[UUID] = None
    ) -> None:
        """Log relationship score change."""
        await self._log_event(
            event_type=AuditEventType.RELATIONSHIP_CHANGED,
            player_id=player_id,
            session_id=session_id,
            details={
                "entity_id": entity_id,
                "old_score": old_score,
                "new_score": new_score,
                "change": new_score - old_score,
                "reason": reason
            }
        )
    
    async def log_dark_world_standing(
        self,
        player_id: UUID,
        family_id: str,
        old_score: float,
        new_score: float,
        trigger_event: str
    ) -> None:
        """Log Dark World standing change."""
        await self._log_event(
            event_type=AuditEventType.DARK_WORLD_STANDING_CHANGED,
            player_id=player_id,
            details={
                "family_id": family_id,
                "old_standing": old_score,
                "new_standing": new_score,
                "change": new_score - old_score,
                "trigger_event": trigger_event
            }
        )
    
    async def log_snapshot_access(
        self,
        player_id: UUID,
        accessor: str,
        cache_hit: bool,
        latency_ms: float
    ) -> None:
        """Log snapshot access for performance tracking."""
        await self._log_event(
            event_type=AuditEventType.SNAPSHOT_ACCESSED,
            player_id=player_id,
            details={
                "accessor": accessor,
                "cache_hit": cache_hit,
                "latency_ms": latency_ms
            },
            low_priority=True  # Don't block on performance logs
        )
    
    async def log_manual_adjustment(
        self,
        player_id: UUID,
        admin_id: str,
        adjustment_type: str,
        old_value: Any,
        new_value: Any,
        reason: str
    ) -> None:
        """Log manual story state adjustments by admins."""
        await self._log_event(
            event_type=AuditEventType.MANUAL_ADJUSTMENT,
            player_id=player_id,
            details={
                "admin_id": admin_id,
                "adjustment_type": adjustment_type,
                "old_value": old_value,
                "new_value": new_value,
                "reason": reason
            }
        )
    
    async def get_audit_trail(
        self,
        player_id: Optional[UUID] = None,
        event_types: Optional[List[AuditEventType]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail with filtering options.
        """
        query_parts = ["SELECT * FROM story_audit_log WHERE 1=1"]
        params = []
        param_count = 0
        
        if player_id:
            param_count += 1
            query_parts.append(f"AND player_id = ${param_count}")
            params.append(player_id)
        
        if event_types:
            param_count += 1
            query_parts.append(f"AND event_type = ANY(${param_count})")
            params.append([e.value for e in event_types])
        
        if start_time:
            param_count += 1
            query_parts.append(f"AND timestamp >= ${param_count}")
            params.append(start_time)
        
        if end_time:
            param_count += 1
            query_parts.append(f"AND timestamp <= ${param_count}")
            params.append(end_time)
        
        query_parts.append("ORDER BY timestamp DESC")
        param_count += 1
        query_parts.append(f"LIMIT ${param_count}")
        params.append(limit)
        
        query = " ".join(query_parts)
        
        async with self.postgres.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        return [dict(row) for row in rows]
    
    async def _log_event(
        self,
        event_type: AuditEventType,
        player_id: UUID,
        details: Dict[str, Any],
        session_id: Optional[UUID] = None,
        low_priority: bool = False
    ) -> None:
        """Internal method to log an event."""
        event = {
            "event_type": event_type.value,
            "player_id": player_id,
            "session_id": session_id,
            "details": details,
            "timestamp": datetime.utcnow(),
            "low_priority": low_priority
        }
        
        async with self._batch_lock:
            self._batch_queue.append(event)
            
            # Flush immediately for high-priority events
            if not low_priority and len(self._batch_queue) >= 10:
                await self._flush_batch()
    
    async def _batch_processor(self):
        """Background task to periodically flush audit logs."""
        while True:
            try:
                await asyncio.sleep(5)  # Flush every 5 seconds
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audit batch processor: {e}")
    
    async def _flush_batch(self):
        """Flush pending audit logs to database."""
        async with self._batch_lock:
            if not self._batch_queue:
                return
            
            batch = self._batch_queue.copy()
            self._batch_queue.clear()
        
        try:
            async with self.postgres.acquire() as conn:
                # Batch insert
                await conn.executemany(
                    """
                    INSERT INTO story_audit_log 
                        (event_type, player_id, session_id, details, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    [
                        (
                            event["event_type"],
                            event["player_id"],
                            event["session_id"],
                            json.dumps(event["details"]),
                            event["timestamp"]
                        )
                        for event in batch
                    ]
                )
                
            logger.debug(f"Flushed {len(batch)} audit events")
            
        except Exception as e:
            logger.error(f"Failed to flush audit batch: {e}")
            # Re-queue high priority events
            high_priority = [e for e in batch if not e.get("low_priority")]
            if high_priority:
                async with self._batch_lock:
                    self._batch_queue.extend(high_priority)
    
    async def _ensure_audit_table(self):
        """Ensure the audit log table exists."""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS story_audit_log (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    event_type VARCHAR(64) NOT NULL,
                    player_id UUID REFERENCES players(id) ON DELETE SET NULL,
                    session_id UUID,
                    details JSONB NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    
                    -- Indexes for efficient querying
                    INDEX idx_audit_player (player_id),
                    INDEX idx_audit_type (event_type),
                    INDEX idx_audit_timestamp (timestamp),
                    INDEX idx_audit_session (session_id)
                )
            """)


class AuditReport:
    """Generate audit reports from audit logs."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    async def generate_player_report(
        self,
        player_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report for a player."""
        
        # Get all events for the player
        events = await self.audit_logger.get_audit_trail(
            player_id=player_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Analyze events
        event_counts = {}
        decision_summary = {
            "total": 0,
            "moral_trend": [],
            "major_decisions": []
        }
        arc_activity = {}
        drift_incidents = []
        
        for event in events:
            event_type = event["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            details = event["details"]
            
            if event_type == AuditEventType.DECISION_MADE.value:
                decision_summary["total"] += 1
                moral_weight = details.get("moral_weight", 0)
                decision_summary["moral_trend"].append(moral_weight)
                
                if abs(moral_weight) > 0.5:
                    decision_summary["major_decisions"].append({
                        "decision_id": details["decision_id"],
                        "choice": details["choice"],
                        "weight": moral_weight,
                        "timestamp": event["timestamp"]
                    })
            
            elif event_type == AuditEventType.ARC_PROGRESS_UPDATED.value:
                arc_id = details["arc_id"]
                if arc_id not in arc_activity:
                    arc_activity[arc_id] = []
                arc_activity[arc_id].append({
                    "from": details["old_state"],
                    "to": details["new_state"],
                    "timestamp": event["timestamp"]
                })
            
            elif event_type == AuditEventType.DRIFT_DETECTED.value:
                drift_incidents.append({
                    "type": details["drift_type"],
                    "severity": details["severity"],
                    "timestamp": event["timestamp"]
                })
        
        # Calculate moral alignment shift
        moral_shift = None
        if decision_summary["moral_trend"]:
            initial_alignment = sum(decision_summary["moral_trend"][:5]) / min(5, len(decision_summary["moral_trend"]))
            recent_alignment = sum(decision_summary["moral_trend"][-5:]) / min(5, len(decision_summary["moral_trend"]))
            moral_shift = recent_alignment - initial_alignment
        
        return {
            "player_id": str(player_id),
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "event_summary": event_counts,
            "total_events": len(events),
            "decision_analysis": {
                "total_decisions": decision_summary["total"],
                "major_decisions": decision_summary["major_decisions"][:10],
                "moral_alignment_shift": moral_shift
            },
            "arc_engagement": {
                arc_id: {
                    "progress_updates": len(updates),
                    "last_update": updates[-1] if updates else None
                }
                for arc_id, updates in arc_activity.items()
            },
            "narrative_health": {
                "drift_incidents": len(drift_incidents),
                "drift_details": drift_incidents[:5]
            }
        }

