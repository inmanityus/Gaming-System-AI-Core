"""
FastAPI server for localization service.
Provides HTTP API endpoints for localization operations.
"""
import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .api_routes import router, initialize_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_pool
    
    # Startup
    logger.info("Starting localization service...")
    
    # Create database connection pool
    try:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database=os.getenv('DB_NAME', 'body_broker'),
            min_size=10,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool created")
        
        # Initialize routes with database
        initialize_routes(db_pool)
        logger.info("Routes initialized")
        
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down localization service...")
    
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")


# Create FastAPI app
app = FastAPI(
    title="Localization Service",
    description="Multi-language localization and translation management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "localization",
        "version": "1.0.0",
        "status": "running"
    }


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    
    host = os.getenv('SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('SERVICE_PORT', '8080'))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
