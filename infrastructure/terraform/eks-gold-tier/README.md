# EKS Gold Tier Cluster - Terraform Configuration

## Purpose
Deploy AWS EKS cluster optimized for real-time NPC inference using TensorRT-LLM.

## Architecture
- **Cluster**: Private EKS cluster (endpoint private only)
- **Node Group**: GPU instances (g6.xlarge L4 or g5.xlarge A10G)
- **Purpose**: Sub-16ms inference for real-time NPCs (Gold tier)

## Prerequisites
1. AWS CLI configured with appropriate permissions
2. Terraform >= 1.5.0 installed
3. kubectl installed
4. S3 bucket for Terraform state (or configure different backend)

## Usage

### Initialize
```bash
cd infrastructure/terraform/eks-gold-tier
terraform init
```

### Plan
```bash
terraform plan -var-file="terraform.tfvars"
```

### Apply
```bash
terraform apply -var-file="terraform.tfvars"
```

### Configure kubectl
```bash
aws eks update-kubeconfig --name gaming-ai-gold-tier --region us-east-1
kubectl get nodes
```

## Variables
Create `terraform.tfvars`:
```hcl
aws_region = "us-east-1"
environment = "dev"
cluster_name = "gaming-ai-gold-tier"
gold_desired_nodes = 16
gold_min_nodes = 8
gold_max_nodes = 64
```

## Modules Required
This configuration requires:
- `./modules/vpc` - VPC and networking
- `./modules/eks` - EKS cluster
- `./modules/node-group` - EKS node group

**Note**: Modules need to be created or use terraform-aws-modules.

---

**Status**: Planning phase - modules need to be implemented or sourced from terraform-aws-modules.









