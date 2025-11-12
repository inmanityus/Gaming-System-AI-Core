# Create Standard Dockerfiles for All Services
# Fixes import issues by setting PYTHONPATH=/app and copying all services/

param(
    [string[]]$Services = @(
        "state-manager:state_manager",
        "world-state:world_state",
        "language-system:language_system:language_system.api.server",
        "settings:settings",
        "model-management:model_management",
        "quest-system:quest_system",
        "payment:payment",
        "performance-mode:performance_mode",
        "ai-integration:ai_integration",
        "router:router",
        "orchestration:orchestration",
        "environmental-narrative:environmental_narrative"
    )
)

$ErrorActionPreference = "Stop"

foreach ($svcSpec in $Services) {
    $parts = $svcSpec -split ":"
    $ecsName = $parts[0]
    $dirName = $parts[1]
    $modulePath = if ($parts.Count -gt 2) { $parts[2] } else { $dirName + ".server" }
    
    $servicePath = "services\$dirName"
    
    if (-not (Test-Path $servicePath)) {
        Write-Host "[SKIP] $ecsName - directory not found" -ForegroundColor Yellow
        continue
    }
    
    $dockerfilePath = "$servicePath\Dockerfile"
    
    $dockerfile = @"
FROM python:3.11-slim

WORKDIR /app

# Copy all services to enable cross-service imports
COPY state_manager/ ./services/state_manager/
COPY shared/ ./services/shared/ 2>/dev/null || :
COPY proto/ ./services/proto/ 2>/dev/null || :

# Copy this service
COPY $dirName/ ./services/$dirName/

# Install requirements
COPY $dirName/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH so 'from services.X' imports work
ENV PYTHONPATH=/app

EXPOSE 8000

# Run service
WORKDIR /app/services
CMD ["python", "-m", "uvicorn", "$modulePath`:app", "--host", "0.0.0.0", "--port", "8000"]
"@
    
    $dockerfile | Out-File $dockerfilePath -Encoding utf8 -Force
    Write-Host "[OK] $ecsName" -ForegroundColor Green
}

Write-Host "`n[OK] All Dockerfiles updated" -ForegroundColor Green

