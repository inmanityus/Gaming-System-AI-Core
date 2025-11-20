# HTTP-NATS Gateway Public ALB Infrastructure
# Purpose: Provide public internet access to the HTTP-NATS gateway service

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "gaming-system-terraform-state"
    key    = "gateway-alb/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = "vpc-045c9e283c23ae01e"
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
  default     = [
    "subnet-0dc768f3432060394",  # us-east-1a public
    "subnet-02c4f6387279b89ce",  # us-east-1b public
    "subnet-0222fe58a7d5858ee"   # us-east-1c public
  ]
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener (optional)"
  type        = string
  default     = ""
}

# Data sources
data "aws_ecs_cluster" "main" {
  cluster_name = "gaming-system-cluster"
}

data "aws_ecs_service" "gateway" {
  cluster_arn  = data.aws_ecs_cluster.main.arn
  service_name = "http-nats-gateway"
}

# Security Group for ALB
resource "aws_security_group" "gateway_alb" {
  name        = "gateway-alb-${var.environment}"
  description = "Security group for HTTP-NATS Gateway ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "gateway-alb-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Application Load Balancer
resource "aws_lb" "gateway" {
  name               = "gateway-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.gateway_alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "gateway-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Target Group for Gateway Service
resource "aws_lb_target_group" "gateway" {
  name     = "gateway-${var.environment}"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name        = "gateway-${var.environment}"
    Environment = var.environment
  }
}

# HTTP Listener
resource "aws_lb_listener" "gateway_http" {
  load_balancer_arn = aws_lb.gateway.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }
}

# HTTPS Listener (optional, if certificate provided)
resource "aws_lb_listener" "gateway_https" {
  count             = var.certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.gateway.arn
  port              = "443"
  protocol          = "HTTPS"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }
}

# Update ECS Service to use ALB (done via AWS CLI after terraform)

# Outputs
output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.gateway.dns_name
}

output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.gateway.arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.gateway.arn
}

output "gateway_url" {
  description = "Public URL for the gateway"
  value       = "http://${aws_lb.gateway.dns_name}"
}
