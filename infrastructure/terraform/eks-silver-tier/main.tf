# EKS Silver Tier Cluster - Main Configuration
# Purpose: Deploy EKS cluster for interactive NPC inference (Silver tier)
# Models: 7B-13B models with vLLM for 80-250ms inference

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  
  backend "s3" {
    bucket = "gaming-ai-terraform-state"
    key    = "eks-silver-tier/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Gaming-AI-Core"
      Tier        = "Silver"
      Purpose     = "Interactive-NPC-Inference"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Use existing VPC or create new one
# For Silver tier, we can reuse Gold tier VPC or create separate
module "vpc" {
  source = "./modules/vpc"
  
  cluster_name    = var.cluster_name
  vpc_cidr        = var.vpc_cidr != null ? var.vpc_cidr : null
  vpc_id          = var.use_existing_vpc ? var.existing_vpc_id : null
  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets
  
  enable_nat_gateway = true
  single_nat_gateway = false  # High availability
  enable_vpn_gateway = false
  
  tags = {
    Tier = "Silver"
    Name = "${var.cluster_name}-vpc"
  }
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Cluster endpoint access
  cluster_endpoint_public_access  = false  # Private only for security
  cluster_endpoint_private_access = true
  
  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
  
  # Node security group
  node_security_group_additional_rules = {
    ingress_from_game_servers = {
      description = "Allow HTTP/gRPC traffic from game servers"
      protocol    = "tcp"
      from_port   = 8000
      to_port     = 8010
      type        = "ingress"
      cidr_blocks = [var.game_servers_cidr]
    }
  }
  
  tags = {
    Tier = "Silver"
  }
}

# EKS Node Group - Silver Tier GPUs
module "silver_tier_node_group" {
  source = "./modules/node-group"
  
  cluster_name = module.eks.cluster_name
  
  node_group_name = "silver-tier-gpu"
  
  instance_types = var.silver_tier_instance_types  # ["g6.12xlarge", "g5.12xlarge"]
  capacity_type  = "ON_DEMAND"  # SPOT for cost savings optional
  
  min_size     = var.silver_min_nodes
  max_size     = var.silver_max_nodes
  desired_size = var.silver_desired_nodes
  
  # AMI for GPU support
  ami_type = "AL2_x86_64_GPU"  # NVIDIA GPU-optimized AMI
  
  # Labels and taints
  labels = {
    tier = "silver"
    gpu  = "l4-a10g"
  }
  
  taints = [
    {
      key    = "tier"
      value   = "silver"
      effect  = "NO_SCHEDULE"
    }
  ]
  
  # Disk size
  disk_size = 200  # GB (larger for model storage)
  
  # Scaling
  update_config = {
    max_unavailable_percentage = 25
  }
  
  tags = {
    Tier    = "Silver"
    Purpose = "Interactive-Inference"
  }
}

# Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "node_group_id" {
  description = "EKS node group ID"
  value       = module.silver_tier_node_group.node_group_id
}

