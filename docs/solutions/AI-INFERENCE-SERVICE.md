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

## PERFORMANCE OPTIMIZATION

### Continuous Batching
- Process multiple requests simultaneously
- vLLM handles batching automatically
- Reduces GPU idle time

### Prefix Caching
- Cache persona prompts across turns
- Reuse context for same NPC
- Significant latency reduction

### Response Streaming
- Stream tokens as generated
- Reduces perceived latency
- Improve user experience

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

