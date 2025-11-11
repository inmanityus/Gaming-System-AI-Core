"""
Authentication API Routes
Handles user login, logout, and session management.
"""

from typing import Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from session_manager import SessionManager, get_session_manager, UserSession
from session_auth import verify_user_session

router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    """Login request."""
    user_id: str = Field(..., description="User ID (UUID format)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional session metadata")

class LoginResponse(BaseModel):
    """Login response."""
    session_id: str
    user_id: str
    message: str

class LogoutResponse(BaseModel):
    """Logout response."""
    success: bool
    message: str

class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    user_id: str
    created_at: str
    last_accessed: str
    is_active: bool

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Create a new user session.
    
    Sessions have NO time-based expiration and last until explicit logout.
    
    Returns:
        session_id: Use this as Bearer token in Authorization header
    """
    try:
        user_id = UUID(request.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format (must be UUID)")
    
    # Create session
    session_id = await session_manager.create_session(user_id, request.metadata)
    
    return LoginResponse(
        session_id=session_id,
        user_id=str(user_id),
        message="Login successful. Use session_id as Bearer token."
    )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    session: UserSession = Depends(verify_user_session),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Logout current session.
    
    Requires: Authorization header with valid session_id
    """
    success = await session_manager.logout(session.session_id)
    
    if success:
        return LogoutResponse(
            success=True,
            message="Logout successful"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to logout")

@router.get("/session", response_model=SessionInfo)
async def get_session_info(
    session: UserSession = Depends(verify_user_session)
):
    """
    Get current session information.
    
    Requires: Authorization header with valid session_id
    """
    return SessionInfo(
        session_id=session.session_id,
        user_id=str(session.user_id),
        created_at=session.created_at.isoformat(),
        last_accessed=session.last_accessed.isoformat(),
        is_active=session.is_active
    )

@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    session: UserSession = Depends(verify_user_session),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get all active sessions for current user.
    
    Requires: Authorization header with valid session_id
    """
    sessions = await session_manager.get_user_sessions(session.user_id)
    
    return [
        SessionInfo(
            session_id=s.session_id,
            user_id=str(s.user_id),
            created_at=s.created_at.isoformat(),
            last_accessed=s.last_accessed.isoformat(),
            is_active=s.is_active
        )
        for s in sessions
    ]

@router.post("/sessions/{session_id}/logout", response_model=LogoutResponse)
async def logout_specific_session(
    session_id: str,
    current_session: UserSession = Depends(verify_user_session),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Logout a specific session (must be your own session).
    
    Requires: Authorization header with valid session_id
    """
    # Verify session belongs to current user
    target_session = await session_manager.validate_session(session_id)
    
    if not target_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if target_session.user_id != current_session.user_id:
        raise HTTPException(status_code=403, detail="Cannot logout another user's session")
    
    success = await session_manager.logout(session_id)
    
    if success:
        return LogoutResponse(
            success=True,
            message=f"Session {session_id} logged out"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to logout session")

@router.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "authentication"}

