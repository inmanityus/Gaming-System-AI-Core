# Router Service Stop Script
# Gaming System AI Core - Multi-Tier Architecture

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $workspaceRoot ".cursor/logs"
$pidFile = Join-Path $logDir "router.pid"
$port = 8000

Write-Host "[ROUTER] Stopping Router Service..." -ForegroundColor Green

# Try to stop by PID file first
if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($pid) {
        try {
            $proc = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "[ROUTER] Stopping process (PID $pid)..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force
            Remove-Item $pidFile -Force
            Write-Host "[ROUTER] Stopped successfully" -ForegroundColor Green
            exit 0
        } catch {
            Write-Host "[WARN] Process $pid not found (may have already exited)" -ForegroundColor Yellow
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    }
}

# Fallback: stop by port
$existingConnection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($existingConnection) {
    $pid = $existingConnection.OwningProcess
    Write-Host "[ROUTER] Stopping process on port $port (PID $pid)..." -ForegroundColor Yellow
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    
    # Verify stopped
    $remaining = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "[ERROR] Failed to stop router on port $port" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "[ROUTER] Stopped successfully" -ForegroundColor Green
    }
} else {
    Write-Host "[ROUTER] No router service found on port $port" -ForegroundColor Gray
}

