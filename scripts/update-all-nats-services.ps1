# Update All NATS ECS Services
# Forces new deployment of all 22 services with latest images

param(
    [string]$Cluster = "gaming-system-cluster",
    [string]$Region = "us-east-1",
    [int]$DesiredCount = 2
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

Write-Host "=== Updating All NATS ECS Services ===" -ForegroundColor Cyan
Write-Host "Cluster: $Cluster"
Write-Host "Region: $Region"
Write-Host "Desired Count: $DesiredCount"

$updated = 0
$failed = 0

foreach ($service in $services) {
    Write-Host "`nUpdating $service..." -ForegroundColor Yellow
    
    try {
        # Force new deployment
        $result = aws ecs update-service `
            --cluster $Cluster `
            --service $service `
            --desired-count $DesiredCount `
            --force-new-deployment `
            --region $Region `
            --output json 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ Failed: $result" -ForegroundColor Red
            $failed++
        } else {
            Write-Host "  ✅ Updated" -ForegroundColor Green
            $updated++
        }
    }
    catch {
        Write-Host "  ❌ Failed: $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Updated: $updated/22" -ForegroundColor $(if ($updated -eq 22) { "Green" } else { "Yellow" })
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($updated -eq 22) {
    Write-Host "`n✅ All services updated!" -ForegroundColor Green
    Write-Host "`nWaiting for tasks to provision (2-4 minutes per service)..."
    Write-Host "Monitor with: aws ecs describe-services --cluster $Cluster --services <service-name>"
} else {
    Write-Host "`n⚠️ Some services failed. Review errors above." -ForegroundColor Yellow
}

