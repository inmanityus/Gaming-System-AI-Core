#Requires -Version 7.0 -RunAsAdministrator
<#
.SYNOPSIS
    Create Windows Scheduled Task for automated Vibe Code backups
.DESCRIPTION
    Sets up weekly backups at 3 AM with proper permissions and settings
#>

param(
    [switch]$Remove = $false
)

$TaskName = "Vibe-Code-Automated-Backup"
$ScriptPath = "E:\Vibe Code\Gaming System\AI Core\scripts\automated-vibe-backup.ps1"
$LogPath = "E:\Innovation Forge\My Drive\Vibe-Backups\Logs\task-setup.log"

function Write-SetupLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogPath -Value $logMessage
    
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        default { Write-Host $logMessage }
    }
}

# Ensure log directory exists
$logDir = Split-Path $LogPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-SetupLog "========================================" 
Write-SetupLog "Vibe Code Backup - Task Scheduler Setup"
Write-SetupLog "========================================"

# Remove task if requested
if ($Remove) {
    Write-SetupLog "Removing scheduled task: $TaskName"
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-SetupLog "Task removed successfully" -Level SUCCESS
    } else {
        Write-SetupLog "Task not found" -Level WARNING
    }
    
    exit 0
}

# Validate script exists
if (-not (Test-Path $ScriptPath)) {
    Write-SetupLog "ERROR: Backup script not found at: $ScriptPath" -Level ERROR
    exit 1
}

Write-SetupLog "Backup script: $ScriptPath"

# Check for existing task
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-SetupLog "Existing task found. Removing..." -Level WARNING
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task action
$action = New-ScheduledTaskAction `
    -Execute "pwsh.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory (Split-Path $ScriptPath)

Write-SetupLog "Task action created: pwsh.exe with backup script"

# Create weekly trigger at 3 AM every Sunday
$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -WeeksInterval 1 `
    -DaysOfWeek Sunday `
    -At 3:00AM

Write-SetupLog "Task trigger created: Weekly on Sundays at 3:00 AM"

# Task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12) `
    -Priority 4

Write-SetupLog "Task settings configured:"
Write-SetupLog "  - Allow start on batteries: Yes"
Write-SetupLog "  - Start when available: Yes"
Write-SetupLog "  - Multiple instances: Ignore New (prevents overlaps)"
Write-SetupLog "  - Execution time limit: 12 hours"
Write-SetupLog "  - Priority: 4 (Below Normal)"

# Create principal (run as current user with highest privileges)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

Write-SetupLog "Task principal: $env:USERNAME with elevated privileges"

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Automated weekly backup of all Vibe Code projects and Cursor profile. Runs at 3 AM every Sunday with monthly and yearly consolidation." `
        -Force
    
    Write-SetupLog "Task registered successfully!" -Level SUCCESS
    
    # Verify task
    $task = Get-ScheduledTask -TaskName $TaskName
    if ($task) {
        Write-SetupLog "`nTask Details:" -Level SUCCESS
        Write-SetupLog "  Name: $($task.TaskName)"
        Write-SetupLog "  State: $($task.State)"
        Write-SetupLog "  Next Run: $(($task | Get-ScheduledTaskInfo).NextRunTime)"
        Write-SetupLog "  Last Run: $(($task | Get-ScheduledTaskInfo).LastRunTime)"
        Write-SetupLog "  Last Result: $(($task | Get-ScheduledTaskInfo).LastTaskResult)"
        
        Write-SetupLog "`nSetup completed successfully!" -Level SUCCESS
        Write-SetupLog "The backup will run automatically every Sunday at 3:00 AM"
        Write-SetupLog "`nManual test command:"
        Write-SetupLog "  Start-ScheduledTask -TaskName '$TaskName'"
        Write-SetupLog "`nManual test with TestMode:"
        Write-SetupLog "  pwsh -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -TestMode"
    }
    
} catch {
    Write-SetupLog "ERROR: Failed to register task: $_" -Level ERROR
    exit 1
}

Write-SetupLog "`n========================================"
Write-SetupLog "Setup Complete"
Write-SetupLog "========================================"



