# Documentation Placement Checking Feature
# This feature verifies documentation is properly organized

function Initialize-DocumentationPlacement {
    Write-Host ""
    Write-Host "Checking documentation placement..." -ForegroundColor Yellow
    if (Test-Path ".\Global-Scripts\check-documentation-placement.ps1") {
        $docCheckResult = & .\Global-Scripts\check-documentation-placement.ps1 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] All documentation properly placed" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Found misplaced documentation files" -ForegroundColor Yellow
            Write-Host "  Run: .\Global-Scripts\check-documentation-placement.ps1 -Fix" -ForegroundColor Gray
        }
    } else {
        Write-Host "[WARNING] Documentation check script not found" -ForegroundColor Yellow
    }
}

