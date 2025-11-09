# Deploy Body Broker to AWS
param(
    [string]$Environment = "dev",
    [string]$InstanceType = "g5.2xlarge"
)

Write-Host "Deploying Body Broker to AWS ($Environment)..." -ForegroundColor Cyan

# Build Docker image
Write-Host "`nBuilding Docker image..."
docker build -t body-broker:latest -f services/body_broker_integration/Dockerfile .

# Push to ECR (assuming ECR repo exists)
Write-Host "`nPushing to ECR..."
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
# docker tag body-broker:latest <account>.dkr.ecr.us-east-1.amazonaws.com/body-broker:latest
# docker push <account>.dkr.ecr.us-east-1.amazonaws.com/body-broker:latest

Write-Host "`n✅ Deployment preparation complete"
Write-Host "Ready for GPU instance provisioning"

