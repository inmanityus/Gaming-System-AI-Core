# AWS Resources Mapping

This document maps all AWS resources used by the Gaming System AI Core.

## Account Information
- **Account ID**: 695353648052
- **Primary Region**: us-east-1
- **GitHub Repository**: https://github.com/inmanityus/Gaming-System-AI-Core

## Resource Breakdown by Service

### Amazon ECS (Elastic Container Service)
```
Cluster: gaming-system-cluster
Services (45 total):
  - knowledge-base
  - knowledge-base-nats
  - ai-integration
  - ai-integration-nats
  - language-system
  - language-system-nats
  - story-teller
  - story-teller-nats
  - npc-behavior
  - npc-behavior-nats
  - orchestration
  - orchestration-nats
  - state-manager
  - state-manager-nats
  ... and 31 more services
```

### Amazon ECR (Elastic Container Registry)
```
Repository: bodybroker-services
URI: 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services
Images:
  - :knowledge-base-latest
  - :ai-integration-latest
  - :language-system-latest
  ... one tag per service
```

### Amazon RDS (Aurora PostgreSQL)
```
Cluster: gaming-system-aurora
Endpoint: [To be documented when created]
Port: 5432
Database: gaming_system
```

### Amazon ElastiCache (Redis)
```
Cluster: gaming-system-redis
Endpoint: [To be documented when created]
Port: 6379
```

### IAM Roles for CI/CD
```
GitHub Actions OIDC:
  - github-actions-ecr-push
  - github-actions-deploy-staging  
  - github-actions-deploy-production

ECS Task Roles:
  - ecsTaskExecutionRole
  - ecsTaskRole
```

### CloudWatch
```
Log Groups:
  - /ecs/gaming-system/*
  - /aws/lambda/*

Alarms:
  - {service-name}-production-error-rate
  - {service-name}-production-latency
  - {service-name}-production-cpu-usage
  - {service-name}-production-memory-usage
```

### VPC and Networking
```
VPC: [Default VPC used currently]
Subnets: 
  - subnet-0f353054b8e31561d
  - subnet-036ef66c03b45b1da
Security Group: sg-00419f4094a7d2101
```

### S3 Buckets (if created)
```
Artifacts: gaming-system-artifacts
Logs: gaming-system-logs
Backups: gaming-system-backups
```

## Service Port Mapping

| Service | Container Port | Host Port | Protocol |
|---------|---------------|-----------|----------|
| knowledge-base | 8000 | Dynamic | HTTP |
| ai-integration | 8000 | Dynamic | HTTP |
| language-system | 8000 | Dynamic | HTTP |
| story-teller | 8000 | Dynamic | HTTP |
| npc-behavior | 8000 | Dynamic | HTTP |
| orchestration | 8000 | Dynamic | HTTP |
| NATS services | 4222 | 4222 | TCP |

## Cost Centers

| Service | Type | Estimated Monthly Cost |
|---------|------|------------------------|
| ECS Fargate | Compute | ~$600 |
| ECR | Storage | ~$50 |
| CloudWatch | Logs/Metrics | ~$100 |
| RDS Aurora | Database | ~$200 |
| ElastiCache | Redis | ~$100 |
| **Total** | | **~$1,050** |

## Monitoring URLs

- ECS Console: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/gaming-system-cluster
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
- ECR Console: https://console.aws.amazon.com/ecr/repositories/bodybroker-services

## Deployment Information

### Container Images
All services use the same ECR repository with different tags:
```bash
# Format
695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:{service-name}-{version}

# Examples
695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:knowledge-base-latest
695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:knowledge-base-20241120
```

### Task Definitions
Each service has its own task definition:
- Family: {service-name}
- Revision: Increments with each update
- CPU: 256-512 (0.25-0.5 vCPU)
- Memory: 512-1024 MB

## Security Notes

- All services run in Fargate (no EC2 instances to manage)
- Services communicate internally via service discovery
- External access requires ALB/API Gateway (to be configured)
- All logs encrypted at rest in CloudWatch
- IAM roles follow least-privilege principle
