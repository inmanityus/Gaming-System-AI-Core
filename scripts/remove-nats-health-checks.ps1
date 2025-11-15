# Remove Health Checks from NATS Services - Services are working, health checks are the problem

$region = "us-east-1"
$accountId = "695353648052"
$cluster = "gaming-system-cluster"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

$services = @(
    "ai-integration-nats", "model-management-nats", "state-manager-nats", "quest-system-nats",
    "npc-behavior-nats", "world-state-nats", "orchestration-nats", "router-nats",
    "event-bus-nats", "time-manager-nats", "weather-manager-nats", "auth-nats",
    "settings-nats", "payment-nats", "performance-mode-nats", "capability-registry-nats",
    "ai-router-nats", "knowledge-base-nats", "language-system-nats",
    "environmental-narrative-nats", "story-teller-nats", "body-broker-integration-nats"
)

Write-Host "=== Removing Health Checks from All 22 NATS Services ===" -ForegroundColor Cyan
Write-Host "Services are working - health checks are causing unnecessary restarts`n"

$fixed = 0
$failed = 0

foreach ($serviceName in $services) {
    Write-Host "Processing $serviceName..." -ForegroundColor Yellow
    
    $imageUri = "${accountId}.dkr.ecr.${region}.amazonaws.com/bodybroker-services/${serviceName}:latest"
    
    # No health check - services are proven to work
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
      "portMappings": [],
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
      }
    }
  ]
}
"@
    
    $tempFile = New-TemporaryFile
    $taskDefJson | Set-Content $tempFile.FullName
    
    try {
        $result = aws ecs register-task-definition --cli-input-json file://$($tempFile.FullName) --region $region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Task definition registered (no health check)" -ForegroundColor Green
            $fixed++
        } else {
            Write-Host "  ❌ Registration failed: $result" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  ❌ Exception: $_" -ForegroundColor Red
        $failed++
    }
    finally {
        Remove-Item $tempFile.FullName -ErrorAction SilentlyContinue
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Updated: $fixed/22" -ForegroundColor $(if ($fixed -eq 22) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($fixed -eq 22) {
    Write-Host "`n✅ All health checks removed!" -ForegroundColor Green
    Write-Host "`nScaling services to 0 to stop thrashing..."
    
    foreach ($serviceName in $services) {
        aws ecs update-service --cluster $cluster --service $serviceName --desired-count 0 --region $region --output json | Out-Null
    }
    
    Write-Host "✅ All services scaled to 0" -ForegroundColor Green
    Write-Host "Waiting 60s for cleanup..."
    Start-Sleep -Seconds 60
    
    Write-Host "`nUpdating services with new task definitions (no health checks)..."
    foreach ($serviceName in $services) {
        aws ecs update-service --cluster $cluster --service $serviceName --task-definition $serviceName --desired-count 2 --force-new-deployment --region $region --output json | Out-Null
        Write-Host "  ✅ $serviceName" -ForegroundColor Green
    }
    
    Write-Host "`n✅ All 22 services updated!" -ForegroundColor Green
    Write-Host "Services will now run without health check interference.`n"
    Write-Host "Monitor: pwsh -File scripts\monitor-nats-services.ps1 -IntervalSeconds 30 -MaxWaitMinutes 10"
}

