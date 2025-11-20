#!/usr/bin/env pwsh
# Update ECS services with TLS configuration for NATS
# Simplified approach using AWS CLI directly

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Updating ECS Services for NATS TLS ===${NC}"

# NATS endpoint with TLS
$natsUrl = "tls://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
Write-Host "NATS URL: $natsUrl"

# Services to update
$services = @(
    "ai-integration-nats",
    "auth-nats", 
    "body-broker-integration-nats",
    "environmental-narrative-nats",
    "event-bus-nats",
    "knowledge-base-nats",
    "language-system-nats",
    "model-management-nats",
    "npc-behavior-nats",
    "orchestration-nats",
    "payment-nats",
    "performance-mode-nats",
    "quest-system-nats",
    "router-nats",
    "settings-nats",
    "state-manager-nats",
    "story-teller-nats",
    "time-manager-nats",
    "weather-manager-nats",
    "world-state-nats",
    "http-nats-gateway"
)

foreach ($service in $services) {
    Write-Host ""
    Write-Host "${YELLOW}Updating $service...${NC}"
    
    # Get current task definition
    $taskDef = aws ecs describe-services `
        --cluster gaming-system-cluster `
        --services $service `
        --query 'services[0].taskDefinition' `
        --output text 2>$null
        
    if (-not $taskDef -or $taskDef -eq "None") {
        Write-Host "${RED}  Service not found${NC}"
        continue
    }
    
    # Get task definition JSON
    $taskDefJson = aws ecs describe-task-definition `
        --task-definition $taskDef `
        --query 'taskDefinition' `
        --output json
        
    if (-not $taskDefJson) {
        Write-Host "${RED}  Failed to get task definition${NC}"
        continue
    }
    
    # Save to temp file
    $tempFile = New-TemporaryFile
    Set-Content -Path $tempFile -Value $taskDefJson
    
    # Parse JSON
    $taskDefObj = Get-Content $tempFile -Raw | ConvertFrom-Json
    
    # Update environment variables
    $container = $taskDefObj.containerDefinitions[0]
    
    # Find existing environment array or create new
    if (-not $container.environment) {
        $container | Add-Member -NotePropertyName "environment" -NotePropertyValue @()
    }
    
    # Update NATS_URL
    $natsUrlFound = $false
    foreach ($env in $container.environment) {
        if ($env.name -eq "NATS_URL") {
            $env.value = $natsUrl
            $natsUrlFound = $true
        }
    }
    
    if (-not $natsUrlFound) {
        $container.environment += @{
            name = "NATS_URL"
            value = $natsUrl
        }
    }
    
    # Create new task definition
    $newTaskDef = @{
        family = $taskDefObj.family
        taskRoleArn = $taskDefObj.taskRoleArn
        executionRoleArn = $taskDefObj.executionRoleArn
        networkMode = $taskDefObj.networkMode
        containerDefinitions = @($container)
        requiresCompatibilities = @("FARGATE")
        cpu = $taskDefObj.cpu
        memory = $taskDefObj.memory
    }
    
    # Save new task def to file
    $newTaskDefJson = $newTaskDef | ConvertTo-Json -Depth 10
    Set-Content -Path $tempFile -Value $newTaskDefJson
    
    # Register new task definition
    $result = aws ecs register-task-definition `
        --cli-input-json file://$tempFile `
        --output json 2>$null
        
    if ($LASTEXITCODE -ne 0) {
        Write-Host "${RED}  Failed to register task definition${NC}"
        Remove-Item $tempFile
        continue
    }
    
    $resultObj = $result | ConvertFrom-Json
    $newTaskDefArn = $resultObj.taskDefinition.taskDefinitionArn
    
    # Update service
    aws ecs update-service `
        --cluster gaming-system-cluster `
        --service $service `
        --task-definition $newTaskDefArn `
        --force-new-deployment `
        --output json | Out-Null
        
    if ($LASTEXITCODE -eq 0) {
        Write-Host "${GREEN}  ✓ Updated successfully${NC}"
    } else {
        Write-Host "${RED}  Failed to update service${NC}"
    }
    
    # Clean up
    Remove-Item $tempFile
}

Write-Host ""
Write-Host "${GREEN}=== Update Complete ===${NC}"
Write-Host ""
Write-Host "To monitor deployment status:"
Write-Host '  watch -n 5 "aws ecs list-services --cluster gaming-system-cluster | jq -r ''.serviceArns[]'' | xargs -I {} aws ecs describe-services --cluster gaming-system-cluster --services {} --query ''services[0].[serviceName,runningCount,desiredCount,pendingCount]'' --output text"'
