# Multi-Tier Model Architecture Solution
**Project**: "The Body Broker" - AI-Driven Horror Game  
**Date**: 2025-11-03  
**Status**: Complete Architecture - Ready for Implementation  
**Review**: GPT-5 Pro (Director), Gemini 2.5 Pro, Claude 3.5 Sonnet  
**Version**: 1.0 - Three-Tier Hybrid Strategy

---

## 🚨 EXECUTIVE SUMMARY

**Architecture**: Three-tier hybrid model system replacing both small models AND for-pay models while maintaining 300+ FPS gameplay and dramatically reducing scaling costs.

**Key Innovation**: Decouple game frame rate (300+ FPS) from LLM update rate (1-2 Hz) using deterministic micro-policies for NPCs with async LLM intent updates. Large MoE models (DeepSeek-V3) handle async high-level tasks (stories, narrative) where latency doesn't matter, enabling maximum quality for specialized roles.

**Cost Impact**: 
- Training: $8.6k-$32k one-time for Bronze tier, $240 for Silver, $75 for Gold
- Inference: 10-50× cheaper than for-pay models
- Break-even: 3-6 months, then massive ongoing savings

---

## ARCHITECTURE OVERVIEW

### Three-Tier Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   GOLD TIER (Real-Time)                  │
│  Sub-16ms per token | 3B-8B models | TensorRT-LLM       │
│  Real-time NPCs, frame-rate synchronous                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                SILVER TIER (Interactive)                │
│  80-250ms | 7B-13B models | vLLM | MCP tools enabled   │
│  Key NPCs, complex dialogue, player support             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                BRONZE TIER (Async)                      │
│  Seconds acceptable | DeepSeek-V3 671B | SageMaker      │
│  Storyteller, worldbuilding, cybersecurity, admin     │
└─────────────────────────────────────────────────────────┘
```

### Core Components

1. **Intelligent Router/Orchestrator**: Routes requests to optimal tier based on SLA, persona, context
2. **Decoupled NPC System**: Micro-policies at frame rate, LLM updates at lower frequency
3. **Intent Cache System**: Smooth transitions between cached and updated intents
4. **State Prediction Service**: Ahead-of-user rendering (3-5 seconds ahead)
5. **MCP Server Hub**: Domain-specific tools (Storyteller, Cybersecurity, Admin, Game State, RAG)

---

## TIER 1: GOLD - REAL-TIME (SUB-16MS)

### Purpose
Handle real-time NPC interactions that must run at game frame rate (300+ FPS).

### Architecture Pattern

**Decoupled Update Loop**:
```python
class RealTimeNPCSystem:
    """
    Decouples frame rate from LLM updates.
    Micro-policies run every frame (deterministic).
    LLM updates intent asynchronously (1-2 Hz).
    """
    
    def update_frame(self, delta_time):
        """Runs every frame (300+ FPS)"""
        # Uses cached intent - never blocks on LLM
        self.micro_policy.execute(
            intent=self.intent_cache.get(self.npc_id),
            state=self.game_state
        )
    
    async def update_llm_intent(self, npc_id):
        """Runs at 1-2 Hz (async, non-blocking)"""
        intent = await self.llm_service.get_intent(
            npc_id=npc_id,
            context=self.get_npc_context(npc_id),
            max_tokens=8  # Short, deterministic intents
        )
        self.intent_cache.update(npc_id, intent)
```

### Model Specifications

**Recommended Models**:
1. **Qwen2.5-3B-Instruct** (Primary)
   - Size: 3B parameters
   - Quantization: 4-bit AWQ
   - Latency: 5-12ms per token on L4 GPU
   - Quality: Excellent with SRL→RLVR training

2. **Llama-3.2-3B-Instruct** (Alternative)
   - Size: 3B parameters
   - Quantization: 4-bit AWQ
   - Latency: 6-15ms per token
   - Quality: Strong base, improves with training

3. **Phi-3.5-mini** (If license permits)
   - Size: 3.8B parameters
   - Quantization: 4-bit AWQ
   - Latency: 4-10ms per token
   - Quality: Microsoft-optimized, very fast

**Fallback**: Mistral-7B-Instruct (aggressively quantized to 4-bit)

### Infrastructure

**Hosting**: EC2 `g6.xlarge` (L4 24GB) or EKS cluster
**Framework**: TensorRT-LLM (optimized CUDA kernels)
**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gold-tier-inference
spec:
  replicas: 4  # Per AZ for redundancy
  template:
    spec:
      containers:
      - name: trtllm-server
        image: nvcr.io/nvidia/tensorrtllm:latest
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
        env:
        - name: MODEL_NAME
          value: "qwen2.5-3b-instruct-awq"
        - name: TRTLLM_ENGINE_PATH
          value: "/models/engines"
```

### Performance Optimizations

**Speculative Decoding**:
```python
# Draft model (1B) proposes tokens quickly
draft_tokens = await draft_model.generate(prompt, max_tokens=4)

# Target model (3B) verifies in parallel
verified_tokens = await target_model.verify(prompt, draft_tokens)

# 1.5-2.2× speedup with no quality loss
```

**KV Cache Management**:
- Per-NPC pinned caches in GPU memory
- LRU eviction for inactive NPCs (>30s inactive)
- Sliding window attention (4K context max)
- Prefix cache for system prompts (reused across NPCs)

**Batching Strategy**:
- Real-time queue: max_batch_size=4, priority=high
- Background queue: max_batch_size=32, priority=low
- Isolated queues prevent tail latency spikes

**Token Control**:
- Max output: 8 tokens for NPC control
- Early exit on high-confidence tokens
- Dynamic truncation if approaching budget

### Integration Points

**Game Engine**:
- gRPC streaming API (zero-copy)
- Pinned memory buffers
- CPU affinity (isolate to dedicated cores)
- Co-locate in same AZ as game servers

**Intent Cache**:
- Redis with sub-millisecond latency
- Per-NPC TTL: 2 seconds
- Predictive prefetching (3-5 seconds ahead)

---

## TIER 2: SILVER - INTERACTIVE (80-250MS)

### Purpose
Handle high-quality NPC interactions that don't need frame-rate synchronization but require quick responses.

### Model Specifications

**Recommended Models**:
1. **Llama-3.1-8B-Instruct** (Primary)
   - Size: 8B parameters
   - Quantization: INT8 or FP8
   - Latency: 50-150ms per token on A10G
   - Quality: Excellent conversational ability

2. **Qwen2.5-7B-Instruct** (Alternative)
   - Size: 7B parameters
   - Quantization: INT8 or AWQ
   - Latency: 60-180ms per token
   - Quality: Strong multilingual support

3. **Mistral-Nemo-12B-Instruct** (For complex tasks)
   - Size: 12B parameters
   - Quantization: INT8
   - Latency: 80-250ms per token
   - Quality: Superior reasoning for complex dialogue

**Specialized Variants**:
- **DeepSeek-Coder-6.7B**: For code-related tasks
- **Qwen2.5-Math-7B**: For reasoning-heavy conversations

### Infrastructure

**Hosting**: EC2 `g6.12xlarge` (L4) or `g5.12xlarge` (A10G) with vLLM
**Framework**: vLLM with PagedAttention and continuous batching
**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: silver-tier-inference
spec:
  replicas: 2  # Autoscales based on demand
  template:
    spec:
      containers:
      - name: vllm-server
        image: vllm/vllm-openai:latest
        resources:
          requests:
            nvidia.com/gpu: 1
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-3.1-8B-Instruct"
        - name: QUANTIZATION
          value: "awq"
        - name: MAX_NUM_BATCHED_TOKENS
          value: "8000"
```

### MCP Integration

**Allowed Tools**:
- ✅ RAG retrieval from OpenSearch
- ✅ Game state queries (read-only)
- ✅ Vector search operations
- ✅ Key/value config lookups
- ❌ No blocking admin operations
- ❌ No long-running tasks

**Tool Call Pattern**:
```python
class SilverTierNPC:
    async def generate_response(self, player_message, npc_context):
        # Can use MCP tools within 80-250ms budget
        if needs_lore_context:
            lore = await self.mcp_storyteller.retrieve_lore(npc_context)
        
        response = await self.model.generate(
            prompt=build_prompt(player_message, lore, npc_context),
            max_tokens=128,
            temperature=0.7
        )
        return response
```

### Performance Optimizations

**vLLM Optimizations**:
- PagedAttention for efficient memory usage
- Continuous batching for throughput
- Prompt caching for common NPC templates
- Speculative decoding optional (3B draft for 8B target)

**Caching Strategy**:
- Response cache (LRU, 1000 entries)
- Lore context cache (TTL: 5 minutes)
- Dialogue history cache (last 10 turns)

---

## TIER 3: BRONZE - ASYNCHRONOUS (SECONDS ACCEPTABLE)

### Purpose
Handle expert-level tasks where quality is paramount and latency doesn't matter.

### Model Specifications

**Primary Model**: **DeepSeek-V3.1-Terminus**
- **Architecture**: MoE (671B total, 37B active per token)
- **Context**: 128K tokens
- **Capabilities**: Complex reasoning, long-form generation, worldbuilding
- **Latency**: ~760ms per token (acceptable for async)
- **Hardware**: 8+ H100/H200 datacenter GPUs (multi-node)

**Backup Models**:
- Mixtral-8x22B (if DeepSeek unavailable)
- For-pay models as last-resort fallback only

### Infrastructure

**Hosting**: SageMaker Async Inference Endpoints or EKS job queues
**Instance**: `p5.48xlarge` (8× H100 80GB) - Multi-node (3-4 nodes = 24 H100s)
**Deployment**:
```python
from sagemaker.async_inference import AsyncInferenceConfig
from sagemaker.model import Model

# Async endpoint configuration
async_config = AsyncInferenceConfig(
    output_path="s3://bucket/outputs/",
    failure_path="s3://bucket/failures/",
    max_concurrent_invocations_per_instance=4
)

# Deploy DeepSeek-V3 model
model = Model(
    image_uri="deepseek-v3-container",
    model_data="s3://bucket/deepseek-v3-model/",
    role=role
)

predictor = model.deploy(
    initial_instance_count=4,  # 4 nodes = 32 H100s
    instance_type="ml.p5.48xlarge",
    async_inference_config=async_config
)
```

### Use Cases

#### 1. Storyteller Service
**Purpose**: Generate narrative content, story arcs, questlines  
**Workflow**:
```python
class StorytellerService:
    async def generate_story_arc(self, theme, length):
        """Async generation - returns job ID"""
        job = await self.bronze_tier.submit_job(
            model="deepseek-v3-storyteller",
            prompt=f"Generate a {length}-part story arc about {theme}",
            max_tokens=2000
        )
        return job.id
    
    async def get_story_arc(self, job_id):
        """Poll for completion or use S3 notification"""
        result = await self.bronze_tier.get_result(job_id)
        return self.process_story(result)
```

**Output Storage**: S3 → Aurora Postgres → Served to Silver/Gold tiers via cache

#### 2. Cybersecurity Service
**Purpose**: Deep code analysis, security audits, threat assessment  
**Workflow**:
```python
class CybersecurityService:
    async def audit_codebase(self, repo_path):
        """Deep analysis - async processing"""
        # Trigger Semgrep, Trivy, custom analyzers via MCP
        analysis = await self.mcp_cybersecurity.scan_codebase(repo_path)
        
        # Generate comprehensive security report
        job = await self.bronze_tier.submit_job(
            model="deepseek-v3-security",
            prompt=f"Analyze security findings: {analysis}",
            tools=["semgrep", "trivy", "aws-security-hub"]
        )
        return job.id
```

#### 3. Admin Service
**Purpose**: Batched operations, reports, system administration  
**Workflow**:
```python
class AdminService:
    async def generate_weekly_report(self, metrics):
        """Async report generation"""
        job = await self.bronze_tier.submit_job(
            model="deepseek-v3-admin",
            prompt=f"Generate weekly operations report: {metrics}",
            tools=["aws-api", "database-query"]
        )
        return job.id
```

### MCP Integration

**Full Tool Access**:
- ✅ Storyteller MCP: Full RAG, plot graphs, asset catalogs
- ✅ Cybersecurity MCP: All security tools (with approval gates)
- ✅ Admin MCP: Read-most AWS APIs, batched operations
- ✅ Long-running operations allowed
- ✅ Batch operations for efficiency

### Nightly Distillation

**Purpose**: Continuously reduce dependency on expensive Bronze tier by distilling knowledge to Silver/Gold

**Workflow**:
```python
class DistillationPipeline:
    async def nightly_distillation(self):
        """Run nightly to distill Bronze → Silver → Gold"""
        
        # Collect Bronze tier traces (high-quality outputs)
        bronze_traces = await self.collect_bronze_traces(limit=1000)
        
        # Distill to Silver tier adapters
        silver_adapter = await self.distill_to_silver(
            teacher_traces=bronze_traces,
            student_model="llama-3.1-8b"
        )
        
        # Distill Silver to Gold tier adapters
        gold_adapter = await self.distill_to_gold(
            teacher_traces=silver_adapter.traces,
            student_model="qwen2.5-3b"
        )
        
        # Deploy updated adapters
        await self.deploy_adapters(silver_adapter, gold_adapter)
```

**Benefit**: Over time, Silver and Gold tiers improve without needing Bronze tier for same tasks.

---

## INTELLIGENT ROUTER/ORCHESTRATOR

### Routing Logic

```python
class ModelRouter:
    """
    Routes requests to optimal tier based on:
    - Request type (real-time vs interactive vs async)
    - SLA requirements (sub-16ms vs 80-250ms vs seconds)
    - Quality requirements (simple vs complex reasoning)
    - Context size (small vs medium vs large)
    - Cost sensitivity (high-volume vs low-volume high-value)
    """
    
    def route(self, request: InferenceRequest) -> Tier:
        # Gold tier: Real-time NPCs
        if request.sla == "real-time" and request.max_tokens <= 8:
            return Tier.GOLD
        
        # Silver tier: Interactive NPCs
        if request.sla == "interactive" and request.needs_tools:
            return Tier.SILVER
        
        # Bronze tier: Async expert work
        if request.sla == "async" or request.requires_expert_reasoning:
            return Tier.BRONZE
        
        # Default: Silver for balanced quality/latency
        return Tier.SILVER
    
    async def execute(self, request: InferenceRequest):
        tier = self.route(request)
        
        if tier == Tier.GOLD:
            # Never blocks, uses cached intent if model unavailable
            return await self.gold_tier.execute_with_fallback(request)
        elif tier == Tier.SILVER:
            # Can use MCP tools
            return await self.silver_tier.execute_with_tools(request)
        else:  # BRONZE
            # Async job queue
            job_id = await self.bronze_tier.submit_job(request)
            return {"job_id": job_id, "status": "queued"}
```

### Fallback Strategy

**Gold Tier Failover**:
1. Primary: Target model (3B-8B)
2. Fallback 1: Smaller distilled model (1B-2B)
3. Fallback 2: Cached intent (last known good)
4. Fallback 3: Deterministic policy (no LLM)

**Silver Tier Failover**:
1. Primary: Target model (7B-13B)
2. Fallback 1: Smaller model (3B-8B)
3. Fallback 2: Cached response
4. Fallback 3: Template-based response

**Bronze Tier**:
- Job queue handles retries automatically
- Can fallback to for-pay models if Bronze unavailable (rare)

---

## MCP SERVER ARCHITECTURE

### Storyteller MCP

**Purpose**: Narrative generation, worldbuilding, lore management  
**Components**:
- OpenSearch Serverless: Vector store for lore retrieval
- Aurora Postgres: Plot/quest graph storage
- S3: Asset catalogs and templates
- Lambda: Narrative consistency checking

**API**:
```python
class StorytellerMCP:
    async def retrieve_lore(self, topic: str, context: dict) -> List[str]:
        """RAG against lore database"""
        return await self.opensearch.search(topic, context)
    
    async def generate_narrative(self, prompt: str) -> str:
        """Trigger Bronze tier narrative generation"""
        job_id = await self.bronze_tier.submit_job(
            model="deepseek-v3-storyteller",
            prompt=prompt
        )
        return job_id
    
    async def check_consistency(self, narrative: str, existing_lore: dict) -> bool:
        """Check narrative against existing lore"""
        return await self.consistency_checker.validate(narrative, existing_lore)
```

### Cybersecurity MCP

**Purpose**: Security analysis, code auditing, threat detection  
**Components**:
- Semgrep: Static code analysis
- Trivy/Syft/Grype: Vulnerability scanning
- AWS Security Hub: Cloud security findings
- CloudTrail/GuardDuty: Log analysis

**API**:
```python
class CybersecurityMCP:
    async def scan_codebase(self, repo_path: str) -> SecurityReport:
        """Comprehensive security scan"""
        findings = await asyncio.gather(
            self.semgrep.scan(repo_path),
            self.trivy.scan(repo_path),
            self.aws_security_hub.get_findings()
        )
        return self.aggregate_findings(findings)
    
    async def audit_with_ai(self, findings: SecurityReport) -> AuditReport:
        """Deep AI analysis of security findings"""
        job_id = await self.bronze_tier.submit_job(
            model="deepseek-v3-security",
            prompt=f"Analyze security findings: {findings}",
            tools=["semgrep", "trivy", "aws-security-hub"]
        )
        return job_id
```

**Access Control**:
- Read operations: Allowed for Silver/Bronze tiers
- Write operations: Require MFA or Slack approval
- Sensitive data: Encrypted at rest, VPC-only access

### Admin MCP

**Purpose**: System administration, website management, operations  
**Components**:
- AWS API Gateway: Read-most AWS APIs
- STS: Assumed roles for least-privilege access
- Slack: Approval workflows
- Fitness Website APIs: Admin operations

**API**:
```python
class AdminMCP:
    async def query_aws_resource(self, service: str, resource: str) -> dict:
        """Read-only AWS resource queries"""
        return await self.aws_client.describe_resource(service, resource)
    
    async def generate_admin_report(self, metrics: dict) -> str:
        """Generate admin reports via Bronze tier"""
        job_id = await self.bronze_tier.submit_job(
            model="deepseek-v3-admin",
            prompt=f"Generate admin report: {metrics}",
            tools=["aws-api", "database-query"]
        )
        return job_id
    
    async def approve_change(self, change_request: dict) -> bool:
        """Human approval required for changes"""
        return await self.approval_workflow.request_approval(change_request)
```

### Game State MCP

**Purpose**: Game world state access for NPCs and AI systems  
**Components**:
- Redis: Hot game state cache
- Aurora Postgres: Persistent game state
- Event Bus: State change notifications

**API**:
```python
class GameStateMCP:
    async def get_npc_state(self, npc_id: str) -> NPCState:
        """Read-only NPC state"""
        return await self.state_cache.get(f"npc:{npc_id}")
    
    async def get_world_state(self, region: str) -> WorldState:
        """Read-only world state snapshot"""
        return await self.state_cache.get(f"world:{region}")
    
    async def queue_state_change(self, change: StateChange) -> str:
        """Queue state change for engine arbitration"""
        return await self.event_bus.publish("state-change", change)
```

**Rules**:
- ✅ Read operations: All tiers can access
- ❌ Write operations: Event-queued only, never direct DB writes
- ✅ Caching: Aggressive caching for Gold tier (sub-millisecond)

### RAG/Vector Search MCP

**Purpose**: Knowledge retrieval, semantic search  
**Components**:
- OpenSearch Serverless: Vector indices
- Per-persona indices: Separate indices per NPC type
- Shared lore index: Cross-cutting knowledge

**API**:
```python
class RAGMCP:
    async def search_lore(self, query: str, persona: str = None) -> List[dict]:
        """Semantic search in lore database"""
        index = f"lore-{persona}" if persona else "lore-shared"
        return await self.opensearch.vector_search(query, index)
    
    async def retrieve_context(self, topic: str, limit: int = 5) -> List[str]:
        """Retrieve relevant context for topic"""
        results = await self.search_lore(topic)
        return [r["content"] for r in results[:limit]]
```

---

## STATE PREDICTION & AHEAD-OF-USER RENDERING

### Prediction Service

**Purpose**: Predict future game states to render ahead of user actions

```python
class StatePredictionService:
    """
    Predicts 3-5 seconds ahead to enable ahead-of-user rendering.
    Generates responses for likely player actions before they happen.
    """
    
    def __init__(self):
        self.prediction_window = 5.0  # seconds
        self.prediction_buffer = TimeSeriesBuffer()
    
    async def update_predictions(self, current_state: GameState):
        """Continuously updates prediction buffer"""
        # Predict likely player actions
        likely_actions = await self.predict_player_actions(current_state)
        
        # Generate responses for each likely action
        for action in likely_actions:
            predicted_response = await self.silver_tier.generate_response(
                prompt=self.build_prompt(action, current_state),
                precompute=True  # Generate ahead of time
            )
            self.prediction_buffer.add(
                timestamp=current_state.time + action.probability * self.prediction_window,
                response=predicted_response
            )
    
    def get_predicted_response(self, player_action: str, timestamp: float) -> Optional[str]:
        """Retrieve pre-computed response if available"""
        return self.prediction_buffer.get_closest(timestamp)
```

### Implementation Strategy

**Prediction Accuracy**:
- Use player behavior analytics to improve predictions
- Track success rate of predicted responses
- Continuously refine prediction models

**Cache Management**:
- Pre-computed responses: TTL 5 seconds
- LRU eviction for unused predictions
- Invalidate on unexpected player actions

**Integration**:
- Silver tier generates predictions (80-250ms acceptable)
- Gold tier consumes cached predictions (<1ms)
- Fallback to on-demand generation if prediction miss

---

## AWS DEPLOYMENT ARCHITECTURE

### Training Infrastructure (SageMaker)

**Bronze Tier Training**:
```yaml
TrainingJob:
  InstanceType: ml.p5.48xlarge
  InstanceCount: 4  # 32 H100s total
  VolumeSize: 500GB
  MaxRuntime: 259200  # 3 days
  HyperParameters:
    - Method: LoRA
    - Rank: 64
    - Alpha: 128
    - TargetModules: ["q_proj", "v_proj"]
  InputDataConfig:
    - Channel: training
      DataSource:
        S3DataSource:
          S3Uri: s3://bucket/training-data/
```

**Silver/Gold Tier Training**:
```yaml
TrainingJob:
  InstanceType: ml.p4d.24xlarge  # For Silver
  # or ml.g6.12xlarge for Gold
  InstanceCount: 1
  VolumeSize: 200GB
  MaxRuntime: 72000  # 20 hours max
  HyperParameters:
    - Method: QLoRA
    - Rank: 32
```

### Inference Infrastructure (EC2/EKS)

**Gold Tier (EKS Cluster)**:
```yaml
NodeGroup:
  Name: gold-tier-gpu
  InstanceTypes:
    - g6.xlarge  # L4 24GB
  MinSize: 8
  MaxSize: 64
  DesiredSize: 16
  Taints:
    - Key: tier
      Value: gold
      Effect: NoSchedule
  Labels:
    tier: gold
    gpu: l4
```

**Silver Tier (EKS Cluster)**:
```yaml
NodeGroup:
  Name: silver-tier-gpu
  InstanceTypes:
    - g6.12xlarge  # L4 or A10G
    - g5.12xlarge
  MinSize: 2
  MaxSize: 32
  DesiredSize: 4
  ScalingPolicy:
    TargetCPU: 70
    TargetGPU: 80
```

**Bronze Tier (SageMaker Async)**:
```yaml
AsyncEndpoint:
  InstanceType: ml.p5.48xlarge
  InitialInstanceCount: 4
  MaxConcurrentInvocationsPerInstance: 4
  OutputConfig:
    S3OutputPath: s3://bucket/async-outputs/
  FailureConfig:
    S3FailurePath: s3://bucket/async-failures/
```

### Networking & Security

**VPC Configuration**:
- Private subnets for inference nodes
- VPC endpoints for S3, SageMaker (reduce egress costs)
- Security groups: Least-privilege access
- Network ACLs: Restrict unnecessary traffic

**Load Balancing**:
- NLB (Network Load Balancer) for Gold/Silver tiers
- gRPC health checks
- Locality-aware routing (prefer same AZ)
- Connection pooling (40-100 connections)

**Encryption**:
- KMS for model storage encryption
- TLS 1.3 for all API communications
- Secrets Manager for API keys and credentials

---

## COST OPTIMIZATION STRATEGIES

### Training Cost Reduction

1. **Spot Instances**: Use SageMaker Spot Training (up to 90% savings)
2. **Checkpointing**: Save checkpoints frequently to resume from failures
3. **Early Stopping**: Stop training when validation loss plateaus
4. **Gradient Accumulation**: Simulate larger batch sizes without memory increase

### Inference Cost Reduction

1. **Auto-Scaling**: Scale down during off-peak hours
2. **Spot Instances**: Use Spot for Bronze tier (acceptable interruptions)
3. **Quantization**: Aggressive quantization reduces GPU requirements
4. **Caching**: Maximize cache hit rates (target: 80%+)
5. **Batching**: Batch requests for Silver/Bronze tiers
6. **Distillation**: Continuously distill Bronze → Silver → Gold (reduce Bronze usage)

### ROI Projections

**Break-Even Analysis**:
- Bronze tier training: $8.6k-$32k one-time
- For-pay model cost: ~$0.01 per 1K tokens
- Break-even: 860K-32M tokens
- **Achieved within 1-3 months for storyteller/admin use cases**

**Scaling Savings**:
- At 1M tokens/day: **$300/month** savings vs for-pay
- At 10M tokens/day: **$3,000/month** savings
- At 100M tokens/day: **$30,000/month** savings
- **Massive ROI at scale**

---

## PERFORMANCE MONITORING & OBSERVABILITY

### Metrics Dashboard

**Gold Tier Metrics**:
- p50/p95/p99 latency per token
- Cache hit rate
- Queue depth
- GPU utilization
- Error rate

**Silver Tier Metrics**:
- p50/p95/p99 latency
- Tool call latency (MCP)
- Response quality scores
- Throughput (tokens/second)

**Bronze Tier Metrics**:
- Job queue depth
- Average job duration
- Success/failure rate
- Cost per job

### Alerting

**Critical Alerts**:
- Gold tier p95 > 16ms
- Cache hit rate < 70%
- Queue depth > 100
- GPU utilization > 95% (potential bottleneck)

**Warning Alerts**:
- Silver tier p95 > 250ms
- Bronze tier job failures > 5%
- Cost anomalies (>20% increase)

### Tracing

**OpenTelemetry Integration**:
- Trace requests across all tiers
- Identify bottlenecks
- Measure end-to-end latency
- Track MCP tool call latencies

---

## QUALITY CONTROL & GUARDRAILS

### Non-AI Detectable Output

**Training Requirements**:
- SRL→RLVR training includes "naturalness" in reward function
- Human evaluators rate output naturalness
- Continuous improvement based on feedback

**Post-Processing**:
- Add natural language variations
- Inject personality-consistent quirks
- Avoid repetitive patterns
- Vary response structure

**Monitoring**:
- A/B testing with human evaluators
- Track "AI-sounding" complaints
- Alert on quality degradation

### Guardrails Enforcement

**Content Filtering Pipeline**:
```python
class GuardrailPipeline:
    def __init__(self):
        self.toxicity_filter = ProtectAIGuard()
        self.bias_detector = BiasMonitor()
        self.content_policy = GameContentPolicy()
    
    async def filter_output(self, output: str, context: dict) -> FilterResult:
        """Multi-layer content filtering"""
        checks = await asyncio.gather(
            self.toxicity_filter.check(output),
            self.bias_detector.check(output),
            self.content_policy.check(output, context)
        )
        
        if any(c.violation for c in checks):
            return FilterResult(blocked=True, reason=checks)
        
        return FilterResult(blocked=False, output=output)
```

**Enforcement Points**:
- Request time: Filter prompts before sending to models
- Response time: Filter outputs before returning to players
- Post-deployment: Continuous monitoring for violations

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation (Weeks 1-2)
- ✅ Stand up EKS with L4 and A10G node groups
- ✅ Deploy vLLM and TensorRT-LLM infrastructure
- ✅ Implement router/orchestrator with three-tier routing
- ✅ Set up OpenSearch Serverless for RAG
- ✅ Baseline latency tests for all tiers
- ✅ Implement KV/prefix caching
- ✅ Instrument telemetry (OpenTelemetry, Prometheus)

### Phase 2: Training (Weeks 3-6)
- ✅ Train Gold tier models (3B-8B) with SRL→RLVR
- ✅ Train Silver tier models (7B-13B) with SRL→RLVR
- ✅ Set up DeepSeek-V3 Bronze tier infrastructure
- ✅ Implement speculative decoding for Gold tier
- ✅ Deploy MCP servers (Storyteller, Cybersecurity, Admin, Game State)
- ✅ Wire up storyteller Bronze jobs via SageMaker Async

### Phase 3: Integration (Weeks 7-10)
- ✅ Implement NPC controller decoupling (micro-policy + LLM intent)
- ✅ Build intent cache system
- ✅ Integrate state prediction service
- ✅ Deploy ahead-of-user rendering
- ✅ Connect all tiers to game engine
- ✅ End-to-end testing

### Phase 4: Optimization (Weeks 11-12)
- ✅ Optimize batching and cost
- ✅ Implement nightly distillation (Bronze → Silver → Gold)
- ✅ Expand multi-region deployment
- ✅ Performance tuning
- ✅ Cost optimization

---

## SUCCESS METRICS

### Performance
- ✅ Gold tier: p95 < 16ms (real-time NPCs)
- ✅ Silver tier: p95 80-250ms (interactive NPCs)
- ✅ Game frame rate: 300+ FPS maintained
- ✅ Cache hit rate: 80%+ for Gold tier

### Quality
- ✅ Output quality matches/exceeds for-pay models
- ✅ Non-AI detectable output (human evaluation >90%)
- ✅ Zero guardrail violations
- ✅ Player satisfaction maintained/improved

### Cost
- ✅ Training costs within budget
- ✅ Inference costs 10-50× lower than for-pay
- ✅ Break-even within 3-6 months
- ✅ Predictable scaling costs

### Reliability
- ✅ 99.9% uptime for Gold tier
- ✅ Graceful degradation on failures
- ✅ Zero game-breaking incidents

---

## MANDATORY ENFORCEMENT

### ALL Rules Apply
**CRITICAL**: All rules in `/all-rules` must be followed:
- Peer-based coding
- Pairwise testing
- Three-AI review
- Comprehensive testing
- Memory consolidation
- 45-minute milestones
- Timer service
- Work visibility
- Automatic continuation

---

**END OF MULTI-TIER MODEL ARCHITECTURE SOLUTION**

