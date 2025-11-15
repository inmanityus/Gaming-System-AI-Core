# Register All 22 NATS Services with Correct Image Paths

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

Write-Host "=== Registering All 22 NATS Services ===" -ForegroundColor Cyan

$registered = 0
$failed = 0

foreach ($serviceName in $services) {
    Write-Host "`nProcessing $serviceName..." -ForegroundColor Yellow
    
    $imageUri = "${accountId}.dkr.ecr.${region}.amazonaws.com/bodybroker-services/${serviceName}:latest"
    
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
        "command": ["CMD-SHELL", "ps aux | grep -q '[p]ython.*nats_server.py' || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
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
            
            # Update service
            aws ecs update-service --cluster $cluster --service $serviceName --task-definition $serviceName --force-new-deployment --region $region --output json | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Service updated" -ForegroundColor Green
                $registered++
            } else {
                Write-Host "  ❌ Service update failed" -ForegroundColor Red
                $failed++
            }
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
Write-Host "Registered: $registered/22" -ForegroundColor $(if ($registered -eq 22) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($registered -eq 22) {
    Write-Host "`n✅ All services registered and updated!" -ForegroundColor Green
    Write-Host "`nWaiting for tasks to provision (2-4 minutes per service)..."
    Write-Host "Monitor with: pwsh -File scripts\monitor-nats-services.ps1"
} else {
    Write-Host "`n⚠️ Some services failed. Review errors above." -ForegroundColor Yellow
}

