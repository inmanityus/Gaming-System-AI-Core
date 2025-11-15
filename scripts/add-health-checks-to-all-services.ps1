# Add Health Check HTTP Endpoints to All NATS Services

$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "weather_manager", "auth", "settings",
    "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "environmental_narrative",
    "story_teller", "body_broker_integration"
)

Write-Host "=== Adding Health Checks to All Services ===" -ForegroundColor Cyan

$updated = 0

foreach ($service in $services) {
    $natsServerPath = "services/$service/nats_server.py"
    
    if (Test-Path $natsServerPath) {
        Write-Host "Updating $service..." -ForegroundColor Yellow
        
        # Read current content
        $content = Get-Content $natsServerPath -Raw
        
        # Check if health endpoint already added
        if ($content -match "health_endpoint") {
            Write-Host "  Already has health endpoint, skipping" -ForegroundColor Gray
            continue
        }
        
        # Add health endpoint import
        if ($content -match "from sdk import") {
            $content = $content -replace "(from sdk import[^\n]+)", "`$1`nfrom sdk.health_endpoint import run_health_check_server"
        }
        
        # Add health server start in main()
        if ($content -match "async def main") {
            # Find the client.connect() line and add health server start after
            $content = $content -replace "(await client\.connect\(\))", "`$1`n    `n    # Start health check server`n    health_server = await run_health_check_server(port=8080, nats_client=client)`n    logger.info('Health check endpoint available on port 8080')"
        }
        
        # Write back
        Set-Content $natsServerPath -Value $content -NoNewline
        
        Write-Host "  ✅ Updated" -ForegroundColor Green
        $updated++
    } else {
        Write-Host "  ⚠️ Not found: $natsServerPath" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Updated: $updated services" -ForegroundColor Green

Write-Host "`nNext steps:"
Write-Host "1. Rebuild all Docker images"
Write-Host "2. Update Dockerfiles to expose port 8080"
Write-Host "3. Update ECS task definitions with health checks"
Write-Host "4. Deploy updated services"

