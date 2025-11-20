# Fix and redeploy failing services
param(
    [string]$Region = "us-east-1",
    [string]$AccountId = "695353648052",
    [string]$Cluster = "gaming-system-cluster"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Fixing Failing Services ===" -ForegroundColor Cyan

# Services that need fixing
$failingServices = @(
    @{Name="knowledge-base"; Path="services/knowledge_base"; Issue="Pydantic regex->pattern"},
    @{Name="ai-integration"; Path="services/ai_integration"; Issue="Module import structure"},
    @{Name="language-system"; Path="services/language_system"; Issue="Unknown"},
    @{Name="body-broker-qa-orchestrator"; Path="services/body_broker_qa_orchestrator"; Issue="Running count mismatch"}
)

# Login to ECR
Write-Host "`nLogging in to ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

# Build base image with all shared dependencies
Write-Host "`nBuilding base image with shared dependencies..." -ForegroundColor Yellow
$baseImageTag = "bodybroker-services:base-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$baseImageUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$baseImageTag"

# Create temporary Dockerfile for base image
$baseDockerfile = @"
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy shared dependencies first
COPY services/shared /app/shared

# Install shared dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    asyncpg \
    pydantic \
    httpx \
    redis \
    nats-py \
    grpcio \
    grpcio-tools \
    prometheus-client

# Environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=""
"@

$baseDockerfile | Out-File -FilePath "Dockerfile.base" -Encoding utf8

# Build and push base image
docker build -f Dockerfile.base -t $baseImageTag .
docker tag $baseImageTag $baseImageUri
docker push $baseImageUri

# Update each failing service
foreach ($service in $failingServices) {
    Write-Host "`nFixing $($service.Name) - Issue: $($service.Issue)" -ForegroundColor Yellow
    
    $servicePath = $service.Path
    $dockerfilePath = Join-Path $servicePath "Dockerfile"
    
    # Create service-specific Dockerfile that properly structures the module
    $serviceDockerfile = @"
FROM $baseImageUri

# Copy service files to proper module structure
COPY $servicePath /app/$($service.Name.Replace('-', '_'))

# Install service-specific requirements if they exist
RUN if [ -f /app/$($service.Name.Replace('-', '_'))/requirements.txt ]; then \
        pip install --no-cache-dir -r /app/$($service.Name.Replace('-', '_'))/requirements.txt; \
    fi

# Set service name
ENV SERVICE_NAME=$($service.Name)

# Default command - will be overridden by task definition
CMD ["python", "-m", "uvicorn", "$($service.Name.Replace('-', '_')).server:app", "--host", "0.0.0.0", "--port", "8000"]
"@
    
    # Save temporary Dockerfile
    $tempDockerfile = "Dockerfile.$($service.Name)"
    $serviceDockerfile | Out-File -FilePath $tempDockerfile -Encoding utf8
    
    # Build and push service image
    $serviceTag = "$($service.Name):$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $serviceUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/bodybroker-services/$serviceTag"
    
    docker build -f $tempDockerfile -t $serviceTag .
    docker tag $serviceTag $serviceUri
    docker push $serviceUri
    
    # Update ECS service to use new image
    Write-Host "Updating ECS service $($service.Name)..." -ForegroundColor Gray
    
    # Get current task definition
    $taskDefArn = aws ecs describe-services `
        --cluster $Cluster `
        --services $service.Name `
        --region $Region `
        --query 'services[0].taskDefinition' `
        --output text
    
    if ($taskDefArn -and $taskDefArn -ne "None") {
        # Get task definition
        $taskDef = aws ecs describe-task-definition `
            --task-definition $taskDefArn `
            --region $Region | ConvertFrom-Json
        
        # Update container image
        $containerDef = $taskDef.taskDefinition.containerDefinitions[0]
        $containerDef.image = $serviceUri
        
        # Create new task definition
        $newTaskDef = @{
            family = $taskDef.taskDefinition.family
            networkMode = $taskDef.taskDefinition.networkMode
            requiresCompatibilities = $taskDef.taskDefinition.requiresCompatibilities
            cpu = $taskDef.taskDefinition.cpu
            memory = $taskDef.taskDefinition.memory
            executionRoleArn = $taskDef.taskDefinition.executionRoleArn
            containerDefinitions = @($containerDef)
        }
        
        if ($taskDef.taskDefinition.taskRoleArn) {
            $newTaskDef.taskRoleArn = $taskDef.taskDefinition.taskRoleArn
        }
        
        $newTaskDefJson = $newTaskDef | ConvertTo-Json -Depth 10
        $newTaskDefJson | Out-File -FilePath "task-def-temp.json" -Encoding utf8
        
        # Register new task definition
        $newTaskDefArn = aws ecs register-task-definition `
            --cli-input-json file://task-def-temp.json `
            --region $Region `
            --query 'taskDefinition.taskDefinitionArn' `
            --output text
        
        # Update service
        aws ecs update-service `
            --cluster $Cluster `
            --service $service.Name `
            --task-definition $newTaskDefArn `
            --force-new-deployment `
            --region $Region `
            --no-cli-pager | Out-Null
        
        Write-Host "  ✓ $($service.Name) updated and redeploying" -ForegroundColor Green
        
        # Clean up temp files
        Remove-Item "task-def-temp.json" -ErrorAction SilentlyContinue
    } else {
        Write-Host "  ✗ Could not find task definition for $($service.Name)" -ForegroundColor Red
    }
    
    # Clean up temp Dockerfile
    Remove-Item $tempDockerfile -ErrorAction SilentlyContinue
}

# Clean up base Dockerfile
Remove-Item "Dockerfile.base" -ErrorAction SilentlyContinue

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Services will take 2-3 minutes to stabilize." -ForegroundColor Yellow
Write-Host "Run this command to check status:" -ForegroundColor Gray
Write-Host "aws ecs list-services --cluster $Cluster --query 'serviceArns[*]' --output json | ConvertFrom-Json | ForEach-Object { aws ecs describe-services --cluster $Cluster --services `$_ --query 'services[0].[serviceName, runningCount, desiredCount]' --output text } | Where-Object { `$_.Split(""`t"")[1] -ne `$_.Split(""`t"")[2] }"
