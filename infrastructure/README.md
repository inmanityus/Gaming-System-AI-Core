# Multi-Tier Model Architecture - Infrastructure

## Directory Structure

```
infrastructure/
├── terraform/           # Terraform IaC configurations
│   └── eks-gold-tier/   # EKS cluster for Gold tier
├── kubernetes/          # Kubernetes manifests
│   ├── tensorrt-llm/    # TensorRT-LLM deployment
│   └── nlb/             # Network Load Balancer config
└── aws-cli/             # AWS CLI alternative scripts
```

## Gold Tier (Real-Time) Infrastructure

### EKS Cluster
- **Purpose**: Host TensorRT-LLM servers for sub-16ms inference
- **Instance Types**: g6.xlarge (L4 24GB) or g5.xlarge (A10G 24GB)
- **Node Count**: 16 desired (8 min, 64 max)
- **Latency Target**: p95 < 16ms per token

### Deployment Options

#### Option 1: Terraform (Recommended)
```bash
cd infrastructure/terraform/eks-gold-tier
terraform init
terraform plan
terraform apply
```

#### Option 2: AWS CLI
```powershell
cd infrastructure/aws-cli
pwsh -File create-eks-gold-tier.ps1
```

### Kubernetes Deployment
```bash
kubectl apply -f infrastructure/kubernetes/tensorrt-llm/deployment.yaml
kubectl apply -f infrastructure/kubernetes/nlb/nlb-service.yaml
```

## Network Configuration

- **VPC**: Private subnets only (security)
- **NLB**: Internal Network Load Balancer for gRPC
- **Security**: Restrict to game servers CIDR only
- **Colocation**: Same AZ as game servers (minimal latency)

## Monitoring

- Prometheus metrics endpoint: `/metrics`
- Health checks: `/health` and `/ready`
- CloudWatch integration for AWS services

---

**Status**: Planning phase - ready for implementation

**Next**: Silver tier (7B-13B) and Bronze tier (671B MoE) infrastructure










