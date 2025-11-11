# Bronze Tier (Async Expert) Infrastructure

## Purpose
Deploy SageMaker async inference endpoints for large MoE models (671B) handling expert-level tasks where latency is acceptable but quality is paramount.

## Architecture
- **Service**: AWS SageMaker Async Inference
- **Instance Type**: ml.p5.48xlarge (8× H100 GPUs, 2TB RAM)
- **Purpose**: Async expert tasks (760ms+ per token acceptable)
- **Models**: DeepSeek-V3.1-Terminus (671B MoE, 37B active)

## Use Cases
- **Storyteller**: Narrative generation, story arcs, questlines
- **Cybersecurity**: Deep code analysis, security audits
- **Admin Operations**: Batched reports, data analysis, system administration

## Cost-Benefit Analysis

### Training Costs
- **Initial Training**: $8,640-$32,400 per fine-tuning run
- **Break-even Point**: 860K-32M tokens (achieved in 1-3 months)
- **After Break-even**: Massive savings vs for-pay models

### Inference Costs (Self-Hosted)
- **Per Request**: ~$0.01-$0.05 (depends on request size)
- **For-Pay Comparison**: 
  - GPT-5 Pro: ~$10-$50 per 1M tokens
  - Claude 4.5 Sonnet: ~$3-$15 per 1M tokens
  - **Savings**: 100-1000× cheaper after break-even

### ROI Calculation
```
Training Cost: $10,000 (one-time)
Monthly For-Pay Cost: $5,000 (assuming 10M tokens/month)
Monthly Self-Hosted: $50 (assuming $0.005 per 1M tokens)
Break-even: 2 months
Annual Savings: $59,400
```

## Deployment

### Terraform
```bash
cd infrastructure/terraform/sagemaker-bronze-tier
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
```

### Variables (terraform.tfvars)
```hcl
model_name = "deepseek-v3.1-terminus"
instance_type = "ml.p5.48xlarge"
initial_instance_count = 1
max_concurrent_invocations = 4
```

### Kubernetes Jobs
```bash
kubectl apply -f infrastructure/kubernetes/bronze-tier/job-queue.yaml
```

### Invoke Async Inference
```powershell
.\infrastructure\scripts\bronze-tier\invoke-async-inference.ps1 `
    -EndpointName "deepseek-v3.1-terminus-async-endpoint-dev" `
    -InputContent '{"prompt": "Generate a story about...", "max_tokens": 1000}'
```

## Performance Characteristics
- **Latency**: 760ms+ per token (async acceptable)
- **Throughput**: 4 concurrent invocations per instance
- **Quality**: Matches/exceeds for-pay models
- **Availability**: 99.9% uptime (SageMaker managed)

## Architecture Pattern: Decouple Async from Real-Time

**Critical Innovation**: Async tasks don't block real-time game operations.

**How It Works**:
1. **Game Server**: Sends async request to SageMaker via S3
2. **SageMaker**: Processes request asynchronously (seconds to minutes)
3. **Result**: Delivered to S3, notification via SNS
4. **Game Server**: Polls S3 or receives SNS notification
5. **Caching**: Results cached for reuse (story templates, etc.)

**Result**: Game maintains 300+ FPS while expert tasks run asynchronously.

## Monitoring
- **CloudWatch**: Endpoint metrics, invocation counts, errors
- **S3**: Input/output tracking, cost monitoring
- **SNS**: Success/error notifications

## Cost Optimization
- **SPOT Instances**: Not available for p5.48xlarge (on-demand only)
- **Reserved Instances**: 40-50% savings with 1-year commitment
- **Auto-scaling**: Scale to zero when idle (if using serverless variant)
- **Caching**: Cache frequently used outputs to reduce invocations

## Security
- **IAM**: Least privilege access to S3 and SageMaker
- **Encryption**: S3 buckets encrypted at rest
- **VPC**: Endpoints can be deployed in private VPC
- **Secrets**: Use AWS Secrets Manager for API keys

---

**Status**: Planning phase - ready for implementation

**Next**: Deploy and measure actual costs vs for-pay models





