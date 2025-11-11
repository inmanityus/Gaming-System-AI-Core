# Updating Command Markdown Files for Session Monitor Integration

This document provides instructions for updating the markdown files in `C:\Users\kento\.cursor\commands\` to integrate with the Session Monitor system while still using watchdogs for specific calls.

## Overview

Commands should continue using watchdog wrappers for individual command execution, but the Session Monitor system provides an additional layer of protection at the session level. The monitor detects when entire sessions are stuck, not just individual commands.

## Integration Pattern

Each command markdown file should be updated to:

1. **Keep watchdog usage** for commands that could hang (builds, installs, long operations)
2. **Add session monitor awareness** in command descriptions
3. **Reference cleanup integration** when sessions are stuck

## Example Updates

### Before (Original Command):

```markdown
# Build Command

## Usage
Type `/build` to build the project.

## What it does
- Runs `npm run build`
- Checks for TypeScript errors
- Validates output

## Implementation
- Uses watchdog with 900s timeout
- Logs to `.cursor/ai-logs/`
```

### After (Updated with Session Monitor):

```markdown
# Build Command

## Usage
Type `/build` to build the project.

## What it does
- Runs `npm run build`
- Checks for TypeScript errors
- Validates output

## Implementation
- Uses watchdog with 900s timeout
- Logs to `.cursor/ai-logs/`
- Session Monitor: This command sends heartbeats during execution. If the entire session is stuck for 10+ minutes, the Session Monitor will trigger automatic cleanup.

## Session Monitor Integration
The Session Monitor system (automatically started in `startup.ps1`) monitors all Cursor sessions. If this session becomes unresponsive for 10 minutes:
1. Monitor detects stale session (no heartbeat)
2. Writes intervention command (cleanup)
3. Session executes cleanup script on next heartbeat check (within 30 seconds)
4. Commands can continue after cleanup completes

This provides protection against session-level hangs beyond individual command timeouts.
```

## Standard Template Addition

Add this section to ALL command markdown files:

```markdown
## Session Monitor Integration

**Automatic Protection**: This command operates under Session Monitor protection.

- **Heartbeat**: Session sends heartbeat every 30 seconds
- **Stuck Detection**: Monitor detects if session is stuck (>10 min no heartbeat)
- **Auto-Intervention**: When stuck, monitor triggers cleanup automatically
- **Recovery**: Session continues after cleanup intervention

**Watchdog Still Required**: This command also uses watchdog timeouts for individual command protection. Session Monitor is an additional layer for session-level protection.

**No Action Required**: Session Monitor is integrated into `startup.ps1` and runs automatically.
```

## Files to Update

Update all markdown files in `C:\Users\kento\.cursor\commands\`:

- `/build.md` - Build operations
- `/test.md` - Testing commands  
- `/deploy.md` - Deployment commands
- `/cleanup.md` - Cleanup commands (should reference session monitor cleanup)
- `/sync.md` - Sync operations
- `/start.md` - Startup commands
- `/stop.md` - Shutdown commands
- And all other command files...

## Command-Specific Notes

### `/cleanup.md`

Add note that cleanup can be triggered automatically by Session Monitor:

```markdown
## Automatic Cleanup

The Session Monitor service may automatically trigger this cleanup command if:
- Session is detected as stuck (no heartbeat for 10 minutes)
- Session heartbeat loop detects intervention file

This ensures stuck sessions are automatically recovered without manual intervention.
```

### Long-Running Commands

For commands that take a long time (deployments, migrations, builds), add:

```markdown
## Session Monitor Notes

This command may take longer than 10 minutes. The Session Monitor will:
- Continue receiving heartbeats during execution (heartbeat loop runs independently)
- Only trigger intervention if the ENTIRE session stops responding (not just this command)
- Allow command to complete even if close to timeout threshold

The command's individual watchdog timeout still applies for command-level protection.
```

## Verification

After updating markdown files:

1. Restart a Cursor session
2. Verify session registers (check `.cursor/session-id.txt` exists)
3. Run a command and verify it continues to use watchdog
4. Check heartbeat is updating:
   ```powershell
   $sessionID = Get-Content ".cursor\session-id.txt"
   Get-Content "$env:USERPROFILE\.cursor\SessionMonitor\Heartbeats\$sessionID.heartbeat"
   ```

## Batch Update Script

To help with bulk updates, create a PowerShell script:

```powershell
# Update-CommandMarkdown.ps1
$commandsPath = "$env:USERPROFILE\.cursor\commands"
$template = Get-Content ".\SessionMonitorIntegration-Template.md" -Raw

Get-ChildItem "$commandsPath\*.md" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -notmatch "Session Monitor Integration") {
        Add-Content -Path $_.FullName -Value "`n$template"
        Write-Host "Updated: $($_.Name)" -ForegroundColor Green
    }
}
```

## Migration Checklist

- [ ] Review all command markdown files
- [ ] Add Session Monitor Integration section to each
- [ ] Update `/cleanup.md` with automatic cleanup notes
- [ ] Update long-running commands with special notes
- [ ] Test commands still work with watchdog
- [ ] Verify session monitor is running
- [ ] Test intervention scenario (manually trigger)

## Questions?

See `Global-Scripts\session-monitor\README.md` for complete system documentation.



