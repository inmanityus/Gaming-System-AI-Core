# Start All NATS Services for Local Testing

param(
    [string]$NatsUrl = "nats://localhost:4222"
)

Write-Host "=== Starting All NATS Services ===" -ForegroundColor Cyan

# Set Python path
$projectRoot = (Get-Location).Path
$env:PYTHONPATH = "$projectRoot\sdk;$projectRoot\generated"
$env:NATS_URL = $NatsUrl

Write-Host "NATS URL: $NatsUrl"
Write-Host "Python Path: $env:PYTHONPATH"

$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "time_manager", "weather_manager", "auth",
    "settings", "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "language_system",
    "environmental_narrative", "story_teller", "body_broker_integration"
)

$started = 0
$failed = 0

foreach ($service in $services) {
    $servicePath = "services\$service\nats_server.py"
    
    if (Test-Path $servicePath) {
        Write-Host "Starting $service..." -ForegroundColor Yellow
        
        $process = Start-Process python -ArgumentList $servicePath -WindowStyle Hidden -PassThru
        Start-Sleep -Milliseconds 300
        
        if (-not $process.HasExited) {
            Write-Host "  ✅ PID: $($process.Id)" -ForegroundColor Green
            $started++
        } else {
            Write-Host "  ❌ Failed" -ForegroundColor Red
            $failed++
        }
    }
    else {
        Write-Host "  ⚠️ Not found: $servicePath" -ForegroundColor DarkYellow
        $failed++
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Started: $started/$($services.Count)" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Yellow" } else { "Green" })
Write-Host "`nTo stop: .\scripts\stop-all-nats-services.ps1"
