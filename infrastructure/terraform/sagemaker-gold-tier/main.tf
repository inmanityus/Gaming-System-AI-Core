# SageMaker Gold Tier Training Infrastructure
# Purpose: Deploy SageMaker training jobs for Gold tier models (3B-8B)
# Models: Qwen2.5-3B, Llama-3.2-3B, Phi-3.5-mini
# Instance: g6.12xlarge (L4) or g5.12xlarge (A10G)
# Managed Spot Training: 100%
# Checkpointing: Every 30 minutes

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
    key    = "sagemaker-gold-tier-training/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Gaming-AI-Core"
      Tier        = "Gold"
      Purpose     = "SRL-RLVR-Training"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# S3 bucket for training data and checkpoints
resource "aws_s3_bucket" "training_data" {
  bucket = "${var.project_name}-gold-training-data-${var.environment}"
  
  tags = {
    Tier    = "Gold"
    Purpose = "Training-Data"
  }
}

resource "aws_s3_bucket_versioning" "training_data" {
  bucket = aws_s3_bucket.training_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "training_data" {
  bucket = aws_s3_bucket.training_data.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket for checkpoints
resource "aws_s3_bucket" "checkpoints" {
  bucket = "${var.project_name}-gold-checkpoints-${var.environment}"
  
  tags = {
    Tier    = "Gold"
    Purpose = "Training-Checkpoints"
  }
}

resource "aws_s3_bucket_versioning" "checkpoints" {
  bucket = aws_s3_bucket.checkpoints.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket for training output
resource "aws_s3_bucket" "training_output" {
  bucket = "${var.project_name}-gold-training-output-${var.environment}"
  
  tags = {
    Tier    = "Gold"
    Purpose = "Training-Output"
  }
}

resource "aws_s3_bucket_versioning" "training_output" {
  bucket = aws_s3_bucket.training_output.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for SageMaker training
resource "aws_iam_role" "sagemaker_training_role" {
  name = "${var.project_name}-gold-training-role-${var.environment}"
  
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
    Tier = "Gold"
  }
}

# IAM policy for SageMaker training
resource "aws_iam_role_policy" "sagemaker_training_policy" {
  name = "${var.project_name}-gold-training-policy-${var.environment}"
  role = aws_iam_role.sagemaker_training_role.id
  
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
          aws_s3_bucket.training_data.arn,
          "${aws_s3_bucket.training_data.arn}/*",
          aws_s3_bucket.checkpoints.arn,
          "${aws_s3_bucket.checkpoints.arn}/*",
          aws_s3_bucket.training_output.arn,
          "${aws_s3_bucket.training_output.arn}/*"
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

# Attach SageMaker full access policy (can be restricted further)
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_training_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# CloudWatch Log Group for training logs
resource "aws_cloudwatch_log_group" "training_logs" {
  name              = "/aws/sagemaker/TrainingJobs/${var.project_name}-gold-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Tier = "Gold"
  }
}

# Local values for configuration
locals {
  checkpoint_s3_uri = "s3://${aws_s3_bucket.checkpoints.bucket}/checkpoints/"
  output_s3_uri     = "s3://${aws_s3_bucket.training_output.bucket}/output/"
  
  instance_config = {
    instance_type  = var.instance_type
    instance_count = 1
    volume_size_gb = 200
  }
  
  # Checkpoint frequency: 30 minutes = 1800 seconds
  checkpoint_frequency = 1800
}

# SageMaker Training Job Configuration
# Note: Actual training job is created via Python scripts, this provides the infrastructure
# This creates a reusable training job template configuration

# Training job configuration JSON for Python scripts
locals {
  training_job_config = jsonencode({
    TrainingJobName = "srl-rlvr-gold-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
    RoleArn         = aws_iam_role.sagemaker_training_role.arn
    AlgorithmSpecification = {
      TrainingImage     = var.training_image
      TrainingInputMode = "File"
    }
    ResourceConfig = {
      InstanceType     = local.instance_config.instance_type
      InstanceCount    = local.instance_config.instance_count
      VolumeSizeInGB   = local.instance_config.volume_size_gb
    }
    EnableManagedSpotTraining = true
    MaxRuntimeInSeconds      = var.max_runtime_seconds
    CheckpointConfig = {
      S3Uri     = local.checkpoint_s3_uri
      LocalPath = "/opt/ml/checkpoints"
    }
    StoppingCondition = {
      MaxRuntimeInSeconds = var.max_runtime_seconds
    }
    InputDataConfig = [
      {
        ChannelName = "training"
        DataSource = {
          S3DataSource = {
            S3DataType             = "S3Prefix"
            S3Uri                  = var.training_data_s3_uri
            S3DataDistributionType = "FullyReplicated"
          }
        }
        ContentType = "application/json"
      }
    ]
    OutputDataConfig = {
      S3OutputPath = local.output_s3_uri
    }
    HyperParameters = merge(
      var.hyperparameters,
      {
        checkpoint_frequency = tostring(local.checkpoint_frequency)
      }
    )
    Tags = [
      {
        Key   = "Tier"
        Value = "Gold"
      },
      {
        Key   = "Purpose"
        Value = "SRL-RLVR-Training"
      },
      {
        Key   = "Environment"
        Value = var.environment
      }
    ]
  })
}

# Output the configuration as a file for Python scripts to use
resource "local_file" "training_job_config" {
  content  = local.training_job_config
  filename = "${path.module}/training-job-config.json"
  
  depends_on = [
    aws_s3_bucket.checkpoints,
    aws_s3_bucket.training_output,
    aws_iam_role.sagemaker_training_role
  ]
}

