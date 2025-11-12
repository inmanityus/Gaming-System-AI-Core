# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
FastAPI server for Orchestration Service.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging
import os

from .api_routes import router
from .orchestration_service import OrchestrationService
from .models_schemas import ContentRequest, ContentResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Orchestration Service", version="1.0.0")

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # SECURITY FIX 2025-11-09
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Global service instance
_orchestration_service: Optional[OrchestrationService] = None


def get_orchestration_service() -> OrchestrationService:
    """Get or create orchestration service instance."""
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService()
    return _orchestration_service


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info("Orchestration Service starting up")
    service = get_orchestration_service()
    logger.info("Orchestration Service initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Orchestration Service shutting down")
    global _orchestration_service
    if _orchestration_service:
        await _orchestration_service.close()
        _orchestration_service = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "orchestration"}


@app.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentRequest,
    user_id: Optional[str] = None,
    service: OrchestrationService = Depends(get_orchestration_service)
):
    """
    Generate content using the 4-layer pipeline.
    
    Args:
        request: Content generation request
        user_id: User ID for tier checking (optional)
        
    Returns:
        Complete content response
    """
    try:
        response = await service.generate_content(request, user_id=user_id)
        return response
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/coordinate-battle")
async def coordinate_battle(
    monsters: list,
    player: dict,
    service: OrchestrationService = Depends(get_orchestration_service)
):
    """
    Coordinate battle with multiple NPCs.
    
    Args:
        monsters: List of monster data
        player: Player state
        
    Returns:
        Battle execution plan
    """
    try:
        plan = await service.coordinate_battle(monsters, player)
        return plan
    except Exception as e:
        logger.error(f"Error coordinating battle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

