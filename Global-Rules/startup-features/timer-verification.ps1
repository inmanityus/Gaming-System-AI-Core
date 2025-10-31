# Timer Verification Feature
# Verifies that timer service is running and accessible
# This feature runs AFTER timer-service.ps1 to ensure timer is active

function Initialize-TimerVerification {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "[TIMER-VERIFY] Verifying Timer Service Status..." -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    
    $timerVerified = $false
    $verificationMethod = ""
    
    # METHOD 1: Check for background job (primary method)
    Write-Host "[TIMER-VERIFY] Checking for background job..." -ForegroundColor Yellow
    try {
        $timerJob = Get-Job -Name "CursorTimerService" -ErrorAction SilentlyContinue
        if ($timerJob -and $timerJob.State -eq "Running") {
            Write-Host "[OK] Timer job found: RUNNING" -ForegroundColor Green
            Write-Host "     Job ID: $($timerJob.Id)" -ForegroundColor Gray
            Write-Host "     Job State: $($timerJob.State)" -ForegroundColor Gray
            $timerVerified = $true
            $verificationMethod = "Background Job"
        } else {
            Write-Host "[WARNING] Timer job not found or not running" -ForegroundColor Yellow
            if ($timerJob) {
                Write-Host "          Job State: $($timerJob.State)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "[WARNING] Could not check timer job: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # METHOD 2: Check for marker file (secondary verification)
    Write-Host "[TIMER-VERIFY] Checking for marker file..." -ForegroundColor Yellow
    $markerFile = ".cursor/timer-service.running"
    if (Test-Path $markerFile) {
        Write-Host "[OK] Timer marker file found" -ForegroundColor Green
        $markerTime = Get-Content $markerFile -ErrorAction SilentlyContinue
        if ($markerTime) {
            Write-Host "     Marker timestamp: $markerTime" -ForegroundColor Gray
            
            # Calculate age of marker
            try {
                $markerDate = [DateTime]::Parse($markerTime)
                $age = (Get-Date) - $markerDate
                $ageMinutes = [math]::Round($age.TotalMinutes, 1)
                
                if ($ageMinutes -lt 60) {
                    Write-Host "     Marker age: $ageMinutes minutes (VALID)" -ForegroundColor Green
                    $timerVerified = $true
                    if ($verificationMethod -eq "") {
                        $verificationMethod = "Marker File"
                    }
                } else {
                    Write-Host "     Marker age: $ageMinutes minutes (STALE)" -ForegroundColor Yellow
                    Write-Host "     Timer may have stopped or session changed" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "     Could not parse marker timestamp" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "[WARNING] Timer marker file not found: $markerFile" -ForegroundColor Yellow
    }
    
    # FINAL VERIFICATION RESULT
    Write-Host ""
    if ($timerVerified) {
        Write-Host "[SUCCESS] Timer service verified: ACTIVE" -ForegroundColor Green
        Write-Host "          Verification method: $verificationMethod" -ForegroundColor Gray
        Write-Host "          Timer protection: ENABLED" -ForegroundColor Gray
        
        # Set environment variable for other scripts to check
        $env:CURSOR_TIMER_VERIFIED = "true"
        $env:CURSOR_TIMER_METHOD = $verificationMethod
    } else {
        Write-Host "[CRITICAL] Timer service NOT verified - PROTECTION DISABLED" -ForegroundColor Red
        Write-Host "           Session may be vulnerable to traps and stalls" -ForegroundColor Red
        Write-Host "           Recommendation: Restart session or manually start timer" -ForegroundColor Yellow
        
        # Set environment variable indicating timer NOT verified
        $env:CURSOR_TIMER_VERIFIED = "false"
        $env:CURSOR_TIMER_METHOD = "none"
        
        # Optional: Ask user if they want to continue anyway
        Write-Host ""
        Write-Host "[ACTION] Timer verification failed but continuing startup..." -ForegroundColor Yellow
        Write-Host "         Session will proceed without timer protection" -ForegroundColor Yellow
    }
    
    Write-Host "================================================================" -ForegroundColor Cyan
}

