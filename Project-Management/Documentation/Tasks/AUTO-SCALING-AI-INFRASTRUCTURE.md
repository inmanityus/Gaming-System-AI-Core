# 🚀 AUTO-SCALING AI INFRASTRUCTURE - Task Definition

**Task ID**: AI-SCALE-001  
**Priority**: CRITICAL  
**Estimated Effort**: 16-24 hours  
**Dependencies**: AI model deployment (AI-001, AI-002, AI-003, AI-004)  
**Status**: NOT STARTED

---

## 🎯 OBJECTIVE

Implement **auto-scaling infrastructure** for AI model serving that automatically scales GPU instances based on player demand from 0 → 10,000+ concurrent players.

---

## 📋 REQUIREMENTS

### Player Scaling Targets

| Players | Gold Tier GPUs | Silver Tier GPUs | Bronze Tier Instances |
|---------|----------------|------------------|-----------------------|
| 0-100 | 1 (min) | 1 (min) | 1 (min) |
| 100-500 | 2-3 | 1-2 | 1 |
| 500-1,000 | 5-10 | 3-5 | 1-2 |
| 1,000-5,000 | 10-25 | 5-15 | 2-4 |
| 5,000-10,000 | 25-50 | 15-30 | 4-8 |

### Scaling Metrics

**Primary Triggers**:
- **Queue Depth**: Messages waiting in SQS (target: < 100)
- **Latency P95**: Response time 95th percentile (Gold: <16ms, Silver: <250ms)
- **GPU Utilization**: Target 70-85% (not 100% - need headroom)
- **Player Count**: Active concurrent connections

**Secondary Triggers**:
- Request rate per second
- Cache hit rate (low = need more capacity)
- Error rate (high = overloaded)

---

## 🏗️ ARCHITECTURE

### Option A: ECS Auto-Scaling with Custom Metrics (RECOMMENDED)

**Components**:
1. **ECS Services** for each tier (gold-tier-inference, silver-tier-inference, bronze-tier-inference)
2. **Application Auto Scaling** with target tracking
3. **Custom CloudWatch Metrics** (queue depth, latency, GPU utilization)
4. **Metric Publisher** (Lambda or sidecar container)

**Scaling Policy**:
```python
# Gold Tier (Real-time)
{
    "TargetValue": 75.0,  # Target 75% GPU utilization
    "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ECSServiceAverageGPUUtilization"
    },
    "ScaleInCooldown": 300,   # 5 min cooldown before scale-in
    "ScaleOutCooldown": 60    # 1 min cooldown before scale-out
}

# Also scale on queue depth
{
    "TargetValue": 50.0,  # Target 50 messages in queue
    "CustomizedMetricSpecification": {
        "MetricName": "GoldTierQueueDepth",
        "Namespace": "GamingSystem/AI",
        "Statistic": "Average"
    }
}
```

**Pros**:
- Native AWS integration
- No additional infrastructure
- CloudWatch dashboards included
- Cost-effective

**Cons**:
- Cold start time (60-90 seconds for GPU tasks)
- Complex custom metric publishing

---

### Option B: SageMaker Auto-Scaling (ALTERNATIVE)

**Components**:
1. **SageMaker Endpoints** per tier
2. **Built-in auto-scaling** (target tracking on invocations)
3. **Multi-model endpoints** (share GPU across models)

**Pros**:
- Built-in model management
- Faster scaling (30-60 seconds)
- A/B testing built-in
- Model versioning included

**Cons**:
- Higher cost (~20% premium over ECS)
- Less control over infrastructure
- Vendor lock-in

---

### Option C: Kubernetes HPA with KEDA (ADVANCED)

**Components**:
1. **EKS Cluster** with GPU node groups
2. **KEDA** (Kubernetes Event Driven Autoscaling)
3. **Prometheus** metrics
4. **HPA** scaling on custom metrics

**Pros**:
- Most flexible
- Can scale to zero
- Multi-cloud portable
- Advanced scheduling (node affinity, taints)

**Cons**:
- Complex setup (40+ hours)
- Requires Kubernetes expertise
- Higher operational overhead

---

## 💡 RECOMMENDED APPROACH

### **Hybrid: ECS for Gold/Silver + SageMaker for Bronze**

**Rationale**:
- **Gold/Silver** (frequent scaling): ECS with target tracking on GPU utilization
- **Bronze** (infrequent, large): SageMaker endpoint with multi-model hosting

**Benefits**:
- Best of both worlds
- Cost-optimized
- Appropriate complexity per tier

---

## 📐 DETAILED IMPLEMENTATION

### Phase 1: Custom Metrics (4-6 hours)

**1.1 Create Metric Publisher Lambda**
```python
# Lambda function runs every 60 seconds
import boto3

cloudwatch = boto3.client('cloudwatch')
sqs = boto3.client('sqs')
ecs = boto3.client('ecs')

def publish_metrics(event, context):
    # Get queue depth for each tier
    gold_queue_depth = get_queue_depth('gaming-system-gold-tier-queue')
    
    # Get current ECS task GPU utilization (via CloudWatch Container Insights)
    gpu_util = get_gpu_utilization('gaming-system-cluster', 'gold-tier-inference')
    
    # Publish custom metrics
    cloudwatch.put_metric_data(
        Namespace='GamingSystem/AI',
        MetricData=[
            {
                'MetricName': 'GoldTierQueueDepth',
                'Value': gold_queue_depth,
                'Unit': 'Count'
            },
            {
                'MetricName': 'GoldTierGPUUtilization',
                'Value': gpu_util,
                'Unit': 'Percent'
            }
        ]
    )
```

**Deliverable**: `services/metrics/gpu_metrics_publisher.py`

---

**1.2 Enable Container Insights for GPU Metrics**
```bash
aws ecs update-cluster-settings \
  --cluster gaming-system-cluster \
  --settings name=containerInsights,value=enabled
```

---

### Phase 2: Scaling Policies (2-3 hours)

**2.1 Register Scalable Targets**
```bash
# Gold tier
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gaming-system-cluster/gold-tier-inference \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 50

# Silver tier
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gaming-system-cluster/silver-tier-inference \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 30

# Bronze tier
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/gaming-system-cluster/bronze-tier-inference \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 8
```

**2.2 Create Target Tracking Policies**
```bash
# Gold tier - scale on GPU utilization
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/gaming-system-cluster/gold-tier-inference \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name gold-tier-gpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://gold-tier-scaling-policy.json

# Gold tier - scale on queue depth
aws application-autoscaling put-scaling-policy \
  --policy-name gold-tier-queue-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://gold-tier-queue-policy.json
```

---

### Phase 3: GPU Instance Management (6-8 hours)

**3.1 Create GPU-Optimized Task Definitions**
```json
{
  "family": "gold-tier-inference",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["EC2"],
  "cpu": "4096",
  "memory": "16384",
  "resourceRequirements": [
    {
      "type": "GPU",
      "value": "1"
    }
  ],
  "containerDefinitions": [{
    "name": "vllm-server",
    "image": "..../vllm-server:qwen2.5-3b-awq",
    "environment": [
      {"name": "MODEL_NAME", "value": "Qwen/Qwen2.5-3B-Instruct-AWQ"},
      {"name": "GPU_MEMORY_UTILIZATION", "value": "0.85"},
      {"name": "MAX_MODEL_LEN", "value": "4096"}
    ]
  }]
}
```

**3.2 Create ECS Capacity Provider for GPU Instances**
```bash
# Create Auto Scaling Group for GPU instances
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name gaming-system-gpu-gold-asg \
  --launch-template LaunchTemplateName=gaming-system-gpu-g5-xlarge \
  --min-size 1 \
  --max-size 50 \
  --desired-capacity 1 \
  --vpc-zone-identifier "subnet-xxx,subnet-yyy"

# Register as ECS capacity provider
aws ecs create-capacity-provider \
  --name gaming-system-gpu-gold \
  --auto-scaling-group-provider \
    autoScalingGroupArn=arn:...:autoScalingGroup:gaming-system-gpu-gold-asg,\
    managedScaling={status=ENABLED,targetCapacity=85,minimumScalingStepSize=1,maximumScalingStepSize=10},\
    managedTerminationProtection=ENABLED
```

---

### Phase 4: Testing & Validation (4-6 hours)

**4.1 Load Testing**
- Simulate player load (100, 500, 1,000, 5,000)
- Measure scale-up time
- Measure scale-down behavior
- Verify cost efficiency

**4.2 Chaos Engineering**
- Kill instances during load
- Verify graceful degradation
- Test auto-recovery

---

## 🎯 SUCCESS CRITERIA

### Auto-Scaling Behavior
- [ ] Scales from 1 → 10 instances in < 5 minutes (player surge)
- [ ] Scales from 10 → 1 instances in < 15 minutes (player drop)
- [ ] GPU utilization stays 70-85% (optimal)
- [ ] Latency P95 maintained (Gold: <16ms, Silver: <250ms)
- [ ] No over-provisioning (cost control)
- [ ] Zero downtime during scaling events

### Cost Efficiency
- [ ] Idle cost: < $100/month (min instances only)
- [ ] 1,000 CCU cost: < $10,000/month
- [ ] 10,000 CCU cost: < $80,000/month
- [ ] Cost per player: < $10/month at scale

---

## 📊 COST ANALYSIS

### Infrastructure Costs (1,000 CCU)

**Gold Tier** (10× g5.xlarge @ $1.006/hr):
- $10.06/hr × 720hr = $7,243/month

**Silver Tier** (5× g5.2xlarge @ $1.212/hr):
- $6.06/hr × 720hr = $4,363/month

**Bronze Tier** (2× c5.4xlarge @ $0.68/hr):
- $1.36/hr × 720hr = $979/month

**Auto-Scaling Infrastructure**:
- CloudWatch custom metrics: $0.30/metric × 10 = $3/month
- Lambda executions: $0.20/million × 0.05M = $0.01/month

**Total**: ~$12,588/month for 1,000 CCU

**With 80% Cache Hit Rate**: ~$6,300/month

---

## 🔗 INTEGRATION POINTS

### With Existing Services
- **model-management**: Registers available models, tracks capacity
- **orchestration**: Routes requests to appropriate tier
- **state_manager**: Tracks player count for scaling decisions
- **event-bus**: Publishes scaling events

### New Services Needed
- **gpu-metrics-publisher**: Publishes custom CloudWatch metrics
- **scaling-controller**: Manages scaling decisions (optional, can use native AWS)
- **capacity-planner**: Predictive scaling based on time-of-day patterns

---

## 📚 DELIVERABLES

### Code (8-10 files)
1. `services/metrics/gpu_metrics_publisher.py` - Custom metric publishing
2. `services/scaling/capacity_planner.py` - Predictive scaling
3. `infrastructure/gpu-task-definitions/` - Task defs for each tier
4. `infrastructure/scaling-policies/` - JSON policies for each tier
5. `scripts/setup-auto-scaling.ps1` - Automation

### Infrastructure
1. ECS Capacity Providers for GPU (Gold, Silver)
2. Auto Scaling Groups for GPU instances
3. Application Auto Scaling targets and policies
4. CloudWatch dashboards for monitoring
5. CloudWatch alarms for capacity alerts

### Documentation
1. Auto-scaling architecture guide
2. Troubleshooting runbook
3. Cost optimization guide
4. Load testing procedures

---

## ⏱️ IMPLEMENTATION TIMELINE

**Phase 1**: Custom metrics (4-6 hours)  
**Phase 2**: Scaling policies (2-3 hours)  
**Phase 3**: GPU instance management (6-8 hours)  
**Phase 4**: Testing & validation (4-6 hours)  

**Total**: 16-24 hours

---

## 🤝 COLLABORATION REQUIREMENTS

Per user mandate, this task REQUIRES:

### Peer Coding (2 models minimum)
- **Coder**: Claude Sonnet 4.5 or GPT-Codex-2
- **Reviewer**: GPT-5 or Gemini 2.5 Pro
- **Validation**: All code reviewed before deployment

### Pairwise Testing (2 models minimum)
- **Tester**: GPT-5 or Claude Sonnet 4.5
- **Reviewer**: Different model from tester
- **Coverage**: 100% test coverage required

### Architecture Review (3-5 models)
- **Director**: Claude Sonnet 4.5
- **Reviewers**: GPT-5, Gemini 2.5 Pro, DeepSeek V3
- **Consensus**: Iterate until all models approve

---

## 📝 NOTES

**Critical**: Auto-scaling is ESSENTIAL for cost management. Without it, running 50 GPU instances 24/7 costs $30K+/month even with zero players.

**With auto-scaling**: $100/month idle, scales to $6-12K at 1,000 CCU, only pay for what you use.

---

**Created**: 2025-11-07  
**Author**: Claude Sonnet 4.5  
**Review Status**: Needs multi-model collaboration  
**Priority**: CRITICAL for production readiness

