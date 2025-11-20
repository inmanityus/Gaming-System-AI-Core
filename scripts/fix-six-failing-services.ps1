# Fix the 6 specific failing services identified
param(
    [string]$Region = "us-east-1",
    [string]$AccountId = "695353648052",
    [string]$Cluster = "gaming-system-cluster"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Fixing 6 Failing Services ===" -ForegroundColor Cyan
Write-Host "Services: knowledge-base, ai-integration, language-system, story-teller, npc-behavior, orchestration" -ForegroundColor Yellow

# Services that need fixing (all have code fixes applied)
$failingServices = @(
    @{Name="knowledge-base"; Path="services/knowledge_base"; Issue="Docker image missing in ECR"},
    @{Name="ai-integration"; Path="services/ai_integration"; Issue="Logger import added"},
    @{Name="language-system"; Path="services/language_system"; Issue="grpcio added to requirements"},
    @{Name="story-teller"; Path="services/story_teller"; Issue="PostgreSQLPool import fixed"},
    @{Name="npc-behavior"; Path="services/npc_behavior"; Issue="ProxyManager import fixed"},
    @{Name="orchestration"; Path="services/orchestration"; Issue="LLMClient import fixed"}
)

# Login to ECR
Write-Host "`nLogging in to ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

# Check/create ECR repositories
Write-Host "`nChecking ECR repositories..." -ForegroundColor Yellow
foreach ($service in $failingServices) {
    $repoName = "bodybroker-services/$($service.Name)"
    
    # Check if repository exists
    $repoExists = aws ecr describe-repositories `
        --repository-names $repoName `
        --region $Region `
        --query 'repositories[0].repositoryName' `
        --output text 2>$null
    
    if ($LASTEXITCODE -ne 0 -or $repoExists -eq "None") {
        Write-Host "Creating ECR repository: $repoName" -ForegroundColor Gray
        aws ecr create-repository `
            --repository-name $repoName `
            --region $Region `
            --no-cli-pager | Out-Null
    }
}

# Build timestamp for all images
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

# Build and deploy each service
foreach ($service in $failingServices) {
    Write-Host "`nProcessing $($service.Name) - Issue: $($service.Issue)" -ForegroundColor Yellow
    
    $servicePath = $service.Path
    
    # Determine which Dockerfile to use (prefer nats, then regular)
    $dockerfile = $null
    if (Test-Path (Join-Path $servicePath "Dockerfile.nats")) {
        $dockerfile = Join-Path $servicePath "Dockerfile.nats"
        Write-Host "  Using Dockerfile.nats" -ForegroundColor Gray
    } elseif (Test-Path (Join-Path $servicePath "Dockerfile")) {
        $dockerfile = Join-Path $servicePath "Dockerfile"
        Write-Host "  Using Dockerfile" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ No Dockerfile found for $($service.Name)" -ForegroundColor Red
        continue
    }
    
    # Build Docker image
    $imageName = "bodybroker-services/$($service.Name):$timestamp"
    $imageUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$imageName"
    
    Write-Host "  Building Docker image..." -ForegroundColor Gray
    docker build -f $dockerfile -t $imageName . 2>&1 | Out-String | Write-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Docker build failed for $($service.Name)" -ForegroundColor Red
        continue
    }
    
    # Tag and push to ECR
    Write-Host "  Pushing to ECR..." -ForegroundColor Gray
    docker tag $imageName $imageUri
    docker push $imageUri 2>&1 | Out-String | Write-Host
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Docker push failed for $($service.Name)" -ForegroundColor Red
        continue
    }
    
    Write-Host "  ✓ Docker image pushed: $imageUri" -ForegroundColor Green
    
    # Get current task definition
    Write-Host "  Updating ECS service..." -ForegroundColor Gray
    
    $taskDefArn = aws ecs describe-services `
        --cluster $Cluster `
        --services $service.Name `
        --region $Region `
        --query 'services[0].taskDefinition' `
        --output text 2>$null
    
    if ($taskDefArn -and $taskDefArn -ne "None") {
        # Get task definition JSON
        $taskDefJson = aws ecs describe-task-definition `
            --task-definition $taskDefArn `
            --region $Region `
            --output json
        
        $taskDef = $taskDefJson | ConvertFrom-Json
        
        # Update container image
        $taskDef.taskDefinition.containerDefinitions[0].image = $imageUri
        
        # Create new task definition structure
        $newTaskDef = @{
            family = $taskDef.taskDefinition.family
            networkMode = $taskDef.taskDefinition.networkMode
            requiresCompatibilities = $taskDef.taskDefinition.requiresCompatibilities
            cpu = $taskDef.taskDefinition.cpu
            memory = $taskDef.taskDefinition.memory
            executionRoleArn = $taskDef.taskDefinition.executionRoleArn
            containerDefinitions = $taskDef.taskDefinition.containerDefinitions
        }
        
        # Add optional fields if present
        if ($taskDef.taskDefinition.taskRoleArn) {
            $newTaskDef.taskRoleArn = $taskDef.taskDefinition.taskRoleArn
        }
        
        # Save to temp file
        $tempFile = "task-def-$($service.Name)-temp.json"
        $newTaskDef | ConvertTo-Json -Depth 10 | Out-File -FilePath $tempFile -Encoding utf8
        
        # Register new task definition
        $newTaskDefArn = aws ecs register-task-definition `
            --cli-input-json file://$tempFile `
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
        
        Write-Host "  ✓ ECS service updated and redeploying" -ForegroundColor Green
        
        # Clean up
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        
        # Add small delay to avoid rate limiting
        Start-Sleep -Seconds 2
    } else {
        Write-Host "  ✗ Could not find task definition for $($service.Name)" -ForegroundColor Red
    }
}

# Clean up local Docker images to save space
Write-Host "`nCleaning up local Docker images..." -ForegroundColor Yellow
docker image prune -f | Out-Null

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Services will take 2-5 minutes to stabilize." -ForegroundColor Yellow
Write-Host "`nCheck deployment status with:" -ForegroundColor Cyan
Write-Host "aws ecs list-services --cluster $Cluster --query 'serviceArns[*]' --output json | ConvertFrom-Json | ForEach-Object { " -NoNewline
Write-Host "aws ecs describe-services --cluster $Cluster --services `$_ --query " -NoNewline
Write-Host "'services[0].[serviceName, runningCount, desiredCount, deployments[0].rolloutState]' --output text }"

# Save deployed image tags for tracking
$deploymentInfo = @{
    Timestamp = Get-Date
    Services = @{}
}

foreach ($service in $failingServices) {
    $deploymentInfo.Services[$service.Name] = @{
        Image = "$AccountId.dkr.ecr.$Region.amazonaws.com/bodybroker-services/$($service.Name):$timestamp"
        Issue = $service.Issue
    }
}

$deploymentInfo | ConvertTo-Json -Depth 3 | Out-File "deployment-$timestamp.json"
Write-Host "`nDeployment info saved to: deployment-$timestamp.json" -ForegroundColor Gray
