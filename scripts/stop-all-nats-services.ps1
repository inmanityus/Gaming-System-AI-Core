# Stop All NATS Services
# Stops all Python processes running nats_server.py

Write-Host "=== Stopping All NATS Services ===" -ForegroundColor Cyan

$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*nats_server.py*"
}

if ($processes) {
    $count = ($processes | Measure-Object).Count
    Write-Host "Found $count NATS service processes"
    
    $processes | ForEach-Object {
        Write-Host "Stopping PID $($_.Id)..."
        Stop-Process -Id $_.Id -Force
    }
    
    Write-Host "✅ All NATS services stopped" -ForegroundColor Green
}
else {
    Write-Host "No NATS services running" -ForegroundColor Yellow
}

