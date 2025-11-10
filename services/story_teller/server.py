"""
Story Teller Service - FastAPI server for AI-powered narrative generation.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from api_routes import router
from database_connection import get_postgres, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Initializes connection pools on startup.
    """
    # Startup
    print("Initializing Story Teller Service...")
    
    try:
        # Initialize PostgreSQL connection pool
        postgres = await get_postgres_pool()
        await postgres.ping()
        print("✓ PostgreSQL connection pool initialized")
    except Exception as e:
        print(f"✗ Failed to initialize PostgreSQL: {e}")
        raise
    
    try:
        # Initialize Redis connection pool
        redis = await get_redis_pool()
        await redis.ping()
        print("✓ Redis connection pool initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Redis: {e}")
        raise
    
    print("✓ Story Teller Service initialized successfully")
    
    yield
    
    # Shutdown
    print("Shutting down Story Teller Service...")
    print("✓ Story Teller Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Story Teller Service",
    description="AI-powered narrative generation and story management for The Body Broker",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # SECURITY FIX 2025-11-09
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/", response_model=Dict[str, Any])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "service": "Story Teller Service",
        "version": "0.1.0",
        "description": "AI-powered narrative generation and story management",
        "status": "running",
        "endpoints": {
            "story_nodes": "/story/nodes",
            "narrative_generation": "/story/generate",
            "choice_processing": "/story/nodes/{node_id}/choices",
            "story_branching": "/story/branches",
            "health_check": "/story/health",
        }
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint."""
    try:
        # Check PostgreSQL connection
        postgres = await get_postgres_pool()
        await postgres.ping()
        postgres_healthy = True
    except Exception:
        postgres_healthy = False
    
    try:
        # Check Redis connection
        redis = await get_redis_pool()
        await redis.ping()
        redis_healthy = True
    except Exception:
        redis_healthy = False
    
    healthy = postgres_healthy and redis_healthy
    
    return {
        "service": "story_teller",
        "status": "healthy" if healthy else "unhealthy",
        "version": "0.1.0",
        "dependencies": {
            "postgresql": "healthy" if postgres_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        },
        "timestamp": "2025-10-29T22:32:17Z",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "services.story_teller.server:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info",
    )
