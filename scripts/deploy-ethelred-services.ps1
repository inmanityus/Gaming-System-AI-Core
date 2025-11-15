# Deploy ETHELRED services to AWS
Write-Host "Deploying ETHELRED services to AWS..." -ForegroundColor Cyan

$services = @(
    @{
        Name = "story-memory-nats"
        Path = "services/story_memory"
        Dockerfile = "Dockerfile.nats.standalone"
        ECR = "story-memory-nats"
        TaskDef = "infrastructure/ecs/task-definitions/story-memory-nats-fargate.json"
    },
    @{
        Name = "story-memory-api"
        Path = "services/story_memory"
        Dockerfile = "Dockerfile.api"
        ECR = "bodybroker-services/story-memory-api"
        TaskDef = "infrastructure/ecs/task-definitions/story-memory-api.json"
    },
    @{
        Name = "ethelred-4d-ingest"
        Path = "services/ethelred_4d_ingest"
        Dockerfile = "Dockerfile"
        ECR = "bodybroker-services/ethelred-4d-ingest"
        TaskDef = "infrastructure/ecs/task-definitions/ethelred-4d-ingest.json"
    },
    @{
        Name = "ethelred-4d-analyzer"
        Path = "services/ethelred_4d_analyzer"
        Dockerfile = "Dockerfile"
        ECR = "bodybroker-services/ethelred-4d-analyzer"
        TaskDef = "infrastructure/ecs/task-definitions/ethelred-4d-analyzer.json"
    }
)

$region = "us-east-1"
$accountId = "695353648052"
$cluster = "language-system-cluster"

# Login to ECR
Write-Host "Logging in to ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $region | docker login --username AWS --password-stdin "$accountId.dkr.ecr.$region.amazonaws.com"

foreach ($service in $services) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Deploying $($service.Name)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # Build and push Docker image
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    
    try {
        # Create build context with shared modules
        $buildContext = "temp-build-context"
        & "$PSScriptRoot\prepare-build-context.ps1" -ServicePath $service.Path -BuildContextPath $buildContext
        
        Push-Location $buildContext
        
        # Build image
        $imageTag = "$accountId.dkr.ecr.$region.amazonaws.com/$($service.ECR):latest"
        docker build -f $service.Dockerfile -t $imageTag .
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker build failed for $($service.Name)"
            Pop-Location
            Remove-Item -Path $buildContext -Recurse -Force
            continue
        }
        
        # Push to ECR
        Write-Host "Pushing to ECR..." -ForegroundColor Yellow
        docker push $imageTag
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker push failed for $($service.Name)"
            Pop-Location
            Remove-Item -Path $buildContext -Recurse -Force
            continue
        }
        
        Pop-Location
        
        # Clean up build context
        Remove-Item -Path $buildContext -Recurse -Force
        
        Write-Host "Successfully pushed $($service.Name) to ECR" -ForegroundColor Green
        
    } catch {
        Write-Error "Error building $($service.Name): $_"
        if (Test-Path $buildContext) {
            Remove-Item -Path $buildContext -Recurse -Force
        }
        continue
    }
    
    # Register task definition
    if (Test-Path $service.TaskDef) {
        Write-Host "Registering task definition..." -ForegroundColor Yellow
        $taskDefJson = Get-Content $service.TaskDef -Raw
        
        # Register the task definition
        $taskDefArn = aws ecs register-task-definition `
            --cli-input-json $taskDefJson `
            --region $region `
            --query "taskDefinition.taskDefinitionArn" `
            --output text
            
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Task definition registered: $taskDefArn" -ForegroundColor Green
            
            # Create or update service
            $serviceName = "$($service.Name)-fargate"
            
            # Check if service exists
            $existingService = aws ecs describe-services `
                --cluster $cluster `
                --services $serviceName `
                --region $region `
                --query "services[?status=='ACTIVE'].serviceName" `
                --output text
                
            if ($existingService) {
                # Update existing service
                Write-Host "Updating existing service..." -ForegroundColor Yellow
                aws ecs update-service `
                    --cluster $cluster `
                    --service $serviceName `
                    --task-definition $taskDefArn `
                    --force-new-deployment `
                    --region $region
                    
                Write-Host "Service updated: $serviceName" -ForegroundColor Green
            } else {
                # Create new service
                Write-Host "Creating new service..." -ForegroundColor Yellow
                
                # Need to specify network configuration for Fargate
                $networkConfig = @{
                    "awsvpcConfiguration" = @{
                        "subnets" = @("subnet-0b8ba7ffd0610b34f")
                        "securityGroups" = @("sg-0e1949ead49a08f97")
                        "assignPublicIp" = "ENABLED"
                    }
                } | ConvertTo-Json -Compress
                
                aws ecs create-service `
                    --cluster $cluster `
                    --service-name $serviceName `
                    --task-definition $taskDefArn `
                    --desired-count 1 `
                    --launch-type FARGATE `
                    --network-configuration $networkConfig `
                    --region $region
                    
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Service created: $serviceName" -ForegroundColor Green
                } else {
                    Write-Warning "Failed to create service. You may need to configure networking manually."
                }
            }
        } else {
            Write-Error "Failed to register task definition for $($service.Name)"
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment process complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Show service status
Write-Host "`nChecking service status..." -ForegroundColor Yellow
aws ecs list-services --cluster $cluster --region $region --query "serviceArns[]" --output table
