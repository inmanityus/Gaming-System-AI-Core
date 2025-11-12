# Session Monitor Feature
# Continuous background monitoring of /all-rules compliance throughout entire session
# Based on three-model collaboration: Claude 3.5, GPT-4o, GPT-4 Turbo consensus

function Initialize-SessionMonitor {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "[MONITOR] Initializing Session Monitor..." -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "PROTECTIVE RATIONALE: Continuous oversight ensures sessions behave" -ForegroundColor Gray
    Write-Host "as expected, stay stable, produce quality code, and don't get stuck" -ForegroundColor Gray
    
    # STEP 1: Cleanup orphaned monitor jobs BEFORE starting new monitor (MANDATORY)
    Write-Host "[MONITOR] Cleaning up orphaned monitor jobs..." -ForegroundColor Yellow
    $existingMonitors = Get-Job -Name "SessionMonitor" -ErrorAction SilentlyContinue
    if ($existingMonitors) {
        Write-Host "[MONITOR] Found $($existingMonitors.Count) orphaned monitor job(s)" -ForegroundColor Yellow
        $existingMonitors | Stop-Job -ErrorAction SilentlyContinue
        $existingMonitors | Remove-Job -ErrorAction SilentlyContinue
        Write-Host "[MONITOR] Cleanup completed" -ForegroundColor Green
    } else {
        Write-Host "[MONITOR] No orphaned monitors found" -ForegroundColor Green
    }
    
    # STEP 2: Create monitoring directories
    Write-Host "[MONITOR] Setting up monitoring infrastructure..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path ".cursor/logs" | Out-Null
    New-Item -ItemType Directory -Force -Path ".cursor/monitor" | Out-Null
    
    # STEP 3: Create session monitor background job
    Write-Host "[MONITOR] Starting continuous session monitor..." -ForegroundColor Yellow
    
    $monitorScript = @'
# Session Monitor Background Process
# Continuously monitors /all-rules compliance throughout entire session
# Based on three-model collaboration design

$monitorInterval = 60  # 60 seconds between checks (lightweight)
$statusFile = ".cursor/monitor/status.json"
$violationsLog = ".cursor/logs/session-monitor.jsonl"
$sessionStartTime = Get-Date

# Initialize log file
$null = @{
    "timestamp" = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    "event" = "Session monitor started"
    "session_start" = $sessionStartTime.ToString("yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json -Compress | Add-Content -Path $violationsLog

# Initialize status
$initialStatus = @{
    "monitor_active" = $true
    "last_check" = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    "compliance" = @{
        "timer_service" = "unknown"
        "peer_coding" = "unknown"
        "pairwise_testing" = "unknown"
        "milestones" = "unknown"
        "work_visibility" = "unknown"
        "memory_consolidation" = "unknown"
        "comprehensive_testing" = "unknown"
        "continuity" = "unknown"
    }
    "violations" = @()
    "uptime_seconds" = 0
} | ConvertTo-Json -Compress
$initialStatus | Out-File -FilePath $statusFile -Encoding UTF8 -NoNewline

# Monitor loop (runs until session ends)
while ($true) {
    try {
        $checkStartTime = Get-Date
        $uptime = ($checkStartTime - $sessionStartTime).TotalSeconds
        
        # Check status (aggregate object for updates)
        $status = @{
            "monitor_active" = $true
            "last_check" = $checkStartTime.ToString("yyyy-MM-dd HH:mm:ss")
            "compliance" = @{}
            "violations" = @()
            "uptime_seconds" = [int]$uptime
        }
        
        # CHECK 1: Timer Service
        $timerJob = Get-Job -Name "CursorTimerService" -ErrorAction SilentlyContinue
        $timerMarker = Test-Path ".cursor/timer-service.running"
        if ($timerJob -and $timerJob.State -eq "Running" -and $timerMarker) {
            $status.compliance["timer_service"] = "ok"
        } else {
            $status.compliance["timer_service"] = "violation"
            $status.violations += @{
                "rule" = "timer_protection"
                "severity" = "critical"
                "details" = "Timer service not running or verified"
            }
            # Auto-remediate: Try to start timer if dead
            if (-not $timerJob -or $timerJob.State -ne "Running") {
                try {
                    $env:CURSOR_TIMER_RESTART = "true"
                    Write-Host "[MONITOR] Auto-remediation: Timer service dead, attempting restart..." -ForegroundColor Yellow
                } catch {
                    # Log but continue
                }
            }
        }
        
        # CHECK 2: Peer Coding Compliance
        # Check if any code was committed without peer review evidence
        $lastCommit = git log -1 --pretty=format:"%H %s" --all 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Simple heuristic: check commit message for peer review mention
            $hasPeerReview = $lastCommit -match "peer|review|collaborate"
            if ($hasPeerReview) {
                $status.compliance["peer_coding"] = "ok"
            } else {
                $status.compliance["peer_coding"] = "warning"
                # Don't add to violations if very recent (might be in progress)
            }
        }
        
        # CHECK 3: Pairwise Testing Compliance
        # Check if comprehensive testing was run recently
        $recentTests = Get-ChildItem ".cursor/logs" -Filter "*test*.log" -ErrorAction SilentlyContinue | 
                       Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-2) }
        if ($recentTests) {
            $status.compliance["pairwise_testing"] = "ok"
        } else {
            $status.compliance["pairwise_testing"] = "warning"
        }
        
        # CHECK 4: Milestone Display
        # Check if milestone files exist and are recent
        $recentMilestones = Get-ChildItem "." -Filter "*MILESTONE*.md" -ErrorAction SilentlyContinue |
                           Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) }
        if ($recentMilestones) {
            $status.compliance["milestones"] = "ok"
        } else {
            $status.compliance["milestones"] = "warning"
        }
        
        # CHECK 5: Work Visibility
        # Check if session is showing work actively (heuristic: recent commits + logs)
        $recentActivity = $false
        $recentCommits = git log --since="2 hours ago" --pretty=format:"%H" 2>&1
        if ($LASTEXITCODE -eq 0 -and $recentCommits) {
            $recentActivity = $true
        }
        if ($recentActivity) {
            $status.compliance["work_visibility"] = "ok"
        } else {
            $status.compliance["work_visibility"] = "warning"
        }
        
        # CHECK 6: Memory Consolidation
        # Check if memory files are being updated
        $recentMemory = Get-ChildItem ".cursor/memory" -Recurse -File -ErrorAction SilentlyContinue |
                       Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) }
        if ($recentMemory) {
            $status.compliance["memory_consolidation"] = "ok"
        } else {
            $status.compliance["memory_consolidation"] = "warning"
        }
        
        # CHECK 7: Comprehensive Testing
        # Check if tests were run recently (already covered in pairwise)
        $status.compliance["comprehensive_testing"] = $status.compliance["pairwise_testing"]
        
        # CHECK 8: Continuity
        # Check if session is actively working (commits, files changes within 1 hour)
        $veryRecentActivity = git log --since="1 hour ago" --pretty=format:"%H" 2>&1
        if ($LASTEXITCODE -eq 0 -and $veryRecentActivity) {
            $status.compliance["continuity"] = "ok"
        } else {
            $status.compliance["continuity"] = "warning"
        }
        
        # Write status update
        $status | ConvertTo-Json -Compress | Out-File -FilePath $statusFile -Encoding UTF8 -NoNewline
        
        # Log violations if any
        if ($status.violations.Count -gt 0) {
            foreach ($violation in $status.violations) {
                $logEntry = @{
                    "timestamp" = $checkStartTime.ToString("yyyy-MM-dd HH:mm:ss")
                    "rule" = $violation.rule
                    "severity" = $violation.severity
                    "details" = $violation.details
                } | ConvertTo-Json -Compress
                $logEntry | Add-Content -Path $violationsLog
            }
        }
        
        # Check duration
        $checkDuration = ((Get-Date) - $checkStartTime).TotalSeconds
        if ($checkDuration -gt 5) {
            # Log if check took too long
            Write-Host "[MONITOR-WARNING] Check duration: $([math]::Round($checkDuration, 2))s (high)" -ForegroundColor Yellow
        }
        
    } catch {
        $errorMsg = "[MONITOR-ERROR] $($_.Exception.Message)"
        Write-Host $errorMsg -ForegroundColor Red
        $errorLog = @{
            "timestamp" = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            "event" = "monitor_error"
            "error" = $_.Exception.Message
        } | ConvertTo-Json -Compress
        $errorLog | Add-Content -Path $violationsLog
    }
    
    # Sleep until next check
    Start-Sleep -Seconds $monitorInterval
}

# Cleanup on exit
$null = @{
    "timestamp" = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    "event" = "Session monitor stopped"
} | ConvertTo-Json -Compress | Add-Content -Path $violationsLog

'@
    
    # Start monitor in background job
    try {
        $monitorJob = Start-Job -ScriptBlock ([scriptblock]::Create($monitorScript)) -Name "SessionMonitor"
        if ($monitorJob) {
            Write-Host "[OK] Session monitor started (background job)" -ForegroundColor Green
            Write-Host "     Check interval: 60 seconds (lightweight)" -ForegroundColor Gray
            Write-Host "     Purpose: Continuous /all-rules compliance monitoring" -ForegroundColor Gray
            Write-Host "     Status: Running asynchronously throughout session" -ForegroundColor Gray
            Write-Host "     Output: .cursor/monitor/status.json" -ForegroundColor Gray
            Write-Host "     Logs: .cursor/logs/session-monitor.jsonl" -ForegroundColor Gray
            
            # Set environment variables
            $env:CURSOR_SESSION_MONITOR_ACTIVE = "true"
            $env:CURSOR_SESSION_MONITOR_JOB_ID = $monitorJob.Id
        } else {
            Write-Host "[WARNING] Session monitor failed to start" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARNING] Session monitor unavailable: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "          Session will run without continuous monitoring" -ForegroundColor Yellow
    }
    
    Write-Host "================================================================" -ForegroundColor Cyan
}

