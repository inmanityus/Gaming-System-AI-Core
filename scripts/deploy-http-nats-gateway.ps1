# Deploy HTTP-NATS Gateway to ECS
param(
    [string]$Cluster = "gaming-system-cluster",
    [string]$ServiceName = "http-nats-gateway",
    [int]$DesiredCount = 2
)

Write-Host "Deploying HTTP-NATS Gateway to ECS..." -ForegroundColor Cyan

# Task Definition
$taskDef = @{
    family = $ServiceName
    requiresCompatibilities = @("FARGATE")
    networkMode = "awsvpc"
    cpu = "512"
    memory = "1024"
    executionRoleArn = "arn:aws:iam::695353648052:role/ecsTaskExecutionRole"
    containerDefinitions = @(
        @{
            name = $ServiceName
            image = "695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services/http-nats-gateway:latest"
            essential = $true
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            environment = @(
                @{
                    name = "NATS_URL"
                    value = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
                },
                @{
                    name = "PORT"
                    value = "8000"
                },
                @{
                    name = "HOST"
                    value = "0.0.0.0"
                },
                @{
                    name = "LOG_LEVEL"
                    value = "INFO"
                }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/$ServiceName"
                    "awslogs-region" = "us-east-1"
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8000/health || exit 1")
                interval = 30
                timeout = 5
                retries = 3
                startPeriod = 60
            }
        }
    )
}

# Create CloudWatch log group
Write-Host "Creating CloudWatch log group..." -ForegroundColor Yellow
aws logs create-log-group --log-group-name "/ecs/$ServiceName" --region us-east-1 2>&1 | Out-Null

# Register task definition
Write-Host "Registering task definition..." -ForegroundColor Yellow
$taskDefJson = $taskDef | ConvertTo-Json -Depth 10
$taskDefFile = New-TemporaryFile
$taskDefJson | Out-File -FilePath $taskDefFile -Encoding UTF8

$result = aws ecs register-task-definition --cli-input-json "file://$($taskDefFile.FullName)" --output json | ConvertFrom-Json
Remove-Item $taskDefFile

if ($result) {
    Write-Host "✅ Task definition registered: $($result.taskDefinition.family):$($result.taskDefinition.revision)" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to register task definition" -ForegroundColor Red
    exit 1
}

# Get VPC and subnet information
Write-Host "Getting VPC information..." -ForegroundColor Yellow
$vpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text
$subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query 'Subnets[*].SubnetId' --output json | ConvertFrom-Json | Select-Object -First 3

# Create or update service
Write-Host "Creating/updating ECS service..." -ForegroundColor Yellow

# Check if service exists
$existingService = aws ecs describe-services --cluster $Cluster --services $ServiceName --query 'services[0].serviceName' --output text 2>&1

if ($existingService -eq $ServiceName) {
    # Update existing service
    Write-Host "Updating existing service..." -ForegroundColor Yellow
    $serviceResult = aws ecs update-service `
        --cluster $Cluster `
        --service $ServiceName `
        --task-definition "$($ServiceName):$($result.taskDefinition.revision)" `
        --desired-count $DesiredCount `
        --force-new-deployment `
        --output json | ConvertFrom-Json
} else {
    # Create new service
    Write-Host "Creating new service..." -ForegroundColor Yellow
    $serviceResult = aws ecs create-service `
        --cluster $Cluster `
        --service-name $ServiceName `
        --task-definition "$($ServiceName):$($result.taskDefinition.revision)" `
        --desired-count $DesiredCount `
        --launch-type FARGATE `
        --network-configuration "awsvpcConfiguration={subnets=[$($subnets -join ',')],assignPublicIp=ENABLED}" `
        --output json | ConvertFrom-Json
}

if ($serviceResult) {
    Write-Host "✅ Service deployed successfully!" -ForegroundColor Green
    Write-Host "   Service: $ServiceName" -ForegroundColor Cyan
    Write-Host "   Cluster: $Cluster" -ForegroundColor Cyan
    Write-Host "   Desired Count: $DesiredCount" -ForegroundColor Cyan
    
    Write-Host "`nMonitor deployment status:" -ForegroundColor Yellow
    Write-Host "aws ecs describe-services --cluster $Cluster --services $ServiceName --query 'services[0].deployments'" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to deploy service" -ForegroundColor Red
}

Write-Host "`n✨ HTTP-NATS Gateway deployment initiated!" -ForegroundColor Green