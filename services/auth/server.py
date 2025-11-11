"""
Authentication Service Server
Standalone FastAPI service for authentication and session management.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from auth_routes import router as auth_router
from rate_limiter import limiter, rate_limit_exceeded_handler

# Create FastAPI app
app = FastAPI(
    title="Authentication Service",
    description="User session authentication with no time limits",
    version="1.0.0"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "authentication",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "authentication"}

if __name__ == "__main__":
    port = int(os.getenv('AUTH_PORT', '8100'))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

