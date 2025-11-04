# Variables for EKS Silver Tier Cluster

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
  default     = "gaming-ai-silver-tier"
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.29"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC (if creating new VPC)"
  type        = string
  default     = null
}

variable "use_existing_vpc" {
  description = "Whether to use existing VPC (true) or create new (false)"
  type        = bool
  default     = false
}

variable "existing_vpc_id" {
  description = "Existing VPC ID (if use_existing_vpc is true)"
  type        = string
  default     = null
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.1.11.0/24", "10.1.12.0/24", "10.1.13.0/24"]
}

variable "game_servers_cidr" {
  description = "CIDR block for game servers (for security group rules)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "silver_tier_instance_types" {
  description = "Instance types for Silver tier node group (using minimal instances initially due to vCPU limits)"
  type        = list(string)
  default     = ["t3.micro"]  # Minimal instance (1 vCPU) to fit within vCPU limits initially
}

variable "silver_min_nodes" {
  description = "Minimum number of nodes in Silver tier node group"
  type        = number
  default     = 1  # Absolute minimum for initial deployment
}

variable "silver_max_nodes" {
  description = "Maximum number of nodes in Silver tier node group"
  type        = number
  default     = 2  # Minimal for initial deployment
}

variable "silver_desired_nodes" {
  description = "Desired number of nodes in Silver tier node group"
  type        = number
  default     = 1  # Absolute minimum: 1 node × 1 vCPU = 1 vCPU (within 16 vCPU limit)
}

