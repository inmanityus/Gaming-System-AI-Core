# Deploy Core NATS Services to ECS
# Deploys the 5 most critical services first

$services = @(
    "model-management-nats",
    "state-manager-nats",
    "quest-system-nats",
    "npc-behavior-nats"
)

$region = "us-east-1"
$cluster = "gaming-system-cluster"
$subnets = "subnet-0f353054b8e31561d,subnet-036ef66c03b45b1da"
$securityGroup = "sg-00419f4094a7d2101"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

Write-Host "=== Deploying Core NATS Services to ECS ===" -ForegroundColor Cyan

foreach ($service in $services) {
    Write-Host "`nDeploying $service..." -ForegroundColor Yellow
    
    # Register task definition
    $taskDef = aws ecs register-task-definition `
        --family $service `
        --network-mode awsvpc `
        --requires-compatibilities FARGATE `
        --cpu 256 `
        --memory 512 `
        --task-role-arn arn:aws:iam::695353648052:role/ecsTaskExecutionRole `
        --execution-role-arn arn:aws:iam::695353648052:role/ecsTaskExecutionRole `
        --container-definitions "[{`"name`":`"$service`",`"image`":`"695353648052.dkr.ecr.$region.amazonaws.com/bodybroker-services/$service:latest`",`"essential`":true,`"environment`":[{`"name`":`"NATS_URL`",`"value`":`"$natsUrl`"}],`"logConfiguration`":{`"logDriver`":`"awslogs`",`"options`":{`"awslogs-group`":`"/ecs/gaming-system-nats`",`"awslogs-region`":`"$region`",`"awslogs-stream-prefix`":`"$service`"}}}]" `
        --query 'taskDefinition.taskDefinitionArn' `
        --output text
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Task definition registration failed" -ForegroundColor Red
        continue
    }
    
    Write-Host "  Task definition: $taskDef"
    
    # Check if service exists
    $existing = aws ecs describe-services `
        --cluster $cluster `
        --services $service `
        --query 'services[0].status' `
        --output text 2>$null
    
    if ($existing -and $existing -ne "None" -and $existing -ne "INACTIVE") {
        # Update existing
        Write-Host "  Updating existing service..."
        aws ecs update-service `
            --cluster $cluster `
            --service $service `
            --task-definition $taskDef `
            --desired-count 2 `
            --force-new-deployment `
            --output text `
            --query 'service.serviceName'
    } else {
        # Create new
        Write-Host "  Creating new service..."
        aws ecs create-service `
            --cluster $cluster `
            --service-name $service `
            --task-definition $taskDef `
            --desired-count 2 `
            --launch-type FARGATE `
            --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$securityGroup],assignPublicIp=ENABLED}" `
            --output text `
            --query 'service.serviceName'
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Deployed" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Deployment failed" -ForegroundColor Red
    }
}

Write-Host "`n=== Core Services Deployed ===" -ForegroundColor Green
Write-Host "Verify: aws ecs list-services --cluster $cluster | Select-String nats"

