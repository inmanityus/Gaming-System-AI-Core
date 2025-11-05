# Emergency Shutdown - Stop ALL Local Models IMMEDIATELY
# Use this when dev computer is struggling

Write-Host "========================================" -ForegroundColor Red
Write-Host "[EMERGENCY] Shutting Down ALL Local Models" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Stop Ollama immediately
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping Ollama..." -ForegroundColor Yellow
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Killing PID $($_.Id)..." -ForegroundColor White
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Write-Host "[OK] Ollama stopped" -ForegroundColor Green

# Stop all Python processes that might be running models
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping Python model processes..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | ForEach-Object {
    $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    if ($cmd -like "*model*" -or $cmd -like "*llm*" -or $cmd -like "*inference*" -or $cmd -like "*ollama*") {
        Write-Host "  Killing Python PID $($_.Id)..." -ForegroundColor White
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "[OK] Python model processes stopped" -ForegroundColor Green

# Stop Docker containers
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping Docker model containers..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker ps -a --format "{{.ID}} {{.Names}}" | Where-Object { $_ -like "*model*" -or $_ -like "*llm*" -or $_ -like "*ollama*" } | ForEach-Object {
        $containerId = ($_ -split ' ')[0]
        Write-Host "  Stopping container $containerId..." -ForegroundColor White
        docker stop $containerId 2>&1 | Out-Null
    }
    Write-Host "[OK] Docker containers stopped" -ForegroundColor Green
}

# Show remaining processes
Write-Host ""
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Checking for remaining model processes..." -ForegroundColor Cyan
$remaining = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "[WARNING] Some Ollama processes may still be running:" -ForegroundColor Yellow
    $remaining | ForEach-Object { Write-Host "  PID: $($_.Id)" -ForegroundColor Yellow }
} else {
    Write-Host "[OK] No Ollama processes found" -ForegroundColor Green
}

# Show resource usage
Write-Host ""
Write-Host "[RESOURCE USAGE]" -ForegroundColor Cyan
$cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
$mem = (Get-Counter "\Memory\Available MBytes").CounterSamples[0].CookedValue
Write-Host "  CPU: $([math]::Round($cpu, 2))%" -ForegroundColor White
Write-Host "  Memory Available: $([math]::Round($mem, 2)) MB" -ForegroundColor White

Write-Host ""
Write-Host "[EMERGENCY SHUTDOWN] ✅ Complete" -ForegroundColor Green
Write-Host "[NEXT] Run '.\scripts\aws-deploy-full.ps1' to deploy to AWS" -ForegroundColor Cyan




