# Multi-Tier Architecture - Integration Patterns

**Date**: 2025-11-03  
**Status**: M5 - Integration & Testing  
**Purpose**: Document integration patterns for Gold, Silver, and Bronze tiers

---

## Overview

This document describes integration patterns for the three-tier model architecture, including:
- Request routing and tier selection
- Fallback strategies
- Cache integration
- State synchronization
- Error handling

---

## Tier Routing Patterns

### Real-Time Requests (Gold Tier)

**Use Case**: NPC actions at game frame rate (300+ FPS)

**Pattern**:
```python
# Router selects Gold tier for real-time requests
request = {
    "prompt": "NPC action: move forward",
    "max_tokens": 8,
    "sla": "real-time",
    "latency_budget_ms": 16
}

response = router.route(request)
# Routes to Gold tier (TensorRT-LLM)
# Expected latency: < 16ms p95
```

**Characteristics**:
- Sub-16ms latency requirement
- Short token generation (4-8 tokens)
- Deterministic micro-policies
- Intent caching for smooth transitions

---

### Interactive Requests (Silver Tier)

**Use Case**: Complex NPC dialogue, player support, tool use

**Pattern**:
```python
# Router selects Silver tier for interactive requests
request = {
    "prompt": "NPC responds to player question",
    "max_tokens": 100,
    "sla": "interactive",
    "latency_budget_ms": 200,
    "tools": ["game_state_query", "rag_search"]
}

response = router.route(request)
# Routes to Silver tier (vLLM with MCP tools)
# Expected latency: 80-250ms p95
```

**Characteristics**:
- 80-250ms latency requirement
- Medium token generation (50-200 tokens)
- MCP tool integration enabled
- Complex dialogue and reasoning

---

### Async Requests (Bronze Tier)

**Use Case**: Story generation, worldbuilding, cybersecurity, admin tasks

**Pattern**:
```python
# Router selects Bronze tier for async requests
request = {
    "prompt": "Generate story arc about player exploration",
    "max_tokens": 500,
    "sla": "async",
    "latency_budget_ms": 5000
}

job = router.route(request)
# Routes to Bronze tier (SageMaker Async Inference)
# Returns job_id for async retrieval
# Expected latency: seconds acceptable
```

**Characteristics**:
- Seconds acceptable latency
- Large token generation (100-2000 tokens)
- SageMaker Async Inference
- Results stored in S3, retrieved via API

---

## Fallback Strategies

### Gold → Silver Fallback

**Trigger**: Gold tier unavailable or latency exceeded

**Pattern**:
```python
try:
    response = gold_tier.infer(request, timeout=0.016)
except (TimeoutError, ConnectionError):
    # Fallback to Silver tier
    response = silver_tier.infer(request, timeout=0.25)
```

**Use Cases**:
- Gold tier overloaded
- Network issues
- Gold tier maintenance

---

### Silver → Bronze Fallback

**Trigger**: Silver tier unavailable or latency exceeded

**Pattern**:
```python
try:
    response = silver_tier.infer(request, timeout=0.25)
except (TimeoutError, ConnectionError):
    # Fallback to Bronze tier (async)
    job = bronze_tier.submit_async(request)
    response = bronze_tier.retrieve_result(job.job_id)
```

**Use Cases**:
- Silver tier overloaded
- Tool call failures
- Silver tier maintenance

---

## Cache Integration Patterns

### Intent Cache (Gold Tier)

**Purpose**: Smooth transitions between cached and updated intents

**Pattern**:
```python
class IntentCache:
    def get_intent(self, npc_id: str) -> Dict:
        """Get cached intent or return default."""
        cached = self.cache.get(npc_id)
        if cached and not cached.expired:
            return cached.intent
        return self.default_intent
    
    def update_intent(self, npc_id: str, intent: Dict):
        """Update cached intent (async, non-blocking)."""
        self.cache.set(npc_id, intent, ttl=1.0)  # 1 second TTL
```

**Integration**:
- Micro-policies read from cache (every frame)
- LLM updates cache asynchronously (1-2 Hz)
- Cache miss → use default intent → update async

---

### Result Cache (Silver/Gold from Bronze)

**Purpose**: Cache Bronze tier results for Silver/Gold tier use

**Pattern**:
```python
# Bronze tier generates story arc
story_arc = bronze_tier.generate_story_arc(prompt)

# Cache result for Silver/Gold tier queries
cache.set(f"story_arc:{story_arc.id}", story_arc, ttl=3600)

# Silver/Gold tier queries use cached result
cached_story = cache.get(f"story_arc:{story_arc.id}")
if cached_story:
    return cached_story
```

**Integration**:
- Bronze tier outputs stored in cache
- Silver/Gold tiers query cache before generating
- Cache miss → generate new content → store in cache

---

## State Synchronization Patterns

### Game State → Silver Tier

**Pattern**: Silver tier queries game state via MCP

```python
# Silver tier uses Game State MCP
game_state = mcp_game_state.query_npc_state(npc_id)
context = {
    "npc_state": game_state,
    "player_state": game_state.get_player_state(),
    "world_state": game_state.get_world_snapshot()
}

response = silver_tier.infer(prompt, context=context)
```

---

### Bronze Tier → Persistent Storage

**Pattern**: Bronze tier outputs stored in Aurora

```python
# Bronze tier generates content
story_arc = bronze_tier.generate_story_arc(prompt)

# Store in Aurora Postgres
db.store_story_arc(story_arc)

# Store assets in S3
s3.store_asset(story_arc.id, story_arc.assets)

# Index in OpenSearch for retrieval
opensearch.index_story_arc(story_arc)
```

---

## Error Handling Patterns

### Timeout Handling

**Pattern**:
```python
try:
    response = tier.infer(request, timeout=latency_budget)
except TimeoutError:
    # Fallback to next tier or return cached result
    if tier == "gold":
        return fallback_to_silver(request)
    elif tier == "silver":
        return fallback_to_bronze(request)
    else:
        return get_cached_result(request)
```

---

### Circuit Breaker Pattern

**Pattern**:
```python
class TierCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen("Tier unavailable")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

---

## Monitoring Patterns

### Latency Monitoring

**Pattern**:
```python
# Track latency per tier
with latency_tracker("gold_tier"):
    response = gold_tier.infer(request)

# Metrics exported to Prometheus
# - gold_tier_latency_p95
# - silver_tier_latency_p95
# - bronze_tier_latency_p95
```

---

### Cost Monitoring

**Pattern**:
```python
# Track cost per tier per request
cost_tracker.record_request(
    tier="gold",
    tokens_generated=8,
    latency_ms=12,
    cost_usd=0.0001
)

# Cost monitoring script aggregates costs
# - Gold tier: EC2 instance costs
# - Silver tier: EC2 instance costs
# - Bronze tier: SageMaker inference costs
```

---

## Testing Patterns

### Integration Test Structure

**Pattern**:
```python
# Test each tier independently
class TestGoldTier:
    def test_latency_requirement(self):
        # Test p95 < 16ms
        pass
    
    def test_health_check(self):
        # Test health endpoint
        pass

# Test router integration
class TestRouter:
    def test_routing_logic(self):
        # Test tier selection
        pass
    
    def test_fallback_strategy(self):
        # Test fallback behavior
        pass
```

---

## Deployment Patterns

### Validation Scripts

**Pattern**:
```powershell
# Validate each tier deployment
.\infrastructure\scripts\validation\validate-gold-tier.ps1
.\infrastructure\scripts\validation\validate-silver-tier.ps1
.\infrastructure\scripts\validation\validate-bronze-tier.ps1

# Validate all tiers
.\infrastructure\scripts\validation\validate-all-tiers.ps1
```

---

## Summary

**Key Integration Points**:
1. **Router**: Routes requests to optimal tier
2. **Cache**: Smooths transitions and reduces latency
3. **Fallback**: Handles tier failures gracefully
4. **State Sync**: Keeps tiers synchronized with game state
5. **Monitoring**: Tracks latency, cost, and health

**Next Steps**:
- Implement router service
- Integrate cache layers
- Deploy monitoring dashboards
- Complete integration testing

---

**Status**: M5 - Integration & Testing in progress

