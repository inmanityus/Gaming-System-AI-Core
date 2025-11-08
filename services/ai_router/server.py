"""
AI Router Service - Routes requests to Gold/Silver tier AI models
Bypasses cross-service dependencies with direct HTTP calls
"""

import httpx
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="AI Router Service",
    description="Routes AI requests to appropriate tier (Gold/Silver/Bronze)",
    version="1.0.0"
)

# GPU instance endpoints
GOLD_TIER_URL = "http://54.234.135.254:8000"
SILVER_TIER_URL = "http://18.208.225.146:8000"

# Tier selection thresholds
REAL_TIME_THRESHOLD_MS = 100  # If need <100ms, use Gold
INTERACTIVE_THRESHOLD_MS = 1000  # If need <1000ms, use Silver


class AIRequest(BaseModel):
    prompt: str
    max_tokens: int = 16
    temperature: float = 0.7
    tier: Optional[str] = None  # 'gold', 'silver', or auto-select
    latency_budget_ms: Optional[int] = None
    npc_id: Optional[str] = None


class AIResponse(BaseModel):
    text: str
    latency_ms: float
    tier_used: str
    tokens_generated: int


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-router",
        "gold_tier": GOLD_TIER_URL,
        "silver_tier": SILVER_TIER_URL
    }


async def call_gold_tier(prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    """Call Gold tier AI model (Qwen2.5-3B, <16ms/token)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GOLD_TIER_URL}/v1/completions",
            json={
                "model": "Qwen/Qwen2.5-3B-Instruct-AWQ",
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )
        response.raise_for_status()
        return response.json()


async def call_silver_tier(prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    """Call Silver tier AI model (Qwen2.5-7B, 80-250ms)."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{SILVER_TIER_URL}/v1/completions",
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )
        response.raise_for_status()
        return response.json()


@app.post("/v1/generate", response_model=AIResponse)
async def generate(request: AIRequest):
    """
    Generate AI response with automatic tier selection.
    
    Tier Selection Logic:
    - If tier specified: Use that tier
    - If latency_budget < 100ms: Use Gold (real-time)
    - If latency_budget < 1000ms: Use Silver (interactive)
    - Default: Use Silver (better quality)
    """
    start_time = time.perf_counter()
    
    # Determine tier
    if request.tier:
        tier = request.tier.lower()
    elif request.latency_budget_ms and request.latency_budget_ms < REAL_TIME_THRESHOLD_MS:
        tier = "gold"
    elif request.latency_budget_ms and request.latency_budget_ms < INTERACTIVE_THRESHOLD_MS:
        tier = "silver"
    else:
        # Default to Silver for better quality
        tier = "silver"
    
    try:
        # Route to appropriate tier
        if tier == "gold":
            result = await call_gold_tier(request.prompt, request.max_tokens, request.temperature)
        elif tier == "silver":
            result = await call_silver_tier(request.prompt, request.max_tokens, request.temperature)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tier: {tier}")
        
        # Extract response
        generated_text = result["choices"][0]["text"]
        tokens_generated = result["usage"]["completion_tokens"]
        
        # Calculate total latency
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        print(f"[AI ROUTER] {tier.upper()} tier: {tokens_generated} tokens in {latency_ms:.2f}ms")
        
        return AIResponse(
            text=generated_text,
            latency_ms=latency_ms,
            tier_used=tier,
            tokens_generated=tokens_generated
        )
        
    except httpx.HTTPError as e:
        print(f"[ERROR] {tier.upper()} tier request failed: {e}")
        raise HTTPException(status_code=503, detail=f"{tier.upper()} tier unavailable")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tiers")
async def get_tiers():
    """Get available AI tiers and their status."""
    return {
        "gold": {
            "url": GOLD_TIER_URL,
            "model": "Qwen2.5-3B-Instruct-AWQ",
            "latency_target": "16ms per token",
            "use_cases": ["NPC actions", "Quick responses", "Real-time interactions"]
        },
        "silver": {
            "url": SILVER_TIER_URL,
            "model": "Qwen2.5-7B-Instruct",
            "latency_target": "80-250ms",
            "use_cases": ["Dialogue", "Quest givers", "Complex conversations"]
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

