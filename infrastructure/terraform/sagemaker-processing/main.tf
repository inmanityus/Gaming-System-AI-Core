terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# SageMaker Processing Job for Data Validation
resource "aws_sagemaker_processing_job" "data_validation" {
  count = var.enable_data_validation ? 1 : 0
  
  processing_job_name = "srl-rlvr-data-validation-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
  role_arn            = aws_iam_role.sagemaker_processing_role.arn

  processing_resources {
    cluster_config {
      instance_count  = 1
      instance_type  = "ml.t3.medium"
      volume_size_in_gb = 30
    }
  }

  processing_inputs {
    input_name = "training-data"
    s3_input {
      s3_uri       = var.training_data_s3_uri
      s3_data_type = "S3Prefix"
      s3_input_mode = "File"
    }
  }

  processing_output_config {
    outputs {
      output_name = "validation-results"
      s3_output {
        s3_uri = "s3://${var.validation_output_bucket}/validation-results/"
        s3_upload_mode = "EndOfJob"
      }
    }
  }

  app_specification {
    image_uri = var.validation_image_uri
    container_arguments = [
      "--tier", var.tier,
      "--data-uri", var.training_data_s3_uri,
      "--output-uri", "s3://${var.validation_output_bucket}/validation-results/"
    ]
  }

  stopping_condition {
    max_runtime_in_seconds = 3600
  }

  tags = {
    Purpose    = "SRL-RLVR-DataValidation"
    Component  = "SageMaker-Processing"
    Environment = var.environment
    Tier       = var.tier
  }
}

# IAM Role for SageMaker Processing
resource "aws_iam_role" "sagemaker_processing_role" {
  name = "srl-rlvr-sagemaker-processing-role"

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
    Purpose    = "SRL-RLVR-DataValidation"
    Component  = "SageMaker-Processing"
    Environment = var.environment
  }
}

# IAM Policy for SageMaker Processing
resource "aws_iam_role_policy" "sagemaker_processing_policy" {
  name = "srl-rlvr-sagemaker-processing-policy"
  role = aws_iam_role.sagemaker_processing_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.training_data_bucket}/*",
          "arn:aws:s3:::${var.training_data_bucket}",
          "arn:aws:s3:::${var.validation_output_bucket}/*",
          "arn:aws:s3:::${var.validation_output_bucket}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

variable "enable_data_validation" {
  description = "Enable data validation processing job"
  type        = bool
  default     = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "tier" {
  description = "Model tier (gold, silver, bronze)"
  type        = string
}

variable "training_data_s3_uri" {
  description = "S3 URI to training data"
  type        = string
}

variable "training_data_bucket" {
  description = "S3 bucket for training data"
  type        = string
}

variable "validation_output_bucket" {
  description = "S3 bucket for validation results"
  type        = string
}

variable "validation_image_uri" {
  description = "ECR URI for validation processing image"
  type        = string
}









