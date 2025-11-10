"""
Quest System Service - FastAPI server for dynamic quest generation and management.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routes import router
from services.state_manager.connection_pool import get_postgres_pool, get_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Initializes connection pools on startup.
    """
    # Startup
    print("Initializing Quest System Service...")
    
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
    
    print("✓ Quest System Service initialized successfully")
    
    yield
    
    # Shutdown
    print("Shutting down Quest System Service...")
    print("✓ Quest System Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Quest System Service",
    description="Dynamic quest generation and management for The Body Broker",
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
        "service": "Quest System Service",
        "version": "0.1.0",
        "description": "Dynamic quest generation and management",
        "status": "running",
        "endpoints": {
            "generate_quest": "/quests/generate",
            "create_quest": "/quests/create",
            "get_quest": "/quests/{quest_id}",
            "get_player_quests": "/quests/player/{player_id}",
            "update_quest_status": "/quests/{quest_id}/status",
            "get_objectives": "/quests/{quest_id}/objectives",
            "update_objective": "/quests/{quest_id}/objectives/{objective_id}",
            "complete_objective": "/quests/{quest_id}/objectives/{objective_id}/complete",
            "complete_rewards": "/quests/{quest_id}/rewards/complete",
            "health_check": "/quests/health",
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
        "service": "quest_system",
        "status": "healthy" if healthy else "unhealthy",
        "version": "0.1.0",
        "dependencies": {
            "postgresql": "healthy" if postgres_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "services.quest_system.server:app",
        host="0.0.0.0",
        port=8011,
        reload=True,
        log_level="info",
    )

