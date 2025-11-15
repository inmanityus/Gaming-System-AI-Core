# NATS Cluster Infrastructure - AWS ECS
# Peer Reviewed: Pending (GPT-5 Pro, Gemini 2.5 Pro, Claude 4.5 Sonnet)
# Purpose: Deploy 5-node NATS cluster with JetStream across 3 AZs

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
    key    = "nats-cluster/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for NATS cluster"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "nats_cluster_size" {
  description = "Number of NATS nodes"
  type        = number
  default     = 5
}

variable "nats_instance_type" {
  description = "EC2 instance type for NATS nodes"
  type        = string
  default     = "m6i.large"
}

variable "nats_version" {
  description = "NATS server version"
  type        = string
  default     = "2.10.7"
}

variable "ebs_volume_size" {
  description = "EBS volume size in GB for JetStream storage"
  type        = number
  default     = 500
}

variable "vpc_id" {
  description = "VPC ID for NATS cluster"
  type        = string
  default     = "vpc-045c9e283c23ae01e"  # consciousness-training-vpc
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for NATS cluster (must span 3 AZs)"
  type        = list(string)
  default     = [
    "subnet-042a9a5caeee61455",  # us-east-1a private
    "subnet-0e0b470d6ebc8065d",  # us-east-1b private
    "subnet-0725bf0a99b2c44ed"   # us-east-1c private
  ]
}

# Security Group for NATS Cluster
resource "aws_security_group" "nats_cluster" {
  name        = "nats-cluster-${var.environment}"
  description = "Security group for NATS cluster"
  vpc_id      = var.vpc_id

  # Client connections (mTLS)
  ingress {
    description = "NATS client connections"
    from_port   = 4222
    to_port     = 4222
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  # Cluster routing
  ingress {
    description = "NATS cluster routing"
    from_port   = 6222
    to_port     = 6222
    protocol    = "tcp"
    self        = true
  }

  # Leafnode connections
  ingress {
    description = "NATS leafnode connections"
    from_port   = 7422
    to_port     = 7422
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  # Monitoring
  ingress {
    description = "NATS monitoring"
    from_port   = 8222
    to_port     = 8222
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }

  # Outbound
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "nats-cluster-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# IAM Role for NATS EC2 Instances
resource "aws_iam_role" "nats_instance_role" {
  name = "nats-instance-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "nats-instance-role-${var.environment}"
    Environment = var.environment
  }
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "nats_profile" {
  name = "nats-instance-profile-${var.environment}"
  role = aws_iam_role.nats_instance_role.name
}

# Attach SSM policy for management
resource "aws_iam_role_policy_attachment" "nats_ssm" {
  role       = aws_iam_role.nats_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach CloudWatch policy for logging
resource "aws_iam_role_policy_attachment" "nats_cloudwatch" {
  role       = aws_iam_role.nats_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# KMS Key for EBS Encryption
resource "aws_kms_key" "nats_ebs" {
  description             = "KMS key for NATS EBS volumes"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "nats-ebs-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "nats_ebs" {
  name          = "alias/nats-ebs-${var.environment}"
  target_key_id = aws_kms_key.nats_ebs.key_id
}

# Launch Template for NATS Nodes
resource "aws_launch_template" "nats" {
  name_prefix   = "nats-${var.environment}-"
  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.nats_instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.nats_profile.name
  }

  vpc_security_group_ids = [aws_security_group.nats_cluster.id]

  block_device_mappings {
    device_name = "/dev/xvda"
    
    ebs {
      volume_size           = 100
      volume_type           = "gp3"
      encrypted             = true
      # Use default AWS managed key instead of CMK
      delete_on_termination = true
    }
  }

  # JetStream data volume
  block_device_mappings {
    device_name = "/dev/xvdf"
    
    ebs {
      volume_size           = var.ebs_volume_size
      volume_type           = "gp3"
      iops                  = 16000
      throughput            = 1000
      encrypted             = true
      # Use default AWS managed key instead of CMK
      delete_on_termination = false
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    
    tags = {
      Name        = "nats-${var.environment}"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Role        = "NATS Server"
    }
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    nats_version    = var.nats_version
    environment     = var.environment
    cluster_size    = var.nats_cluster_size
    aws_region      = var.aws_region
  }))
}

# Auto Scaling Group for NATS Cluster
resource "aws_autoscaling_group" "nats" {
  name                = "nats-cluster-${var.environment}"
  vpc_zone_identifier = var.private_subnet_ids
  desired_capacity    = var.nats_cluster_size
  min_size            = var.nats_cluster_size
  max_size            = var.nats_cluster_size + 2
  health_check_type   = "EC2"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.nats.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "nats-${var.environment}"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "Terraform"
    propagate_at_launch = true
  }
}

# Network Load Balancer for NATS Client Connections
resource "aws_lb" "nats" {
  name               = "nats-${var.environment}"
  internal           = true
  load_balancer_type = "network"
  subnets            = var.private_subnet_ids

  enable_deletion_protection = false
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "nats-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Target Group for NATS Client Port
resource "aws_lb_target_group" "nats_client" {
  name     = "nats-client-${var.environment}"
  port     = 4222
  protocol = "TCP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    protocol            = "TCP"
    port                = 4222
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 10
  }

  tags = {
    Name        = "nats-client-${var.environment}"
    Environment = var.environment
  }
}

# Listener for Client Connections
resource "aws_lb_listener" "nats_client" {
  load_balancer_arn = aws_lb.nats.arn
  port              = 4222
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nats_client.arn
  }
}

# Attach ASG to Target Group
resource "aws_autoscaling_attachment" "nats" {
  autoscaling_group_name = aws_autoscaling_group.nats.id
  lb_target_group_arn    = aws_lb_target_group.nats_client.arn
}

# Data Sources
data "aws_vpc" "selected" {
  id = var.vpc_id
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Outputs
output "nats_nlb_dns" {
  description = "DNS name of NATS NLB"
  value       = aws_lb.nats.dns_name
}

output "nats_connection_string" {
  description = "NATS connection string for services"
  value       = "nats://${aws_lb.nats.dns_name}:4222"
}

output "nats_security_group_id" {
  description = "Security group ID for NATS cluster"
  value       = aws_security_group.nats_cluster.id
}

