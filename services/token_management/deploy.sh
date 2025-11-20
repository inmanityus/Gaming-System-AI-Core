#!/bin/bash

# Token Window Management System Deployment Script

set -e

echo "🚀 Deploying Token Window Management System..."

# Configuration
SERVICE_NAME="token-management"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_TAG="${ECR_REGISTRY}/${SERVICE_NAME}:latest"
ECS_CLUSTER="gaming-system-cluster"
ECS_SERVICE="token-management-service"

# Build Docker image
echo "📦 Building Docker image..."
docker build -t ${SERVICE_NAME} .

# Tag for ECR
echo "🏷️  Tagging image for ECR..."
docker tag ${SERVICE_NAME}:latest ${IMAGE_TAG}

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Create repository if it doesn't exist
echo "📁 Creating ECR repository if needed..."
aws ecr describe-repositories --repository-names ${SERVICE_NAME} --region ${AWS_REGION} || \
    aws ecr create-repository --repository-name ${SERVICE_NAME} --region ${AWS_REGION}

# Push to ECR
echo "⬆️  Pushing image to ECR..."
docker push ${IMAGE_TAG}

# Update ECS task definition
echo "📝 Updating ECS task definition..."
cat > task-definition.json <<EOF
{
    "family": "${SERVICE_NAME}",
    "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskRole",
    "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
    "networkMode": "awsvpc",
    "containerDefinitions": [
        {
            "name": "${SERVICE_NAME}",
            "image": "${IMAGE_TAG}",
            "memory": 2048,
            "cpu": 1024,
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 8080,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "OPENAI_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:openai-api-key"
                },
                {
                    "name": "ANTHROPIC_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:anthropic-api-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/${SERVICE_NAME}",
                    "awslogs-region": "${AWS_REGION}",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8080/ || exit 1"],
                "interval": 30,
                "timeout": 3,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ],
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048"
}
EOF

# Register task definition
TASK_REVISION=$(aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region ${AWS_REGION} \
    --query 'taskDefinition.revision' \
    --output text)

echo "✅ Registered task definition revision: ${TASK_REVISION}"

# Check if service exists
if aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --region ${AWS_REGION} | grep -q "ACTIVE"; then
    echo "🔄 Updating existing service..."
    aws ecs update-service \
        --cluster ${ECS_CLUSTER} \
        --service ${ECS_SERVICE} \
        --task-definition ${SERVICE_NAME}:${TASK_REVISION} \
        --region ${AWS_REGION}
else
    echo "➕ Creating new service..."
    aws ecs create-service \
        --cluster ${ECS_CLUSTER} \
        --service-name ${ECS_SERVICE} \
        --task-definition ${SERVICE_NAME}:${TASK_REVISION} \
        --desired-count 2 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${PRIVATE_SUBNET_1},${PRIVATE_SUBNET_2}],securityGroups=[${SECURITY_GROUP_ID}]}" \
        --load-balancers "targetGroupArn=${TARGET_GROUP_ARN},containerName=${SERVICE_NAME},containerPort=8080" \
        --region ${AWS_REGION}
fi

# Wait for service to stabilize
echo "⏳ Waiting for service to stabilize..."
aws ecs wait services-stable \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION}

echo "✅ Token Window Management System deployed successfully!"

# Cleanup
rm -f task-definition.json

# Show service status
aws ecs describe-services \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION} \
    --query 'services[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount}'
