"""
Router Service - Main FastAPI application.
Handles intelligent routing to Gold, Silver, and Bronze tiers.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_routes import router
from intelligent_router import IntelligentRouter


# Global instance
router_service: IntelligentRouter = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global router_service
    
    # Startup
    print("🚀 Starting Router Service...")
    
    # Initialize components
    router_service = IntelligentRouter()
    
    print("✅ Router Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Router Service...")
    
    if router_service:
        await router_service.close()
    
    print("✅ Router Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Router Service",
    description="Intelligent routing for multi-tier architecture",
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


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Router Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Intelligent routing for multi-tier architecture"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "router",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

