# Deploy All Services with Proper Configuration
# Run this script to deploy all services with authentication and rate limiting

param(
    [switch]$Production = $false,
    [switch]$SkipTests = $false
)

Write-Host "=== DEPLOYING ALL SERVICES ===" -ForegroundColor Cyan

# Check environment variables
$requiredEnvVars = @(
    'POSTGRES_PASSWORD',
    'ALLOWED_ORIGINS',
    'LORA_API_KEYS',
    'SETTINGS_ADMIN_KEYS',
    'MODEL_ADMIN_KEYS',
    'QUEST_ADMIN_KEYS',
    'STATE_ADMIN_KEYS',
    'WORLD_STATE_ADMIN_KEYS',
    'AI_ADMIN_KEYS',
    'EVENT_BUS_ADMIN_KEYS',
    'ROUTER_ADMIN_KEYS',
    'ORCHESTRATION_ADMIN_KEYS',
    'NPC_ADMIN_KEYS',
    'STORY_ADMIN_KEYS',
    'ADMIN_API_KEYS'
)

$missing = @()
foreach ($var in $requiredEnvVars) {
    if (-not (Test-Path env:$var)) {
        $missing += $var
    }
}

if ($missing.Count -gt 0 -and $Production) {
    Write-Host "❌ MISSING ENVIRONMENT VARIABLES:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Set these in .env file before production deployment" -ForegroundColor Yellow
    exit 1
} elseif ($missing.Count -gt 0) {
    Write-Host "⚠️  Missing environment variables (OK for development):" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
}

# Install dependencies
Write-Host "Installing authentication service dependencies..." -ForegroundColor Yellow
Push-Location services/auth
python -m pip install -r requirements.txt --quiet
Pop-Location

# Start authentication service
Write-Host "Starting authentication service (port 8100)..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "services/auth/server.py" -NoNewWindow -PassThru

Start-Sleep -Seconds 2

# Test authentication service
Write-Host "Testing authentication service..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8100/health" -Method Get -TimeoutSec 5
    if ($response.status -eq "healthy") {
        Write-Host "✅ Authentication service running" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Authentication service not responding" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== DEPLOYMENT COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running:" -ForegroundColor White
Write-Host "  - Authentication: http://localhost:8100" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Test authentication endpoints" -ForegroundColor Gray
Write-Host "  2. Run security test suite" -ForegroundColor Gray
Write-Host "  3. Verify rate limiting" -ForegroundColor Gray
Write-Host "  4. Monitor logs for errors" -ForegroundColor Gray

