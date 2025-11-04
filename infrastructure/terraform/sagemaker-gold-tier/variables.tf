# Variables for SageMaker Gold Tier Training Infrastructure

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
  description = "EC2 instance type for training (g6.12xlarge or g5.12xlarge)"
  type        = string
  default     = "ml.g6.12xlarge"
  
  validation {
    condition     = contains(["ml.g6.12xlarge", "ml.g5.12xlarge"], var.instance_type)
    error_message = "Instance type must be ml.g6.12xlarge or ml.g5.12xlarge for Gold tier."
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
  default     = 28800  # 8 hours
}

variable "hyperparameters" {
  description = "Hyperparameters for training job"
  type        = map(string)
  default     = {}
}

