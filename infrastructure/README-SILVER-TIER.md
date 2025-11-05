# Silver Tier (Interactive) Infrastructure

## Purpose
Deploy AWS EKS cluster and vLLM servers for interactive NPC inference with 80-250ms latency targets.

## Architecture
- **Cluster**: Private EKS cluster (endpoint private only)
- **Node Group**: GPU instances (g6.12xlarge L4 or g5.12xlarge A10G)
- **Purpose**: 80-250ms inference for interactive NPCs (Silver tier)
- **Models**: 7B-13B models (Llama-3.1-8B, Qwen2.5-7B, Mistral-Nemo-12B)

## Deployment

### Terraform
```bash
cd infrastructure/terraform/eks-silver-tier
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
```

### Kubernetes
```bash
# Configure kubectl
aws eks update-kubeconfig --name gaming-ai-silver-tier --region us-east-1

# Deploy vLLM
kubectl apply -f infrastructure/kubernetes/vllm/deployment.yaml

# Deploy NLB
kubectl apply -f infrastructure/kubernetes/nlb/silver-tier-nlb.yaml
```

## Key Features

### vLLM Deployment
- **Dynamic Batching**: Continuous batching for optimal throughput
- **Auto-scaling**: HPA scales 2-8 replicas based on CPU/memory
- **Health Checks**: Liveness and readiness probes
- **Model Storage**: 200GB PVC for model files
- **Cache Storage**: 100GB emptyDir for model cache

### Network Load Balancer
- **Sticky Sessions**: Source IP stickiness for better caching
- **Health Checks**: HTTP health check on /health endpoint
- **Cross-Zone**: Enabled for high availability

## Performance Targets
- **Latency**: p95 < 250ms, p50 < 120ms
- **Throughput**: 100+ requests/second per replica
- **Availability**: 99.9% uptime

## Cost Optimization
- **SPOT Instances**: Optional for cost savings (75% reduction)
- **HPA**: Scale down during low traffic
- **Instance Types**: g6.12xlarge primary, g5.12xlarge fallback

---

**Status**: Planning phase - ready for implementation


