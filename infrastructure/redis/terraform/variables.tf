variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID for Redis cluster"
  type        = string
  default     = "vpc-045c9e283c23ae01e"  # consciousness-training-vpc (where ECS services run)
}

variable "subnet_ids" {
  description = "Subnet IDs for Redis cluster"
  type        = list(string)
  default     = ["subnet-0f353054b8e31561d", "subnet-036ef66c03b45b1da"]  # ECS subnets
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
  default     = "sg-00419f4094a7d2101"  # gaming-system-services
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r7g.large"  # 13.07 GiB memory, network optimized

  validation {
    condition     = can(regex("^cache\\.(r[67]g|r6gd|r7gd|m[67]g)\\.(large|xlarge|2xlarge|4xlarge)$", var.node_type))
    error_message = "Node type must be r6g, r7g, or m6g/m7g family with at least large size"
  }
}

variable "num_shards" {
  description = "Number of shards (node groups) for Redis cluster"
  type        = number
  default     = 3

  validation {
    condition     = var.num_shards >= 1 && var.num_shards <= 500
    error_message = "Number of shards must be between 1 and 500"
  }
}

variable "replicas_per_shard" {
  description = "Number of replicas per shard"
  type        = number
  default     = 1

  validation {
    condition     = var.replicas_per_shard >= 0 && var.replicas_per_shard <= 5
    error_message = "Replicas per shard must be between 0 and 5"
  }
}

variable "alarm_sns_topic_arns" {
  description = "SNS topic ARNs for CloudWatch alarms"
  type        = list(string)
  default     = []
}

