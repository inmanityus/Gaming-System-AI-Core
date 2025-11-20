# Timer Service Clarification - ADD TO HANDOFF

## ⏰ CRITICAL: How Timer Service Actually Works

**USER ISSUE**: Sessions keep spawning PowerShell windows with "Session is still active" spam.

**ROOT CAUSE**: Timer Service was outputting to console in background job.

**FIX APPLIED**: Updated `Global-Workflows/startup-features/timer-service.ps1` to log to file instead of console.

## ✅ CORRECT Timer Service Usage (For Next Session)

### What Timer Service Is

- **Automatic background job** started by startup.ps1
- Runs every 10 minutes silently
- Logs to `.cursor/timer-service.log`
- Updates `.cursor/timer-service.running` marker
- **NO manual calls needed**
- **NO visible windows**
- **NO console output**

### What AI Sessions Should Do

**NOTHING.** Timer Service runs automatically. Just work normally.

### What NOT To Do

❌ Don't call `Global-Scripts\global-command-timer.ps1` directly  
❌ Don't try to "start" the timer  
❌ Don't wrap normal commands with timer  
❌ Don't check timer status unless debugging

### The global-command-timer.ps1 Script

This is a **different tool** - it wraps individual commands with timeout:

```powershell
# ONLY use for potentially-hanging commands
pwsh -File "Global-Scripts/global-command-timer.ps1" `
    -TimeoutSec 300 `
    -Command "docker build ..." `
    -Label "build"
```

**This is NOT the persistent Timer Service.**

## 📝 For Long-Running Operations (What User Actually Wants)

User wants to see progress for long scripts. Use this pattern:

```powershell
$start = Get-Date
Write-Host "[Build] Started at $(Get-Date -Format 'HH:mm:ss')"

# Do work...
docker build ...

# Every 30-60 seconds in loop, show elapsed:
$elapsed = ((Get-Date) - $start).TotalSeconds
Write-Host "[Build] Running for $([int]$elapsed)s..."

# At end:
$duration = ((Get-Date) - $start).TotalSeconds  
Write-Host "[Build] Completed in $([int]$duration)s"
```

This is SEPARATE from Timer Service protection.

## 🎯 Action Items for Next Session

1. ✅ Timer Service fixed - now runs silently
2. ✅ Usage documented correctly
3. 📋 Just work normally - Timer Service is automatic
4. 📋 For long operations, add manual progress output (see pattern above)
5. 📋 Never call timer scripts manually

---

**Next session should just work normally. Timer Service will protect silently in background.**






