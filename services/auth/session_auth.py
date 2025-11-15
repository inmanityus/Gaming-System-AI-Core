"""
Session Authentication Middleware
FastAPI dependencies for session-based authentication.
"""

from typing import Optional
from uuid import UUID
from fastapi import Header, HTTPException, Depends

from .session_manager import SessionManager, get_session_manager, UserSession

async def verify_user_session(
    authorization: Optional[str] = Header(None),
    session_manager: SessionManager = Depends(get_session_manager)
) -> UserSession:
    """
    Verify user session from Authorization header.
    
    Header format: "Bearer <session_id>"
    
    Returns:
        UserSession if valid
    
    Raises:
        HTTPException 401 if invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Format: 'Bearer <session_id>'"
        )
    
    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: 'Bearer <session_id>'"
        )
    
    session_id = parts[1]
    
    # Validate session
    session = await session_manager.validate_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please log in again."
        )
    
    return session

async def get_current_user_id(session: UserSession = Depends(verify_user_session)) -> UUID:
    """
    Extract user ID from validated session.
    
    Use this dependency to get authenticated user ID in endpoints.
    
    Example:
        @router.get("/my-data")
        async def get_my_data(user_id: UUID = Depends(get_current_user_id)):
            # user_id is authenticated user's ID
            return fetch_user_data(user_id)
    """
    return session.user_id

async def require_user_session(
    authorization: Optional[str] = Header(None),
    session_manager: SessionManager = Depends(get_session_manager)
) -> bool:
    """
    Simple session requirement (returns bool for _auth pattern).
    
    Use this for endpoints that just need to verify user is logged in.
    
    Example:
        @router.post("/action")
        async def action(_auth: bool = Depends(require_user_session)):
            # User is authenticated
            return do_action()
    """
    await verify_user_session(authorization, session_manager)
    return True

