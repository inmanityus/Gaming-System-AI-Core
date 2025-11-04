# SageMaker Bronze Tier - Async Inference Configuration
# Purpose: Deploy SageMaker async inference endpoints for large MoE models (671B)
# Models: DeepSeek-V3.1-Terminus (671B MoE, 37B active) for expert-level async tasks
# Use Cases: Storyteller, Cybersecurity, Admin operations

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "gaming-ai-terraform-state"
    key    = "sagemaker-bronze-tier/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Gaming-AI-Core"
      Tier        = "Bronze"
      Purpose     = "Async-Expert-Inference"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# S3 bucket for SageMaker models and output
resource "aws_s3_bucket" "sagemaker_models" {
  bucket = "${var.project_name}-sagemaker-models-${var.environment}"
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Model-Storage"
  }
}

resource "aws_s3_bucket_versioning" "sagemaker_models" {
  bucket = aws_s3_bucket.sagemaker_models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sagemaker_models" {
  bucket = aws_s3_bucket.sagemaker_models.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket for async inference output
resource "aws_s3_bucket" "async_output" {
  bucket = "${var.project_name}-async-output-${var.environment}"
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Async-Inference-Output"
  }
}

resource "aws_s3_bucket_versioning" "async_output" {
  bucket = aws_s3_bucket.async_output.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for SageMaker
resource "aws_iam_role" "sagemaker_role" {
  name = "${var.project_name}-sagemaker-bronze-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Tier = "Bronze"
  }
}

# IAM policy for SageMaker
resource "aws_iam_role_policy" "sagemaker_policy" {
  name = "${var.project_name}-sagemaker-bronze-policy-${var.environment}"
  role = aws_iam_role.sagemaker_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.sagemaker_models.arn,
          "${aws_s3_bucket.sagemaker_models.arn}/*",
          aws_s3_bucket.async_output.arn,
          "${aws_s3_bucket.async_output.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
}

# SageMaker Model
resource "aws_sagemaker_model" "bronze_tier_model" {
  name               = "${replace(var.model_name, ".", "-")}-${var.environment}"
  execution_role_arn = aws_iam_role.sagemaker_role.arn
  
  primary_container {
    image = var.model_container_image
    
    environment = {
      MODEL_NAME           = var.model_name
      MAX_MODEL_LEN        = var.max_model_len
      TENSOR_PARALLEL_SIZE = var.tensor_parallel_size
    }
    
    model_data_url = "s3://${aws_s3_bucket.sagemaker_models.bucket}/${var.model_s3_path}"
  }
  
  tags = {
    Tier    = "Bronze"
    Model   = var.model_name
    Purpose = "Async-Expert-Tasks"
  }
}

# SageMaker Async Inference Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "bronze_tier_async" {
  name = "${replace(var.model_name, ".", "-")}-async-config-${var.environment}"
  
  # Use async inference
  async_inference_config {
    output_config {
      s3_output_path = "s3://${aws_s3_bucket.async_output.bucket}/output/"
      
      notification_config {
        error_topic   = var.sns_error_topic_arn
        success_topic = var.sns_success_topic_arn
      }
    }
    
    client_config {
      max_concurrent_invocations_per_instance = var.max_concurrent_invocations
    }
  }
  
  production_variants {
    variant_name            = "${replace(var.model_name, ".", "-")}-variant"
    model_name             = aws_sagemaker_model.bronze_tier_model.name
    instance_type          = var.instance_type
    initial_instance_count = var.initial_instance_count
    initial_variant_weight = 1
  }
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Async-Inference"
  }
}

# SageMaker Async Inference Endpoint
resource "aws_sagemaker_endpoint" "bronze_tier_endpoint" {
  name                 = "${replace(var.model_name, ".", "-")}-async-endpoint-${var.environment}"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.bronze_tier_async.name
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Async-Expert-Inference"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "sagemaker_bronze" {
  name              = "/aws/sagemaker/Endpoints/${replace(var.model_name, ".", "-")}-async-endpoint-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Tier = "Bronze"
  }
}

# Outputs
output "endpoint_name" {
  description = "Name of the SageMaker async inference endpoint"
  value       = aws_sagemaker_endpoint.bronze_tier_endpoint.name
}

output "endpoint_arn" {
  description = "ARN of the SageMaker async inference endpoint"
  value       = aws_sagemaker_endpoint.bronze_tier_endpoint.arn
}

output "s3_model_bucket" {
  description = "S3 bucket for model storage"
  value       = aws_s3_bucket.sagemaker_models.bucket
}

output "s3_output_bucket" {
  description = "S3 bucket for async inference output"
  value       = aws_s3_bucket.async_output.bucket
}

