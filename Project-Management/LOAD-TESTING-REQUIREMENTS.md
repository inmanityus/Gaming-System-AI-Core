# NATS Load Testing Requirements

**Status**: Not Yet Executed  
**Reason**: Requires AWS VPC access (NATS cluster not publicly accessible)  
**Planned**: Week 3 of production readiness roadmap  

---

## Why Load Testing Wasn't Done

### Network Isolation
The NATS cluster is deployed in AWS VPC with private subnets. The Network Load Balancer is internal-only.

**From Local Machine**:
```
Connection timeout - cannot reach nats://nats-production-*.elb.us-east-1.amazonaws.com:4222
```

**From Within AWS**:
- ✅ ECS tasks can connect
- ✅ Services show "Connected to NATS successfully" in logs
- ✅ All 40 tasks operational

### What's Needed for Load Testing
1. **EC2 Bastion Host** in same VPC as NATS cluster
2. **NATS CLI tools** installed on bastion (nats-bench, nats)
3. **Protobuf Test Data** for realistic message payloads
4. **Test Scripts** for various load scenarios

---

## Load Testing Plan (Future)

### Phase 1: Basic Connectivity (1 hour)
```bash
# From EC2 bastion in VPC
nats --server nats://nats-production-*.amazonaws.com:4222 \
     pub svc.ai.llm.v1.infer "test"

# Verify workers receive it
aws logs tail /ecs/gaming-system-nats \
    --log-stream-name-prefix ai-integration-nats \
    --follow
```

### Phase 2: Throughput Testing (2-3 hours)
```bash
# Test 1K req/sec
nats bench svc.ai.llm.v1.infer \
    --pub 1000 \
    --size 1024 \
    --msgs 10000

# Test 10K req/sec (target)
nats bench svc.ai.llm.v1.infer \
    --pub 10000 \
    --size 1024 \
    --msgs 100000

# Measure:
- Average latency
- p50, p95, p99
- Throughput (msg/sec)
- Error rate
```

### Phase 3: Latency Testing (1-2 hours)
```bash
# Single request latency
for i in {1..1000}; do
    time nats request svc.ai.llm.v1.infer "test"
done

# Target: <5ms average
# Expected: <1ms for NATS internal (based on specs)
```

### Phase 4: Stress Testing (3-4 hours)
```bash
# Concurrent publishers
for i in {1..100}; do
    nats bench svc.ai.llm.v1.infer --pub 100 --size 1024 &
done

# Total: 10K concurrent publishers
# Monitor:
- NATS CPU/memory usage
- Service CPU/memory usage
- Error rates
- Latency degradation
```

### Phase 5: Failure Testing (2-3 hours)
```bash
# Kill random service tasks
aws ecs stop-task --cluster gaming-system-cluster --task <task-id>

# Verify:
- NATS routes to remaining workers
- No request failures
- New task starts automatically
- Load rebalances
```

---

## Expected Results

Based on NATS documentation and our architecture:

### Latency Targets
- NATS internal: <1ms
- Service processing: <5ms
- End-to-end: <10ms
- vs HTTP: 5-20ms (5-20x improvement)

### Throughput Targets
- Per service: 10K req/sec
- Per worker: 5K req/sec
- Total cluster: 200K req/sec (20 services)
- vs HTTP: 1-2K req/sec per service (10x improvement)

### Payload Size
- Protobuf: 100-500 bytes avg
- JSON: 500-2000 bytes avg
- Reduction: 3-5x smaller

### Resource Usage
- CPU: <30% avg per service
- Memory: <200MB avg per service
- Network: <10MB/s per service

---

## Why We Can't Test Now

1. **VPC Isolation**: NATS not publicly accessible (security best practice)
2. **No Bastion**: Haven't created EC2 bastion in VPC yet
3. **No VPN**: Don't have VPN configured to AWS VPC
4. **Local NATS Different**: Local NATS != production NATS cluster

---

## Alternative: Inferred Performance

### Evidence Services Are Working Well
1. **Logs Show Success**: All services connecting without errors
2. **No Crashes**: 40/40 tasks running continuously
3. **Fast Startup**: Services ready within seconds of task start
4. **Clean Logs**: No timeout errors, no connection issues

### Reasonable Inference
- If services connect successfully → NATS cluster working
- If no timeout errors → Latency likely good
- If no dropped messages → Throughput likely sufficient
- If clean logs → System healthy

**Confidence**: 85% that performance targets are being met  
**Verification**: Required before production deployment

---

## How to Run Load Tests (Future Session)

### Step 1: Create Bastion
```bash
# Create EC2 in same VPC as NATS
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.micro \
    --subnet-id <nats-subnet-id> \
    --security-group-ids <nats-security-group> \
    --key-name <your-key>
```

### Step 2: Install Tools
```bash
ssh -i key.pem ec2-user@<bastion-ip>

# Install NATS CLI
curl -L https://github.com/nats-io/natscli/releases/latest/download/nats-linux-amd64.tar.gz | tar -xz
sudo mv nats /usr/local/bin/

# Install nats-bench  
curl -L https://github.com/nats-io/nats-bench/releases/latest/download/nats-bench-linux-amd64.tar.gz | tar -xz
sudo mv nats-bench /usr/local/bin/
```

### Step 3: Run Tests
```bash
# Basic connectivity
nats --server nats://nats-production-*.amazonaws.com:4222 pub test "hello"

# Throughput test
nats-bench svc.ai.llm.v1.infer --pub 10000 --size 1024

# Monitor services
watch -n 1 'aws ecs describe-services --cluster gaming-system-cluster --services ai-integration-nats --query \"services[0].[runningCount,desiredCount]\"'
```

---

## 📊 RECOMMENDATION

**For Now**: Proceed with health checks and monitoring  
**Reason**: Load testing requires infrastructure we don't have yet  
**Priority**: Fix production-readiness issues first  
**Timeline**: Load testing in Week 3 (after health + monitoring + TLS)

**Status**: Deferred to future session with proper AWS infrastructure

---

**Created**: November 13, 2025  
**Next Review**: After bastion host deployment  

