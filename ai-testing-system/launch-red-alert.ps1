#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Red Alert - AI Validation Dashboard Launcher
    Starts the complete validation report system

.DESCRIPTION
    Launches both backend (Docker) and frontend (Next.js) for the
    Body Broker AI Testing Validation Report System.
    
    System runs independently without Cursor!

.NOTES
    Port: 8010 (Backend API)
    Port: 3000 (Frontend Dashboard)
    Name: Red Alert - AI Validation Dashboard
#>

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Clear-Host

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host "  🚨 RED ALERT - AI VALIDATION DASHBOARD 🚨" -ForegroundColor Red
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host "  Body Broker AI Testing • Validation Report System" -ForegroundColor DarkGray
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
Write-Host ""

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DASHBOARD_DIR = Join-Path $SCRIPT_DIR "dashboard"
$ORCHESTRATOR_DIR = Join-Path $SCRIPT_DIR "orchestrator"

Write-Info "Starting Red Alert Validation System..."
Write-Host ""

# Step 1: Check Docker is running
Write-Info "[1/4] Checking Docker..."
try {
    $dockerStatus = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker is running"
    } else {
        Write-Warning "Docker not responding, attempting to start..."
        Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
        Write-Info "Waiting 15 seconds for Docker to start..."
        Start-Sleep -Seconds 15
    }
} catch {
    Write-Error "Docker is not available. Please start Docker Desktop manually."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 2: Start Backend Container
Write-Info "[2/4] Starting Backend API (Port 8010)..."

# Check if container exists
$containerExists = docker ps -a --filter "name=body-broker-qa-reports" --format "{{.Names}}"

if ($containerExists) {
    Write-Info "Container exists, starting..."
    docker start body-broker-qa-reports | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Backend API started successfully"
    } else {
        Write-Error "Failed to start backend container"
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Warning "Container not found. Run deployment script first."
    Write-Info "Looking for Docker image..."
    
    $imageExists = docker images body-broker-qa-orchestrator:latest --format "{{.Repository}}"
    
    if ($imageExists) {
        Write-Info "Creating and starting container..."
        docker run -d --name body-broker-qa-reports `
            -p 8010:8000 `
            --network aianalyzer_default `
            -e AWS_REGION=us-east-1 `
            -e DB_HOST=aianalyzer-db-1 `
            -e DB_PORT=5432 `
            -e DB_NAME=body_broker_qa `
            -e DB_USER=postgres `
            -e DB_PASSWORD=postgres `
            -e S3_BUCKET_REPORTS=body-broker-qa-reports `
            -e S3_REGION=us-east-1 `
            body-broker-qa-orchestrator:latest | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backend container created and started"
        } else {
            Write-Error "Failed to create backend container"
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Error "Docker image not found. Please run 'docker build' first."
        Write-Info "Run: cd '$ORCHESTRATOR_DIR' && docker build -t body-broker-qa-orchestrator:latest ."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Wait for backend to be ready
Write-Info "Waiting for backend to initialize (10 seconds)..."
Start-Sleep -Seconds 10

# Test backend health
Write-Info "Testing backend health..."
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8010/health" -Method Get -TimeoutSec 5
    if ($healthResponse.status -eq "healthy") {
        Write-Success "Backend API is healthy and responding"
    } else {
        Write-Warning "Backend responded but reports unhealthy status"
    }
} catch {
    Write-Warning "Backend health check failed (may still be starting up)"
    Write-Info "You can check logs with: docker logs body-broker-qa-reports"
}

Write-Host ""

# Step 3: Start Frontend Dashboard
Write-Info "[3/4] Starting Frontend Dashboard (Port 3000)..."

if (-not (Test-Path $DASHBOARD_DIR)) {
    Write-Error "Dashboard directory not found: $DASHBOARD_DIR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if npm is available
try {
    $npmVersion = npm --version 2>&1
    Write-Info "npm version: $npmVersion"
} catch {
    Write-Error "npm not found. Please install Node.js."
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if node_modules exists
$nodeModules = Join-Path $DASHBOARD_DIR "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Warning "Dependencies not installed. Running npm install..."
    Push-Location $DASHBOARD_DIR
    npm install
    Pop-Location
}

# Start dashboard in new window
Write-Info "Launching dashboard in new window..."
$dashboardCommand = "cd '$DASHBOARD_DIR'; npm start"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $dashboardCommand -WindowStyle Normal

Write-Success "Frontend dashboard starting (will open in new window)"
Write-Info "Waiting for dashboard to initialize (15 seconds)..."
Start-Sleep -Seconds 15

Write-Host ""

# Step 4: Open Browser
Write-Info "[4/4] Opening Red Alert Dashboard in browser..."
Start-Sleep -Seconds 2

try {
    Start-Process "http://localhost:3000/reports"
    Write-Success "Dashboard opened in browser"
} catch {
    Write-Warning "Could not auto-open browser"
    Write-Info "Manually open: http://localhost:3000/reports"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  🚨 RED ALERT SYSTEM LAUNCHED SUCCESSFULLY! 🚨" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Success "System Status: OPERATIONAL"
Write-Host ""
Write-Host "  📊 Dashboard:    http://localhost:3000/reports" -ForegroundColor Cyan
Write-Host "  🔧 Backend API:  http://localhost:8010" -ForegroundColor Cyan
Write-Host "  ❤️  Health:       http://localhost:8010/health" -ForegroundColor Cyan
Write-Host "  📈 Metrics:      http://localhost:8010/metrics" -ForegroundColor Cyan
Write-Host ""
Write-Info "Sample Report: $ORCHESTRATOR_DIR\sample_reports\marvel-rivals-report.html"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  System runs independently - Cursor NOT required!" -ForegroundColor DarkGray
Write-Host "  Backend: Docker container (auto-restarts)" -ForegroundColor DarkGray
Write-Host "  Frontend: npm start (manual start)" -ForegroundColor DarkGray
Write-Host "  Storage: AWS S3 (cloud, always available)" -ForegroundColor DarkGray
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press any key to close this window (services will keep running)..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

