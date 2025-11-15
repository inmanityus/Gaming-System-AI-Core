# Add Health Check Infrastructure to All Services
# Updates Dockerfiles, rebuilds images, updates task definitions

$region = "us-east-1"
$accountId = "695353648052"
$cluster = "gaming-system-cluster"

$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "weather_manager", "auth", "settings",
    "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "environmental_narrative",
    "story_teller", "body_broker_integration"
)

Write-Host "=== Adding Health Check Infrastructure ===" -ForegroundColor Cyan

# Step 1: Update Dockerfiles
Write-Host "`nStep 1: Updating Dockerfiles to expose port 8080..." -ForegroundColor Yellow
$dockerfilesUpdated = 0

foreach ($service in $services) {
    $dockerfilePath = "services/$service/Dockerfile.nats"
    
    if (Test-Path $dockerfilePath) {
        $content = Get-Content $dockerfilePath -Raw
        
        # Check if port already exposed
        if ($content -notmatch "EXPOSE 8080") {
            # Add EXPOSE 8080 before CMD
            $content = $content -replace "(ENV NATS_URL=[^\n]+)", "`$1`nEXPOSE 8080"
            Set-Content $dockerfilePath -Value $content -NoNewline
            Write-Host "  ✅ $service Dockerfile updated" -ForegroundColor Green
            $dockerfilesUpdated++
        }
    }
}

Write-Host "  Updated $dockerfilesUpdated Dockerfiles`n"

# Step 2: Rebuild and push images
Write-Host "Step 2: Rebuilding Docker images..." -ForegroundColor Yellow
$ecrRepo = "$accountId.dkr.ecr.$region.amazonaws.com/bodybroker-services"

$rebuilt = 0
foreach ($service in $services) {
    $imageName = $service.Replace("_", "-")
    $dockerfilePath = "services/$service/Dockerfile.nats"
    
    if (Test-Path $dockerfilePath) {
        Write-Host "  Building $imageName-nats..."
        docker build -f $dockerfilePath -t "$imageName-nats:latest" . --quiet | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            docker tag "$imageName-nats:latest" "$ecrRepo/$imageName-nats:latest"
            docker push "$ecrRepo/$imageName-nats:latest" --quiet | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✅ Built and pushed" -ForegroundColor Green
                $rebuilt++
            }
        }
    }
}

Write-Host "  Rebuilt and pushed: $rebuilt images`n"

# Step 3: Update task definitions with health checks
Write-Host "Step 3: Updating ECS task definitions with health checks..." -ForegroundColor Yellow
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

$tasksUpdated = 0

foreach ($service in $services) {
    $serviceName = $service.Replace("_", "-") + "-nats"
    $imageUri = "${ecrRepo}/${serviceName}:latest"
    
    $taskDefJson = @"
{
  "family": "$serviceName",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "taskRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "$serviceName",
      "image": "$imageUri",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NATS_URL", "value": "$natsUrl"},
        {"name": "SERVICE_NAME", "value": "$serviceName"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/gaming-system-nats",
          "awslogs-region": "$region",
          "awslogs-stream-prefix": "$serviceName"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "wget -q -O - http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 30
      }
    }
  ]
}
"@
    
    $tempFile = New-TemporaryFile
    $taskDefJson | Set-Content $tempFile.FullName
    
    try {
        aws ecs register-task-definition --cli-input-json file://$($tempFile.FullName) --region $region --output json | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $serviceName task definition updated" -ForegroundColor Green
            $tasksUpdated++
        }
    }
    catch {
        Write-Host "  ❌ $serviceName failed: $_" -ForegroundColor Red
    }
    finally {
        Remove-Item $tempFile.FullName -ErrorAction SilentlyContinue
    }
}

Write-Host "  Updated $tasksUpdated task definitions`n"

# Step 4: Update services
Write-Host "Step 4: Updating ECS services..." -ForegroundColor Yellow
$servicesUpdated = 0

foreach ($service in $services) {
    $serviceName = $service.Replace("_", "-") + "-nats"
    
    aws ecs update-service `
        --cluster $cluster `
        --service $serviceName `
        --task-definition $serviceName `
        --force-new-deployment `
        --region $region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $serviceName" -ForegroundColor Green
        $servicesUpdated++
    }
}

Write-Host "  Updated $servicesUpdated services`n"

Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Dockerfiles: $dockerfilesUpdated updated"
Write-Host "Images: $rebuilt rebuilt and pushed"
Write-Host "Task Definitions: $tasksUpdated updated with health checks"
Write-Host "Services: $servicesUpdated redeployed"

Write-Host "`nMonitor with: pwsh -File scripts\monitor-nats-services.ps1"

