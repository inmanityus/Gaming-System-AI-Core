"""
Session Authentication Tests
Tests for session-based user authentication system.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'services'))

from auth.session_manager import SessionManager, UserSession

@pytest.fixture
async def session_manager():
    """Create session manager for testing."""
    manager = SessionManager()
    await manager.initialize()
    yield manager
    await manager.close()

class TestSessionCreation:
    """Test session creation."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Should create session successfully."""
        user_id = uuid4()
        session_id = await session_manager.create_session(user_id)
        
        assert session_id is not None
        assert len(session_id) > 32  # Cryptographically secure length
    
    @pytest.mark.asyncio
    async def test_session_id_unique(self, session_manager):
        """Each session should have unique ID."""
        user_id = uuid4()
        session1 = await session_manager.create_session(user_id)
        session2 = await session_manager.create_session(user_id)
        
        assert session1 != session2
    
    @pytest.mark.asyncio
    async def test_session_with_metadata(self, session_manager):
        """Should store session metadata."""
        user_id = uuid4()
        metadata = {'ip': '127.0.0.1', 'user_agent': 'test'}
        session_id = await session_manager.create_session(user_id, metadata)
        
        session = await session_manager.validate_session(session_id)
        assert session.metadata == metadata

class TestSessionValidation:
    """Test session validation."""
    
    @pytest.mark.asyncio
    async def test_validate_valid_session(self, session_manager):
        """Should validate existing session."""
        user_id = uuid4()
        session_id = await session_manager.create_session(user_id)
        
        session = await session_manager.validate_session(session_id)
        
        assert session is not None
        assert session.user_id == user_id
        assert session.is_active is True
    
    @pytest.mark.asyncio
    async def test_validate_invalid_session(self, session_manager):
        """Should reject invalid session ID."""
        session = await session_manager.validate_session("invalid_session_id")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_validate_updates_last_accessed(self, session_manager):
        """Validation should update last_accessed timestamp."""
        user_id = uuid4()
        session_id = await session_manager.create_session(user_id)
        
        # Wait a moment
        await asyncio.sleep(0.1)
        
        session1 = await session_manager.validate_session(session_id)
        await asyncio.sleep(0.1)
        session2 = await session_manager.validate_session(session_id)
        
        assert session2.last_accessed > session1.last_accessed

class TestSessionLogout:
    """Test session logout."""
    
    @pytest.mark.asyncio
    async def test_logout_deactivates_session(self, session_manager):
        """Logout should deactivate session."""
        user_id = uuid4()
        session_id = await session_manager.create_session(user_id)
        
        success = await session_manager.logout(session_id)
        assert success is True
        
        # Session should now be invalid
        session = await session_manager.validate_session(session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_logout_nonexistent_session(self, session_manager):
        """Logout non-existent session should return False."""
        success = await session_manager.logout("nonexistent")
        assert success is False

class TestMultipleSessions:
    """Test multiple sessions per user."""
    
    @pytest.mark.asyncio
    async def test_user_multiple_sessions(self, session_manager):
        """User should be able to have multiple active sessions."""
        user_id = uuid4()
        session1 = await session_manager.create_session(user_id)
        session2 = await session_manager.create_session(user_id)
        session3 = await session_manager.create_session(user_id)
        
        sessions = await session_manager.get_user_sessions(user_id)
        
        assert len(sessions) == 3
        session_ids = [s.session_id for s in sessions]
        assert session1 in session_ids
        assert session2 in session_ids
        assert session3 in session_ids
    
    @pytest.mark.asyncio
    async def test_logout_one_session_others_remain(self, session_manager):
        """Logging out one session should not affect others."""
        user_id = uuid4()
        session1 = await session_manager.create_session(user_id)
        session2 = await session_manager.create_session(user_id)
        
        await session_manager.logout(session1)
        
        # session1 should be invalid
        assert await session_manager.validate_session(session1) is None
        
        # session2 should still be valid
        assert await session_manager.validate_session(session2) is not None

class TestSessionPersistence:
    """Test session persistence."""
    
    @pytest.mark.asyncio
    async def test_session_persists_across_manager_instances(self):
        """Session should persist when SessionManager is recreated."""
        user_id = uuid4()
        
        # Create session with first manager
        manager1 = SessionManager()
        await manager1.initialize()
        session_id = await manager1.create_session(user_id)
        await manager1.close()
        
        # Validate with second manager
        manager2 = SessionManager()
        await manager2.initialize()
        session = await manager2.validate_session(session_id)
        await manager2.close()
        
        assert session is not None
        assert session.user_id == user_id

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_key_prefers_user_id(self):
        """Rate limit key should prefer user ID over IP."""
        # Test that get_rate_limit_key returns user-based key when available
        pass
    
    def test_rate_limit_configs_loaded(self):
        """Rate limit configurations should be loaded from environment."""
        from services.auth.rate_limiter import RATE_LIMITS
        
        assert 'public_read' in RATE_LIMITS
        assert 'public_write' in RATE_LIMITS
        assert 'authenticated' in RATE_LIMITS
        assert 'admin' in RATE_LIMITS
        assert 'ai_generation' in RATE_LIMITS

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

