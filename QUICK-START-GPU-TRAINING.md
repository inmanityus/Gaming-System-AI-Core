# 🚀 Quick Start: GPU Training & Testing

**Prerequisites**: Phase 1 + 2 Complete ✅  
**Next**: GPU environment setup and adapter training

---

## 1️⃣ GPU ENVIRONMENT SETUP

### Required Hardware:
- **GPU**: NVIDIA A10G (24GB VRAM) or better
- **Instance**: AWS g5.2xlarge or equivalent
- **OS**: Ubuntu 22.04 or Windows with WSL2

### Install Dependencies:

```bash
# Install Python packages
pip install -r training/requirements.txt

# Install vLLM with LoRA support
pip install vllm>=0.4.0 --extra-index-url https://download.pytorch.org/whl/cu121

# Install Redis
# Ubuntu: sudo apt install redis-server
# Windows: choco install redis-64

# Install PostgreSQL client
pip install asyncpg
```

---

## 2️⃣ START SERVICES

### Start vLLM Server:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --quantization awq \
  --dtype float16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9 \
  --enable-lora \
  --max-loras 35 \
  --max-lora-rank 64 \
  --host 0.0.0.0 \
  --port 8000
```

### Start Redis:

```bash
redis-server --daemonize yes
```

### Create PostgreSQL Tables:

```sql
-- Run from: psql -h localhost -p 5443 -U postgres -d gaming_system_ai_core

-- Already have these tables from earlier setup
-- Verify with: \dt
```

---

## 3️⃣ TRAIN ADAPTERS

### Train Vampire Adapters (all 7):

```bash
cd training
python train_lora_adapter.py --archetype vampire --task all
```

**Time**: ~8-14 hours total (2-4 hrs per adapter)  
**Output**: `training/adapters/vampire/{task}/`

### Train Zombie Adapters (all 7):

```bash
python train_lora_adapter.py --archetype zombie --task all
```

**Time**: ~4-8 hours total  
**Output**: `training/adapters/zombie/{task}/`

---

## 4️⃣ TEST WITH EVALUATION HARNESS

### Initialize System:

```python
import asyncio
from examples.archetype_system_demo import main

# Run integration demo
asyncio.run(main())
```

### Run Evaluation Tests:

```python
from tests.evaluation.archetype_eval_harness import ArchetypeEvaluationHarness

harness = ArchetypeEvaluationHarness()

# Vampire test (8-10 min conversation)
result = await harness.run_vampire_conversation_test(duration_min=10.0)
print(f"Vampire test: {'✅ PASSED' if result.passed else '❌ FAILED'}")

# Zombie test (100-300 concurrent)
result = await harness.run_zombie_horde_test(num_zombies=300)
print(f"Zombie test: {'✅ PASSED' if result.passed else '❌ FAILED'}")
```

---

## 5️⃣ VALIDATE MEMORY USAGE

```python
import psutil
import GPUtil

# Check GPU memory
gpus = GPUtil.getGPUs()
for gpu in gpus:
    print(f"GPU: {gpu.memoryUsed/1024:.1f}GB / {gpu.memoryTotal/1024:.1f}GB")
    if gpu.memoryUsed / 1024 < 15.0:
        print("✅ Memory usage < 15GB target")
```

---

## 6️⃣ DEPLOY TO PRODUCTION

Once validated:

```bash
# Register adapters with registry
# Load into vLLM
# Connect to AI integration service
# Begin serving NPC requests
```

**Status**: Foundation complete, ready for GPU training!

