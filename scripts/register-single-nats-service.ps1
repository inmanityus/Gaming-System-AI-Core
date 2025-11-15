# Register a Single NATS Service Task Definition (for testing)

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName
)

$region = "us-east-1"
$accountId = "695353648052"
$cluster = "gaming-system-cluster"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

$imageUri = "${accountId}.dkr.ecr.${region}.amazonaws.com/bodybroker-services/${ServiceName}:latest"

Write-Host "Service: $ServiceName"
Write-Host "Image: $imageUri`n"

$taskDefJson = @"
{
  "family": "$ServiceName",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "taskRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "$ServiceName",
      "image": "$imageUri",
      "essential": true,
      "portMappings": [],
      "environment": [
        {"name": "NATS_URL", "value": "$natsUrl"},
        {"name": "SERVICE_NAME", "value": "$ServiceName"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/gaming-system-nats",
          "awslogs-region": "$region",
          "awslogs-stream-prefix": "$ServiceName"
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

Write-Host "Task Definition JSON:"
Write-Host $taskDefJson

Write-Host "`nRegistering task definition..."
$result = aws ecs register-task-definition --cli-input-json file://$($tempFile.FullName) --region $region 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Task definition registered" -ForegroundColor Green
    
    Write-Host "`nUpdating service..."
    aws ecs update-service --cluster $cluster --service $ServiceName --task-definition $ServiceName --force-new-deployment --region $region --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Service updated" -ForegroundColor Green
    } else {
        Write-Host "❌ Service update failed" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Task definition registration failed:" -ForegroundColor Red
    Write-Host $result
}

Remove-Item $tempFile.FullName -ErrorAction SilentlyContinue

