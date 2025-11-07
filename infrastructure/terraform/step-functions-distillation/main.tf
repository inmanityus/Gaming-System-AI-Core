terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Step Functions State Machine for Distillation Pipeline
resource "aws_sfn_state_machine" "distillation_pipeline" {
  name     = "srl-rlvr-distillation-pipeline"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "SRL→RLVR Nightly Distillation Pipeline"
    StartAt = "CollectBronzeTraces"
    States = jsondecode(file("${path.module}/../step-functions/distillation-pipeline.json"))
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = {
    Purpose    = "SRL-RLVR-Distillation"
    Component  = "Step-Functions"
    Environment = var.environment
  }
}

# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "step_functions" {
  name              = "/aws/stepfunctions/srl-rlvr-distillation"
  retention_in_days = 30

  tags = {
    Purpose    = "SRL-RLVR-Distillation"
    Component  = "Step-Functions"
    Environment = var.environment
  }
}

# IAM Role for Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = "srl-rlvr-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Purpose    = "SRL-RLVR-Distillation"
    Component  = "Step-Functions"
    Environment = var.environment
  }
}

# IAM Policy for Step Functions
resource "aws_iam_role_policy" "step_functions_policy" {
  name = "srl-rlvr-step-functions-policy"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:*:*:function:srl-distillation-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreateTrainingJob",
          "sagemaker:DescribeTrainingJob",
          "sagemaker:StopTrainingJob"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.distillation_s3_bucket}/*",
          "arn:aws:s3:::${var.distillation_s3_bucket}",
          "arn:aws:s3:::${var.checkpoint_s3_bucket}/*",
          "arn:aws:s3:::${var.checkpoint_s3_bucket}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# EventBridge Rule for Nightly Distillation
resource "aws_cloudwatch_event_rule" "nightly_distillation" {
  name                = "srl-rlvr-nightly-distillation"
  description         = "Trigger distillation pipeline nightly at 2 AM UTC"
  schedule_expression = "cron(0 2 * * ? *)"

  tags = {
    Purpose    = "SRL-RLVR-Distillation"
    Component  = "EventBridge"
    Environment = var.environment
  }
}

# EventBridge Target
resource "aws_cloudwatch_event_target" "distillation_pipeline" {
  rule      = aws_cloudwatch_event_rule.nightly_distillation.name
  target_id = "DistillationPipeline"
  arn       = aws_sfn_state_machine.distillation_pipeline.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
}

# IAM Role for EventBridge
resource "aws_iam_role" "eventbridge_role" {
  name = "srl-rlvr-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Purpose    = "SRL-RLVR-Distillation"
    Component  = "EventBridge"
    Environment = var.environment
  }
}

# IAM Policy for EventBridge
resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "srl-rlvr-eventbridge-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = [
          aws_sfn_state_machine.distillation_pipeline.arn
        ]
      }
    ]
  })
}

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

output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.distillation_pipeline.arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = aws_sfn_state_machine.distillation_pipeline.name
}




