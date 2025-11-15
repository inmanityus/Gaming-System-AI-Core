# Deploy Health Check to Single Service (Test)
# Tests health check on capability-registry before rolling out to all

$region = "us-east-1"
$accountId = "695353648052"
$cluster = "gaming-system-cluster"
$serviceName = "capability-registry-nats"
$imageUri = "${accountId}.dkr.ecr.${region}.amazonaws.com/bodybroker-services/${serviceName}:health-test"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

Write-Host "Testing health check on $serviceName..." -ForegroundColor Yellow

# Create task definition with health check
$taskDefJson = @"
{
  "family": "$serviceName-health-test",
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
          "awslogs-stream-prefix": "${serviceName}-health-test"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
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

# Register task definition
aws ecs register-task-definition --cli-input-json file://$($tempFile.FullName) --region $region | Out-Null
Remove-Item $tempFile.FullName

# Scale current service to 1 task temporarily
Write-Host "Scaling to 1 task temporarily..."
aws ecs update-service --cluster $cluster --service $serviceName --desired-count 1 --region $region | Out-Null

Start-Sleep -Seconds 30

# Update service to use health check task definition
Write-Host "Updating to health check task definition..."
aws ecs update-service --cluster $cluster --service $serviceName --task-definition "${serviceName}-health-test" --force-new-deployment --region $region | Out-Null

Write-Host "`nWaiting 2 minutes for health check test..."
Start-Sleep -Seconds 120

# Check result
$result = aws ecs describe-services --cluster $cluster --services $serviceName --query 'services[0].[runningCount,desiredCount]' --output json --region $region | ConvertFrom-Json

Write-Host "`nResult: $($result[0])/$($result[1]) tasks"

if ($result[0] -eq 1) {
    Write-Host "✅ Health check working! Service stable at 1/1" -ForegroundColor Green
    Write-Host "`nScaling back to 2..."
    aws ecs update-service --cluster $cluster --service $serviceName --desired-count 2 --region $region | Out-Null
    Write-Host "✅ Health check test PASSED - safe to roll out" -ForegroundColor Green
    $success = $true
} else {
    Write-Host "❌ Health check FAILED - service not running" -ForegroundColor Red
    Write-Host "Checking logs..."
    aws logs tail /ecs/gaming-system-nats --log-stream-name-prefix "${serviceName}-health-test" --since 5m --format short --region $region 2>&1 | Select-Object -Last 10
    $success = $false
}

return $success

