# Deploy Remaining NATS Services to ECS (17 services)

$services = @(
    "world-state-nats", "orchestration-nats", "router-nats", "event-bus-nats",
    "time-manager-nats", "weather-manager-nats", "auth-nats", "settings-nats",
    "payment-nats", "performance-mode-nats", "capability-registry-nats",
    "ai-router-nats", "knowledge-base-nats", "language-system-nats",
    "environmental-narrative-nats", "story-teller-nats", "body-broker-integration-nats"
)

$region = "us-east-1"
$cluster = "gaming-system-cluster"
$subnets = "subnet-0f353054b8e31561d,subnet-036ef66c03b45b1da"
$securityGroup = "sg-00419f4094a7d2101"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

Write-Host "Deploying $($services.Count) remaining services..." -ForegroundColor Cyan

$deployed = 0

foreach ($service in $services) {
    Write-Host "  $service..." -NoNewline
    
    # Register task definition
    $taskDef = aws ecs register-task-definition `
        --family $service `
        --network-mode awsvpc `
        --requires-compatibilities FARGATE `
        --cpu 256 --memory 512 `
        --task-role-arn arn:aws:iam::695353648052:role/ecsTaskExecutionRole `
        --execution-role-arn arn:aws:iam::695353648052:role/ecsTaskExecutionRole `
        --container-definitions "[{`"name`":`"$service`",`"image`":`"695353648052.dkr.ecr.$region.amazonaws.com/bodybroker-services/$service:latest`",`"essential`":true,`"environment`":[{`"name`":`"NATS_URL`",`"value`":`"$natsUrl`"}],`"logConfiguration`":{`"logDriver`":`"awslogs`",`"options`":{`"awslogs-group`":`"/ecs/gaming-system-nats`",`"awslogs-region`":`"$region`",`"awslogs-stream-prefix`":`"$service`"}}}]" `
        --query 'taskDefinition.taskDefinitionArn' `
        --output text 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host " ❌" -ForegroundColor Red
        continue
    }
    
    # Create service
    aws ecs create-service `
        --cluster $cluster `
        --service-name $service `
        --task-definition $service `
        --desired-count 2 `
        --launch-type FARGATE `
        --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$securityGroup],assignPublicIp=ENABLED}" `
        --output text `
        --query 'service.serviceName' 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅" -ForegroundColor Green
        $deployed++
    } else {
        Write-Host " ❌" -ForegroundColor Red
    }
}

Write-Host "`nDeployed: $deployed/$($services.Count)" -ForegroundColor Green

