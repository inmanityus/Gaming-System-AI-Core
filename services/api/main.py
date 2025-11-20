"""
Gaming System AI Core - Main API Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import os
import json
from datetime import datetime

# Import routers
from services.api.routers import audio, engagement, localization

# Create FastAPI app
app = FastAPI(
    title="Gaming System AI Core API",
    description="AI-powered gaming system core with deep learning capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio.router, prefix="/api/v1/audio", tags=["Audio Analytics"])
app.include_router(engagement.router, prefix="/api/v1/engagement", tags=["Engagement Analytics"])
app.include_router(localization.router, prefix="/api/v1/localization", tags=["Localization"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "gaming-system-ai-core"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Gaming System AI Core API",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

# Metrics endpoint for monitoring
@app.get("/metrics")
async def metrics():
    """Metrics endpoint for Prometheus/CloudWatch"""
    # Add actual metrics collection here
    return {
        "requests_total": 0,
        "requests_active": 0,
        "errors_total": 0,
        "latency_seconds": 0.0
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG") == "true" else "An error occurred",
            "request_id": request.headers.get("X-Request-ID")
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Starting Gaming System AI Core API...")
    # Add database connection initialization here
    print("API started successfully!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    print("Shutting down Gaming System AI Core API...")
    # Add cleanup code here
    print("API shut down successfully!")