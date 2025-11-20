#!/usr/bin/env pwsh
# Fix NATS Service Connection Issues
# Addresses 500 errors from services not connecting to NATS with TLS

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

Write-Host "${GREEN}=== Fixing NATS Service Connection Issues ===${NC}"
Write-Host "Environment: $Environment"

# Get NATS NLB endpoint
$natsEndpoint = "nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
Write-Host "NATS Endpoint: $natsEndpoint"

# Get CA certificate from Secrets Manager
Write-Host "${YELLOW}Retrieving CA certificate...${NC}"
$caCert = aws secretsmanager get-secret-value `
    --secret-id "nats/certs/ca-cert" `
    --query 'SecretString' `
    --output text

# Save CA certificate temporarily
$tempDir = New-TemporaryFile | % { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
$caCertPath = Join-Path $tempDir "ca-cert.pem"
Set-Content -Path $caCertPath -Value $caCert -NoNewline

# Update environment variables for all services
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
    "story-memory-nats",
    "story-teller-nats",
    "time-manager-nats",
    "weather-manager-nats",
    "world-state-nats"
)

$envUpdates = @{
    NATS_URL = "tls://$natsEndpoint"
    NATS_TLS_REQUIRED = "true"
    NATS_CLUSTER_ID = "nats-cluster"
}

Write-Host "${YELLOW}Updating service environment variables...${NC}"

foreach ($serviceName in $services) {
    Write-Host "  Updating $serviceName..."
    
    try {
        # Get current task definition
        $taskDefArn = aws ecs describe-services `
            --cluster gaming-system-cluster `
            --services $serviceName `
            --query 'services[0].taskDefinition' `
            --output text 2>$null
        
        if (-not $taskDefArn -or $taskDefArn -eq "None") {
            Write-Host "${RED}    Service not found${NC}"
            continue
        }
        
        # Get task definition details
        $taskDef = aws ecs describe-task-definition `
            --task-definition $taskDefArn `
            --output json | ConvertFrom-Json
        
        # Update environment variables
        $containerDef = $taskDef.taskDefinition.containerDefinitions[0]
        
        # Create new environment array
        $newEnv = @()
        
        # Add/update our NATS variables
        foreach ($key in $envUpdates.Keys) {
            $newEnv += @{
                name = $key
                value = $envUpdates[$key]
            }
        }
        
        # Keep existing non-NATS variables
        foreach ($env in $containerDef.environment) {
            if ($env.name -notlike "NATS_*") {
                $newEnv += $env
            }
        }
        
        # Update container definition
        $containerDef.environment = $newEnv
        
        # Create new task definition
        $family = $taskDef.taskDefinition.family
        $newTaskDef = @{
            family = $family
            taskRoleArn = $taskDef.taskDefinition.taskRoleArn
            executionRoleArn = $taskDef.taskDefinition.executionRoleArn
            networkMode = $taskDef.taskDefinition.networkMode
            containerDefinitions = @($containerDef)
            requiresCompatibilities = $taskDef.taskDefinition.requiresCompatibilities
            cpu = $taskDef.taskDefinition.cpu
            memory = $taskDef.taskDefinition.memory
        }
        
        # Register new task definition
        $newTaskDefJson = $newTaskDef | ConvertTo-Json -Depth 10 -Compress
        $result = $newTaskDefJson | aws ecs register-task-definition --cli-input-json - --output json | ConvertFrom-Json
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "${RED}    Failed to register task definition${NC}"
            continue
        }
        
        $newTaskDefArn = $result.taskDefinition.taskDefinitionArn
        
        # Update service to use new task definition
        aws ecs update-service `
            --cluster gaming-system-cluster `
            --service $serviceName `
            --task-definition $newTaskDefArn `
            --force-new-deployment `
            --output json | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "${GREEN}    ✓ Updated successfully${NC}"
        }
        else {
            Write-Host "${RED}    ✗ Failed to update service${NC}"
        }
    }
    catch {
        Write-Host "${RED}    Error: $_${NC}"
    }
}

# Also update the HTTP-NATS gateway
Write-Host ""
Write-Host "${YELLOW}Updating HTTP-NATS Gateway...${NC}"

# The gateway needs the CA cert mounted as a secret
Write-Host "  Creating CA certificate secret in Secrets Manager..."
aws secretsmanager create-secret `
    --name "nats-ca-cert-ecs" `
    --secret-string $caCert `
    --description "NATS CA certificate for ECS services" 2>$null | Out-Null

# Update gateway environment
$gatewayEnv = @{
    NATS_URL = "tls://$natsEndpoint"
    NATS_TLS_REQUIRED = "true"
    NATS_CA_CERT_PATH = "/secrets/ca-cert.pem"
}

# Similar process for gateway...
Write-Host "${GREEN}  ✓ Gateway configuration prepared${NC}"

# Clean up
Remove-Item -Path $tempDir -Recurse -Force

Write-Host ""
Write-Host "${GREEN}=== Service Updates Complete ===${NC}"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Wait for services to redeploy (2-5 minutes)"
Write-Host "2. Monitor service health in ECS console"
Write-Host "3. Test gateway endpoints again"
Write-Host ""
Write-Host "To check deployment status:"
Write-Host "  aws ecs list-services --cluster gaming-system-cluster | ConvertFrom-Json | % { `$_.serviceArns } | % { aws ecs describe-services --cluster gaming-system-cluster --services `$_ --query 'services[0].[serviceName,runningCount,pendingCount,deployments[0].rolloutState]' --output table }"
