"""
Silver Tier AI Inference Server
Interactive dialogue with 80-250ms latency target
Model: Llama-3.1-8B-Instruct-INT8
"""

import os
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vllm import LLM, SamplingParams

app = FastAPI(
    title="Silver Tier AI Inference",
    description="Interactive dialogue AI with tool use",
    version="1.0.0"
)

MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
GPU_MEMORY_UTIL = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.90"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "8192"))
MAX_NUM_SEQS = int(os.getenv("MAX_NUM_SEQS", "4"))
TENSOR_PARALLEL = int(os.getenv("TENSOR_PARALLEL_SIZE", "1"))
QUANTIZATION = os.getenv("QUANTIZATION", "int8")

print(f"[SILVER TIER] Initializing vLLM with {MODEL_NAME}")

llm = LLM(
    model=MODEL_NAME,
    gpu_memory_utilization=GPU_MEMORY_UTIL,
    max_model_len=MAX_MODEL_LEN,
    max_num_seqs=MAX_NUM_SEQS,
    tensor_parallel_size=TENSOR_PARALLEL,
    trust_remote_code=True,
    quantization=QUANTIZATION
)

print(f"[SILVER TIER] Model loaded successfully")


class DialogueRequest(BaseModel):
    prompt: str
    max_tokens: int = 128
    temperature: float = 0.8
    top_p: float = 0.95
    npc_id: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None


class DialogueResponse(BaseModel):
    text: str
    latency_ms: float
    tokens_generated: int
    npc_id: Optional[str] = None


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tier": "silver",
        "model": MODEL_NAME,
        "max_sequences": MAX_NUM_SEQS
    }


@app.post("/v1/dialogue", response_model=DialogueResponse)
async def dialogue(request: DialogueRequest):
    """
    Generate dialogue for NPC interactions.
    Target: 80-250ms latency, supports longer conversations.
    """
    start_time = time.perf_counter()
    
    try:
        sampling_params = SamplingParams(
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            skip_special_tokens=True
        )
        
        outputs = llm.generate([request.prompt], sampling_params)
        generated_text = outputs[0].outputs[0].text
        tokens_generated = len(outputs[0].outputs[0].token_ids)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        print(f"[SILVER TIER] Generated {tokens_generated} tokens in {latency_ms:.2f}ms")
        
        if latency_ms > 250.0:
            print(f"[WARNING] Latency {latency_ms:.2f}ms exceeds 250ms SLA")
        
        return DialogueResponse(
            text=generated_text,
            latency_ms=latency_ms,
            tokens_generated=tokens_generated,
            npc_id=request.npc_id
        )
        
    except Exception as e:
        print(f"[ERROR] Dialogue generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    return {
        "model": MODEL_NAME,
        "tier": "silver",
        "quantization": QUANTIZATION,
        "max_sequences": MAX_NUM_SEQS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

