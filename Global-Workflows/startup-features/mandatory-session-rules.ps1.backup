# Mandatory Session Rules Enforcement Feature
# Enforces critical session rules: Timer Service and Work Visibility

function Initialize-MandatorySessionRules {
    Write-Host ""
    Write-Host "[RULES] Loading Mandatory Session Rules..." -ForegroundColor Cyan
    
    # Load mandatory rules document
    $rulesFile = "Global-Workflows\mandatory-session-rules.md"
    if (Test-Path $rulesFile) {
        Write-Host "[OK] Mandatory session rules document found" -ForegroundColor Green
        
        # Display critical rules
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host "🚨 MANDATORY SESSION RULES - ACTIVE" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "RULE 1: TIMER SERVICE - MANDATORY CONTINUOUS OPERATION" -ForegroundColor Cyan
        Write-Host "  • Timer Service MUST run continuously throughout session" -ForegroundColor White
        Write-Host "  • Timer Service cleanup runs BEFORE starting new service" -ForegroundColor White
        Write-Host "  • Timer Service auto-renews at natural breakpoints" -ForegroundColor White
        Write-Host "  • No orphaned timer processes allowed" -ForegroundColor White
        Write-Host ""
        
        Write-Host "RULE 2: WORK VISIBILITY - MANDATORY SESSION WINDOW DISPLAY" -ForegroundColor Cyan
        Write-Host "  • ALWAYS show work progress in session window" -ForegroundColor White
        Write-Host "  • Display current directory, startup status, command progress" -ForegroundColor White
        Write-Host "  • Show service check results, timer cleanup results" -ForegroundColor White
        Write-Host "  • No silent operations allowed" -ForegroundColor White
        Write-Host ""
        
        Write-Host "ENFORCEMENT: These rules are MANDATORY - No Exceptions" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host ""
        
        # Set environment variables for rule enforcement
        $env:CURSOR_TIMER_SERVICE_MANDATORY = "true"
        $env:CURSOR_WORK_VISIBILITY_MANDATORY = "true"
        $env:CURSOR_MANDATORY_RULES_LOADED = "true"
        
        Write-Host "[OK] Mandatory session rules loaded and active" -ForegroundColor Green
        Write-Host "     Timer Service: MANDATORY" -ForegroundColor Yellow
        Write-Host "     Work Visibility: MANDATORY" -ForegroundColor Yellow
    } else {
        Write-Host "[WARNING] Mandatory session rules document not found: $rulesFile" -ForegroundColor Yellow
        Write-Host "          Rules will still be enforced via command files" -ForegroundColor Yellow
        
        # Set environment variables anyway
        $env:CURSOR_TIMER_SERVICE_MANDATORY = "true"
        $env:CURSOR_WORK_VISIBILITY_MANDATORY = "true"
    }
    
    Write-Host "================================================================" -ForegroundColor Cyan
}

