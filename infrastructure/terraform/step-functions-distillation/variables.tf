variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "distillation_s3_bucket" {
  description = "S3 bucket for distillation traces and adapters"
  type        = string
}

variable "checkpoint_s3_bucket" {
  description = "S3 bucket for training checkpoints"
  type        = string
}

variable "sagemaker_role_arn" {
  description = "ARN of SageMaker execution role"
  type        = string
}

variable "distillation_image_uri" {
  description = "ECR URI for distillation training image"
  type        = string
}

variable "distillation_output_bucket" {
  description = "S3 bucket for distillation output"
  type        = string
}










