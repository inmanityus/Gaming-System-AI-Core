# EKS Gold Tier Infrastructure Setup Plan
**Task**: GOLD-001  
**Status**: Planning Phase  
**Date**: 2025-11-03

## Infrastructure Requirements

### EKS Cluster Configuration
- **Name**: `gaming-ai-gold-tier`
- **Region**: `us-east-1` (or configured region)
- **Kubernetes Version**: Latest stable (1.29+)
- **Purpose**: Host TensorRT-LLM servers for real-time NPC inference

### Node Group: Gold Tier GPUs
```yaml
NodeGroup:
  Name: gold-tier-gpu
  InstanceTypes:
    - g6.xlarge  # L4 24GB (primary)
    - g5.xlarge  # A10G 24GB (alternative)
  MinSize: 8
  MaxSize: 64
  DesiredSize: 16
  AMI: NVIDIA GPU-optimized AMI
  Labels:
    tier: gold
    gpu: l4
  Taints:
    - Key: tier
      Value: gold
      Effect: NoSchedule
```

### TensorRT-LLM Deployment
- **Container**: `nvcr.io/nvidia/tensorrtllm/release:gpt-oss-dev`
- **Models**: Qwen2.5-3B-Instruct-AWQ, Llama-3.2-3B-Instruct-AWQ
- **Replicas**: 4 per AZ (minimum for redundancy)
- **Resources**: 1 GPU per pod

### Network Configuration
- **VPC**: New or existing VPC with private subnets
- **Load Balancer**: Network Load Balancer (NLB) for gRPC
- **Security Groups**: Restrict to game servers only
- **Colocation**: Same AZ as game servers for minimal latency

## Implementation Steps (Next Tasks)
1. Create EKS cluster via AWS CLI or Terraform
2. Create node group with GPU instances
3. Deploy TensorRT-LLM container
4. Configure NLB for gRPC
5. Set up health checks and monitoring
6. Test latency (target: p95 < 16ms)

---

**Next**: Create Terraform configs or AWS CLI scripts





