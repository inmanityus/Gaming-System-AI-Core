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

