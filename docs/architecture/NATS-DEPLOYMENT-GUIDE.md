# NATS Binary Messaging - Deployment Guide

**Status**: Infrastructure Deployed, Services Ready for Deployment  
**Date**: 2025-11-13  
**Progress**: 70% Complete

---

## ✅ COMPLETED WORK

### Infrastructure (100%)
- ✅ **Redis Cluster**: 3 shards, r7g.large, Multi-AZ deployed
  - Endpoint: `clustercfg.gaming-system-redis.wfaijn.use1.cache.amazonaws.com:6379`
  - TLS + AUTH enabled
  - CloudWatch monitoring configured
  - Cost: $1,288/month

- ✅ **NATS Cluster**: 5 nodes, m6i.large, 3 AZs deployed
  - Endpoint: `nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222`
  - Internal NLB configured
  - JetStream ready (500GB per node)
  - Cost: $420/month
  - **Note**: Running without TLS for dev/test (TLS certificates pending)

### Protocol Buffers (100%)
- ✅ 23 proto schemas created and compiled
- ✅ Peer reviewed by GPT-5 Pro with critical fixes applied
- ✅ All schemas versioned (v1)
- ✅ 46 Python files generated (pb2.py + pb2_grpc.py)

### Python SDK (100%)
- ✅ Production-ready SDK with 6 modules
- ✅ Request/reply, pub/sub, queue groups, streaming
- ✅ Circuit breakers, retries, tracing
- ✅ End-to-end tested and working

### Service Migrations (100%)
- ✅ 22/22 services migrated to NATS:
  - Core AI: ai_integration, model_management, ai_router
  - Game: quest_system, npc_behavior, world_state, body_broker_integration
  - Infrastructure: router, event_bus, orchestration, auth, capability-registry
  - Content: story_teller, environmental_narrative, language_system, knowledge_base
  - Utilities: time_manager, weather_manager, settings, payment, performance_mode, state_manager

### Gateway (100%)
- ✅ HTTP→NATS gateway with production fixes
- ✅ Streaming support (SSE)
- ✅ Error mapping and backpressure handling

### Testing (50%)
- ✅ End-to-end test passing (AI Integration)
- ✅ NATS communication verified
- ⏳ Comprehensive test suite created (needs all services running)
- ⏳ Load testing pending
- ⏳ Latency benchmarking pending

---

## 🚧 PENDING WORK

### TLS Certificates (High Priority)
1. Create ACM Private CA
2. Generate server certificates for NATS
3. Deploy certificates to NATS instances via SSM
4. Update NATS config to enable TLS
5. Restart NATS services

### Docker Images (High Priority)
1. Build Docker images for all 22 services
2. Push to ECR
3. Create ECS task definitions
4. Deploy to ECS Fargate

### ECS Deployment
1. Create task definitions (22 services)
2. Create ECS services with NATS_URL environment
3. Configure auto-scaling
4. Deploy gateway service
5. Update ALB routing

### Monitoring
1. Deploy Prometheus + Grafana
2. Configure NATS surveyor
3. Set up CloudWatch dashboards
4. Create alerts for latency/errors

### Testing & Validation
1. Run all services in AWS
2. Execute comprehensive test suite
3. Load testing at 10x scale
4. Latency validation (<5ms)
5. Red Alert integration

### Cutover
1. Deploy dual-stack (HTTP + NATS)
2. Traffic shadowing
3. Gradual cutover (10% → 100%)
4. HTTP retirement

---

## 📋 DEPLOYMENT CHECKLIST

### Phase 1: TLS Setup (Week 1)
- [ ] Create ACM Private CA
- [ ] Generate NATS server certificates
- [ ] Deploy via AWS Systems Manager
- [ ] Configure NATS with TLS
- [ ] Verify NATS cluster health

### Phase 2: Service Deployment (Week 2)
- [ ] Build all 22 Docker images
- [ ] Push to ECR
- [ ] Create ECS task definitions
- [ ] Deploy services to Fargate
- [ ] Verify all services healthy
- [ ] Deploy HTTP→NATS gateway
- [ ] Configure ALB

### Phase 3: Testing (Week 3)
- [ ] Run end-to-end tests
- [ ] Load testing (10K req/sec)
- [ ] Latency benchmarking
- [ ] Error handling validation
- [ ] Concurrency testing (100+ simultaneous)

### Phase 4: Migration (Week 4-5)
- [ ] Deploy dual-stack services
- [ ] Traffic shadowing setup
- [ ] Gradual cutover (10% → 50% → 100%)
- [ ] Validate latency improvements
- [ ] Monitor error rates

### Phase 5: Cleanup (Week 6)
- [ ] Retire HTTP endpoints
- [ ] Remove gateway
- [ ] Performance optimization
- [ ] Final documentation

---

## 🚀 QUICK START - LOCAL TESTING

### Prerequisites
```bash
# Install NATS server locally
# Windows: Download from https://github.com/nats-io/nats-server/releases
# Linux/Mac: brew install nats-server or apt/yum install nats-server

# Install Python dependencies
pip install nats-py protobuf opentelemetry-api opentelemetry-sdk
```

### Start NATS Server
```bash
# Windows
C:\Users\kento\nats-server\nats-server-v2.10.7-windows-amd64\nats-server.exe --jetstream

# Linux/Mac
nats-server --jetstream
```

### Set Python Path
```bash
# Windows PowerShell
$env:PYTHONPATH = "E:\Vibe Code\Gaming System\AI Core\sdk;E:\Vibe Code\Gaming System\AI Core\generated"

# Linux/Mac
export PYTHONPATH="$PWD/sdk:$PWD/generated"
```

### Start Example Service
```bash
python examples/ai_integration_service.py
```

### Run Example Client
```bash
python examples/ai_integration_client.py
```

Expected output:
```
Connected to NATS
Sending request to svc.ai.llm.v1.infer
Generation ID: gen-abc123
Output: Response to: Tell me about NATS messaging
Tokens used: 30
Finish reason: stop
```

### Run Tests
```bash
python -m pytest tests/nats/test_end_to_end.py -v
```

---

## 🏗️ AWS DEPLOYMENT

### Build Docker Image (Example)
```bash
cd "E:\Vibe Code\Gaming System\AI Core"

# Build
docker build -f services/ai_integration/Dockerfile.nats -t ai-integration-nats:latest .

# Tag for ECR
docker tag ai-integration-nats:latest 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services/ai-integration-nats:latest

# Push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 695353648052.dkr.ecr.us-east-1.amazonaws.com
docker push 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services/ai-integration-nats:latest
```

### Create ECS Service
```bash
aws ecs create-service \
  --cluster gaming-system-cluster \
  --service-name ai-integration-nats \
  --task-definition gaming-system-nats-services \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0f353054b8e31561d,subnet-036ef66c03b45b1da],securityGroups=[sg-00419f4094a7d2101],assignPublicIp=ENABLED}"
```

---

## 📊 PERFORMANCE EXPECTATIONS

### Latency
- **Target**: <5ms end-to-end
- **Current HTTP**: 5-20ms
- **Expected NATS**: 1-3ms (AWS intra-VPC)
- **Local Testing**: <1ms
- **Improvement**: 5-20x faster

### Throughput
- **Target**: 10K req/sec per service
- **Current HTTP**: ~1K req/sec
- **NATS Capacity**: 50K+ req/sec per node
- **Improvement**: 10x higher

### Payload Size
- **JSON (HTTP)**: ~2-5KB typical
- **Protobuf (NATS)**: ~0.5-1.5KB typical
- **Improvement**: 3-5x smaller

---

## 🔧 TROUBLESHOOTING

### NATS Server Not Accessible
```bash
# Check if running
ps aux | grep nats-server

# Check logs
tail -f /var/log/nats/nats-server.log

# Test connection
nc -zv localhost 4222
```

### Service Import Errors
```bash
# Ensure PYTHONPATH is set
echo $PYTHONPATH

# Should include:
# - /path/to/sdk
# - /path/to/generated
```

### No Responders Error
- Service not running or not subscribed
- Check service logs
- Verify NATS_URL matches server
- Verify subject name matches exactly

### Docker Build Failures
- Ensure SDK and generated directories exist
- Check Dockerfile paths are correct
- Verify Python dependencies in requirements

---

## 📖 REFERENCES

- [Binary Messaging Requirements](./BINARY-MESSAGING-REQUIREMENTS.md)
- [ADR-002: NATS Architecture](./ADR-002-NATS-Binary-Messaging.md)
- [Migration Handoff](../../Project-Management/HANDOFF-NATS-Migration-2025-11-13.md)
- [NATS Documentation](https://docs.nats.io/)
- [Protocol Buffers](https://protobuf.dev/)

---

## 🎯 SUCCESS CRITERIA

**Infrastructure Complete When**:
- [x] Redis Cluster deployed and operational
- [x] NATS Cluster deployed with 5 healthy nodes
- [ ] TLS certificates configured

**Services Complete When**:
- [x] All 22 services migrated to NATS code
- [ ] All services deployed to ECS
- [ ] All services healthy and responding
- [ ] <5ms latency validated

**Migration Complete When**:
- [ ] Dual-stack operational
- [ ] Traffic shadowing validated
- [ ] 100% NATS cutover
- [ ] HTTP endpoints retired
- [ ] Performance targets met

---

**Current Phase**: Infrastructure Deployed, Services Ready for Docker/ECS
**Next Phase**: TLS Configuration → Docker Build → ECS Deployment  
**Timeline**: 1-2 weeks for complete AWS deployment

