"""
Story Memory Service - Main application entry point.
"""
import asyncio
import os
import signal
import sys
from contextlib import asynccontextmanager

import asyncpg
import uvicorn
from fastapi import FastAPI
from loguru import logger
from nats.aio.client import Client as NATS

from .api_routes import router, story_manager, drift_detector
from .story_state_manager import StoryStateManager
from .drift_detector import DriftDetector
from .event_ingestor import EventIngestor


# Global instances
postgres_pool: Optional[asyncpg.Pool] = None
nats_client: Optional[NATS] = None
event_ingestor: Optional[EventIngestor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global postgres_pool, nats_client, story_manager, drift_detector, event_ingestor
    
    logger.info("Starting Story Memory Service")
    
    try:
        # Create PostgreSQL connection pool
        postgres_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'gaming_system'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            min_size=5,
            max_size=20
        )
        logger.info("PostgreSQL pool created")
        
        # Connect to NATS
        nats_client = NATS()
        await nats_client.connect(
            servers=[os.getenv('NATS_URL', 'nats://localhost:4222')]
        )
        logger.info("Connected to NATS")
        
        # Initialize components
        story_manager = StoryStateManager(postgres_pool)
        drift_detector = DriftDetector(nats_client, story_manager, postgres_pool)
        event_ingestor = EventIngestor(nats_client, story_manager, postgres_pool)
        
        # Start background tasks
        await event_ingestor.start()
        await drift_detector.start()
        
        logger.info("Story Memory Service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down Story Memory Service")
        
        if nats_client:
            await nats_client.close()
            
        if postgres_pool:
            await postgres_pool.close()
            
        logger.info("Story Memory Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Story Memory Service",
    description="Manages long-term narrative memory for The Body Broker",
    version="1.0.0",
    lifespan=lifespan
)

# Include routes
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    checks = {
        "service": "healthy",
        "postgres": "unknown",
        "nats": "unknown"
    }
    
    # Check PostgreSQL
    if postgres_pool:
        try:
            async with postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                checks["postgres"] = "healthy"
        except Exception:
            checks["postgres"] = "unhealthy"
    
    # Check NATS
    if nats_client and nats_client.is_connected:
        checks["nats"] = "healthy"
    else:
        checks["nats"] = "unhealthy"
    
    # Overall health
    all_healthy = all(v == "healthy" for v in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks
    }


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Run the service
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        log_level="info"
    )

