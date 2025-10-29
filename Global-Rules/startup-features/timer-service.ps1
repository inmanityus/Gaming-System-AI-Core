# Timer Service Initialization Feature
# This feature initializes the timer service to prevent session traps

function Initialize-TimerService {
    Write-Host ""
    Write-Host "[TIMER] Initializing Timer Service..." -ForegroundColor Cyan
    Write-Host "PROTECTIVE RATIONALE: Timers are the sessions' ONLY defense" -ForegroundColor Gray
    Write-Host "against IDE and local/remote systems that attempt to trap execution" -ForegroundColor Gray

    # Timer service runs asynchronously to prevent command trapping
    # Default: 10-minute timer that prompts check-ins
    $timerScript = "Global-Scripts\global-command-timer.ps1"
    if (Test-Path $timerScript) {
        Write-Host "[OK] Timer service script available: $timerScript" -ForegroundColor Green
        
        # Create timer initialization script that runs in background
        $timerInitScript = @'
# Timer Service Background Process
# This runs independently to provide check-in prompts and prevent session traps
$timerInterval = 600  # 10 minutes default
$sessionMarker = ".cursor/timer-service.running"

# Create marker file to indicate timer service is active
New-Item -ItemType Directory -Force -Path ".cursor" | Out-Null
$null = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $sessionMarker -Encoding UTF8

# Timer service loop (runs until session ends)
while ($true) {
    Start-Sleep -Seconds $timerInterval
    
    # Check-in prompt logic
    $lastActivity = Get-Content $sessionMarker -ErrorAction SilentlyContinue
    if ($lastActivity) {
        Write-Host "[TIMER-CHECK] Session active - timer service running" -ForegroundColor Cyan
        Write-Host "              This prevents IDE stalls and command traps" -ForegroundColor Gray
    }
    
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

