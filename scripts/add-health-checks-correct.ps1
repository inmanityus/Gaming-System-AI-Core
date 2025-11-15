# Add Health Checks to NATS Services (Correct Implementation)
# Uses simple HTTP server in background thread

$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "time_manager", "weather_manager", "auth",
    "settings", "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "environmental_narrative",
    "story_teller", "body_broker_integration"
)

Write-Host "Adding health checks to services..." -ForegroundColor Cyan

$updated = 0

foreach ($service in $services) {
    $natsServer = "services/$service/nats_server.py"
    
    if (Test-Path $natsServer) {
        $content = Get-Content $natsServer -Raw
        
        # Check if already has health check
        if ($content -match "health_check_http") {
            continue
        }
        
        # Add import after other SDK imports
        $content = $content -replace "(from sdk import[^\n]+)", "`$1`nfrom sdk.health_check_http import start_health_check_server"
        
        # Add health server start after client.connect()
        $content = $content -replace "(await client\.connect\(\)[^\n]*)", "`$1`n    `n    # Start health check HTTP server`n    health_server = start_health_check_server(port=8080, nats_client=client)"
        
        Set-Content $natsServer -Value $content -NoNewline
        Write-Host "  ✅ $service" -ForegroundColor Green
        $updated++
    }
}

Write-Host "Updated $updated services"

