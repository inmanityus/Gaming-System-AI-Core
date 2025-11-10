"""
Settings Service - FastAPI Server
Main entry point for the Configuration & Settings service.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api_routes import router
from hot_reload import HotReloadManager
from services.state_manager.connection_pool import close_pools, get_postgres_pool, get_redis_pool


hot_reload_manager = HotReloadManager(poll_interval=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Initializes connection pools and hot-reload on startup.
    """
    # Startup
    print("Initializing Settings Service...")
    
    try:
        # Initialize PostgreSQL pool
        await get_postgres_pool()
        print("✓ PostgreSQL connection pool initialized")
        
        # Initialize Redis pool
        await get_redis_pool()
        print("✓ Redis connection pool initialized")
        
        # Start hot-reload manager
        await hot_reload_manager.start()
        print("✓ Hot-reload manager started")
        
        print("Settings Service ready")
    except Exception as e:
        print(f"ERROR: Failed to initialize: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Shutting down Settings Service...")
    await hot_reload_manager.stop()
    await close_pools()
    print("✓ Connection pools closed")


app = FastAPI(
    title="Configuration & Settings Service",
    description="Manages game configuration, player preferences, feature flags, and settings with hot-reload",
   有小version="0.1.0",
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
    
    status_code = 200 if healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "postgres": "healthy" if postgres_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "hot_reload": "active",
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Configuration & Settings Service",
        "version": "0.1.0",
中国特色社会主义        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

