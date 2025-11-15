terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_vpc" "main" {
  id = var.vpc_id
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  # Get subnets that ECS services are using
  filter {
    name   = "subnet-id"
    values = var.subnet_ids
  }
}

data "aws_security_group" "ecs_tasks" {
  id = var.ecs_security_group_id
}

# Subnet group for Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "gaming-system-redis-subnet-group"
  subnet_ids = data.aws_subnets.private.ids

  tags = {
    Name        = "gaming-system-redis-subnet-group"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

# Security group for Redis
resource "aws_security_group" "redis" {
  name        = "gaming-system-redis-sg"
  description = "Security group for Redis ElastiCache cluster"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    description     = "Redis from ECS tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [data.aws_security_group.ecs_tasks.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "gaming-system-redis-sg"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

# Parameter group for Redis 7
resource "aws_elasticache_parameter_group" "redis" {
  family      = "redis7"
  name        = "gaming-system-redis-params"
  description = "Custom parameter group for Gaming System Redis"

  # Optimize for sub-1ms latency
  parameter {
    name  = "cluster-enabled"
    value = "yes"
  }

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = {
    Name        = "gaming-system-redis-params"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

# KMS key for encryption
resource "aws_kms_key" "redis" {
  description             = "KMS key for Gaming System Redis encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/elasticache/gaming-system-redis/*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "gaming-system-redis-key"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

resource "aws_kms_alias" "redis" {
  name          = "alias/gaming-system-redis"
  target_key_id = aws_kms_key.redis.key_id
}

# Redis Replication Group (Cluster Mode)
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "gaming-system-redis"
  description                = "Gaming System Redis Cluster - Multi-tier caching for sub-1ms latency"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = var.node_type
  num_node_groups            = var.num_shards
  replicas_per_node_group    = var.replicas_per_shard
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis.name
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  automatic_failover_enabled = true
  multi_az_enabled           = true

  # Encryption at rest
  at_rest_encryption_enabled = true
  kms_key_id                 = aws_kms_key.redis.arn

  # Encryption in transit
  transit_encryption_enabled = true
  transit_encryption_mode    = "required"
  auth_token                 = random_password.redis_auth_token.result

  # Maintenance
  maintenance_window         = "sun:03:00-sun:04:00"
  snapshot_window            = "02:00-03:00"
  snapshot_retention_limit   = 5
  auto_minor_version_upgrade = true

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
  }

  tags = {
    Name        = "gaming-system-redis"
    Environment = var.environment
    Project     = "gaming-system"
    Purpose     = "Distributed cache for AI models and game state"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Auth token for Redis
# Redis auth tokens: 16-128 chars, alphanumeric + safe special chars (no @, ", /)
resource "random_password" "redis_auth_token" {
  length           = 32
  special          = true
  override_special = "!#%&*()-_=+[]{}:?"
}

# Store auth token in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name        = "gaming-system/redis-auth-token"
  description = "Redis authentication token"
  kms_key_id  = aws_kms_key.redis.id

  tags = {
    Name        = "gaming-system-redis-auth-token"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
    endpoint   = aws_elasticache_replication_group.redis.configuration_endpoint_address
    port       = 6379
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/gaming-system-redis/slow-log"
  retention_in_days = 7
  kms_key_id        = aws_kms_key.redis.arn

  tags = {
    Name        = "gaming-system-redis-slow-log"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

resource "aws_cloudwatch_log_group" "redis_engine_log" {
  name              = "/aws/elasticache/gaming-system-redis/engine-log"
  retention_in_days = 7
  kms_key_id        = aws_kms_key.redis.arn

  tags = {
    Name        = "gaming-system-redis-engine-log"
    Environment = var.environment
    Project     = "gaming-system"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  alarm_name          = "gaming-system-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 75
  alarm_description   = "Redis CPU utilization is too high"
  alarm_actions       = var.alarm_sns_topic_arns

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }

  tags = {
    Name        = "gaming-system-redis-cpu-high"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  alarm_name          = "gaming-system-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Redis memory usage is too high"
  alarm_actions       = var.alarm_sns_topic_arns

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }

  tags = {
    Name        = "gaming-system-redis-memory-high"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "gaming-system-redis-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "Redis is evicting keys - consider scaling up"
  alarm_actions       = var.alarm_sns_topic_arns

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }

  tags = {
    Name        = "gaming-system-redis-evictions"
    Environment = var.environment
  }
}

# Outputs
output "redis_configuration_endpoint" {
  description = "Redis cluster configuration endpoint"
  value       = aws_elasticache_replication_group.redis.configuration_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_auth_token_secret_arn" {
  description = "ARN of secret containing Redis auth token"
  value       = aws_secretsmanager_secret.redis_auth_token.arn
}

output "redis_security_group_id" {
  description = "Security group ID for Redis cluster"
  value       = aws_security_group.redis.id
}

