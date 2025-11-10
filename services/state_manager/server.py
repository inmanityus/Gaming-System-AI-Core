"""
State Management Service - FastAPI Server
Main entry point for the State Management service.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api_routes import router
from .connection_pool import close_pools, get_postgres_pool, get_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Initializes connection pools on startup and closes them on shutdown.
    """
    # Startup
    print("Initializing State Management Service...")
    
    try:
        # Initialize PostgreSQL pool
        await get_postgres_pool()
        print("✓ PostgreSQL connection pool initialized")
        
        # Initialize Redis pool
        await get_redis_pool()
        print("✓ Redis connection pool initialized")
        
        print("State Management Service ready")
    except Exception as e:
        print(f"ERROR: Failed to initialize connection pools: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Shutting down State Management Service...")
    await close_pools()
    print("✓ Connection pools closed")


app = FastAPI(
    title="State Management Service",
    description="Centralized game state management with Redis caching and PostgreSQL persistence",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
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


@app.get("/healthz")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    try:
        # Check PostgreSQL connection
        postgres = await get_postgres_pool()
        await postgres.execute("SELECT 1")
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
    
    status_code = 200 if healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "postgres": "healthy" if postgres_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "State Management Service",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

