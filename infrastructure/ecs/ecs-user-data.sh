#!/bin/bash
# ECS container instance setup script

# Update system
yum update -y

# Configure ECS agent
echo ECS_CLUSTER=gaming-system-cluster >> /etc/ecs/ecs.config
echo ECS_AVAILABLE_LOGGING_DRIVERS='["json-file","awslogs"]' >> /etc/ecs/ecs.config

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Start services
systemctl enable amazon-ecs-agent
systemctl start amazon-ecs-agent

