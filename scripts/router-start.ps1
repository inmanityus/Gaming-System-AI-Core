# Router Service Startup Script
# Gaming System AI Core - Multi-Tier Architecture

param(
    [int]$Port = 8000,
    [string]$LogPath = ".cursor/logs/router.log"
)

Write-Host "[ROUTER] Starting Router Service..." -ForegroundColor Green

$workspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $workspaceRoot

# Create logs directory
$logDir = Split-Path -Parent $LogPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Check if port is already in use
$existingConnection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($existingConnection) {
    Write-Host "[WARN] Port $Port is already in use (PID $($existingConnection.OwningProcess))" -ForegroundColor Yellow
    Write-Host "[WARN] Stopping existing process..." -ForegroundColor Yellow
    Stop-Process -Id $existingConnection.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# Start router service
Write-Host "[ROUTER] Launching router on port $Port..."

$command = "cd `"$workspaceRoot`"; python -m uvicorn services.router.server:app --host 0.0.0.0 --port $Port 2>&1 | Tee-Object -FilePath `"$LogPath`" -Append"
$proc = Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoLogo", "-NoProfile", "-NoExit", "-Command", $command `
    -WindowStyle Normal `
    -PassThru

Start-Sleep -Milliseconds 500

if ($proc.HasExited) {
    $exit = $proc.ExitCode
    Write-Host "[ERROR] Router service exited immediately with code $exit" -ForegroundColor Red
    if (Test-Path $LogPath) {
        Write-Host "[LOG] Last 20 lines:" -ForegroundColor Yellow
        Get-Content -Path $LogPath -Tail 20
    }
    exit 1
}

Write-Host "[ROUTER] Started successfully (PID $($proc.Id))" -ForegroundColor Green
Write-Host "[ROUTER] Logs: $LogPath" -ForegroundColor Cyan
Write-Host "[ROUTER] Endpoint: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "[ROUTER] Health: http://localhost:$Port/health" -ForegroundColor Cyan

# Save PID to file for stop script
$pidFile = Join-Path $logDir "router.pid"
$proc.Id | Out-File -FilePath $pidFile -Encoding ASCII

Write-Host "[ROUTER] Process ID saved to $pidFile" -ForegroundColor Gray

