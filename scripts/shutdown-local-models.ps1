# Shutdown Local AI Models
# Stops all local model services to free up resources

$ErrorActionPreference = "Stop"

Write-Host "[SHUTDOWN] Stopping Local AI Model Services..." -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Checking for running model services..." -ForegroundColor White

$stopped = 0
$errors = 0

# Stop Ollama (local LLM service)
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping Ollama..." -ForegroundColor White
try {
    $ollama = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($ollama) {
        Stop-Process -Name "ollama" -Force -ErrorAction Stop
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Ollama stopped" -ForegroundColor Green
        $stopped++
    }
    else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚪ Ollama not running" -ForegroundColor Gray
    }
}
catch {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ Could not stop Ollama: $_" -ForegroundColor Yellow
    $errors++
}

# Stop any Python services running model inference
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping Python model services..." -ForegroundColor White
try {
    $pythonServices = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*model*" -or 
        $_.CommandLine -like "*llm*" -or
        $_.CommandLine -like "*inference*"
    }
    
    if ($pythonServices) {
        $pythonServices | ForEach-Object {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping PID $($_.Id)..." -ForegroundColor White
            Stop-Process -Id $_.Id -Force -ErrorAction Stop
            $stopped++
        }
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Python model services stopped" -ForegroundColor Green
    }
    else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚪ No Python model services running" -ForegroundColor Gray
    }
}
catch {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ Could not stop Python services: $_" -ForegroundColor Yellow
    $errors++
}

# Stop any Docker containers running models
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping Docker model containers..." -ForegroundColor White
try {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $modelContainers = docker ps -a --filter "name=model" --filter "name=llm" --filter "name=ollama" --format "{{.ID}}"
        if ($modelContainers) {
            $modelContainers | ForEach-Object {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping container $_..." -ForegroundColor White
                docker stop $_ 2>&1 | Out-Null
                $stopped++
            }
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Docker model containers stopped" -ForegroundColor Green
        }
        else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚪ No Docker model containers running" -ForegroundColor Gray
        }
    }
}
catch {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ Could not stop Docker containers: $_" -ForegroundColor Yellow
    $errors++
}

# Display summary
Write-Host ""
Write-Host "[SHUTDOWN SUMMARY]" -ForegroundColor Cyan
Write-Host "  Services stopped: $stopped" -ForegroundColor $(if ($stopped -gt 0) { "Green" } else { "Gray" })
Write-Host "  Errors: $errors" -ForegroundColor $(if ($errors -gt 0) { "Yellow" } else { "Green" })

if ($errors -eq 0) {
    Write-Host "[RESULT] ✅ Local models shut down successfully" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "[RESULT] ⚠️ Some services may still be running - check manually" -ForegroundColor Yellow
    exit 1
}



