# Variables for EKS Gold Tier Cluster

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "gaming-ai-gold-tier"
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.29"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "game_servers_cidr" {
  description = "CIDR block for game servers (for security group rules)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "gold_tier_instance_types" {
  description = "Instance types for Gold tier node group (using minimal instances initially due to vCPU limits)"
  type        = list(string)
  default     = ["t3.micro"]  # Minimal instance (1 vCPU) to fit within vCPU limits
}

variable "gold_min_nodes" {
  description = "Minimum number of nodes in Gold tier node group"
  type        = number
  default     = 1  # Absolute minimum
}

variable "gold_max_nodes" {
  description = "Maximum number of nodes in Gold tier node group"
  type        = number
  default     = 2  # Minimal for initial deployment
}

variable "gold_desired_nodes" {
  description = "Desired number of nodes in Gold tier node group"
  type        = number
  default     = 1  # Absolute minimum: 1 node × 1 vCPU = 1 vCPU (within 16 vCPU limit)
}

