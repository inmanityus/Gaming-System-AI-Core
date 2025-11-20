# AWS ML Deployment Knowledge Base

**Source**: Previous Linux Cursor deployment to AWS  
**Date**: 2025-11-03  
**Purpose**: Universal ML deployment patterns for AWS

---

## Architecture

### Training Pipeline
```
SageMaker Training → S3 Model Storage → EKS Deployment → Production
```

### Key Services
| Service | Purpose | Cost Range |
|---------|---------|------------|
| SageMaker | GPU training | $1.52-$37/hour |
| EKS | Model serving (Kubernetes) | $75/month + nodes |
| S3 | Model storage | $0.023/GB-month |
| ECR | Docker registry | $0.10/GB-month |

---

## Training Costs

### Instance Selection
| Model Size | Instance | GPU | Cost/Instance | Est. Total |
|-----------|----------|-----|---------------|------------|
| 3-8B params | ml.g5.2xlarge | 1× A10G, 24GB | $1.52/hr | $30-$45 |
| 13B params | ml.g5.4xlarge | 1× A10G, 48GB | $2.03/hr | $60-$80 |
| 70B+ params | ml.p4d.24xlarge | 8× A100, 320GB | $37.69/hr | $2,700+ |

### Cost Optimization
- **Spot instances**: 70% savings on training
- **Mixed instance policy**: Reduces interruptions
- **S3 lifecycle policies**: Auto-archive old models
- **Quantization**: 50-75% cost reduction

---

## Deployment Patterns

### EKS Cluster Setup
```hcl
# GPU inference nodes
gpu_inference = {
  instance_types = ["g4dn.2xlarge"]
  capacity_type  = "ON_DEMAND"
}

# GPU training nodes (spot for savings)
gpu_training = {
  instance_types = ["g4dn.2xlarge"]
  capacity_type  = "SPOT"  # 70% savings
}
```

### Kubernetes Deployment
Key features:
- **Init container**: Downloads model from S3
- **GPU resource requests**: `nvidia.com/gpu: 1`
- **Health checks**: Liveness + readiness probes
- **Load balancer**: Service type LoadBalancer
- **Auto-scaling**: HPA based on CPU/memory

---

## Prerequisites Checklist

### AWS Setup
- [ ] AWS CLI v2 configured
- [ ] S3 buckets created
- [ ] SageMaker IAM role configured
- [ ] EKS cluster created
- [ ] kubectl configured
- [ ] ECR repositories created

### Windows Development
- [ ] WSL2 installed
- [ ] Git configured: `core.autocrlf false`
- [ ] Tools installed in WSL2
- [ ] AWS credentials configured

### Model Preparation
- [ ] Training script tested locally
- [ ] Model artifacts in S3
- [ ] Docker image built and pushed
- [ ] Health endpoint working

---

## Deployment Workflow

### Stage 1: Pre-Deployment
1. Verify model artifacts in S3
2. Build and push Docker image to ECR
3. Create Kubernetes manifests
4. Configure namespace and secrets

### Stage 2: Initial Deployment
1. Apply Kubernetes deployment
2. Monitor pod startup (60s init delay)
3. Verify health checks passing
4. Test inference endpoint

### Stage 3: Validation
1. Run evaluation script
2. Check CloudWatch metrics
3. Verify latency SLAs
4. Cost monitoring setup

### Stage 4: Scale & Optimize
1. Enable HPA auto-scaling
2. Configure pod disruption budgets
3. Set up canary deployments
4. Implement blue-green strategies

---

## Monitoring & Troubleshooting

### Common Issues

**OOM (Out of Memory)**
- Reduce batch size
- Enable gradient checkpointing
- Use larger instance
- Mixed precision training

**Pod Stuck Pending**
- Check GPU nodes exist
- Verify NVIDIA device plugin
- Check resource requests
- Scale node group if needed

**Auth Failures**
```bash
aws eks update-kubeconfig --region us-east-1 --name ml-models-cluster
```

---

## Model Quantization

**Benefits**: 50-75% cost reduction, 2-4x faster inference

```python
# Quantize to int8
from torch.quantization import quantize_dynamic
quantized_model = quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)
```

**Savings Example**:
- Model size: 13GB → 3GB (75% reduction)
- Instance: g4dn.2xlarge → c5.2xlarge (55% cheaper)
- Latency: Similar or better

---

## Key Learnings

1. **Always use WSL2 on Windows** - Avoids path/line-ending issues
2. **Spot instances for training** - 70% savings with checkpointing
3. **Init containers for model download** - Better than mounting S3
4. **Health checks are critical** - Prevents bad deployments
5. **Quantization before deployment** - Major cost savings
6. **CloudWatch from day 1** - Essential for debugging

---

## Windows-Specific Notes

**PowerShell Scripts**
```powershell
# ECR login (single pipeline)
aws ecr get-login-password --region us-east-1 | 
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name ml-models-cluster
```

**Git Configuration**
```bash
git config --global core.autocrlf false
git config --global core.eol lf
```

---

## Multi-Tier Architecture Integration

This knowledge applies to our Gold/Silver/Bronze tiers:

**Gold Tier** (Real-time, <16ms):
- Instance: g4dn.xlarge or smaller
- Quantization: Yes (required for latency)
- Spot: No (needs consistency)

**Silver Tier** (Interactive, 80-250ms):
- Instance: g4dn.2xlarge
- Quantization: Recommended
- Spot: Optional for testing

**Bronze Tier** (Async, seconds):
- SageMaker Async Inference
- Spot: Yes (can retry)
- p5.48xlarge nodes

---

**Reference**: See original docs at:
- `C:\Users\kento\Bizignition Dropbox\Ken Tola\AI\Transfer\README.md`
- `C:\Users\kento\Bizignition Dropbox\Ken Tola\AI\Transfer\AWS-ML-MODEL-DEPLOYMENT-COMPLETE-GUIDE.md`

