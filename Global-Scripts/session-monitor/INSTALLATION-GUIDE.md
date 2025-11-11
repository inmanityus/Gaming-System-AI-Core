# Cursor Session Monitor - Installation Guide

## Quick Start

### 1. Install Monitor Service

Choose one of two options:

#### Option A: Scheduled Task (Recommended - No NSSM Required)

```powershell
cd Global-Scripts\session-monitor
.\Install-MonitorService.ps1 -UseScheduledTask
```

#### Option B: Windows Service (Requires NSSM)

1. Download NSSM from https://nssm.cc/download
2. Extract to `C:\nssm` or add to PATH
3. Install service:

```powershell
cd Global-Scripts\session-monitor
.\Install-MonitorService.ps1
```

### 2. Verify Integration

The system is already integrated into `startup.ps1`. To verify:

1. Start a new Cursor session
2. You should see:
   ```
   ✓ Session registered with monitor service: {GUID}
   ✓ Heartbeat loop started (checks every 30 seconds)
   ```

### 3. Check Service Status

**For Scheduled Task:**
```powershell
Get-ScheduledTask -TaskName "CursorSessionMonitor"
```

**For Windows Service:**
```powershell
Get-Service -Name "CursorSessionMonitor"
```

### 4. View Logs

```powershell
# Monitor service logs
Get-Content "$env:USERPROFILE\.cursor\SessionMonitor\Logs\monitor-service.log" -Tail 50 -Wait

# Session registration logs
Get-Content "$env:USERPROFILE\.cursor\SessionMonitor\Logs\session-registration.log" -Tail 50

# Heartbeat logs
Get-Content "$env:USERPROFILE\.cursor\SessionMonitor\Logs\heartbeat.log" -Tail 50
```

## Verification Steps

### Check Session Registration

```powershell
# Check session ID file exists
Test-Path ".cursor\session-id.txt"
Get-Content ".cursor\session-id.txt"

# Check heartbeat file exists and is recent
$sessionID = Get-Content ".cursor\session-id.txt"
$heartbeatFile = "$env:USERPROFILE\.cursor\SessionMonitor\Heartbeats\$sessionID.heartbeat"
if (Test-Path $heartbeatFile) {
    $timestamp = [DateTime]::FromFileTime([long](Get-Content $heartbeatFile))
    Write-Host "Last heartbeat: $timestamp" -ForegroundColor Green
    Write-Host "Time since: $((Get-Date) - $timestamp)" -ForegroundColor Cyan
}
```

### Check Registered Sessions

```powershell
$registry = "$env:USERPROFILE\.cursor\SessionMonitor\Registry\sessions.json"
if (Test-Path $registry) {
    Get-Content $registry | ConvertFrom-Json | Format-Table
} else {
    Write-Host "No active sessions registered" -ForegroundColor Yellow
}
```

### Check Heartbeat Job

```powershell
$jobId = Get-Content ".cursor\heartbeat-job-id.txt" -ErrorAction SilentlyContinue
if ($jobId) {
    Get-Job -Id $jobId
    Receive-Job -Id $jobId -Keep
}
```

## Testing Stuck Session Detection

To test that the system detects stuck sessions:

1. Register a test session
2. Stop the heartbeat loop for that session:
   ```powershell
   $jobId = Get-Content ".cursor\heartbeat-job-id.txt"
   Stop-Job -Id $jobId
   Remove-Job -Id $jobId
   ```
3. Wait 10 minutes (or temporarily reduce timeout in Monitor-CursorSessions.ps1)
4. Check monitor logs - should show intervention sent

## Troubleshooting

### Service/Task Not Running

**Scheduled Task:**
```powershell
# Check status
Get-ScheduledTask -TaskName "CursorSessionMonitor"

# Start if not running
Start-ScheduledTask -TaskName "CursorSessionMonitor"

# Check last run time
(Get-ScheduledTaskInfo -TaskName "CursorSessionMonitor").LastRunTime
```

**Windows Service:**
```powershell
# Check status
Get-Service -Name "CursorSessionMonitor"

# Start if not running
Start-Service -Name "CursorSessionMonitor"

# Check if service exists
Get-Service -Name "CursorSessionMonitor" -ErrorAction SilentlyContinue
```

### Session Not Registering

1. Check startup.ps1 integration:
   ```powershell
   Select-String -Path "scripts\utilities\startup.ps1" -Pattern "Session Monitor"
   ```

2. Manually register session:
   ```powershell
   .\Register-CursorSession.ps1
   ```

3. Check for errors in registration log:
   ```powershell
   Get-Content "$env:USERPROFILE\.cursor\SessionMonitor\Logs\session-registration.log" -Tail 20
   ```

### Heartbeat Not Updating

1. Manually update heartbeat:
   ```powershell
   $sessionID = Get-Content ".cursor\session-id.txt"
   .\Update-SessionHeartbeat.ps1 -SessionID $sessionID
   ```

2. Restart heartbeat loop:
   ```powershell
   # Stop existing job
   $jobId = Get-Content ".cursor\heartbeat-job-id.txt" -ErrorAction SilentlyContinue
   if ($jobId) {
       Stop-Job -Id $jobId -ErrorAction SilentlyContinue
       Remove-Job -Id $jobId -ErrorAction SilentlyContinue
   }
   
   # Start new loop
   $sessionID = Get-Content ".cursor\session-id.txt"
   .\Start-HeartbeatLoop.ps1 -SessionID $sessionID
   ```

## Updating Command Markdown Files

See `UPDATE-COMMANDS-MARKDOWN.md` for instructions on updating command files in `C:\Users\kento\.cursor\commands\`.

The key points:
- Commands should still use watchdogs for individual command protection
- Add Session Monitor integration section to each command markdown
- Explain that Session Monitor provides session-level protection beyond command timeouts

## Uninstallation

### Remove Scheduled Task

```powershell
Unregister-ScheduledTask -TaskName "CursorSessionMonitor" -Confirm:$false
```

### Remove Windows Service

```powershell
Stop-Service -Name "CursorSessionMonitor"
nssm remove CursorSessionMonitor confirm
```

### Clean Up Files

```powershell
Remove-Item "$env:USERPROFILE\.cursor\SessionMonitor" -Recurse -Force
Remove-Item ".cursor\session-id.txt" -ErrorAction SilentlyContinue
Remove-Item ".cursor\heartbeat-job-id.txt" -ErrorAction SilentlyContinue
```

## Support

For issues or questions:
- See `README.md` for complete system documentation
- Check logs in `$env:USERPROFILE\.cursor\SessionMonitor\Logs\`
- Review startup.ps1 integration section



