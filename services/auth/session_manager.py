"""
Session-Based User Authentication System
Provides per-user session authentication with no time limits.
"""

import os
import secrets
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import asyncpg
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """User session data."""
    session_id: str
    user_id: UUID
    created_at: datetime
    last_accessed: datetime
    metadata: Dict[str, Any]
    is_active: bool = True

class SessionManager:
    """
    Manages user sessions with no expiration.
    
    Features:
    - Per-user session tracking
    - No time-based expiration (sessions last forever unless explicitly logged out)
    - PostgreSQL persistence
    - Async-safe operations
    - Session metadata storage
    """
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self._init_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize database connection and schema."""
        async with self._init_lock:
            if self.db_pool is not None:
                return
            
            # Get database credentials
            password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD')
            if not password:
                raise RuntimeError("POSTGRES_PASSWORD or DB_PASSWORD environment variable required")
            
            # Create connection pool
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', '5443')),
                database=os.getenv('POSTGRES_DB', 'gaming_system_ai_core'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=password,
                min_size=2,
                max_size=10
            )
            
            # Create sessions table if not exists
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    CREATE SCHEMA IF NOT EXISTS auth;
                    
                    CREATE TABLE IF NOT EXISTS auth.user_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id UUID NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON auth.user_sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON auth.user_sessions(is_active);
                ''')
            
            logger.info("✅ Session Manager initialized")
    
    def generate_session_id(self) -> str:
        """Generate cryptographically secure session ID."""
        return secrets.token_urlsafe(32)
    
    async def create_session(
        self,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: User UUID
            metadata: Optional session metadata
        
        Returns:
            session_id: New session ID (use as bearer token)
        """
        if self.db_pool is None:
            await self.initialize()
        
        session_id = self.generate_session_id()
        now = datetime.now()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO auth.user_sessions (session_id, user_id, created_at, last_accessed, metadata, is_active)
                VALUES ($1, $2, $3, $4, $5, TRUE)
            ''', session_id, user_id, now, now, metadata or {})
        
        logger.info(f"✅ Created session for user {user_id}")
        return session_id
    
    async def validate_session(self, session_id: str) -> Optional[UserSession]:
        """
        Validate session and return session data.
        
        Args:
            session_id: Session ID to validate
        
        Returns:
            UserSession if valid, None if invalid
        """
        if self.db_pool is None:
            await self.initialize()
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow('''
                UPDATE auth.user_sessions
                SET last_accessed = NOW()
                WHERE session_id = $1 AND is_active = TRUE
                RETURNING session_id, user_id, created_at, last_accessed, metadata, is_active
            ''', session_id)
            
            if not row:
                return None
            
            return UserSession(
                session_id=row['session_id'],
                user_id=row['user_id'],
                created_at=row['created_at'],
                last_accessed=row['last_accessed'],
                metadata=row['metadata'],
                is_active=row['is_active']
            )
    
    async def logout(self, session_id: str) -> bool:
        """
        Logout user (deactivate session).
        
        Args:
            session_id: Session ID to deactivate
        
        Returns:
            True if session was deactivated, False if not found
        """
        if self.db_pool is None:
            await self.initialize()
        
        async with self.db_pool.acquire() as conn:
            result = await conn.execute('''
                UPDATE auth.user_sessions
                SET is_active = FALSE
                WHERE session_id = $1 AND is_active = TRUE
            ''', session_id)
            
            # Check if any rows were updated
            rows_affected = int(result.split()[-1]) if result else 0
            
            if rows_affected > 0:
                logger.info(f"✅ Session {session_id} logged out")
                return True
            return False
    
    async def get_user_sessions(self, user_id: UUID) -> list[UserSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User UUID
        
        Returns:
            List of active sessions
        """
        if self.db_pool is None:
            await self.initialize()
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT session_id, user_id, created_at, last_accessed, metadata, is_active
                FROM auth.user_sessions
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY last_accessed DESC
            ''', user_id)
            
            return [
                UserSession(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    created_at=row['created_at'],
                    last_accessed=row['last_accessed'],
                    metadata=row['metadata'],
                    is_active=row['is_active']
                )
                for row in rows
            ]
    
    async def cleanup_inactive_sessions(self, days_inactive: int = 90) -> int:
        """
        Optional cleanup of very old inactive sessions.
        
        Args:
            days_inactive: Number of days without access before cleanup
        
        Returns:
            Number of sessions cleaned up
        """
        if self.db_pool is None:
            await self.initialize()
        
        async with self.db_pool.acquire() as conn:
            result = await conn.execute('''
                DELETE FROM auth.user_sessions
                WHERE is_active = FALSE
                  AND last_accessed < NOW() - INTERVAL '%s days'
            ''' % days_inactive)
            
            rows_deleted = int(result.split()[-1]) if result else 0
            logger.info(f"🗑️ Cleaned up {rows_deleted} inactive sessions")
            return rows_deleted
    
    async def close(self):
        """Close database connection."""
        if self.db_pool:
            await self.db_pool.close()

# Global instance
_session_manager: Optional[SessionManager] = None

async def get_session_manager() -> SessionManager:
    """Get or create global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
        await _session_manager.initialize()
    return _session_manager

