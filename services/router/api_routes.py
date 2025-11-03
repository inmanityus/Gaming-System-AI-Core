"""
API Routes - FastAPI routes for Router Service.
Handles request routing and tier management.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .intelligent_router import IntelligentRouter


# Pydantic models
class RoutingRequest(BaseModel):
    """Request for routing."""
    prompt: str
    max_tokens: int = 100
    sla: str = "interactive"
    latency_budget_ms: int = 200


class RoutingResponse(BaseModel):
    """Response from router."""
    tier: str
    endpoint: str
    sla: str
    health: bool
    async_job: bool = False
    job_id: str = None


# Router
router = APIRouter(prefix="/v1", tags=["Router"])


# Routes
@router.post("/route", response_model=RoutingResponse)
async def route_request(request: RoutingRequest) -> RoutingResponse:
    """
    Route request to appropriate tier.
    
    Args:
        request: Routing request with prompt, SLA, etc.
    
    Returns:
        Routing response with tier and endpoint
    """
    try:
        # Get router instance
        from .server import router_service
        if router_service is None:
            raise HTTPException(
                status_code=503,
                detail="Router service not initialized"
            )
        
        # Convert to dict
        request_dict = {
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "sla": request.sla,
            "latency_budget_ms": request.latency_budget_ms
        }
        
        # Route request
        result = await router_service.route(request_dict)
        
        # Build response
        response = RoutingResponse(
            tier=result["tier"],
            endpoint=result["endpoint"],
            sla=result["sla"],
            health=result["health"]
        )
        
        # Add async info if Bronze tier
        if "async" in result:
            response.async_job = True
            response.job_id = result.get("job_id")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiers/health")
async def get_tier_health() -> Dict[str, Any]:
    """
    Get health status for all tiers.
    
    Returns:
        Dict with health status for each tier
    """
    try:
        from .server import router_service
        if router_service is None:
            raise HTTPException(
                status_code=503,
                detail="Router service not initialized"
            )
        
        status = await router_service.get_tier_health_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tiers/health/check")
async def check_tier_health(tier: str = None) -> Dict[str, Any]:
    """
    Check health of specific tier or all tiers.
    
    Args:
        tier: Tier name (gold, silver, bronze) or None for all
    
    Returns:
        Health status
    """
    try:
        from .server import router_service
        if router_service is None:
            raise HTTPException(
                status_code=503,
                detail="Router service not initialized"
            )
        
        if tier:
            # Import Tier enum
            from .intelligent_router import Tier
            tier_enum = Tier(tier.lower())
            is_healthy = await router_service.check_health(tier_enum)
            return {tier: is_healthy}
        else:
            results = await router_service.check_all_tiers_health()
            return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "router"}

