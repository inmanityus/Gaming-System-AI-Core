# Context Window Monitor Background Process
# This runs independently to monitor context size and trigger cleanup/handoff

$monitorInterval = 300  # Check every 5 minutes
$thresholdPercent = 60  # 60% threshold
$monitorMarker = ".cursor/context-monitor.running"
$lastCheckFile = ".cursor/context-last-check.json"

# Function to estimate context window usage
function Get-ContextWindowUsage {
    # Note: Actual context window size detection depends on Cursor API
    # This is a placeholder that should be replaced with actual context measurement
    # For now, we'll use file-based heuristics and session state
    
    # Check session state files for context indicators
    $contextIndicators = @{
        ActiveFiles = (Get-ChildItem -Path ".cursor" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
        LogFiles = (Get-ChildItem -Path ".cursor/ai-logs" -File -ErrorAction SilentlyContinue | Measure-Object).Count
        MemoryFiles = (Get-ChildItem -Path ".cursor/memory" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    }
    
    # Estimate usage based on indicators (simplified heuristic)
    # In production, this should use actual Cursor API context measurement
    $estimatedUsage = [Math]::Min(100, ($contextIndicators.ActiveFiles * 0.5) + ($contextIndicators.LogFiles * 0.3) + ($contextIndicators.MemoryFiles * 0.2))
    
    return @{
        Percent = $estimatedUsage
        Indicators = $contextIndicators
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
}

# Function to trigger cleanup
function Invoke-CleanSession {
    Write-Host "[CONTEXT] Context threshold exceeded - triggering /clean-session" -ForegroundColor Yellow
    
    # Note: Actual implementation should invoke the /clean-session command
    # This is a placeholder - in production, this should trigger the actual command
    # For now, we'll create a trigger file that the session can detect
    
    $triggerFile = ".cursor/trigger-clean-session.flag"
    $null = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $triggerFile -Encoding UTF8
    Write-Host "[CONTEXT] Clean session trigger created: $triggerFile" -ForegroundColor Yellow
}

# Function to trigger handoff
function Invoke-Handoff {
    Write-Host "[CONTEXT] Context still above threshold after cleanup - triggering /handoff" -ForegroundColor Red
    
    # Note: Actual implementation should invoke the /handoff command
    # This is a placeholder - in production, this should trigger the actual command
    # For now, we'll create a trigger file that the session can detect
    
    $triggerFile = ".cursor/trigger-handoff.flag"
    $null = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $triggerFile -Encoding UTF8
    Write-Host "[CONTEXT] Handoff trigger created: $triggerFile" -ForegroundColor Red
}

# Main monitoring loop
while ($true) {
    try {
        # Check if monitor marker still exists (session still active)
        if (-not (Test-Path $monitorMarker)) {
            Write-Host "[CONTEXT] Monitor marker removed - stopping context monitor" -ForegroundColor Yellow
            break
        }
        
        # Get current context usage
        $contextUsage = Get-ContextWindowUsage
        
        # Save last check result
        $checkResult = @{
            Timestamp = $contextUsage.Timestamp
            Percent = $contextUsage.Percent
            Threshold = $thresholdPercent
            Action = "Monitoring"
        } | ConvertTo-Json
        $checkResult | Out-File -FilePath $lastCheckFile -Encoding UTF8
        
        # Check threshold
        if ($contextUsage.Percent -ge $thresholdPercent) {
            Write-Host "[CONTEXT] WARNING: Context window at $($contextUsage.Percent)% - threshold is $thresholdPercent%" -ForegroundColor Yellow
            
            # Check if cleanup was already triggered recently (within last 5 minutes)
            $cleanupTriggerFile = ".cursor/trigger-clean-session.flag"
            $handoffTriggerFile = ".cursor/trigger-handoff.flag"
            $cleanupCompleteFile = ".cursor/cleanup-complete.flag"
            
            if (Test-Path $handoffTriggerFile) {
                # Handoff already triggered - wait for session to process
                Write-Host "[CONTEXT] Handoff already triggered - waiting for session transfer" -ForegroundColor Yellow
            } elseif (Test-Path $cleanupCompleteFile) {
                # Cleanup completed - check if still above threshold
                $cleanupTime = (Get-Item $cleanupCompleteFile).LastWriteTime
                $timeSinceCleanup = (Get-Date) - $cleanupTime
                
                if ($timeSinceCleanup.TotalMinutes -lt 5) {
                    # Recent cleanup - check if still above threshold
                    if ($contextUsage.Percent -ge $thresholdPercent) {
                        Write-Host "[CONTEXT] Context still above threshold after cleanup - triggering handoff" -ForegroundColor Red
                        Invoke-Handoff
                    } else {
                        Write-Host "[CONTEXT] Context reduced below threshold after cleanup" -ForegroundColor Green
                        # Remove cleanup complete flag to allow future cleanups
                        Remove-Item $cleanupCompleteFile -ErrorAction SilentlyContinue
                    }
                } else {
                    # Cleanup was a while ago - can trigger again if needed
                    Remove-Item $cleanupCompleteFile -ErrorAction SilentlyContinue
                    if ($contextUsage.Percent -ge $thresholdPercent) {
                        Invoke-CleanSession
                    }
                }
            } elseif (Test-Path $cleanupTriggerFile) {
                # Cleanup already triggered - wait for completion
                Write-Host "[CONTEXT] Cleanup already triggered - waiting for completion" -ForegroundColor Yellow
            } else {
                # Trigger cleanup
                Invoke-CleanSession
            }
        } else {
            Write-Host "[CONTEXT] Context window at $($contextUsage.Percent)% - within normal range" -ForegroundColor Green
        }
        
        # Wait before next check
        Start-Sleep -Seconds $monitorInterval
        
    } catch {
        Write-Host "[CONTEXT] Error in context monitoring: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds $monitorInterval
    }
}
