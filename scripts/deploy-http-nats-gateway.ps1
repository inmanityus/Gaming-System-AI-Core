# Deploy HTTP→NATS Gateway to ECS

$region = "us-east-1"
$accountId = "695353648052"
$cluster = "gaming-system-cluster"
$serviceName = "http-nats-gateway"
$imageUri = "${accountId}.dkr.ecr.${region}.amazonaws.com/bodybroker-services/http-nats-gateway:latest"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

Write-Host "=== Deploying HTTP→NATS Gateway ===" -ForegroundColor Cyan

# Create task definition
$taskDefJson = @"
{
  "family": "$serviceName",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "taskRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "$serviceName",
      "image": "$imageUri",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NATS_URL", "value": "$natsUrl"},
        {"name": "PORT", "value": "8000"},
        {"name": "HOST", "value": "0.0.0.0"}
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
    Write-Host "Registering task definition..."
    $taskDefArn = aws ecs register-task-definition --cli-input-json file://$($tempFile.FullName) --region $region --query 'taskDefinition.taskDefinitionArn' --output text
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Task definition registered" -ForegroundColor Green
        
        # Get VPC configuration
        $vpcConfig = aws ecs describe-services --cluster $cluster --services ai-integration-nats --query 'services[0].networkConfiguration.awsvpcConfiguration' --output json | ConvertFrom-Json
        $subnets = ($vpcConfig.subnets -join ',')
        $securityGroup = $vpcConfig.securityGroups[0]
        
        Write-Host "Creating service with public load balancer..."
        
        # Create service  
        $result = aws ecs create-service `
            --cluster $cluster `
            --service-name $serviceName `
            --task-definition $serviceName `
            --desired-count 2 `
            --launch-type FARGATE `
            --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$securityGroup],assignPublicIp=ENABLED}" `
            --region $region `
            --output json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Service created!" -ForegroundColor Green
            Write-Host "`nGateway deploying... Monitor with:"
            Write-Host "  aws ecs describe-services --cluster $cluster --services $serviceName"
        } else {
            # Try update if already exists
            Write-Host "Service may exist, trying update..."
            aws ecs update-service `
                --cluster $cluster `
                --service $serviceName `
                --task-definition $serviceName `
                --desired-count 2 `
                --force-new-deployment `
                --region $region `
                --output json | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Service updated!" -ForegroundColor Green
            } else {
                Write-Host "❌ Failed to create/update service: $result" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "❌ Task definition registration failed" -ForegroundColor Red
    }
}
finally {
    Remove-Item $tempFile.FullName -ErrorAction SilentlyContinue
}

