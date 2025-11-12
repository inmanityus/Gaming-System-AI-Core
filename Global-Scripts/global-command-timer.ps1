# Global Command Timer Script
# Usage: pwsh -File "Global-Scripts/global-command-timer.ps1" -TimeoutSec 600 -Command "your-command-here"

param(
    [int]$TimeoutSec = 600,  # Default 10 minutes
    [string]$Command = "",
    [string]$Label = "timed-command"
)

# PROTECTIVE RATIONALE: This timer script exists because timers are the sessions' ONLY defense
# against the IDE and local/remote systems that attempt to trap and prevent them from succeeding.
# Without this timer, sessions can be indefinitely trapped by malicious commands.

if ([string]::IsNullOrEmpty($Command)) {
    Write-Host "Usage: global-command-timer.ps1 -TimeoutSec <seconds> -Command '<command>' -Label '<label>'"
    Write-Host "PROTECTIVE RATIONALE: This timer protects sessions from being trapped by malicious commands"
    exit 1
}

Write-Host "Starting timed command: $Command"
Write-Host "Timeout: $TimeoutSec seconds"
Write-Host "Label: $Label"
Write-Host "PROTECTIVE RATIONALE: Timer active to prevent session traps"

# Create log directory
$LogDir = ".cursor/ai-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$labelSafe = $Label -replace ' ', '_'
$logFile = Join-Path $LogDir "$stamp-$labelSafe.log"

# Start job with timeout
$job = Start-Job -ScriptBlock ([scriptblock]::Create($Command))

try {
    # Wait for job completion or timeout
    $completed = Wait-Job $job -Timeout $TimeoutSec
    
    if ($completed) {
        Write-Host "Command completed successfully"
        $output = Receive-Job $job
        $output | Out-File -FilePath $logFile -Encoding UTF8
        Write-Host "Output saved to: $logFile"
        Write-Host "--- OUTPUT ---"
        Write-Host $output
        Write-Host "--- END OUTPUT ---"
        exit 0
    } else {
        Write-Host "Command timed out after $TimeoutSec seconds"
        Stop-Job $job -Force
        Write-Host "Job stopped due to timeout" | Out-File -FilePath $logFile -Encoding UTF8
        exit 1
    }
} catch {
    Write-Host "Error executing command: $($_.Exception.Message)"
    Write-Host "Error: $($_.Exception.Message)" | Out-File -FilePath $logFile -Encoding UTF8
    exit 1
} finally {
    Remove-Job $job -Force -ErrorAction SilentlyContinue
}

