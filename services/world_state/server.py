"""
World State Service - Main FastAPI application.
Handles dynamic world state management, events, factions, and economy.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_routes import router
from world_state_manager import WorldStateManager
from event_system import EventSystem
from faction_manager import FactionManager
from economic_manager import EconomicManager


# Global instances
world_state_manager: WorldStateManager = None
event_system: EventSystem = None
faction_manager: FactionManager = None
economic_manager: EconomicManager = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global world_state_manager, event_system, faction_manager, economic_manager
    
    # Startup
    print("🚀 Starting World State Service...")
    
    # Initialize components
    world_state_manager = WorldStateManager()
    event_system = EventSystem()
    faction_manager = FactionManager()
    economic_manager = EconomicManager()
    
    print("✅ World State Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down World State Service...")
    
    # Clear caches
    if world_state_manager:
        await world_state_manager.clear_cache()
    
    if faction_manager:
        await faction_manager.clear_cache()
    
    if economic_manager:
        await economic_manager.clear_cache()
    
    print("✅ World State Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="World State Service",
    description="Dynamic world state management for The Body Broker",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "World State Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Dynamic world state management, events, factions, and economy"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "world_state",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
