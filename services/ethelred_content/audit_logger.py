"""
Content Governance Audit Logger
================================

Provides comprehensive audit logging for all content governance operations
to satisfy compliance and legal requirements.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

import asyncpg
from loguru import logger
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of audit events."""
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_OVERRIDE = "policy_override"
    PROFILE_CHANGED = "profile_changed"
    VIOLATION_DETECTED = "violation_detected"
    CONTENT_BLOCKED = "content_blocked"
    CONTENT_MODIFIED = "content_modified"
    COMPLIANCE_EXPORT = "compliance_export"


class AuditEvent(BaseModel):
    """Structured audit event."""
    event_id: UUID = Field(default_factory=UUID)
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Who
    player_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    admin_id: Optional[str] = None  # For admin actions
    service_name: str = "content_governance"
    
    # What
    action: str
    resource_type: str  # "policy", "profile", "content"
    resource_id: Optional[str] = None
    
    # Details
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Compliance
    compliance_tags: List[str] = Field(default_factory=list)
    retention_days: int = 365  # Default 1 year


class ContentGovernanceAuditLogger:
    """
    Handles audit logging for content governance with compliance focus.
    
    Features:
    - Immutable audit trail in PostgreSQL
    - Structured events for easy querying
    - Compliance-ready export formats
    - Automatic retention management
    """
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.pool: Optional[asyncpg.Pool] = None
        
        # Buffer for batch inserts
        self._event_buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Initialize the audit logger."""
        self.pool = await asyncpg.create_pool(self.postgres_url)
        await self._ensure_audit_table()
        
        # Start background flusher
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
        logger.info("Content Governance Audit Logger started")
    
    async def stop(self) -> None:
        """Stop the audit logger."""
        # Final flush
        await self._flush_buffer()
        
        if self._flush_task:
            self._flush_task.cancel()
        
        if self.pool:
            await self.pool.close()
        
        logger.info("Content Governance Audit Logger stopped")
    
    async def _ensure_audit_table(self) -> None:
        """Ensure audit table exists."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS content_governance_audit (
                    event_id UUID PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    
                    -- Actor
                    player_id UUID,
                    session_id UUID,
                    admin_id VARCHAR(255),
                    service_name VARCHAR(100) NOT NULL,
                    
                    -- Action
                    action TEXT NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    resource_id TEXT,
                    
                    -- State
                    before_state JSONB,
                    after_state JSONB,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    
                    -- Compliance
                    compliance_tags TEXT[],
                    retention_days INTEGER NOT NULL DEFAULT 365,
                    expires_at TIMESTAMP NOT NULL,
                    
                    -- Indexes
                    INDEX idx_audit_timestamp (timestamp),
                    INDEX idx_audit_player (player_id),
                    INDEX idx_audit_session (session_id),
                    INDEX idx_audit_type (event_type),
                    INDEX idx_audit_compliance (compliance_tags),
                    INDEX idx_audit_expires (expires_at)
                )
            """)
    
    async def log_policy_change(
        self,
        player_id: UUID,
        action: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        admin_id: Optional[str] = None,
        session_id: Optional[UUID] = None,
    ) -> None:
        """Log a policy change event."""
        event = AuditEvent(
            event_type=AuditEventType.POLICY_UPDATED,
            player_id=player_id,
            session_id=session_id,
            admin_id=admin_id,
            action=action,
            resource_type="policy",
            resource_id=str(player_id),
            before_state=before,
            after_state=after,
            compliance_tags=["policy_change", "gdpr_relevant"],
        )
        
        await self._add_event(event)
        
        logger.info(f"Audit: Policy change for player {player_id}: {action}")
    
    async def log_profile_change(
        self,
        player_id: UUID,
        old_profile: str,
        new_profile: str,
        reason: str,
        admin_id: Optional[str] = None,
    ) -> None:
        """Log a content profile change."""
        event = AuditEvent(
            event_type=AuditEventType.PROFILE_CHANGED,
            player_id=player_id,
            admin_id=admin_id,
            action=f"Changed profile from {old_profile} to {new_profile}",
            resource_type="profile",
            resource_id=new_profile,
            before_state={"profile": old_profile},
            after_state={"profile": new_profile},
            metadata={"reason": reason},
            compliance_tags=["profile_change", "content_settings"],
        )
        
        await self._add_event(event)
    
    async def log_violation(
        self,
        violation: Dict[str, Any],
        session_id: UUID,
        player_id: UUID,
        action_taken: str,
    ) -> None:
        """Log a content violation event."""
        event = AuditEvent(
            event_type=AuditEventType.VIOLATION_DETECTED,
            player_id=player_id,
            session_id=session_id,
            action=f"Content violation: {violation.get('category')}",
            resource_type="content",
            resource_id=violation.get('content_id'),
            after_state=violation,
            metadata={
                "action_taken": action_taken,
                "severity": violation.get('severity'),
                "evidence_refs": violation.get('evidence_refs', []),
            },
            compliance_tags=["violation", violation.get('category', 'unknown')],
            retention_days=730,  # 2 years for violations
        )
        
        await self._add_event(event)
    
    async def log_content_moderation(
        self,
        session_id: UUID,
        player_id: UUID,
        content_type: str,
        action: str,
        details: Dict[str, Any],
    ) -> None:
        """Log content moderation action."""
        event_type = (
            AuditEventType.CONTENT_BLOCKED 
            if action == "blocked" 
            else AuditEventType.CONTENT_MODIFIED
        )
        
        event = AuditEvent(
            event_type=event_type,
            session_id=session_id,
            player_id=player_id,
            action=f"Content {action}: {content_type}",
            resource_type="content",
            metadata=details,
            compliance_tags=["moderation", content_type],
        )
        
        await self._add_event(event)
    
    async def _add_event(self, event: AuditEvent) -> None:
        """Add event to buffer for batch insertion."""
        async with self._buffer_lock:
            self._event_buffer.append(event)
            
            # Flush if buffer is large
            if len(self._event_buffer) >= 100:
                await self._flush_buffer()
    
    async def _flush_buffer(self) -> None:
        """Flush event buffer to database."""
        async with self._buffer_lock:
            if not self._event_buffer:
                return
            
            events = self._event_buffer[:]
            self._event_buffer.clear()
        
        try:
            async with self.pool.acquire() as conn:
                # Prepare batch insert
                values = []
                for event in events:
                    expires_at = event.timestamp + timedelta(days=event.retention_days)
                    values.append((
                        event.event_id,
                        event.event_type,
                        event.timestamp,
                        event.player_id,
                        event.session_id,
                        event.admin_id,
                        event.service_name,
                        event.action,
                        event.resource_type,
                        event.resource_id,
                        json.dumps(event.before_state) if event.before_state else None,
                        json.dumps(event.after_state) if event.after_state else None,
                        json.dumps(event.metadata),
                        event.compliance_tags,
                        event.retention_days,
                        expires_at,
                    ))
                
                # Batch insert
                await conn.executemany(
                    """
                    INSERT INTO content_governance_audit (
                        event_id, event_type, timestamp,
                        player_id, session_id, admin_id, service_name,
                        action, resource_type, resource_id,
                        before_state, after_state, metadata,
                        compliance_tags, retention_days, expires_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    """,
                    values
                )
                
                logger.debug(f"Flushed {len(events)} audit events to database")
        
        except Exception as e:
            logger.error(f"Failed to flush audit events: {e}")
            # Re-add to buffer for retry
            async with self._buffer_lock:
                self._event_buffer.extend(events)
    
    async def _periodic_flush(self) -> None:
        """Periodically flush the event buffer."""
        while True:
            await asyncio.sleep(10)  # Flush every 10 seconds
            await self._flush_buffer()
    
    async def export_for_compliance(
        self,
        start_date: datetime,
        end_date: datetime,
        player_id: Optional[UUID] = None,
        event_types: Optional[List[AuditEventType]] = None,
        compliance_tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Export audit data for compliance review.
        
        Returns events in a format suitable for ESRB/PEGI review.
        """
        query = """
            SELECT 
                event_id, event_type, timestamp,
                player_id, session_id, action,
                resource_type, resource_id,
                before_state, after_state, metadata,
                compliance_tags
            FROM content_governance_audit
            WHERE timestamp BETWEEN $1 AND $2
        """
        
        params = [start_date, end_date]
        conditions = []
        
        if player_id:
            conditions.append(f"player_id = ${len(params) + 1}")
            params.append(player_id)
        
        if event_types:
            conditions.append(f"event_type = ANY(${len(params) + 1})")
            params.append(event_types)
        
        if compliance_tags:
            conditions.append(f"compliance_tags && ${len(params) + 1}")
            params.append(compliance_tags)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        # Format for export
        events = []
        for row in rows:
            events.append({
                "event_id": str(row["event_id"]),
                "event_type": row["event_type"],
                "timestamp": row["timestamp"].isoformat(),
                "player_id": str(row["player_id"]) if row["player_id"] else None,
                "session_id": str(row["session_id"]) if row["session_id"] else None,
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "before_state": json.loads(row["before_state"]) if row["before_state"] else None,
                "after_state": json.loads(row["after_state"]) if row["after_state"] else None,
                "metadata": json.loads(row["metadata"]),
                "compliance_tags": row["compliance_tags"],
            })
        
        logger.info(
            f"Exported {len(events)} audit events for compliance "
            f"(date range: {start_date} to {end_date})"
        )
        
        return events
    
    async def cleanup_expired(self) -> int:
        """Remove expired audit records per retention policy."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM content_governance_audit WHERE expires_at < $1",
                datetime.utcnow()
            )
            
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Cleaned up {count} expired audit records")
            
            return count


# Import at end to avoid circular imports
from datetime import timedelta
