# Variables for SageMaker Bronze Tier

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
  description = "Project name prefix for resources"
  type        = string
  default     = "gaming-ai"
}

variable "model_name" {
  description = "Name of the model (e.g., deepseek-v3.1-terminus)"
  type        = string
  default     = "deepseek-v3.1-terminus"
}

variable "model_container_image" {
  description = "Docker container image URI for the model"
  type        = string
  default     = "763104351884.dkr.ecr.us-east-1.amazonaws.com/deepseek-v3:latest"
}

variable "model_s3_path" {
  description = "S3 path to model artifacts (relative to model bucket)"
  type        = string
  default     = "models/deepseek-v3.1-terminus/model.tar.gz"
}

variable "max_model_len" {
  description = "Maximum model context length"
  type        = string
  default     = "32768"
}

variable "tensor_parallel_size" {
  description = "Tensor parallel size for model sharding"
  type        = number
  default     = 8
}

variable "instance_type" {
  description = "SageMaker instance type for async inference"
  type        = string
  default     = "ml.p5.48xlarge"  # 8× H100 GPUs, 64 vCPUs, 2TB memory
}

variable "initial_instance_count" {
  description = "Initial number of instances"
  type        = number
  default     = 1
}

variable "max_concurrent_invocations" {
  description = "Max concurrent invocations per instance"
  type        = number
  default     = 4
}

variable "serverless_max_concurrency" {
  description = "Max concurrency for serverless config (if using serverless)"
  type        = number
  default     = 10
}

variable "serverless_memory_size_mb" {
  description = "Memory size in MB for serverless config"
  type        = number
  default     = 6144  # 6GB
}

variable "sns_error_topic_arn" {
  description = "ARN of SNS topic for error notifications"
  type        = string
  default     = null
}

variable "sns_success_topic_arn" {
  description = "ARN of SNS topic for success notifications"
  type        = string
  default     = null
}

# Training-specific variables
variable "training_image" {
  description = "Docker image URI for training container"
  type        = string
  default     = ""
}

variable "training_data_s3_uri" {
  description = "S3 URI for training data (optional, uses bucket if empty)"
  type        = string
  default     = ""
}

variable "training_instance_type" {
  description = "EC2 instance type for training (p5.48xlarge for multi-node)"
  type        = string
  default     = "ml.p5.48xlarge"
  
  validation {
    condition     = contains(["ml.p5.48xlarge"], var.training_instance_type)
    error_message = "Training instance type must be ml.p5.48xlarge for Bronze tier distributed training."
  }
}

variable "training_instance_count" {
  description = "Number of training instances for distributed training (multi-node)"
  type        = number
  default     = 2
  
  validation {
    condition     = var.training_instance_count >= 2
    error_message = "Bronze tier requires at least 2 instances for distributed training."
  }
}

variable "distributed_strategy" {
  description = "Distributed training strategy (FSDP, SMDDP, or DDP)"
  type        = string
  default     = "FSDP"
  
  validation {
    condition     = contains(["FSDP", "SMDDP", "DDP"], var.distributed_strategy)
    error_message = "Distributed strategy must be FSDP, SMDDP, or DDP."
  }
}

variable "max_runtime_seconds" {
  description = "Maximum runtime for training job in seconds"
  type        = number
  default     = 172800  # 48 hours (longer for Bronze tier)
}

variable "hyperparameters" {
  description = "Hyperparameters for training job"
  type        = map(string)
  default     = {}
}

