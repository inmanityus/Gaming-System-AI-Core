"""
API Routes - FastAPI routes for AI Integration Service.
Handles AI generation requests and service coordination.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .llm_client import LLMClient
from .context_manager import ContextManager
from .service_coordinator import ServiceCoordinator
from .response_optimizer import ResponseOptimizer


# Pydantic models
class GenerationRequest(BaseModel):
    layer: str
    prompt: str
    context_type: str = "full"
    max_tokens: int = 1000
    temperature: float = 0.7
    use_cache: bool = True


class GenerationResponse(BaseModel):
    success: bool
    text: str
    layer: str
    service: str
    cached: bool = False
    response_time: float
    tokens_used: int = 0
    error: Optional[str] = None


class ContextRequest(BaseModel):
    player_id: UUID
    context_type: str = "full"


class ServiceStatusResponse(BaseModel):
    llm_services: Dict[str, Any]
    service_health: Dict[str, Any]
    performance_metrics: Dict[str, Any]


# Router
router = APIRouter(prefix="/ai", tags=["AI Integration"])

# Dependencies
def get_llm_client() -> LLMClient:
    return LLMClient()


def get_context_manager() -> ContextManager:
    return ContextManager()


def get_service_coordinator() -> ServiceCoordinator:
    return ServiceCoordinator()


def get_response_optimizer() -> ResponseOptimizer:
    return ResponseOptimizer()


# Routes
@router.post("/generate", response_model=GenerationResponse)
async def generate_text(
    request: GenerationRequest,
    player_id: UUID,
    llm_client: LLMClient = Depends(get_llm_client),
    context_manager: ContextManager = Depends(get_context_manager),
    response_optimizer: ResponseOptimizer = Depends(get_response_optimizer),
):
    """Generate text using AI with context management and optimization."""
    try:
        # Get context for the player
        context = await context_manager.get_optimized_context(
            player_id, request.context_type
        )
        
        # Generate text using LLM - REAL IMPLEMENTATION
        # First, always call the real LLM service
        llm_response = await llm_client.generate_text(
            request.layer,
            request.prompt,
            context,
            max_tokens=request.max_tokens or 1000,
            temperature=request.temperature or 0.7
        )
        
        # Check if LLM call was successful
        if not llm_response.get("success", False):
            raise HTTPException(
                status_code=503,
                detail=f"LLM service unavailable: {llm_response.get('error', 'Unknown error')}"
            )
        
        # Extract real response data
        llm_result = {
            "text": llm_response.get("text", ""),
            "tokens_used": llm_response.get("tokens_used", 0),
            "model_id": llm_response.get("model_id"),
            "layer": llm_response.get("layer"),
            "latency_ms": llm_response.get("latency_ms", 0),
        }
        
        if request.use_cache:
            # Use optimized response with caching - pass REAL LLM result
            response = await response_optimizer.optimize_response(
                request.layer,
                request.prompt,
                context,
                llm_result  # REAL LLM response, not placeholder
            )
        else:
            # Direct LLM call without caching - use REAL result
            response = llm_result
        
        return GenerationResponse(
            success=response.get("success", True),
            text=response.get("text", ""),
            layer=request.layer,
            service=response.get("service", "unknown"),
            cached=response.get("cached", False),
            response_time=response.get("response_time", 0.0),
            tokens_used=response.get("tokens_used", 0),
            error=response.get("error"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{player_id}", response_model=Dict[str, Any])
async def get_player_context(
    player_id: UUID,
    context_type: str = "full",
    context_manager: ContextManager = Depends(get_context_manager),
):
    """Get player context for AI generation."""
    try:
        context = await context_manager.get_optimized_context(player_id, context_type)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/{player_id}/refresh")
async def refresh_player_context(
    player_id: UUID,
    context_manager: ContextManager = Depends(get_context_manager),
):
    """Refresh player context cache."""
    try:
        await context_manager.update_context_cache(player_id)
        return {"success": True, "message": "Context cache refreshed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/status", response_model=ServiceStatusResponse)
async def get_service_status(
    llm_client: LLMClient = Depends(get_llm_client),
    service_coordinator: ServiceCoordinator = Depends(get_service_coordinator),
    response_optimizer: ResponseOptimizer = Depends(get_response_optimizer),
):
    """Get status of all AI services."""
    try:
        # Get LLM service status
        llm_status = await llm_client.get_service_status()
        
        # Get service health
        service_health = await service_coordinator.get_service_health()
        
        # Get performance metrics
        performance_metrics = await response_optimizer.get_performance_metrics()
        
        return ServiceStatusResponse(
            llm_services=llm_status,
            service_health=service_health,
            performance_metrics=performance_metrics,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/services/reset-circuit-breaker")
async def reset_circuit_breaker(
    service_name: str,
    llm_client: LLMClient = Depends(get_llm_client),
):
    """Reset circuit breaker for a specific LLM service."""
    try:
        success = await llm_client.reset_circuit_breaker(service_name)
        if success:
            return {"success": True, "message": f"Circuit breaker reset for {service_name}"}
        else:
            return {"success": False, "message": f"Service {service_name} not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    layer: Optional[str] = None,
    response_optimizer: ResponseOptimizer = Depends(get_response_optimizer),
):
    """Clear response cache."""
    try:
        await response_optimizer.clear_cache(layer)
        return {"success": True, "message": f"Cache cleared for {layer or 'all layers'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/performance")
async def get_performance_metrics(
    response_optimizer: ResponseOptimizer = Depends(get_response_optimizer),
):
    """Get performance metrics."""
    try:
        metrics = await response_optimizer.get_performance_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coordinate/aggregate")
async def aggregate_context(
    player_id: UUID,
    context_types: List[str],
    service_coordinator: ServiceCoordinator = Depends(get_service_coordinator),
):
    """Aggregate context from multiple services."""
    try:
        context = await service_coordinator.aggregate_context(player_id, context_types)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coordinate/broadcast")
async def broadcast_update(
    update_type: str,
    data: Dict[str, Any],
    service_coordinator: ServiceCoordinator = Depends(get_service_coordinator),
):
    """Broadcast update to all relevant services."""
    try:
        result = await service_coordinator.broadcast_update(update_type, data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai_integration"}
