<#
.SYNOPSIS
    Startup feature for Rule Enforcement Service
    
.DESCRIPTION
    This feature ensures the RuleEnforcerService is installed and running
    when the startup script executes. It integrates with the global startup
    process to provide automatic rule enforcement across all projects.
#>

function Initialize-RuleEnforcement {
    param(
        [string]$ProjectRoot = $PWD.Path
    )
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🚨 RULE ENFORCEMENT SERVICE" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    $serviceName = "RuleEnforcerService"
    $installScript = Join-Path $ProjectRoot "Global-Scripts\rule-enforcement\Install-RuleEnforcerService.ps1"
    $serviceScript = Join-Path $ProjectRoot "Global-Scripts\rule-enforcement\RuleEnforcerService.ps1"

    # Check if service script exists
    if (-not (Test-Path $serviceScript)) {
        Write-Host "⚠️  Rule Enforcement Service script not found" -ForegroundColor Yellow
        Write-Host "   Expected: $serviceScript" -ForegroundColor Gray
        Write-Host "   Service will not be available" -ForegroundColor Gray
        Write-Host ""
        return
    }

    # Check if service is installed
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

    if (-not $service) {
        Write-Host "⚠️  Rule Enforcement Service not installed" -ForegroundColor Yellow
        Write-Host "   To install, run as Administrator:" -ForegroundColor Gray
        Write-Host "   pwsh -ExecutionPolicy Bypass -File `"$installScript`"" -ForegroundColor White
        Write-Host ""
        Write-Host "   The service will enforce ALL rules from /all-rules command" -ForegroundColor Gray
        Write-Host "   across all AI coding sessions automatically." -ForegroundColor Gray
        Write-Host ""
    } else {
        # Check service status
        $service.Refresh()
        
        if ($service.Status -ne "Running") {
            Write-Host "⚠️  Rule Enforcement Service is stopped" -ForegroundColor Yellow
            Write-Host "   Attempting to start..." -ForegroundColor Gray
            
            try {
                # Try to start service (may require admin)
                Start-Service -Name $serviceName -ErrorAction Stop
                Start-Sleep -Seconds 2
                $service.Refresh()
                
                if ($service.Status -eq "Running") {
                    Write-Host "✅ Service started successfully" -ForegroundColor Green
                } else {
                    Write-Host "⚠️  Service start may require Administrator privileges" -ForegroundColor Yellow
                    Write-Host "   Status: $($service.Status)" -ForegroundColor Gray
                }
            } catch {
                Write-Host "⚠️  Failed to start service: $_" -ForegroundColor Yellow
                Write-Host "   You may need to run as Administrator:" -ForegroundColor Gray
                Write-Host "   Start-Service -Name $serviceName" -ForegroundColor White
            }
        } else {
            Write-Host "✅ Rule Enforcement Service: Running" -ForegroundColor Green
        }
        
        # Check service health
        try {
            $status = Invoke-RestMethod -Uri "http://localhost:5757/status" -TimeoutSec 2 -ErrorAction Stop
            Write-Host "   Rules Loaded: $($status.rulesLoaded)" -ForegroundColor Gray
            Write-Host "   Active Sessions: $($status.activeSessions)" -ForegroundColor Gray
            Write-Host "   Open Violations: $($status.openViolations)" -ForegroundColor $(if ($status.openViolations -gt 0) { "Yellow" } else { "Gray" })
            Write-Host "   Last Rules Load: $($status.lastRulesLoad)" -ForegroundColor Gray
        } catch {
            Write-Host "   ⚠️  Service API not responding (may be starting)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "💡 RULE ENFORCEMENT FEATURES:" -ForegroundColor Cyan
        Write-Host "   • Enforces ALL rules from /all-rules command" -ForegroundColor Gray
        Write-Host "   • Monitors AI coding sessions in real-time" -ForegroundColor Gray
        Write-Host "   • Detects violations automatically" -ForegroundColor Gray
        Write-Host "   • Takes corrective actions (warnings, blocks, notifications)" -ForegroundColor Gray
        Write-Host "   • Integrates with git hooks for commit blocking" -ForegroundColor Gray
        Write-Host "   • Tracks peer coding, pairwise testing, milestones" -ForegroundColor Gray
        Write-Host ""
        Write-Host "📖 Documentation: Global-Scripts/rule-enforcement/README.md" -ForegroundColor White
        Write-Host ""
    }

    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

