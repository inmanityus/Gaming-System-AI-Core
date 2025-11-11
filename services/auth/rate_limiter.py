"""
Rate Limiting Middleware
Provides rate limiting for all public endpoints using slowapi.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Optional

def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key - prefers user ID from session over IP address.
    
    Priority:
    1. User ID from session (if authenticated)
    2. IP address (fallback for unauthenticated requests)
    """
    # Try to get user ID from request state (set by session auth)
    if hasattr(request.state, 'user_id'):
        return f"user:{request.state.user_id}"
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"

# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[os.getenv('RATE_LIMIT_DEFAULT', "100/minute")]
)

# Rate limit configurations
RATE_LIMITS = {
    'public_read': os.getenv('RATE_LIMIT_PUBLIC_READ', "200/minute"),
    'public_write': os.getenv('RATE_LIMIT_PUBLIC_WRITE', "50/minute"),
    'authenticated': os.getenv('RATE_LIMIT_AUTHENTICATED', "500/minute"),
    'admin': os.getenv('RATE_LIMIT_ADMIN', "1000/minute"),
    'ai_generation': os.getenv('RATE_LIMIT_AI_GEN', "10/minute"),
}

def get_rate_limit(endpoint_type: str = 'public_read') -> str:
    """
    Get rate limit for specific endpoint type.
    
    Args:
        endpoint_type: Type of endpoint (public_read, public_write, authenticated, admin, ai_generation)
    
    Returns:
        Rate limit string (e.g., "100/minute")
    """
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS['public_read'])

# Exception handler for rate limit exceeded
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded exceptions."""
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Please try again later. (Limit: {exc.detail})"
    )

