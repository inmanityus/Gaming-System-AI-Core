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

# VPC (create new or use existing)
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr != null ? var.vpc_cidr : "10.1.0.0/16"
  azs  = slice(data.aws_availability_zones.available.names, 0, 3)
  
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
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"
  
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
  
  # EKS Node Group - Silver Tier GPUs
  eks_managed_node_groups = {
    silver_tier_gpu = {
      name = "silver-tier-gpu"
      
      instance_types = var.silver_tier_instance_types  # ["g6.12xlarge", "g5.12xlarge"]
      capacity_type  = "SPOT"  # Using Spot instances to bypass vCPU limits (100 limit available)
      
      min_size     = var.silver_min_nodes
      max_size     = var.silver_max_nodes
      desired_size = var.silver_desired_nodes
      
      # AMI type (using standard AMI initially due to vCPU limits)
      ami_type = "AL2_x86_64"  # Standard AMI (GPU support can be added later)
      
      # Labels and taints
      labels = {
        tier = "silver"
        gpu  = "l4-a10g"
      }
      
      taints = [
        {
          key    = "tier"
          value  = "silver"
          effect = "NO_SCHEDULE"
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
  }
}

