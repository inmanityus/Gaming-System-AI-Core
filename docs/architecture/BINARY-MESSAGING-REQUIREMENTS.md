# Binary Messaging Architecture Requirements
**Project**: Gaming System AI Core (The Body Broker)  
**Date**: 2025-11-13  
**Status**: Architecture Design Phase  
**Peer Reviewed By**: GPT-5 Pro, Gemini 2.0 Flash, Claude 3.7 Sonnet

---

## 🎯 MISSION

Migrate 22 microservices from HTTP/REST to binary messaging architecture optimized for AI model-to-AI model communication at gaming scale.

---

## 📊 MODEL CONSENSUS ANALYSIS

### Consulted Models (3)

1. **GPT-5 Pro** (openai/gpt-5-pro) → **NATS primary recommendation**
2. **Gemini 2.0 Flash** (google/gemini-2.0-flash-exp:free) → **NATS + gRPC hybrid**
3. **Claude 3.7 Sonnet** (anthropic/claude-3.7-sonnet) → **gRPC primary, NATS runner-up**

### Consensus Decision: **NATS with JetStream**

**Why NATS Won** (2/3 models primary, 3/3 models favorable):

1. **Latency**: Sub-millisecond (0.3-1ms p50, 1-3ms p99) vs HTTP 5-20ms
2. **AI-to-AI Optimized**: Binary protocol, no human readability overhead
3. **Patterns Match Use Case**: Request/reply + pub/sub + queue groups
4. **Operational Simplicity**: Far simpler than Kafka, cleaner than gRPC mesh
5. **Scalability**: Interest-based routing, linear scaling with queue groups
6. **Distributed by Design**: Built-in clustering, JetStream for durability
7. **Security**: Native mTLS, JWT/NKey ACLs, subject-level permissions

**gRPC Role**: Secondary for infrastructure services requiring strict schemas (Model Management, fine-tuning APIs)

**Kafka**: Eliminated - 10-50ms latency unacceptable for AI inference critical path

---

## 📋 REQUIREMENTS

### REQ-BINARY-001: Ultra-Low Latency
**Priority**: P0 (Critical)  
**Target**: <5ms end-to-end for AI inference critical path  
**Current**: 5-20ms HTTP overhead  
**Solution**: NATS 0.3-1ms p50 latency

### REQ-BINARY-002: Binary Protocol
**Priority**: P0 (Critical)  
**Requirement**: All inter-service messages MUST be binary (not JSON)  
**Rationale**: Security, performance, compact payloads  
**Solution**: Protocol Buffers (protobuf) serialization

### REQ-BINARY-003: AI-to-AI Optimization
**Priority**: P0 (Critical)  
**Requirement**: Optimized for AI model-to-model communication  
**No Requirement**: Human readability NOT needed  
**Solution**: Binary protobuf, no JSON fallback

### REQ-BINARY-004: Rapid Scaling
**Priority**: P0 (Critical)  
**Requirement**: Handle 10x traffic spikes within 60 seconds  
**Use Case**: Game launch, viral growth scenarios  
**Solution**: NATS queue groups + ECS auto-scaling

### REQ-BINARY-005: Distributed Caching
**Priority**: P0 (Critical)  
**Requirement**: Multi-tier caching for stability under load  
**Solution**: Redis Cluster (distributed) + in-process LRU (local)  
**Target**: <1ms cache hit latency

### REQ-BINARY-006: Network Stress Tolerance
**Priority**: P1 (High)  
**Requirement**: System remains stable under game testing network stress  
**Solution**: NATS broker absorbs bursts, JetStream buffering

### REQ-BINARY-007: Security
**Priority**: P0 (Critical)  
**Requirement**: Binary messages more secure than HTTP/JSON  
**Solution**: mTLS, JWT/NKey per-service ACLs, subject-level permissions

### REQ-BINARY-008: AWS ECS Fargate Deployment
**Priority**: P0 (Critical)  
**Requirement**: Must work on existing AWS ECS Fargate infrastructure  
**Solution**: NATS cluster on EC2, services on Fargate connect via NLB

### REQ-BINARY-009: Service Discovery
**Priority**: P0 (Critical)  
**Requirement**: Automatic service discovery, no manual endpoint management  
**Solution**: NATS subject-based routing + Key-Value store for metadata

### REQ-BINARY-010: Schema Management
**Priority**: P0 (Critical)  
**Requirement**: Versioned schemas, backward compatibility  
**Solution**: Protocol Buffers with buf.build tooling, subject versioning (v1, v2)

### REQ-BINARY-011: Zero-Downtime Migration
**Priority**: P0 (Critical)  
**Requirement**: Migrate from HTTP without service interruption  
**Solution**: Dual-stack (HTTP + NATS), gradual cutover, traffic shadowing

### REQ-BINARY-012: Observable
**Priority**: P1 (High)  
**Requirement**: Full observability of message flows  
**Solution**: NATS surveyor, prometheus exporter, OpenTelemetry tracing

---

## 🏗️ ARCHITECTURE DESIGN

### Primary Messaging: NATS Core + JetStream

**NATS Topology**:
```
NATS Cluster (5 nodes across 3 AZs)
├── Node Type: EC2 m6i.large (2 vCPU, 8GB RAM)
├── Storage: gp3 EBS 500GB per node (encrypted, KMS CMK)
├── Network: Internal NLB for 4222 (client TLS)
├── Security: mTLS via ACM Private CA, JWT/NKey per service
└── JetStream: File storage for durable streams
```

**Communication Patterns**:
1. **Request/Reply** (synchronous AI inference)
   - Subject: `ai.<service>.<operation>.request.v1`
   - Reply: Caller provides inbox, responder replies once
   - Latency: 0.3-1ms p50

2. **Pub/Sub** (world state, NPC events, orchestration)
   - Subject: `ai.<domain>.state.update.v1.<entity_id>`
   - JetStream: 1-5 minute retention for replay
   - Latency: 1-3ms end-to-end

3. **Queue Groups** (load-balanced workers)
   - Pattern: Multiple instances subscribe with same queue group
   - NATS load balances across instances
   - Scale linearly by adding instances

4. **Streaming** (LLM token generation)
   - Temporary inbox for response stream
   - Multiple small frames with sequence numbers
   - Final frame with EOS header

### Secondary Messaging: gRPC (Infrastructure)

**Use Cases**:
- Model Management API (model registry, versioning)
- Fine-tuning Pipeline (long-running operations)
- Admin Operations (management, configuration)

**Why gRPC Here**:
- Strong schema enforcement needed
- Less latency-critical than inference
- Complex request/response structures

### Distributed Cache: Redis Cluster

**Configuration**:
```
Amazon ElastiCache for Redis 7 (Cluster Mode)
├── Shards: 3 (r6g.large or r7g.large)
├── Replicas: 1 per shard
├── Security: TLS in-transit, AUTH with ACLs, KMS at-rest
└── Purpose: Game state, model weights, AI responses
```

**Caching Strategy**:
- **Layer 1**: In-process LRU (25-100ms TTL) - shave RTT
- **Layer 2**: Redis Cluster (distributed) - 0.5-1ms latency
- **Key Patterns**:
  - `world:{world_id}:snapshot` → msgpack/zstd, 1-5s TTL
  - `npc:{npc_id}:state` → protobuf, 100-500ms TTL
  - `model:{model_id}:tokenizer` → binary, hours TTL

### Service Discovery

**NATS-Native** (for NATS services):
- Subject-based routing (built-in)
- Services subscribe with queue groups
- NATS Key-Value store for metadata
- No external discovery needed

**AWS Cloud Map** (for gRPC services):
- DNS-based discovery
- ECS Service Connect integration
- Centralized registration

---

## 📐 SUBJECT DESIGN

### Namespace Structure
```
ai.<domain>.<service>.<operation>.v<major>.<optional_id>
```

### Examples
```
ai.world.state.update.v1.<world_id>
ai.npc.behavior.request.v1
ai.npc.behavior.reply.v1
ai.quest.generate.request.v1
ai.quest.generate.reply.v1
ai.model.infer.request.v1.<model_id>
ai.model.infer.token.v1.<request_id>
ai.audit.event.v1
ai.training.signal.v1
```

### Queue Groups
```
q.quest      → Quest generation workers
q.npc        → NPC behavior workers
q.model      → Model inference workers
q.world      → World state workers
```

---

## 🔐 SECURITY ARCHITECTURE

### Layer 1: Transport Security
- TLS 1.2/1.3 mTLS between all services and NATS
- ACM Private CA for certificate issuance
- Certificate rotation every 90 days

### Layer 2: Authentication
- JWT tokens with NKeys per service account
- No authentication fallback (deny all unauthenticated)
- Separate accounts per environment (dev/test/prod)

### Layer 3: Authorization
- Per-subject ACLs via NATS accounts
- Least privilege: services can only pub/sub to their subjects
- Deny-by-default rules

### Layer 4: Data Protection
- Payload encryption for sensitive data
- zstd compression for large payloads (>16KB)
- Path traversal prevention in subject names

---

## 🔄 MIGRATION STRATEGY

### Phase 0: Infrastructure Setup (Week 1)
- [ ] Deploy NATS cluster (5 nodes, 3 AZs)
- [ ] Configure mTLS and JWT/NKey authentication
- [ ] Set up Internal NLB
- [ ] Deploy Redis Cluster (ElastiCache)
- [ ] Create shared Python SDK (NATS client wrapper)
- [ ] Set up monitoring (Prometheus, Grafana)

### Phase 1: Schema Definition (Week 1-2)
- [ ] Define Protocol Buffer schemas for all 22 services
- [ ] Set up buf.build for schema management
- [ ] Generate Python code from protobuf
- [ ] Publish proto stubs to internal PyPI
- [ ] Create contract tests

### Phase 2: Adapter Bridge (Week 2-3)
- [ ] Implement NATS→HTTP adapters for each service
- [ ] Deploy adapters as sidecars or embedded
- [ ] Services still use HTTP internally, NATS externally
- [ ] Validate end-to-end with adapters

### Phase 3: Service Refactoring (Week 3-6)
- [ ] Refactor Tier 1 services (independent) to native NATS
- [ ] Refactor Tier 2 services (core) to native NATS
- [ ] Refactor Tier 3-6 services (application) to native NATS
- [ ] Remove adapters as services converted
- [ ] Implement queue groups for scaling

### Phase 4: HTTP Retirement (Week 6-7)
- [ ] Traffic shadowing (dual HTTP + NATS)
- [ ] Gradual cutover to 100% NATS
- [ ] Remove all HTTP endpoints except external APIs
- [ ] Performance validation and tuning

### Phase 5: Optimization (Week 7-8)
- [ ] JetStream configuration tuning
- [ ] Cache hit ratio optimization
- [ ] Latency profiling and optimization
- [ ] Load testing at 10x scale

---

## 🎯 SUCCESS CRITERIA

### Performance Targets
- [x] Latency: <5ms end-to-end for AI inference (Target: 1-3ms with NATS)
- [x] Throughput: Handle 10K req/sec per service
- [x] Cache hit rate: >90% for frequently accessed data
- [x] Zero message loss on critical paths (JetStream)

### Reliability Targets
- [x] 99.9% uptime for NATS cluster
- [x] Graceful degradation on node failures
- [x] Zero-downtime deployments
- [x] Sub-minute scaling response

### Security Targets
- [x] mTLS on all service-to-NATS connections
- [x] Per-service JWT/NKey authentication
- [x] Subject-level authorization
- [x] Encrypted at-rest (EBS, S3)

---

## 📊 EXPECTED IMPROVEMENTS

### vs Current HTTP/REST

| Metric | HTTP/REST | NATS | Improvement |
|--------|-----------|------|-------------|
| Latency (p50) | 5-20ms | 0.3-1ms | **5-20x faster** |
| Latency (p99) | 20-50ms | 2-4ms | **10-25x faster** |
| Throughput | 1K req/sec | 10K+ req/sec | **10x higher** |
| Payload Size | JSON verbose | Protobuf compact | **3-5x smaller** |
| Security | TLS optional | mTLS required | **Stronger** |
| Scaling | Manual | Queue groups | **Automatic** |

---

## 🛠️ TECHNOLOGY STACK

### Messaging
- **NATS Core + JetStream** (primary, 95% of traffic)
- **gRPC** (secondary, infrastructure APIs)
- **Protocol Buffers** (schema definition)

### Caching
- **Redis Cluster** (Amazon ElastiCache, cluster mode)
- **In-process LRU** (cachetools, 25-100ms TTL)

### Service Discovery
- **NATS subject-based routing** (built-in)
- **AWS Cloud Map** (optional, for gRPC)

### Deployment
- **NATS Cluster**: EC2 m6i.large, 5 nodes, 3 AZs
- **Microservices**: AWS ECS Fargate (existing)
- **Load Balancer**: Internal NLB for NATS

### Observability
- **NATS Surveyor** (metrics collection)
- **Prometheus + Grafana** (metrics visualization)
- **OpenTelemetry** (distributed tracing)
- **CloudWatch** (AWS integration)

---

## 🚀 IMPLEMENTATION PRIORITY

### Critical Path (Week 1-2)
1. NATS cluster deployment
2. Schema definition for AI inference services
3. AI Integration → Model Management migration
4. Quest System → NPC Behavior migration

### High Priority (Week 3-4)
5. State Manager integration
6. World State pub/sub
7. Orchestration service
8. All AI-critical services

### Medium Priority (Week 5-6)
9. Remaining application services
10. HTTP retirement
11. Performance optimization

---

## 📝 NEXT STEPS

1. **Design Validation**: Review this document with 3+ models
2. **Detailed Design**: Create ADR with specific schemas
3. **Infrastructure**: Deploy NATS cluster and Redis
4. **Schema Repository**: Create protobuf definitions
5. **SDK Development**: Build shared Python NATS client library
6. **Migration Phase 1**: Deploy adapter bridges
7. **Service Refactoring**: Convert services to native NATS
8. **Testing**: Comprehensive latency and load testing
9. **Production Cutover**: Gradual migration with monitoring
10. **HTTP Retirement**: Remove old HTTP endpoints

---

## 🎓 KEY INSIGHTS FROM MODEL CONSULTATION

### From GPT-5 Pro
- **NATS is the clear winner** for sub-millisecond AI-to-AI at scale
- ProcessPoolExecutor patterns from NATS allow non-blocking operations
- Use queue groups for automatic load balancing
- JetStream provides durability where needed without sacrificing speed
- Subject design critical: `ai.<domain>.<service>.<operation>.v<version>`

### From Gemini 2.0 Flash
- **Hybrid approach**: NATS for critical path, gRPC for infrastructure
- Redis Cluster essential for distributed caching
- AWS ECS specifics: Fargate for services, EC2 for NATS nodes
- Operational complexity: NATS far simpler than Kafka

### From Claude 3.7 Sonnet
- Both gRPC and NATS are solid choices
- gRPC good for strongly typed APIs
- NATS better for flexible patterns and pub/sub
- Migration via dual-stack is safest approach

---

## ⚠️ CRITICAL DECISIONS

### Decision 1: NATS over Kafka
**Reason**: 10-50ms Kafka latency unacceptable for AI inference  
**Trade-off**: Lose Kafka's exactly-once semantics (use idempotency keys instead)  
**Validation**: GPT-5 Pro confirmed NATS superior for this use case

### Decision 2: Protocol Buffers over MessagePack/Avro
**Reason**: Schema enforcement, versioning, tooling maturity  
**Trade-off**: Slightly larger than MessagePack, simpler than Avro  
**Validation**: All 3 models recommended protobuf

### Decision 3: EC2 for NATS, Fargate for Services
**Reason**: JetStream needs persistent EBS disks  
**Trade-off**: Manage EC2 Auto Scaling Group  
**Validation**: GPT-5 Pro specified this pattern

### Decision 4: Queue Groups over Direct Service Mesh
**Reason**: Automatic load balancing, simpler operations  
**Trade-off**: Lose some point-to-point control  
**Validation**: NATS best practice for scalability

---

## 📖 REFERENCES

- **ADR-002**: Binary Messaging Migration (to be created)
- **GPT-5 Pro Analysis**: See consultation logs
- **Gemini 2.0 Analysis**: See consultation logs
- **Claude 3.7 Analysis**: See consultation logs
- **NATS Documentation**: https://docs.nats.io/
- **Protocol Buffers**: https://protobuf.dev/
- **buf.build**: https://buf.build/docs/

---

**Status**: Requirements Complete ✅  
**Next**: Detailed design phase with /complex-solution  
**Timeline**: 6-8 weeks for complete migration  
**Expected Result**: 5-20x latency improvement, production-grade AI messaging

