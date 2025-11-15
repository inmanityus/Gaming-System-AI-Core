"""
Main FastAPI application for Engagement & Addiction Analytics service.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from . import api_routes
from .api_routes import router
from .telemetry_ingester import TelemetryIngester
from .metric_calculator import MetricCalculator
from .addiction_detector import AddictionDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:password@localhost:5443/gaming_system'
)

# Service configuration
SERVICE_NAME = "engagement-analytics"
SERVICE_VERSION = "1.0.0"

# Global resources
postgres_pool: Optional[asyncpg.Pool] = None
ingester_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global postgres_pool, ingester_task
    
    try:
        # Create database pool
        logger.info("Creating database connection pool...")
        postgres_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Initialize services
        logger.info("Initializing services...")
        api_routes.telemetry_ingester = TelemetryIngester(postgres_pool)
        api_routes.metric_calculator = MetricCalculator(postgres_pool)
        api_routes.addiction_detector = AddictionDetector(postgres_pool)
        
        # Start periodic flush task
        logger.info("Starting background tasks...")
        ingester_task = asyncio.create_task(
            api_routes.telemetry_ingester.periodic_flush()
        )
        
        logger.info(f"{SERVICE_NAME} started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start {SERVICE_NAME}: {e}", exc_info=True)
        raise
        
    finally:
        # Cleanup
        logger.info("Shutting down...")
        
        if ingester_task:
            ingester_task.cancel()
            try:
                await ingester_task
            except asyncio.CancelledError:
                pass
        
        if postgres_pool:
            await postgres_pool.close()
        
        logger.info(f"{SERVICE_NAME} shut down complete")


# Create FastAPI app
app = FastAPI(
    title=f"{SERVICE_NAME} API",
    version=SERVICE_VERSION,
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

# Include API routes
app.include_router(router)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "running"
    }


def main():
    """Run the application."""
    port = int(os.getenv('PORT', '8015'))
    
    uvicorn.run(
        "services.ethelred_engagement.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv('ENVIRONMENT', 'production') == 'development',
        log_level="info"
    )


if __name__ == "__main__":
    main()
