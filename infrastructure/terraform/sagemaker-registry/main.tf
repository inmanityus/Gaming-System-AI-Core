# SageMaker Model Registry
# Purpose: Centralized model versioning and metadata tracking
# Features: Model versioning, cost/performance tagging, approval workflows

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
    key    = "sagemaker-registry/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Gaming-AI-Core"
      Purpose     = "Model-Registry"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# SageMaker Model Package Group
# Groups related model versions together
resource "aws_sagemaker_model_package_group" "main" {
  model_package_group_name = "${var.project_name}-model-registry-${var.environment}"
  model_package_group_description = "Model registry for SRL-RLVR trained models"
  
  tags = {
    Purpose = "Model-Versioning"
  }
}

# Model Package Group for each tier
resource "aws_sagemaker_model_package_group" "gold_tier" {
  model_package_group_name = "${var.project_name}-gold-tier-models-${var.environment}"
  model_package_group_description = "Gold tier models (3B-8B) for real-time inference"
  
  tags = {
    Tier    = "Gold"
    Purpose = "Model-Versioning"
  }
}

resource "aws_sagemaker_model_package_group" "silver_tier" {
  model_package_group_name = "${var.project_name}-silver-tier-models-${var.environment}"
  model_package_group_description = "Silver tier models (7B-13B) for interactive inference"
  
  tags = {
    Tier    = "Silver"
    Purpose = "Model-Versioning"
  }
}

resource "aws_sagemaker_model_package_group" "bronze_tier" {
  model_package_group_name = "${var.project_name}-bronze-tier-models-${var.environment}"
  model_package_group_description = "Bronze tier models (671B MoE) for expert async tasks"
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Model-Versioning"
  }
}

# S3 bucket for model package artifacts
resource "aws_s3_bucket" "model_packages" {
  bucket = "${var.project_name}-model-packages-${var.environment}"
  
  tags = {
    Purpose = "Model-Package-Storage"
  }
}

resource "aws_s3_bucket_versioning" "model_packages" {
  bucket = aws_s3_bucket.model_packages.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "model_packages" {
  bucket = aws_s3_bucket.model_packages.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM role for model registry operations
resource "aws_iam_role" "model_registry_role" {
  name = "${var.project_name}-model-registry-role-${var.environment}"
  
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
    Purpose = "Model-Registry"
  }
}

# IAM policy for model registry
resource "aws_iam_role_policy" "model_registry_policy" {
  name = "${var.project_name}-model-registry-policy-${var.environment}"
  role = aws_iam_role.model_registry_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreateModelPackage",
          "sagemaker:DescribeModelPackage",
          "sagemaker:ListModelPackages",
          "sagemaker:UpdateModelPackage",
          "sagemaker:DeleteModelPackage"
        ]
        Resource = [
          "${aws_sagemaker_model_package_group.main.arn}/*",
          "${aws_sagemaker_model_package_group.gold_tier.arn}/*",
          "${aws_sagemaker_model_package_group.silver_tier.arn}/*",
          "${aws_sagemaker_model_package_group.bronze_tier.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.model_packages.arn,
          "${aws_s3_bucket.model_packages.arn}/*"
        ]
      }
    ]
  })
}

# Attach SageMaker full access
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.model_registry_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

