# Update Dockerfiles to expose port 8080 for health checks

$services = @(
    "ai_integration", "model_management", "state_manager", "quest_system",
    "npc_behavior", "world_state", "orchestration", "router",
    "event_bus", "time_manager", "weather_manager", "auth",
    "settings", "payment", "performance_mode", "capability-registry",
    "ai_router", "knowledge_base", "environmental_narrative",
    "story_teller", "body_broker_integration"
)

foreach ($service in $services) {
    $dockerfile = "services/$service/Dockerfile.nats"
    
    if (Test-Path $dockerfile) {
        $content = Get-Content $dockerfile -Raw
        
        # Add EXPOSE 8080 if not present
        if ($content -notmatch "EXPOSE 8080") {
            $content = $content -replace "(ENV NATS_URL=[^\n]+)", "`$1`nEXPOSE 8080"
            Set-Content $dockerfile -Value $content -NoNewline
        }
    }
}

Write-Host "Updated all Dockerfiles"

