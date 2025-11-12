# Timer Service Initialization Feature
# This feature initializes the timer service to prevent session traps

function Initialize-TimerService {
    Write-Host ""
    Write-Host "[TIMER] Initializing Timer Service..." -ForegroundColor Cyan
    Write-Host "PROTECTIVE RATIONALE: Timers are the sessions' ONLY defense" -ForegroundColor Gray
    Write-Host "against IDE and local/remote systems that attempt to trap execution" -ForegroundColor Gray

    # STEP 1: Cleanup orphaned timers BEFORE starting new service (MANDATORY)
    Write-Host "[TIMER] Cleaning up orphaned timer services..." -ForegroundColor Yellow
    $cleanupScript = "Global-Scripts\cleanup-orphaned-timers-auto.ps1"
    if (Test-Path $cleanupScript) {
        try {
            $cleanupResult = & pwsh -ExecutionPolicy Bypass -File $cleanupScript -AutoClean 2>&1
            Write-Host "[TIMER] Cleanup completed" -ForegroundColor Green
            if ($cleanupResult -match "CLEANUPS PERFORMED") {
                Write-Host "[TIMER] Orphaned timers were cleaned up" -ForegroundColor Yellow
            } else {
                Write-Host "[TIMER] No orphaned timers found" -ForegroundColor Green
            }
        } catch {
            Write-Host "[WARNING] Timer cleanup failed: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "         Continuing with timer service initialization..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARNING] Timer cleanup script not found: $cleanupScript" -ForegroundColor Yellow
        Write-Host "         Timer service will start without cleanup (may cause issues)" -ForegroundColor Yellow
    }

    # STEP 2: Start timer service
    # Timer service runs asynchronously to prevent command trapping
    # Default: 10-minute timer that prompts check-ins
    $timerScript = "Global-Scripts\global-command-timer.ps1"
    if (Test-Path $timerScript) {
        Write-Host "[OK] Timer service script available: $timerScript" -ForegroundColor Green
        
        # Create timer initialization script that runs in background
        $timerInitScript = @'
# Timer Service Background Process
# This runs SILENTLY in background - NO console output
$timerInterval = 600  # 10 minutes default
$sessionMarker = ".cursor/timer-service.running"
$logFile = ".cursor/timer-service.log"

# Create marker file to indicate timer service is active
New-Item -ItemType Directory -Force -Path ".cursor" | Out-Null
$null = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $sessionMarker -Encoding UTF8

# Timer service loop (runs until session ends) - SILENT
while ($true) {
    Start-Sleep -Seconds $timerInterval
    
    # Log to file, NOT console
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - Timer check-in - Session active" | Add-Content -Path $logFile
    
    # Update marker to show timer is still active
    $null = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $sessionMarker -Encoding UTF8
}
'@
        
        # Start timer service in background job
        try {
            $timerJob = Start-Job -ScriptBlock ([scriptblock]::Create($timerInitScript)) -Name "CursorTimerService"
            if ($timerJob) {
                Write-Host "[OK] Timer service started (background job)" -ForegroundColor Green
                Write-Host "     Timer interval: 10 minutes (600 seconds)" -ForegroundColor Gray
                Write-Host "     Purpose: Prevents session traps and IDE stalls" -ForegroundColor Gray
                Write-Host "     Status: Running asynchronously" -ForegroundColor Gray
            } else {
                Write-Host "[WARNING] Timer service failed to start" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[WARNING] Timer service unavailable: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "          Session will run without timer protection" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARNING] Timer service script not found: $timerScript" -ForegroundColor Yellow
        Write-Host "          Timer protection will not be available" -ForegroundColor Yellow
    }

    Write-Host "================================================================" -ForegroundColor Cyan
}

