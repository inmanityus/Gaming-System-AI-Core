"""
Gold Tier AI Inference Server
Real-time NPC interactions with <16ms latency target
Model: Qwen2.5-3B-Instruct-AWQ
"""

import os
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vllm import LLM, SamplingParams
from vllm.entrypoints.openai.api_server import router as vllm_router

app = FastAPI(
    title="Gold Tier AI Inference",
    description="Real-time NPC AI with <16ms latency",
    version="1.0.0"
)

# Initialize vLLM engine
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct-AWQ")
GPU_MEMORY_UTIL = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.85"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "4096"))
MAX_NUM_SEQS = int(os.getenv("MAX_NUM_SEQS", "8"))
TENSOR_PARALLEL = int(os.getenv("TENSOR_PARALLEL_SIZE", "1"))

print(f"[GOLD TIER] Initializing vLLM with {MODEL_NAME}")
print(f"[GOLD TIER] GPU Memory: {GPU_MEMORY_UTIL}, Max Length: {MAX_MODEL_LEN}, Max Seqs: {MAX_NUM_SEQS}")

llm = LLM(
    model=MODEL_NAME,
    gpu_memory_utilization=GPU_MEMORY_UTIL,
    max_model_len=MAX_MODEL_LEN,
    max_num_seqs=MAX_NUM_SEQS,
    tensor_parallel_size=TENSOR_PARALLEL,
    trust_remote_code=True,
    quantization="AWQ"  # 4-bit for speed
)

print(f"[GOLD TIER] Model loaded successfully")


class InferenceRequest(BaseModel):
    """Request for AI inference."""
    prompt: str
    max_tokens: int = 8  # Short for real-time
    temperature: float = 0.7
    top_p: float = 0.9
    npc_id: Optional[str] = None
    context: Optional[Dict] = None


class InferenceResponse(BaseModel):
    """Response from AI inference."""
    text: str
    latency_ms: float
    tokens_generated: int
    npc_id: Optional[str] = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "tier": "gold",
        "model": MODEL_NAME,
        "max_sequences": MAX_NUM_SEQS
    }


@app.post("/v1/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """
    Generate AI response for NPC interaction.
    Target: <16ms per token for real-time gameplay.
    """
    start_time = time.perf_counter()
    
    try:
        # Create sampling parameters optimized for speed
        sampling_params = SamplingParams(
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            # Skip special tokens for speed
            skip_special_tokens=True
        )
        
        # Generate response
        outputs = llm.generate([request.prompt], sampling_params)
        
        # Extract generated text
        generated_text = outputs[0].outputs[0].text
        tokens_generated = len(outputs[0].outputs[0].token_ids)
        
        # Calculate latency
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        # Log performance
        per_token_ms = latency_ms / tokens_generated if tokens_generated > 0 else 0
        print(f"[GOLD TIER] Generated {tokens_generated} tokens in {latency_ms:.2f}ms ({per_token_ms:.2f}ms/token)")
        
        # Check if within SLA
        if per_token_ms > 16.0:
            print(f"[WARNING] Latency {per_token_ms:.2f}ms exceeds 16ms SLA")
        
        return InferenceResponse(
            text=generated_text,
            latency_ms=latency_ms,
            tokens_generated=tokens_generated,
            npc_id=request.npc_id
        )
        
    except Exception as e:
        print(f"[ERROR] Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Expose metrics for monitoring."""
    # vLLM provides internal metrics
    return {
        "model": MODEL_NAME,
        "tier": "gold",
        "max_sequences": MAX_NUM_SEQS,
        "gpu_memory_utilization": GPU_MEMORY_UTIL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

