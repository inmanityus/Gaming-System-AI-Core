#!/usr/bin/env python3
"""
Database Service
PostgreSQL integration for persistent report storage.

P0-5 CRITICAL FIX: Replaces in-memory storage with PostgreSQL to prevent data loss.
"""

import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    PostgreSQL database service for report persistence using psycopg3.
    
    P0-5: Provides durable storage to prevent data loss on restart.
    Uses psycopg3 for better Windows compatibility (no compilation required).
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5443,
        database: str = 'body_broker_qa',
        user: str = 'postgres',
        password: str = None,
        min_pool_size: int = 2,
        max_pool_size: int = 10
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password or ''
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool: Optional[AsyncConnectionPool] = None
        
        # Build connection string
        self.conninfo = f"host={host} port={port} dbname={database} user={user}"
        if self.password:
            self.conninfo += f" password={self.password}"
        
        logger.info(f"Database service configured: {host}:{port}/{database}")
    
    async def connect(self) -> None:
        """Initialize connection pool."""
        try:
            self._pool = AsyncConnectionPool(
                conninfo=self.conninfo,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
                timeout=30,
                open=False  # Don't open immediately to allow graceful degradation
            )
            
            # Try to open pool, but don't fail if DB unavailable
            try:
                await self._pool.open(wait=True, timeout=5)
                logger.info(f"Database pool created: {self.min_pool_size}-{self.max_pool_size} connections")
            except Exception as e:
                logger.warning(f"Database connection delayed: {e}")
                # Pool exists but not connected - will retry on first use
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}", exc_info=True)
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database pool closed")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self._pool.connection() as conn:
                result = await conn.execute('SELECT 1')
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def create_report(
        self,
        report_id: str,
        test_run_id: str,
        game_title: str,
        game_version: Optional[str],
        test_environment: str,
        format: str,
        status: str = 'queued'
    ) -> Dict[str, Any]:
        """Create new report record."""
        try:
            async with self._pool.connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO reports (
                        id, test_run_id, game_title, game_version,
                        test_environment, format, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (report_id, test_run_id, game_title, game_version,
                     test_environment, format, status, datetime.utcnow())
                )
            
            logger.info(f"Created report record: {report_id}")
            return await self.get_report(report_id)
            
        except Exception as e:
            logger.error(f"Failed to create report {report_id}: {e}", exc_info=True)
            raise
    
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        try:
            async with self._pool.connection() as conn:
                # Use dict_row factory for dict results
                conn.row_factory = dict_row
                
                cursor = await conn.execute(
                    """
                    SELECT id, test_run_id, game_title, game_version,
                           test_environment, format, status, s3_bucket, s3_key,
                           file_size_bytes, created_at, started_at, completed_at,
                           error_message, duration_seconds, report_data
                    FROM reports
                    WHERE id = %s
                    """,
                    (report_id,)
                )
                
                row = await cursor.fetchone()
            
            if not row:
                return None
            
            report = dict(row)
            
            # Convert datetime to ISO format
            for field in ['created_at', 'started_at', 'completed_at']:
                if report.get(field):
                    report[field] = report[field].isoformat()
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}", exc_info=True)
            raise
    
    async def update_report(
        self,
        report_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update report fields."""
        try:
            # Build UPDATE query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'report_data' and value is not None:
                    # Convert dict to JSON for JSONB
                    set_clauses.append(f"{key} = %s::jsonb")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            values.append(report_id)
            query = f"""
                UPDATE reports
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            
            async with self._pool.connection() as conn:
                await conn.execute(query, tuple(values))
            
            logger.debug(f"Updated report {report_id}: {list(updates.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {e}", exc_info=True)
            raise
    
    async def list_reports(
        self,
        game_title: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List reports with filtering and pagination."""
        try:
            # Build query with filters
            where_clauses = []
            values = []
            
            if game_title:
                where_clauses.append("game_title = %s")
                values.append(game_title)
            
            if status:
                where_clauses.append("status = %s")
                values.append(status)
            
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # Add pagination
            values.extend([limit, offset])
            
            query = f"""
                SELECT id, test_run_id, game_title, game_version,
                       test_environment, format, status, s3_key,
                       file_size_bytes, created_at, completed_at,
                       error_message, duration_seconds
                FROM reports
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            
            async with self._pool.connection() as conn:
                conn.row_factory = dict_row
                cursor = await conn.execute(query, tuple(values))
                rows = await cursor.fetchall()
            
            # Convert rows to dicts with formatted dates
            reports = []
            for row in rows:
                report = dict(row)
                # Convert datetime to ISO format
                for field in ['created_at', 'started_at', 'completed_at']:
                    if report.get(field):
                        report[field] = report[field].isoformat()
                reports.append(report)
            
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports: {e}", exc_info=True)
            raise
    
    async def log_event(
        self,
        report_id: str,
        event_type: str,
        message: str = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Log event to audit trail."""
        try:
            async with self._pool.connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO report_events (report_id, event_type, message, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (report_id, event_type, message,
                     json.dumps(metadata) if metadata else None,
                     datetime.utcnow())
                )
            
            logger.debug(f"Logged event for report {report_id}: {event_type}")
            
        except Exception as e:
            # Don't fail the request if event logging fails
            logger.error(f"Failed to log event for {report_id}: {e}")
    
    async def delete_report(self, report_id: str) -> bool:
        """Delete report and associated artifacts."""
        try:
            async with self._pool.connection() as conn:
                await conn.execute(
                    "DELETE FROM reports WHERE id = %s",
                    (report_id,)
                )
            
            logger.info(f"Deleted report: {report_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}", exc_info=True)
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            async with self._pool.connection() as conn:
                conn.row_factory = dict_row
                cursor = await conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_reports,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed,
                        COUNT(*) FILTER (WHERE status = 'processing') as processing,
                        COUNT(*) FILTER (WHERE status = 'queued') as queued,
                        AVG(duration_seconds) FILTER (WHERE status = 'completed') as avg_duration
                    FROM reports
                    """
                )
                stats_row = await cursor.fetchone()
            
            return dict(stats_row) if stats_row else {}
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            raise

