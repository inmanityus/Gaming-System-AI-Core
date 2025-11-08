"""
AI Integration Service - Main FastAPI application.
Handles LLM service integration and coordination.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_routes import router
from lora_routes import router as lora_router  # AI-003: LoRA adapter routes
from multi_tier_routes import router as multi_tier_router  # AI-004: Multi-tier model serving routes
from llm_client import LLMClient
from context_manager import ContextManager
from service_coordinator import ServiceCoordinator
from response_optimizer import ResponseOptimizer


# Global instances
llm_client: LLMClient = None
context_manager: ContextManager = None
service_coordinator: ServiceCoordinator = None
response_optimizer: ResponseOptimizer = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global llm_client, context_manager, service_coordinator, response_optimizer
    
    # Startup
    print("🚀 Starting AI Integration Service...")
    
    # Initialize components
    llm_client = LLMClient()
    context_manager = ContextManager()
    service_coordinator = ServiceCoordinator()
    response_optimizer = ResponseOptimizer()
    
    print("✅ AI Integration Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down AI Integration Service...")
    
    # Close connections
    if llm_client:
        await llm_client.close()
    
    if service_coordinator:
        await service_coordinator.close()
    
    print("✅ AI Integration Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Integration Service",
    description="LLM service integration and coordination for The Body Broker",
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
app.include_router(lora_router)  # AI-003: LoRA adapter management routes
app.include_router(multi_tier_router)  # AI-004: Multi-tier model serving routes


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Integration Service",
        "version": "1.0.0",
        "status": "running",
        "description": "LLM service integration and coordination"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai_integration",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
