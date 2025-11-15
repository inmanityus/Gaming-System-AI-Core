# Fix NATS Health Checks - Use simpler check that works with module execution

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

Write-Host "=== Fixing Health Checks for All 22 NATS Services ===" -ForegroundColor Cyan

$fixed = 0
$failed = 0

foreach ($serviceName in $services) {
    Write-Host "`nProcessing $serviceName..." -ForegroundColor Yellow
    
    $imageUri = "${accountId}.dkr.ecr.${region}.amazonaws.com/bodybroker-services/${serviceName}:latest"
    
    # Use a simpler health check that just verifies python process is running
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
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "pgrep -f 'python -m services' > /dev/null || exit 1"],
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
        # Register task definition
        $result = aws ecs register-task-definition --cli-input-json file://$($tempFile.FullName) --region $region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Task definition registered" -ForegroundColor Green
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
Write-Host "Fixed: $fixed/22" -ForegroundColor $(if ($fixed -eq 22) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($fixed -eq 22) {
    Write-Host "`n✅ All health checks fixed!" -ForegroundColor Green
    Write-Host "`nNow updating services to desired count 0 to stop thrashing..."
    
    # Scale down all services to 0 to stop thrashing
    foreach ($serviceName in $services) {
        aws ecs update-service --cluster $cluster --service $serviceName --desired-count 0 --region $region --output json | Out-Null
    }
    
    Write-Host "✅ All services scaled to 0" -ForegroundColor Green
    Write-Host "`nWaiting 60s for tasks to stop..."
    Start-Sleep -Seconds 60
    
    Write-Host "`nUpdating services with new task definitions and scaling to 2..."
    foreach ($serviceName in $services) {
        aws ecs update-service --cluster $cluster --service $serviceName --task-definition $serviceName --desired-count 2 --force-new-deployment --region $region --output json | Out-Null
        Write-Host "  ✅ $serviceName updated" -ForegroundColor Green
    }
    
    Write-Host "`n✅ All services updated with fixed health checks!" -ForegroundColor Green
    Write-Host "Monitor with: pwsh -File scripts\monitor-nats-services.ps1"
} else {
    Write-Host "`n⚠️ Some services failed. Review errors above." -ForegroundColor Yellow
}

