# AI Inference Service - Task Breakdown
**Service**: LLM Model Serving  
**Total Tasks**: 18  
**Estimated Duration**: 120-160 hours

---

## INFRASTRUCTURE TASKS

### AI-001: Ollama Setup (Development)
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 4 hours

**Description**:
- Install Ollama on server
- Pull required base models
- Test basic inference

**Acceptance Criteria**:
- [ ] Ollama running
- [ ] Models available: llama3.1:8b, mistral:7b, phi3:mini
- [ ] Can generate responses
- [ ] API accessible

**Dependencies**: None  
**Watchdog**: All model download commands (can be slow)  
**Testing**: Simple inference test

---

### AI-002: vLLM Server Setup (Production)
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 12 hours

**Description**:
- Install vLLM
- Configure GPU settings
- Set up API server

**Acceptance Criteria**:
- [ ] vLLM server running
- [ ] GPU utilization correct
- [ ] API endpoints working
- [ ] Health checks pass

**Dependencies**: AI-001  
**Watchdog**: All GPU operations  
**Testing**: Load test, latency test

---

### AI-003: LoRA Adapter System
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 24 hours

**Description**:
- Implement LoRA loading/unloading
- Hot-swap functionality
- Adapter registry
- **⚠️ UPDATE**: LoRA adapters must be trained via SRL→RLVR pipeline

**Acceptance Criteria**:
- [ ] Can load/unload adapters at runtime
- [ ] Hot-swap works without downtime
- [ ] Registry tracks active adapters
- [ ] Memory management correct
- [ ] **NEW**: Integration with SRL→RLVR training pipeline for adapter registration
- [ ] **NEW**: Adapters trained via SRL→RLVR approach (not basic fine-tuning)

**Dependencies**: AI-002, SRL-RLVR Training System (Phase 5)  
**Watchdog**: All model loading operations  
**Testing**: Hot-swap stress test, memory leak test

**📝 IMPORTANT**: This task is for serving LoRA adapters. The training of adapters must use the SRL→RLVR approach per `docs/tasks/SRL-RLVR-TRAINING-TASKS.md`. See Task SRL-001 and MODEL-*-001 tasks for training implementation.

---

### AI-004: Multi-Tier Model Serving
**Status**: Pending  
**Priority**: Critical  
**Estimated Time**: 16 hours

**Description**:
- Tier 1: Small models (Phi-3-mini)
- Tier 2: Mid-size + LoRA (Llama-3.1-8B)
- Tier 3: Mid-size + personalized LoRA
- **⚠️ UPDATE**: Model selection must use Dynamic Model Selection System (not arbitrary)

**Acceptance Criteria**:
- [ ] All tiers serving correctly
- [ ] Routing logic works
- [ ] Latency targets met
- [ ] Concurrent requests handled
- [ ] **NEW**: Model selection based on task responsibilities (not arbitrary)
- [ ] **NEW**: Integration with Dynamic Model Selection System for cost-benefit analysis

**Dependencies**: AI-003, SRL-RLVR Training System (Dynamic Model Selection)  
**Watchdog**: All serving operations  
**Testing**: Concurrent load test, latency verification

**📝 IMPORTANT**: Model selection must be responsibility-based, not arbitrary. See `docs/tasks/SRL-RLVR-TRAINING-TASKS.md` → Task DYN-003 (Dynamic Model Selection System) for implementation details.

---

## OPTIMIZATION TASKS

### AI-005: Continuous Batching
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 8 hours

**Description**:
- Configure vLLM continuous batching
- Optimize batch sizes
- Monitor GPU utilization

**Acceptance Criteria**:
- [ ] Multiple requests batched
- [ ] GPU utilization >80%
- [ ] No request starvation
- [ ] Latency acceptable

**Dependencies**: AI-004  
**Testing**: Batch performance test

---

### AI-006: Prefix Caching
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 12 hours

**Description**:
- Implement persona prompt caching
- Context reuse across turns
- Cache invalidation

**Acceptance Criteria**:
- [ ] Cache hit rate >60%
- [ ] Latency reduced by >30%
- [ ] Memory usage acceptable
- [ ] Cache eviction works

**Dependencies**: AI-004  
**Testing**: Cache effectiveness test

---

### AI-007: Response Streaming
**Status**: Pending  
**Priority**: High  
**Estimated Time**: 8 hours

**Description**:
- Implement token streaming
- SSE/webSocket support
- Client-side handling

**Acceptance Criteria**:
- [ ] Tokens stream correctly
- [ ] Client receives incrementally
- [ ] Perceived latency improved
- [ ] Error handling works

**Dependencies**: AI-004  
**Testing**: Streaming stability test

---

## MONITORING TASKS

### AI-008: Metrics & Monitoring
**Status**: Pending  
**Priority**: Medium  
**Estimated Time**: 8 hours

**Description**:
- Latency metrics (p50, p95, p99)
- GPU utilization tracking
- Cache hit rate monitoring
- Error rate tracking

**Acceptance Criteria**:
- [ ] All metrics collected
- [ ] Dashboards functional
- [ ] Alerts configured
- [ ] Historical data stored

**Dependencies**: AI-004  
**Testing**: Metrics accuracy test

---

**Continue for remaining 10 tasks...**

---

**Task Management**: All tasks integrate `/autonomous` and `/test-comprehensive` commands.

