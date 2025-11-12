# Resource Management System Feature
# This feature initializes resource management tools and displays health scores

function Initialize-ResourceManagement {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "[MEMORY] AI SESSION RESOURCE MANAGEMENT" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan

    # Initialize session tracking
    $sessionStartFile = ".cursor/session-start.txt"
    New-Item -ItemType Directory -Path ".cursor" -Force -ErrorAction SilentlyContinue | Out-Null
    Set-Content -Path $sessionStartFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

    # Check if resource management tools exist
    $resourceTools = @{
        "monitor-resources.ps1" = "Global-Scripts/monitor-resources.ps1"
        "resource-cleanup.ps1" = "Global-Scripts/resource-cleanup.ps1"
        "emergency-flush.ps1" = "Global-Scripts/emergency-flush.ps1"
        "extract-facts.py" = "Global-Scripts/extract-facts.py"
    }

    $allToolsAvailable = $true
    foreach ($tool in $resourceTools.GetEnumerator()) {
        if (-not (Test-Path $tool.Value)) {
            $allToolsAvailable = $false
            break
        }
    }

    if ($allToolsAvailable) {
        Write-Host "[OK] Resource Management Tools: Available" -ForegroundColor Green
        Write-Host ""
        
        # Run initial health check
        try {
            $healthResult = & ".\Global-Scripts\monitor-resources.ps1" -JSON 2>&1 | ConvertFrom-Json
            $healthScore = $healthResult.healthScore
            
            $healthStatus = "EXCELLENT"
            $healthColor = "Green"
            if ($healthScore -lt 90) { $healthStatus = "GOOD"; $healthColor = "Cyan" }
            if ($healthScore -lt 75) { $healthStatus = "FAIR"; $healthColor = "Yellow" }
            if ($healthScore -lt 60) { $healthStatus = "WARNING"; $healthColor = "DarkYellow" }
            if ($healthScore -lt 40) { $healthStatus = "CRITICAL"; $healthColor = "Red" }
            
            Write-Host "   Session Health Score: $healthScore/100 - $healthStatus" -ForegroundColor $healthColor
            
            if ($healthScore -lt 60) {
                Write-Host ""
                Write-Host "   [WARNING] Session health below optimal!" -ForegroundColor Yellow
                Write-Host "   Recommend running: .\Global-Scripts\resource-cleanup.ps1" -ForegroundColor White
            }
            
            if ($healthScore -lt 40) {
                Write-Host ""
                Write-Host "   [CRITICAL] Session health critical!" -ForegroundColor Red
                Write-Host "   IMMEDIATELY run: .\Global-Scripts\emergency-flush.ps1" -ForegroundColor Red
            }
        } catch {
            Write-Host "[WARNING] Could not determine health score: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "   Available Commands:" -ForegroundColor White
        Write-Host "   - .\Global-Scripts\monitor-resources.ps1   - Check session health" -ForegroundColor Gray
        Write-Host "   - .\Global-Scripts\resource-cleanup.ps1    - Clean after milestones" -ForegroundColor Gray
        Write-Host "   - .\Global-Scripts\emergency-flush.ps1     - Emergency cleanup" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "   [GUIDE] Protocol: Global-Workflows\Aggressive-Resource-Management.md" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "   [TIP] BEST PRACTICE:" -ForegroundColor Yellow
        Write-Host "   - Run resource-cleanup.ps1 after EVERY 45-minute milestone" -ForegroundColor White
        Write-Host "   - Keep active context under 50 lines" -ForegroundColor White
        Write-Host "   - Use external memory (History/Reasoning/Facts)" -ForegroundColor White
        Write-Host "   - Emergency flush if health < 40" -ForegroundColor White
    } else {
        Write-Host "[WARNING] Some resource management tools are missing" -ForegroundColor Yellow
        Write-Host "   Full resource management features may not be available" -ForegroundColor Yellow
    }
    
    Write-Host "================================================================" -ForegroundColor Cyan
}

