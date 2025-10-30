"""
NPC Behavior Service - Main FastAPI application.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_routes import router
from .behavior_engine import BehaviorEngine


# Global instances
behavior_engine: BehaviorEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global behavior_engine
    
    # Startup
    print("🚀 Starting NPC Behavior Service...")
    behavior_engine = BehaviorEngine()
    print("✅ NPC Behavior Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down NPC Behavior Service...")
    print("✅ NPC Behavior Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="NPC Behavior Service",
    description="AI-driven NPC behavior management for The Body Broker",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "NPC Behavior Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "npc_behavior"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
