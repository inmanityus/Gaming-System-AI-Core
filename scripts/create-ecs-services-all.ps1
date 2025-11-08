# Create ECS Services for All Deployed Images
# Systematically deploys all services to ECS with binary messaging support

param(
    [string]$Region = "us-east-1",
    [string]$Cluster = "gaming-system-cluster",
    [string]$SecurityGroup = "sg-00419f4094a7d2101",
    [string[]]$Subnets = @("subnet-0f353054b8e31561d", "subnet-036ef66c03b45b1da"),
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "=== CREATING ECS SERVICES FOR ALL IMAGES ===" -ForegroundColor Green
Write-Host ""

$accountId = aws sts get-caller-identity --query "Account" --output text

# Service configurations
$services = @(
    @{
        Name = "ai-integration"
        Family = "ai-integration"
        Port = 8001
        CPU = 512
        Memory = 1024
        NeedsBinaryMessaging = $true
    },
    @{
        Name = "capability-registry"
        Family = "capability-registry"
        Port = 8080
        CPU = 256
        Memory = 512
        NeedsBinaryMessaging = $false
    },
    @{
        Name = "event-bus"
        Family = "event-bus"
        Port = 8002
        CPU = 512
        Memory = 1024
        NeedsBinaryMessaging = $true
    },
    @{
        Name = "language-system"
        Family = "language-system"
        Port = 8003
        CPU = 512
        Memory = 1024
        NeedsBinaryMessaging = $true
    },
    @{
        Name = "model-management"
        Family = "model-management"
        Port = 8004
        CPU = 512
        Memory = 1024
        NeedsBinaryMessaging = $true
    },
    @{
        Name = "story-teller"
        Family = "story-teller"
        Port = 8005
        CPU = 512
        Memory = 1024
        NeedsBinaryMessaging = $true
    },
    @{
        Name = "storyteller"
        Family = "storyteller"
        Port = 8006
        CPU = 256
        Memory = 512
        NeedsBinaryMessaging = $false
    },
    @{
        Name = "ue-version-monitor"
        Family = "ue-version-monitor"
        Port = 8007
        CPU = 256
        Memory = 512
        NeedsBinaryMessaging = $false
    }
)

Write-Host "📊 Services to deploy: $($services.Count)" -ForegroundColor Cyan
Write-Host "  With binary messaging: $(($services | Where-Object { $_.NeedsBinaryMessaging }).Count)" -ForegroundColor White
Write-Host "  Without binary messaging: $(($services | Where-Object { -not $_.NeedsBinaryMessaging }).Count)" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - Would create services:" -ForegroundColor Yellow
    $services | ForEach-Object {
        $binary = if ($_.NeedsBinaryMessaging) { "[BINARY]" } else { "" }
        Write-Host "  - $($_.Name) (Port: $($_.Port)) $binary" -ForegroundColor Gray
    }
    exit 0
}

# Create shared task role for services with binary messaging
Write-Host "[1/3] Creating shared task role for binary messaging..." -ForegroundColor Yellow
$taskRoleArn = "arn:aws:iam::${accountId}:role/gamingSystemServicesTaskRole"
$roleExists = aws iam get-role --role-name gamingSystemServicesTaskRole 2>&1
if ($LASTEXITCODE -ne 0) {
    aws iam create-role `
        --role-name gamingSystemServicesTaskRole `
        --assume-role-policy-document file://.cursor/aws/ecs-task-assume-role-policy.json `
        --description "Shared task role for Gaming System ECS services" `
        --tags Key=Name,Value=gamingSystemServicesTaskRole Key=Project,Value=GamingSystemAICore | Out-Null
    
    # Attach binary messaging policy
    aws iam attach-role-policy `
        --role-name gamingSystemServicesTaskRole `
        --policy-arn arn:aws:iam::${accountId}:policy/GamingSystemDistributedMessaging | Out-Null
    
    Write-Host "  ✓ Created and configured gamingSystemServicesTaskRole" -ForegroundColor Green
} else {
    Write-Host "  ℹ gamingSystemServicesTaskRole already exists" -ForegroundColor Yellow
}
Write-Host ""

# Deploy each service
Write-Host "[2/3] Creating ECS services..." -ForegroundColor Yellow
$deployed = 0
$skipped = 0

foreach ($service in $services) {
    Write-Host "  Deploying $($service.Name)..." -ForegroundColor Cyan
    
    # Generate task definition
    $taskRole = if ($service.NeedsBinaryMessaging) { $taskRoleArn } else { $null }
    
    $envVars = @(
        @{name="SERVICE_NAME"; value=$service.Name}
    )
    
    if ($service.NeedsBinaryMessaging) {
        $envVars += @(
            @{name="WEATHER_EVENTS_TOPIC_ARN"; value="arn:aws:sns:us-east-1:${accountId}:gaming-system-weather-events"},
            @{name="AWS_REGION"; value=$Region}
        )
    }
    
    $taskDef = @{
        family = $service.Family
        networkMode = "awsvpc"
        requiresCompatibilities = @("FARGATE")
        cpu = [string]$service.CPU
        memory = [string]$service.Memory
        executionRoleArn = "arn:aws:iam::${accountId}:role/ecsTaskExecutionRole"
        containerDefinitions = @(
            @{
                name = $service.Name
                image = "${accountId}.dkr.ecr.${Region}.amazonaws.com/bodybroker-services:$($service.Name)-latest"
                portMappings = @(@{containerPort=$service.Port; protocol="tcp"})
                essential = $true
                environment = $envVars
                logConfiguration = @{
                    logDriver = "awslogs"
                    options = @{
                        "awslogs-group" = "/ecs/gaming-system/$($service.Name)"
                        "awslogs-region" = $Region
                        "awslogs-stream-prefix" = "ecs"
                        "awslogs-create-group" = "true"
                    }
                }
            }
        )
    }
    
    if ($taskRole) {
        $taskDef.taskRoleArn = $taskRole
    }
    
    # Save task definition
    $taskDefPath = ".cursor/aws/task-def-$($service.Name).json"
    $taskDef | ConvertTo-Json -Depth 10 | Out-File -FilePath $taskDefPath -Encoding UTF8
    
    # Register task definition
    $taskDefArn = aws ecs register-task-definition `
        --region $Region `
        --cli-input-json file://$taskDefPath `
        --query "taskDefinition.taskDefinitionArn" `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    ✗ Failed to register task definition: $taskDefArn" -ForegroundColor Red
        $skipped++
        continue
    }
    
    # Check if service already exists
    $serviceExists = aws ecs describe-services `
        --region $Region `
        --cluster $Cluster `
        --services $service.Name `
        --query "services[0].serviceName" `
        --output text 2>&1
    
    if ($serviceExists -eq $service.Name) {
        Write-Host "    ℹ Service exists, updating..." -ForegroundColor Yellow
        aws ecs update-service `
            --region $Region `
            --cluster $Cluster `
            --service $service.Name `
            --force-new-deployment | Out-Null
    } else {
        # Create ECS service
        aws ecs create-service `
            --region $Region `
            --cluster $Cluster `
            --service-name $service.Name `
            --task-definition $service.Family `
            --desired-count 1 `
            --launch-type FARGATE `
            --network-configuration "awsvpcConfiguration={subnets=[$($Subnets -join ',')],securityGroups=[$SecurityGroup],assignPublicIp=ENABLED}" `
            --tags key=Name,value=$service.Name key=Project,value=GamingSystemAICore | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $($service.Name) deployed" -ForegroundColor Green
        $deployed++
    } else {
        Write-Host "    ✗ Failed to create service" -ForegroundColor Red
        $skipped++
    }
}

Write-Host ""
Write-Host "[3/3] Deployment complete!" -ForegroundColor Yellow
Write-Host "  ✓ Deployed: $deployed" -ForegroundColor Green
Write-Host "  ✗ Skipped: $skipped" -ForegroundColor $(if ($skipped -gt 0) { "Red" } else { "Gray" })
Write-Host ""

Write-Host "⏳ Waiting 60 seconds for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

Write-Host ""
Write-Host "📊 FINAL STATUS:" -ForegroundColor Cyan
$serviceNames = $services | ForEach-Object { $_.Name }
aws ecs describe-services `
    --region $Region `
    --cluster $Cluster `
    --services $serviceNames `
    --query "services[].[serviceName,runningCount,desiredCount]" `
    --output table

Write-Host ""
Write-Host "✅ All services deployed! Check status above." -ForegroundColor Green
Write-Host ""
Write-Host "To monitor logs:" -ForegroundColor Cyan
Write-Host "  aws logs tail /ecs/gaming-system/<service-name> --region $Region --follow" -ForegroundColor Yellow

