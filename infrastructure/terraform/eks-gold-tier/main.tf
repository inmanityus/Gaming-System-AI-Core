# EKS Gold Tier Cluster - Main Configuration
# Purpose: Deploy EKS cluster for real-time NPC inference (Gold tier)
# Models: 3B-8B models with TensorRT-LLM for sub-16ms inference

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
    key    = "eks-gold-tier/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Gaming-AI-Core"
      Tier        = "Gold"
      Purpose     = "Real-Time-NPC-Inference"
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

# VPC (create new or use existing)
module "vpc" {
  source = "./modules/vpc"
  
  cluster_name    = var.cluster_name
  vpc_cidr        = var.vpc_cidr
  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets
  
  enable_nat_gateway = true
  single_nat_gateway = false  # High availability
  enable_vpn_gateway = false
  
  tags = {
    Tier = "Gold"
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
      description = "Allow gRPC traffic from game servers"
      protocol    = "tcp"
      from_port   = 8000
      to_port     = 8000
      type        = "ingress"
      cidr_blocks = [var.game_servers_cidr]
    }
  }
  
  tags = {
    Tier = "Gold"
  }
}

# EKS Node Group - Gold Tier GPUs
module "gold_tier_node_group" {
  source = "./modules/node-group"
  
  cluster_name = module.eks.cluster_name
  
  node_group_name = "gold-tier-gpu"
  
  instance_types = var.gold_tier_instance_types  # ["g6.xlarge", "g5.xlarge"]
  capacity_type  = "ON_DEMAND"  # SPOT for cost savings optional
  
  min_size     = var.gold_min_nodes
  max_size     = var.gold_max_nodes
  desired_size = var.gold_desired_nodes
  
  # AMI for GPU support
  ami_type = "AL2_x86_64_GPU"  # NVIDIA GPU-optimized AMI
  
  # Labels and taints
  labels = {
    tier = "gold"
    gpu  = "l4"
  }
  
  taints = [
    {
      key    = "tier"
      value   = "gold"
      effect  = "NO_SCHEDULE"
    }
  ]
  
  # Disk size
  disk_size = 100  # GB
  
  # Scaling
  update_config = {
    max_unavailable_percentage = 25
  }
  
  tags = {
    Tier    = "Gold"
    Purpose = "Real-Time-Inference"
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
  value       = module.gold_tier_node_group.node_group_id
}

