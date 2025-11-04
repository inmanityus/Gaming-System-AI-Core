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
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr
  azs  = slice(data.aws_availability_zones.available.names, 0, 3)
  
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
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"
  
  cluster_name    = var.cluster_name
  cluster_version  = var.kubernetes_version
  
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
  
  # EKS Node Group - Gold Tier GPUs
  eks_managed_node_groups = {
    gold_tier_gpu = {
      name = "gold-tier-gpu"
      
      instance_types = var.gold_tier_instance_types  # ["g6.xlarge", "g5.xlarge"]
      capacity_type  = "SPOT"  # Using Spot instances to bypass vCPU limits (100 limit available)
      
      min_size     = var.gold_min_nodes
      max_size     = var.gold_max_nodes
      desired_size = var.gold_desired_nodes
      
      # AMI type (changed from GPU to standard for initial deployment due to vCPU limits)
      ami_type = "AL2_x86_64"  # Standard AMI (GPU support can be added later after vCPU limit increase)
      
      # Labels and taints
      labels = {
        tier = "gold"
        gpu  = "l4"
      }
      
      taints = [
        {
          key    = "tier"
          value  = "gold"
          effect = "NO_SCHEDULE"
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
  }
}

