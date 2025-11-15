# Deploy All NATS Services to AWS ECS
# Creates/updates ECS services for all 22 NATS microservices

param(
    [string]$Region = "us-east-1",
    [string]$Cluster = "gaming-system-cluster",
    [string]$AccountId = "695353648052",
    [int]$DesiredCount = 2
)

$ErrorActionPreference = "Stop"

Write-Host "=== Deploying NATS Services to ECS ===" -ForegroundColor Cyan
Write-Host "Region: $Region"
Write-Host "Cluster: $Cluster"
Write-Host "Desired Count: $DesiredCount"

$ecrRepo = "$AccountId.dkr.ecr.$Region.amazonaws.com/bodybroker-services"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

# Get VPC configuration from existing services
Write-Host "`nGetting VPC configuration..." -ForegroundColor Yellow
$existingService = aws ecs describe-services `
    --cluster $Cluster `
    --services ai-router `
    --query 'services[0].networkConfiguration.awsvpcConfiguration' `
    --output json | ConvertFrom-Json

$subnets = $existingService.subnets -join ','
$securityGroups = $existingService.securityGroups -join ','

Write-Host "Subnets: $subnets"
Write-Host "Security Groups: $securityGroups"

$services = @(
    "ai-integration", "model-management", "state-manager", "quest-system",
    "npc-behavior", "world-state", "orchestration", "router",
    "event-bus", "time-manager", "weather-manager", "auth",
    "settings", "payment", "performance-mode", "capability-registry",
    "ai-router", "knowledge-base", "language-system",
    "environmental-narrative", "story-teller", "body-broker-integration"
)

$deployed = 0
$failed = 0

foreach ($service in $services) {
    $serviceName = "$service-nats"
    $imageName = "$service-nats".Replace("_", "-")
    
    Write-Host "`n=== Deploying $serviceName ===" -ForegroundColor Yellow
    
    # Create task definition
    $taskDef = @{
        family = $serviceName
        networkMode = "awsvpc"
        requiresCompatibilities = @("FARGATE")
        cpu = "256"
        memory = "512"
        taskRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
        executionRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
        containerDefinitions = @(
            @{
                name = $serviceName
                image = "$ecrRepo/$imageName:latest"
                essential = $true
                portMappings = @()
                environment = @(
                    @{name = "NATS_URL"; value = $natsUrl},
                    @{name = "SERVICE_NAME"; value = $serviceName}
                )
                logConfiguration = @{
                    logDriver = "awslogs"
                    options = @{
                        "awslogs-group" = "/ecs/gaming-system-nats"
                        "awslogs-region" = $Region
                        "awslogs-stream-prefix" = $serviceName
                    }
                }
                healthCheck = @{
                    command = @("CMD-SHELL", "ps aux | grep -q '[p]ython.*nats_server.py' || exit 1")
                    interval = 30
                    timeout = 5
                    retries = 3
                    startPeriod = 10
                }
            }
        )
    }
    
    # Save task definition to temp file
    $taskDefFile = [System.IO.Path]::GetTempFileName()
    $taskDef | ConvertTo-Json -Depth 10 | Set-Content $taskDefFile
    
    try {
        # Register task definition
        Write-Host "  Registering task definition..."
        $taskDefArn = aws ecs register-task-definition `
            --cli-input-json file://$taskDefFile `
            --query 'taskDefinition.taskDefinitionArn' `
            --output text
        
        # Check if service exists
        $existingService = aws ecs describe-services `
            --cluster $Cluster `
            --services $serviceName `
            --query 'services[0].status' `
            --output text 2>$null
        
        if ($existingService -and $existingService -ne "None" -and $existingService -ne "INACTIVE") {
            # Update existing service
            Write-Host "  Updating existing service..."
            aws ecs update-service `
                --cluster $Cluster `
                --service $serviceName `
                --task-definition $taskDefArn `
                --desired-count $DesiredCount `
                --force-new-deployment `
                --output json | Out-Null
        } else {
            # Create new service
            Write-Host "  Creating new service..."
            aws ecs create-service `
                --cluster $Cluster `
                --service-name $serviceName `
                --task-definition $taskDefArn `
                --desired-count $DesiredCount `
                --launch-type FARGATE `
                --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$securityGroups],assignPublicIp=ENABLED}" `
                --output json | Out-Null
        }
        
        Write-Host "  ✅ Deployed" -ForegroundColor Green
        $deployed++
    }
    catch {
        Write-Host "  ❌ Failed: $_" -ForegroundColor Red
        $failed++
    }
    finally {
        Remove-Item $taskDefFile -ErrorAction SilentlyContinue
    }
}

Write-Host "`n=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "Deployed: $deployed/$($services.Count)" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

Write-Host "`nVerify deployment:"
Write-Host "  aws ecs list-services --cluster $Cluster | grep nats"
Write-Host "  aws ecs describe-services --cluster $Cluster --services <service-name>"

