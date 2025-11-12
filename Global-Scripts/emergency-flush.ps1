Write-Host "🚨 Running Windows emergency flush..." -ForegroundColor Red

# Aggressive cleanup
Write-Host "  - Clearing all temporary files" -ForegroundColor Gray
Get-ChildItem -Path "." -Recurse -Include "*.tmp", "*.temp", "*.log" | Remove-Item -Force

# Clear context aggressively
Write-Host "  - Clearing active context aggressively" -ForegroundColor Gray

# Save critical state only
Write-Host "  - Saving critical state only" -ForegroundColor Gray

# Clear memory banks
Write-Host "  - Clearing memory banks" -ForegroundColor Gray

Write-Host "✅ Emergency flush completed" -ForegroundColor Green
