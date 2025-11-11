"""
Authentication Service
Session-based user authentication with no time limits.
"""

from .session_manager import SessionManager, UserSession, get_session_manager
from .session_auth import verify_user_session, get_current_user_id, require_user_session
from .rate_limiter import limiter, get_rate_limit, rate_limit_exceeded_handler

__all__ = [
    'SessionManager',
    'UserSession',
    'get_session_manager',
    'verify_user_session',
    'get_current_user_id',
    'require_user_session',
    'limiter',
    'get_rate_limit',
    'rate_limit_exceeded_handler',
]

