# Fix NATS Task Definitions with Correct Image References
# Re-registers all 22 task definitions with proper image paths

param(
    [string]$Region = "us-east-1",
    [string]$AccountId = "695353648052",
    [string]$Cluster = "gaming-system-cluster"
)

$ErrorActionPreference = "Continue"

$services = @(
    "ai-integration-nats", "model-management-nats", "state-manager-nats", "quest-system-nats",
    "npc-behavior-nats", "world-state-nats", "orchestration-nats", "router-nats",
    "event-bus-nats", "time-manager-nats", "weather-manager-nats", "auth-nats",
    "settings-nats", "payment-nats", "performance-mode-nats", "capability-registry-nats",
    "ai-router-nats", "knowledge-base-nats", "language-system-nats",
    "environmental-narrative-nats", "story-teller-nats", "body-broker-integration-nats"
)

$ecrRepo = "$AccountId.dkr.ecr.$Region.amazonaws.com/bodybroker-services"
$natsUrl = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

Write-Host "=== Fixing NATS Task Definitions ===" -ForegroundColor Cyan
Write-Host "Region: $Region"
Write-Host "Account: $AccountId"
Write-Host "ECR Repo: $ecrRepo`n"

$fixed = 0
$failed = 0

foreach ($service in $services) {
    Write-Host "Fixing $service..." -ForegroundColor Yellow
    
    # Build correct image path
    $imagePath = "$ecrRepo/$service:latest"
    
    # Create task definition JSON
    $taskDef = @{
        family = $service
        networkMode = "awsvpc"
        requiresCompatibilities = @("FARGATE")
        cpu = "256"
        memory = "512"
        taskRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
        executionRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
        containerDefinitions = @(
            @{
                name = $service
                image = $imagePath
                essential = $true
                portMappings = @()
                environment = @(
                    @{name = "NATS_URL"; value = $natsUrl},
                    @{name = "SERVICE_NAME"; value = $service}
                )
                logConfiguration = @{
                    logDriver = "awslogs"
                    options = @{
                        "awslogs-group" = "/ecs/gaming-system-nats"
                        "awslogs-region" = $Region
                        "awslogs-stream-prefix" = $service
                    }
                }
                healthCheck = @{
                    command = @("CMD-SHELL", "ps aux | grep -q '[p]ython.*nats_server.py' || exit 1")
                    interval = 30
                    timeout = 5
                    retries = 3
                    startPeriod = 10
                }
            }
        )
    }
    
    # Save to temp file
    $tempFile = [System.IO.Path]::GetTempFileName()
    $taskDef | ConvertTo-Json -Depth 10 | Set-Content $tempFile
    
    try {
        # Register task definition
        $result = aws ecs register-task-definition `
            --cli-input-json file://$tempFile `
            --region $Region `
            --query 'taskDefinition.taskDefinitionArn' `
            --output text 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Registered: $imagePath" -ForegroundColor Green
            $fixed++
            
            # Update service to use new task definition
            aws ecs update-service `
                --cluster $Cluster `
                --service $service `
                --task-definition $service `
                --force-new-deployment `
                --region $Region `
                --output json | Out-Null
            
            Write-Host "  ✅ Service updated" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Failed: $result" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  ❌ Exception: $_" -ForegroundColor Red
        $failed++
    }
    finally {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Fixed: $fixed/22" -ForegroundColor $(if ($fixed -eq 22) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($fixed -eq 22) {
    Write-Host "`n✅ All task definitions fixed!" -ForegroundColor Green
    Write-Host "`nServices are now deploying with correct images."
    Write-Host "Monitor with: pwsh -File scripts\monitor-nats-services.ps1"
} else {
    Write-Host "`n⚠️ Some task definitions failed. Review errors above." -ForegroundColor Yellow
}

