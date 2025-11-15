# Monitor NATS ECS Services
# Checks status of all 22 services and reports running/desired counts

param(
    [string]$Cluster = "gaming-system-cluster",
    [string]$Region = "us-east-1",
    [int]$IntervalSeconds = 30,
    [int]$MaxWaitMinutes = 30
)

$services = @(
    "ai-integration-nats", "model-management-nats", "state-manager-nats", "quest-system-nats",
    "npc-behavior-nats", "world-state-nats", "orchestration-nats", "router-nats",
    "event-bus-nats", "time-manager-nats", "weather-manager-nats", "auth-nats",
    "settings-nats", "payment-nats", "performance-mode-nats", "capability-registry-nats",
    "ai-router-nats", "knowledge-base-nats", "language-system-nats",
    "environmental-narrative-nats", "story-teller-nats", "body-broker-integration-nats"
)

$startTime = Get-Date
$maxWaitTime = $startTime.AddMinutes($MaxWaitMinutes)

Write-Host "=== Monitoring NATS Services ===" -ForegroundColor Cyan
Write-Host "Cluster: $Cluster"
Write-Host "Services: 22"
Write-Host "Target: 44/44 tasks running (2 per service)"
Write-Host "Max wait: $MaxWaitMinutes minutes`n"

while ((Get-Date) -lt $maxWaitTime) {
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Checking status (${elapsed}m elapsed)..." -ForegroundColor Cyan
    
    $totalRunning = 0
    $totalDesired = 0
    $operational = 0
    $provisioning = 0
    $failing = 0
    
    foreach ($service in $services) {
        $result = aws ecs describe-services `
            --cluster $Cluster `
            --services $service `
            --region $Region `
            --query 'services[0].[serviceName,runningCount,desiredCount,status]' `
            --output json 2>&1 | ConvertFrom-Json
        
        if ($result) {
            $serviceName = $result[0]
            $running = $result[1]
            $desired = $result[2]
            $status = $result[3]
            
            $totalRunning += $running
            $totalDesired += $desired
            
            if ($running -eq $desired -and $running -gt 0) {
                $operational++
                $indicator = "✅"
            } elseif ($running -lt $desired) {
                $provisioning++
                $indicator = "⏳"
            } else {
                $failing++
                $indicator = "❌"
            }
            
            Write-Host "  $indicator $serviceName`: $running/$desired" -ForegroundColor $(if ($running -eq $desired) { "Green" } elseif ($running -gt 0) { "Yellow" } else { "Red" })
        }
    }
    
    Write-Host "`n  Total: $totalRunning/$totalDesired tasks running" -ForegroundColor $(if ($totalRunning -eq $totalDesired) { "Green" } else { "Yellow" })
    Write-Host "  Operational: $operational/22 services" -ForegroundColor Green
    Write-Host "  Provisioning: $provisioning/22 services" -ForegroundColor Yellow
    Write-Host "  Failing: $failing/22 services" -ForegroundColor $(if ($failing -gt 0) { "Red" } else { "Green" })
    
    if ($totalRunning -eq $totalDesired -and $totalDesired -eq 44) {
        Write-Host "`n🎉 SUCCESS! All 44/44 tasks running!" -ForegroundColor Green
        Write-Host "All 22 services are fully operational.`n"
        exit 0
    }
    
    Write-Host "`nWaiting ${IntervalSeconds}s before next check...`n"
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Host "`n⚠️ Maximum wait time reached. Some services may still be provisioning." -ForegroundColor Yellow
Write-Host "Current status: $totalRunning/$totalDesired tasks running"
exit 1

