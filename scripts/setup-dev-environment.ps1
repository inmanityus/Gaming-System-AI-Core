# Setup Development Environment for Body Broker

Write-Host "Setting up Body Broker development environment..." -ForegroundColor Cyan

# Check Python
Write-Host "`nChecking Python..."
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $version = python --version
    Write-Host "  ✅ $version"
} else {
    Write-Host "  ❌ Python not found" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "`nInstalling Python dependencies..."
pip install -r requirements-complete.txt

# Check Docker
Write-Host "`nChecking Docker..."
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "  ✅ Docker available"
} else {
    Write-Host "  ⚠️ Docker not found (optional)" -ForegroundColor Yellow
}

# Start Redis (if Docker available)
if ($docker) {
    Write-Host "`nStarting Redis..."
    docker run -d -p 6379:6379 --name body-broker-redis redis:latest
    Write-Host "  ✅ Redis started on port 6379"
}

# Check PostgreSQL
Write-Host "`nChecking PostgreSQL..."
try {
    $null = psql -h localhost -p 5443 -U postgres -d gaming_system_ai_core -c "SELECT 1" 2>&1
    Write-Host "  ✅ PostgreSQL accessible"
} catch {
    Write-Host "  ⚠️ PostgreSQL not accessible (will be needed for production)" -ForegroundColor Yellow
}

# Validate systems
Write-Host "`nValidating all systems..."
python examples\body_broker_complete_demo.py

Write-Host "`n" + ("="*60)
Write-Host "✅ DEVELOPMENT ENVIRONMENT READY" -ForegroundColor Green
Write-Host ("="*60)
Write-Host "`nNext: Provision GPU for adapter training"

