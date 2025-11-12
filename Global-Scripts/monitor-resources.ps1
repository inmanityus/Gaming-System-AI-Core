Write-Host "📊 Monitoring Windows session health..." -ForegroundColor Green

# Calculate health score
$healthScore = 100

# Check context size (simulate)
$contextSize = 25  # Simulated
if ($contextSize -gt 50) {
    $healthScore -= 20
    Write-Host "⚠️  Context size too large: $contextSize lines" -ForegroundColor Yellow
}

# Check memory usage
$memoryUsage = Get-Process | Measure-Object WorkingSet -Sum | Select-Object -ExpandProperty Sum
$memoryUsageMB = [math]::Round($memoryUsage / 1MB, 2)
if ($memoryUsageMB -gt 2000) {  # 2GB threshold
    $healthScore -= 15
    Write-Host "⚠️  Memory usage high: $memoryUsageMB MB" -ForegroundColor Yellow
}

# Check session duration
$sessionStart = Get-Date "2025-01-24 09:00:00"  # Simulated
$sessionDuration = (Get-Date) - $sessionStart
if ($sessionDuration.TotalHours -gt 10) {
    $healthScore -= 10
    Write-Host "⚠️  Session duration long: $($sessionDuration.TotalHours.ToString('F1')) hours" -ForegroundColor Yellow
}

# Display health score
$color = switch ($healthScore) {
    { $_ -ge 90 } { "Green" }
    { $_ -ge 75 } { "Yellow" }
    { $_ -ge 60 } { "Red" }
    default { "DarkRed" }
}

Write-Host "Health Score: $healthScore/100" -ForegroundColor $color
Write-Host "Context Size: $contextSize lines" -ForegroundColor Gray
Write-Host "Memory Usage: $memoryUsageMB MB" -ForegroundColor Gray
Write-Host "Session Duration: $($sessionDuration.TotalHours.ToString('F1')) hours" -ForegroundColor Gray

if ($healthScore -lt 60) {
    Write-Host "🚨 HEALTH SCORE CRITICAL - Run emergency cleanup!" -ForegroundColor Red
    exit 1
} else {
    exit 0
}
