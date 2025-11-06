"""
AI-004: Multi-Tier Model Serving API Routes
FastAPI routes for multi-tier model serving.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .multi_tier_router import MultiTierModelRouter, ModelTier
from .llm_client import LLMClient

router = APIRouter(prefix="/api/v1/multi-tier", tags=["Multi-Tier Model Serving"])

# Pydantic models
class TierGenerationRequest(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class TierGenerationResponse(BaseModel):
    success: bool
    text: str
    tier: str
    model: str
    lora_adapter: Optional[str] = None
    latency_ms: float
    tokens_used: int = 0
    error: Optional[str] = None


class TierMetricsResponse(BaseModel):
    tier: str
    model: str
    request_count: int
    success_count: int
    error_count: int
    success_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    active_requests: int
    concurrency_limit: int
    latency_target_ms: int


# Dependency
def get_multi_tier_router(llm_client: LLMClient = Depends(lambda: LLMClient())) -> MultiTierModelRouter:
    """Get multi-tier router from LLM client."""
    return llm_client.multi_tier_router


@router.post("/generate", response_model=TierGenerationResponse)
async def generate_with_tier(
    request: TierGenerationRequest,
    router: MultiTierModelRouter = Depends(get_multi_tier_router)
):
    """Generate text using multi-tier model routing."""
    try:
        result = await router.route_request(
            prompt=request.prompt,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        if result.get("success"):
            return TierGenerationResponse(
                success=True,
                text=result.get("text", ""),
                tier=result.get("tier", ""),
                model=result.get("model", ""),
                lora_adapter=result.get("lora_adapter"),
                latency_ms=result.get("latency_ms", 0.0),
                tokens_used=result.get("tokens_used", 0)
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Generation failed")
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, TierMetricsResponse])
async def get_tier_metrics(
    tier: Optional[str] = None,
    router: MultiTierModelRouter = Depends(get_multi_tier_router)
):
    """Get metrics for all tiers or a specific tier."""
    try:
        if tier:
            # Get specific tier
            tier_enum = ModelTier(tier)
            metrics = router.get_tier_metrics(tier_enum)
            return {tier: TierMetricsResponse(**metrics)}
        else:
            # Get all tiers
            all_metrics = router.get_tier_metrics()
            return {
                tier_name: TierMetricsResponse(**metrics)
                for tier_name, metrics in all_metrics.items()
            }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure/{tier}")
async def configure_tier(
    tier: str,
    model_name: Optional[str] = None,
    lora_adapter: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    latency_target_ms: Optional[int] = None,
    concurrency_limit: Optional[int] = None,
    router: MultiTierModelRouter = Depends(get_multi_tier_router)
):
    """Configure a model tier."""
    try:
        tier_enum = ModelTier(tier)
        router.configure_tier(
            tier=tier_enum,
            model_name=model_name,
            lora_adapter=lora_adapter,
            max_tokens=max_tokens,
            temperature=temperature,
            latency_target_ms=latency_target_ms,
            concurrency_limit=concurrency_limit
        )
        return {"success": True, "message": f"Tier {tier} configured"}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

