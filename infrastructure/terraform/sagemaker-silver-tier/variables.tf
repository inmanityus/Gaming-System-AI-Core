# Variables for SageMaker Silver Tier Training Infrastructure

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

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "gaming-ai-core"
}

variable "instance_type" {
  description = "EC2 instance type for training (p5.48xlarge for 8× H100)"
  type        = string
  default     = "ml.p5.48xlarge"
  
  validation {
    condition     = contains(["ml.p5.48xlarge", "ml.p4d.24xlarge"], var.instance_type)
    error_message = "Instance type must be ml.p5.48xlarge (8× H100) or ml.p4d.24xlarge (8× A100) for Silver tier."
  }
}

variable "training_image" {
  description = "Docker image URI for training container"
  type        = string
}

variable "training_data_s3_uri" {
  description = "S3 URI for training data"
  type        = string
}

variable "max_runtime_seconds" {
  description = "Maximum runtime for training job in seconds"
  type        = number
  default     = 86400  # 24 hours (longer for Silver tier)
}

variable "hyperparameters" {
  description = "Hyperparameters for training job"
  type        = map(string)
  default     = {}
}

