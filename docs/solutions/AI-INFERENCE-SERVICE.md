# AI Inference Service Solution
**Service**: LLM Model Serving & Inference Execution  
**Date**: January 29, 2025

---

## SERVICE OVERVIEW

Serves LLM models for NPC dialogue, behavior generation, and content creation. Handles Ollama, vLLM, and TensorRT-LLM deployment with LoRA adapter management.

---

## ARCHITECTURE

### Technology Stack
- **Serving**: vLLM (production) or Ollama (development)
- **Framework**: Python, FastAPI/gRPC
- **Hardware**: 2x RTX 5090 (32GB each) - can serve multiple models
- **Quantization**: 8-bit (AWQ/FP8) preferred, 4-bit (GPTQ) fallback

### Model Serving Strategy

**One Base Model Per GPU + LoRA Adapters**:
```python
# vLLM with LoRA support
from vllm import LLM

# Initialize base model
llm = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    enable_lora=True,
    max_lora_rank=64,
    max_loras=20
)

# Load LoRA adapters
llm.load_lora("vampire_lora", "/path/to/vampire-lora")
llm.load_lora("werewolf_lora", "/path/to/werewolf-lora")
```

**API Server**:
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class DialogueRequest(BaseModel):
    npc_id: str
    tier: int  # 1, 2, or 3
    prompt: str
    context: dict

@app.post("/v1/dialogue")
async def generate_dialogue(request: DialogueRequest):
    # Select model based on tier
    if request.tier == 1:
        model = tier1_model  # Phi-3-mini
    elif request.tier == 2:
        model = tier2_model  # Llama-3.1-8B + LoRA
    else:
        model = tier3_model  # Llama-3.1-8B + personalized LoRA
    
    # Generate with streaming
    response = model.generate_stream(
        prompt=request.prompt,
        max_tokens=512,
        temperature=0.7
    )
    return StreamingResponse(response)
```

### Model Tiers

**Tier 1** (Generic NPCs):
- **Primary**: phi3:mini (2.2 GB) - Available ✅
- **Fastest**: tinyllama (637 MB) - Available ✅
- **Alternatives**: qwen2.5:3b (1.9 GB), llama3.2:3b (2.0 GB) - Available ✅
- Quantization: Q4_K_M (4-bit)
- VRAM: 1.5-2GB per instance
- Latency: 50-150ms TTFT (30-100ms for tinyllama)
- Concurrency: 10-20 NPCs per GPU

**Tier 2** (Elite NPCs):
- **Primary**: llama3.1:8b (4.9 GB) - Available ✅
- **Secondary**: mistral:7b (4.4 GB) - Available ✅
- **Alternatives**: qwen2.5:7b (4.7 GB), mistral-openorca:7b (4.1 GB) - Available ✅
- LoRA: Per-monster-type adapter (50-200MB)
- Quantization: Q8_0 (8-bit)
- VRAM: 4-6GB per instance
- Latency: 100-300ms TTFT
- Concurrency: 5-10 NPCs per GPU

**Tier 3** (Major NPCs):
- **Primary**: llama3.1:8b (4.9 GB) + personalized LoRA - Available ✅
- **Alternative**: mistral:7b (4.4 GB) + personalized LoRA - Available ✅
- Quantization: Q5_K_M or Q8_0 (higher quality)
- VRAM: 6-8GB per instance
- Latency: 200-500ms TTFT
- Concurrency: 2-5 NPCs per GPU

**Note**: DeepSeek V3.1 is NOT available locally in Ollama. Use DeepSeek V3.1 via Azure deployment or Direct API for orchestration. For local reasoning tasks, `deepseek-r1` (5.2 GB) is available.

### LoRA Adapter Management

**Hot-Swapping**:
```python
# Load adapter
llm.load_lora("vampire_lora", "/path/to/lora")

# Use for generation
response = llm.generate(
    prompt,
    lora_request=LoRARequest("vampire_lora")
)

# Unload when done
llm.unload_lora("vampire_lora")
```

**Training Pipeline**:
1. Cloud LLM generates training data (2000-5000 examples)
2. Fine-tune LoRA adapter (2-6 hours on A100)
3. Validate with QA team (>80% approval)
4. Deploy to inference servers

---

## PERFORMANCE OPTIMIZATION (UPDATED - Based on Research)

### Model Quantization ⭐ **NEW**
**Technique**: FP32 → INT8/BF16 quantization  
**Latency Reduction**: 2.3× faster inference  
**Implementation**:
```python
from vllm import LLM

# Quantized model loading
llm = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    quantization="awq",  # 8-bit quantization
    # Or use "gptq" for 4-bit
    max_model_len=4096
)
```
**Impact**:
- Layer 3: 600-1500ms → 260-650ms (57% reduction)
- Layer 4: 1000-3000ms → 435-1300ms (57% reduction)

### Continuous Batching
- Process multiple requests simultaneously
- vLLM handles batching automatically
- Reduces GPU idle time
- Throughput improvement: 5-10×

### Prefix Caching (Enhanced) ⭐ **UPDATED**
- Cache tokenized prompts for 90%+ hit rate
- Reuse context for same NPC
- Multi-tier caching:
  - L1 (in-memory): 10MB, 1000 entries, 5min TTL
  - L2 (Redis): 10GB, 100k entries, 1hr TTL
  - L3 (Semantic): Similarity matching, 24hr TTL
- Latency reduction: 80-95% for cached requests

### Response Streaming ⭐ **ENHANCED**
- Stream tokens as generated (token-by-token)
- First token delivery: 200-500ms (vs 1000ms full response)
- Perceived latency: 70% reduction
- Implementation:
```python
from fastapi.responses import StreamingResponse

async def stream_generation(prompt: str):
    async for token in llm.generate_stream(prompt):
        yield f"data: {json.dumps({'token': token})}\n\n"
```
- gRPC streaming support for production

### Knowledge Distillation ⭐ **NEW**
- Create smaller models from large ones
- Latency reduction: 30-50%
- Use for common scenarios while keeping full models for complex cases
- Training: Transfer learning from Claude 4.5 → smaller local model

### Token Control & Truncation ⭐ **NEW**
- Dynamic prompt truncation
- Token filtering before generation
- Latency reduction: 20-40% per request
- Pre-process prompts to limit max tokens

### Edge Computing Deployment ⭐ **NEW**
- Deploy Ollama models to edge locations
- CloudFlare Workers or Lambda@Edge
- Latency reduction: 30-50ms per request
- Use for Tier 1-2 NPCs primarily

### Connection Pooling ⭐ **NEW**
**gRPC Connection Pool Configuration**:
```python
import grpc

channel = grpc.insecure_channel(
    'inference_service:50051',
    options=[
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_frame_size', 4194304),  # 4MB
        ('grpc.http2.max_connection_window_size', 1048576000),  # 1GB
    ]
)

# Connection pool of 40-100 connections
pool_size = 100
connection_pool = [grpc.insecure_channel(...) for _ in range(pool_size)]
```

### Adaptive Tier Routing ⭐ **NEW**
- ML model predicts query complexity
- Routes simple → Layer 1-2, complex → Layer 3
- Target: 80% handled by Layers 1-2 (<500ms)
- Reduces expensive cloud API calls

---

## DEPLOYMENT

### Development (Ollama)
```bash
ollama pull llama3.1:8b
ollama run llama3.1:8b
```

### Production (vLLM)
```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --enable-lora \
  --max-lora-rank 64 \
  --port 8000
```

### Docker Deployment
- Multi-GPU support
- Auto-scaling based on load
- Health checks and monitoring

---

## MONITORING

### Metrics
- Request latency (p50, p95, p99)
- GPU utilization
- Cache hit rate
- Error rate
- Model switching frequency

---

**Next**: See `ORCHESTRATION-SERVICE.md` for how inference integrates with the hierarchical pipeline.

