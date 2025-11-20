# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${var.project}-${var.environment}-alb-"
  description = "Security group for Application Load Balancers"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-alb-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Security Group
resource "aws_security_group" "ecs" {
  name_prefix = "${var.project}-${var.environment}-ecs-"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  # Allow traffic from ALB
  ingress {
    description     = "HTTP from ALB"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow ECS tasks to communicate with each other
  ingress {
    description = "All traffic from ECS tasks"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Allow health checks from ECS
  ingress {
    description = "Health checks from VPC"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    description = "All traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-ecs-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${var.project}-${var.environment}-rds-"
  description = "Security group for RDS databases"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL from ECS
  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  # PostgreSQL from EKS (to be added in TASK-003)
  # ingress {
  #   description     = "PostgreSQL from EKS"
  #   from_port       = 5432
  #   to_port         = 5432
  #   protocol        = "tcp"
  #   security_groups = [aws_security_group.eks_nodes.id]
  # }

  egress {
    description = "All traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-rds-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ElastiCache Security Group
resource "aws_security_group" "elasticache" {
  name_prefix = "${var.project}-${var.environment}-elasticache-"
  description = "Security group for ElastiCache"
  vpc_id      = aws_vpc.main.id

  # Redis from ECS
  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  # Redis Cluster Bus
  ingress {
    description     = "Redis Cluster Bus from ECS"
    from_port       = 16379
    to_port         = 16379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    description = "All traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-elasticache-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# NATS Security Group
resource "aws_security_group" "nats" {
  name_prefix = "${var.project}-${var.environment}-nats-"
  description = "Security group for NATS messaging"
  vpc_id      = aws_vpc.main.id

  # NATS Client Port from ECS
  ingress {
    description     = "NATS Client from ECS"
    from_port       = 4222
    to_port         = 4222
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  # NATS Cluster Port
  ingress {
    description = "NATS Cluster"
    from_port   = 6222
    to_port     = 6222
    protocol    = "tcp"
    self        = true
  }

  # NATS HTTP Monitoring
  ingress {
    description     = "NATS Monitoring from ECS"
    from_port       = 8222
    to_port         = 8222
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    description = "All traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-nats-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Bastion Security Group (for management access)
resource "aws_security_group" "bastion" {
  name_prefix = "${var.project}-${var.environment}-bastion-"
  description = "Security group for Bastion hosts"
  vpc_id      = aws_vpc.main.id

  # SSH from specific IP ranges (update with your IP)
  ingress {
    description = "SSH from allowed IPs"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.bastion_allowed_cidrs
  }

  egress {
    description = "All traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-bastion-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Outputs for security groups
output "security_groups" {
  description = "Map of all security group IDs"
  value = {
    alb         = aws_security_group.alb.id
    ecs         = aws_security_group.ecs.id
    rds         = aws_security_group.rds.id
    elasticache = aws_security_group.elasticache.id
    nats        = aws_security_group.nats.id
    bastion     = aws_security_group.bastion.id
  }
}
