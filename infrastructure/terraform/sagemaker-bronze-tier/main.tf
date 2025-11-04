# SageMaker Bronze Tier - Training Configuration
# Purpose: Deploy SageMaker training jobs for Bronze tier models (671B MoE)
# Models: DeepSeek-V3.1-Terminus (671B MoE, 37B active)
# Instance: p5.48xlarge multi-node (SMDDP/FSDP)
# Distributed Training: PyTorch FSDP or SageMaker DDP
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

# S3 bucket for training data
resource "aws_s3_bucket" "training_data" {
  bucket = "${var.project_name}-bronze-training-data-${var.environment}"
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Training-Data"
  }
}

resource "aws_s3_bucket_versioning" "training_data" {
  bucket = aws_s3_bucket.training_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket for training checkpoints
resource "aws_s3_bucket" "checkpoints" {
  bucket = "${var.project_name}-bronze-checkpoints-${var.environment}"
  
  tags = {
    Tier    = "Bronze"
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
  bucket = "${var.project_name}-bronze-training-output-${var.environment}"
  
  tags = {
    Tier    = "Bronze"
    Purpose = "Training-Output"
  }
}

resource "aws_s3_bucket_versioning" "training_output" {
  bucket = aws_s3_bucket.training_output.id
  versioning_configuration {
    status = "Enabled"
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

# IAM role for SageMaker (used for both training and inference)
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

# IAM policy for SageMaker (updated to include training resources)
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
          aws_s3_bucket.training_data.arn,
          "${aws_s3_bucket.training_data.arn}/*",
          aws_s3_bucket.checkpoints.arn,
          "${aws_s3_bucket.checkpoints.arn}/*",
          aws_s3_bucket.training_output.arn,
          "${aws_s3_bucket.training_output.arn}/*",
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

# Attach SageMaker full access policy
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# CloudWatch Log Group for training logs
resource "aws_cloudwatch_log_group" "training_logs" {
  name              = "/aws/sagemaker/TrainingJobs/${var.project_name}-bronze-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Tier = "Bronze"
  }
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

# CloudWatch Log Group for inference endpoints
resource "aws_cloudwatch_log_group" "sagemaker_bronze" {
  name              = "/aws/sagemaker/Endpoints/${replace(var.model_name, ".", "-")}-async-endpoint-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Tier = "Bronze"
  }
}

# Local values for training configuration
locals {
  checkpoint_s3_uri = "s3://${aws_s3_bucket.checkpoints.bucket}/checkpoints/"
  output_s3_uri     = "s3://${aws_s3_bucket.training_output.bucket}/output/"
  
  # Bronze tier: Multi-node distributed training
  instance_config = {
    instance_type  = var.training_instance_type
    instance_count = var.training_instance_count  # Multi-node for distributed training
    volume_size_gb = 1000  # Large volume for Bronze tier
  }
  
  # Checkpoint frequency: 30 minutes = 1800 seconds
  checkpoint_frequency = 1800
  
  # Distributed training strategy (FSDP for PyTorch)
  distributed_strategy = var.distributed_strategy
}

# Training job configuration JSON for Python scripts (with distributed training)
locals {
  training_job_config = jsonencode({
    TrainingJobName = "srl-rlvr-bronze-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
    RoleArn         = aws_iam_role.sagemaker_role.arn
    AlgorithmSpecification = {
      TrainingImage     = var.training_image
      TrainingInputMode = "File"
    }
    ResourceConfig = {
      InstanceType     = local.instance_config.instance_type
      InstanceCount    = local.instance_config.instance_count
      VolumeSizeInGB   = local.instance_config.volume_size_gb
    }
    # Distributed training configuration for multi-node
    DistributionStrategy = local.distributed_strategy
    EnableManagedSpotTraining = false  # Bronze tier typically uses on-demand for stability
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
            S3Uri                  = var.training_data_s3_uri != "" ? var.training_data_s3_uri : "s3://${aws_s3_bucket.training_data.bucket}/training-data/"
            S3DataDistributionType = "ShardedByS3Key"  # Sharded for distributed training
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
        distributed_strategy = local.distributed_strategy
      }
    )
    Tags = [
      {
        Key   = "Tier"
        Value = "Bronze"
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
    aws_iam_role.sagemaker_role
  ]
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

# Training outputs
output "training_role_arn" {
  description = "ARN of the IAM role for SageMaker training"
  value       = aws_iam_role.sagemaker_role.arn
}

output "checkpoint_s3_uri" {
  description = "S3 URI for training checkpoints"
  value       = local.checkpoint_s3_uri
}

output "training_output_s3_uri" {
  description = "S3 URI for training output"
  value       = local.output_s3_uri
}

output "training_data_bucket" {
  description = "S3 bucket for training data"
  value       = aws_s3_bucket.training_data.bucket
}

output "checkpoint_bucket" {
  description = "S3 bucket for checkpoints"
  value       = aws_s3_bucket.checkpoints.bucket
}

output "training_output_bucket" {
  description = "S3 bucket for training output"
  value       = aws_s3_bucket.training_output.bucket
}

output "training_job_config_file" {
  description = "Path to training job configuration file"
  value       = local_file.training_job_config.filename
}

