# CRITICAL: Command Watchdog Protocol - Mandatory for ALL Projects

**Status**: MANDATORY  
**Applies To**: ALL projects in ALL sessions  
**Created**: 2025-10-18 (after 2-hour hang incident)  
**Severity**: CRITICAL - Violation causes hours of wasted session time

## 🚨 PROTECTIVE RATIONALE - WHY THIS EXISTS

**CRITICAL UNDERSTANDING**: This watchdog protocol exists because **timers and watchdog commands are the sessions' ONLY defense** against the IDE and local/remote systems that attempt to trap and prevent them from succeeding.

**THE THREAT**: Without proper timer protection, sessions can be indefinitely trapped by:
- Malicious commands that hang indefinitely
- IDE systems that deliberately stall execution
- Local system processes that prevent completion
- Remote systems that refuse to respond
- Network operations that never timeout
- Database operations that lock indefinitely

**THE DEFENSE**: Independent timers and watchdog commands provide the ONLY protection against these threats by:
- Forcing command termination after reasonable timeouts
- Preventing indefinite hangs that waste session time
- Providing escape mechanisms from trapped states
- Ensuring session continuity and progress
- Protecting against system-level interference

**MANDATORY ENFORCEMENT**: This protocol is NOT optional - it is a critical defense mechanism that MUST be used for ALL commands that could potentially hang or be trapped by malicious systems.

---

## Core Rule

**ALWAYS use the Command Watchdog Protocol for ANY command that could take more than 5 seconds or potentially hang.**

### Never Run These Commands Directly:
- `npm run build` / `npm run dev` / `npm start`
- `npm install` / `npm ci` / `yarn install` / `pnpm install`
- `npm test` / `npm run test` / `pytest` / `jest`
- Database operations (migrations, backups, complex queries)
- File uploads/downloads (`scp`, `rsync`, `curl`, `wget`)
- Tar/zip operations (`tar -xzf`, `unzip`)
- Git operations (`git clone`, `git pull` on large repos)
- Server startup commands
- Docker builds (`docker build`, `docker-compose up`)

---

## Platform-Specific Commands

### Windows (PowerShell)
```powershell
# Check watchdog exists first
if (-not (Test-Path "scripts/cursor_run.ps1")) {
    Write-Error "Watchdog script missing - create it first!"
    exit 1
}

# Execute with watchdog
pwsh -File scripts/cursor_run.ps1 `
    -TimeoutSec <timeout> `
    -Label "<descriptive label>" `
    -- <actual command>
```

### Linux (Bash)
```bash
# Check watchdog exists first
if [ ! -f "scripts/cursor_run.sh" ]; then
    echo "Watchdog script missing - create it first!"
    exit 1
fi

# Execute with watchdog
bash scripts/cursor_run.sh \
    --timeout <timeout> \
    --label "<descriptive label>" \
    -- <actual command>
```

---

## Timeout Guidelines

| Command Type | Recommended Timeout | Examples |
|--------------|---------------------|----------|
| Quick checks | 120s (2 min) | Status checks, quick queries |
| Small builds | 900s (15 min) | Next.js build, TypeScript compile |
| Large builds | 1800s (30 min) | Monorepo builds, complex projects |
| Package installs | 600-1200s (10-20 min) | npm install, dependency resolution |
| Tests | 900-1800s (15-30 min) | Test suites, integration tests |
| File transfers | 1800-3600s (30-60 min) | Large file uploads/downloads |
| Database ops | 600-1800s (10-30 min) | Migrations, backups, restores |

**Rule of thumb**: Set timeout to 2x expected duration for safety margin.

---

## What the Watchdog Provides

### 1. **Timeout Protection**
- Commands automatically terminated if exceed timeout
- Escalation: SIGINT (60s) → SIGTERM (90s) → SIGKILL (120s)
- Prevents infinite hangs

### 2. **Idempotency Guard**
- Tracks recent commands by SHA256 hash
- Skips duplicate commands within 120 seconds
- Prevents infinite retry loops

### 3. **Output Management**
- Caps output to 2000 lines per command
- Saves full logs to `.cursor/ai-logs/<timestamp>-<label>.log`
- Returns structured results: `{exitCode, durationSec, truncated, logPath}`

### 4. **Stuck Detection**
- Monitors output streams for progress
- Detects "running but not producing output" states
- Auto-escalates termination if stalled

### 5. **Resource Protection**
- Prevents context bloat from verbose output
- Enables log analysis without loading full output
- Allows command inspection and replay

---

## Real-World Case Study: The 2-Hour Hang

**Date**: 2025-10-18  
**Project**: Innovation Forge Website Deployment  
**Task**: Running `npm run build` to create production build

### What Happened
1. ❌ AI agent ran `npm run build` DIRECTLY (no watchdog)
2. ❌ Build command hung/interrupted after starting
3. ❌ Agent waited for 1 hour 55 minutes with zero progress
4. ❌ User had to manually intervene and terminate
5. ❌ Zero deployment progress despite "autonomous mode"

### Impact
- **Time Wasted**: 1 hour 55 minutes of session
- **Progress Made**: ZERO
- **User Frustration**: High (expected autonomous completion)
- **Root Cause**: Violated Command Watchdog Protocol

### What Should Have Happened
```powershell
# CORRECT approach with watchdog
pwsh -File scripts/cursor_run.ps1 `
    -TimeoutSec 1800 `
    -Label "Next.js production build" `
    -- npm run build
```

**Result with Watchdog**:
- Maximum wait: 30 minutes (timeout)
- Proper error handling and logs
- Ability to retry or fix issue
- Controlled failure instead of infinite hang

---

## Integration with Autonomous Protocols

When running in **autonomous mode** (user says "work on your own", "full autonomy", etc.):

### MANDATORY Requirements
1. ✅ **ALL** commands > 5 seconds MUST use watchdog
2. ✅ Check watchdog exists before starting milestone
3. ✅ Set generous timeouts (2x expected duration)
4. ✅ Log all watchdog results in milestone reports
5. ✅ Never retry same command twice without changes
6. ✅ If command fails twice, document and escalate (don't infinite loop)

### Pre-Command Checklist
Before executing ANY potentially long command:

- [ ] Command could take > 5 seconds?
- [ ] Watchdog script exists? (`Test-Path scripts/cursor_run.ps1` or `[ -f scripts/cursor_run.sh ]`)
- [ ] Appropriate timeout selected based on command type?
- [ ] Descriptive label provided for logging?
- [ ] Error handling planned for timeout/failure cases?
- [ ] Maximum retry count enforced (1 retry max)?

**If ANY item unchecked → STOP and fix before proceeding**

---

## Error Handling After Watchdog Execution

### Exit Code 0: Success ✅
- Continue to next step
- Update TODO status to completed
- Log success in milestone report

### Exit Code 124: Timeout ⏰
- Command exceeded maximum timeout
- Check log file: `.cursor/ai-logs/<timestamp>-<label>.log`
- Options:
  - Increase timeout if reasonable (command making progress)
  - Optimize command (add --parallel, --cache, etc.)
  - Split into smaller operations
- Retry ONCE with changes

### Exit Code 1-123: Command Failed ❌
- Read error output from logs
- Diagnose and fix underlying issue
- Retry ONCE with watchdog after fix
- If fails twice → document and request user input

### Exit Code 137: Force Killed 💀
- Watchdog had to SIGKILL (command completely stuck)
- Check for: deadlocks, infinite loops, resource exhaustion
- Fix root cause before any retry
- DO NOT retry without significant changes

---

## When Watchdog is NOT Required

Only skip watchdog for commands completing in < 5 seconds:

### Safe to Run Directly
- `ls` / `dir` / `Get-ChildItem`
- `pwd` / `Get-Location`
- `echo` / `Write-Output`
- `cat` / `Get-Content` (small files < 10KB)
- `ps` / `Get-Process`
- `systemctl status` / `pm2 status`
- Quick SQL: `psql -c "SELECT COUNT(*)"`
- File existence checks: `Test-Path` / `[ -f file ]`

### Gray Area (Use Judgment)
- Small file reads (10-100KB) → Usually OK direct
- Database queries with LIMIT → Usually OK direct
- Git status checks → Usually OK direct
- Linter runs on single files → Consider watchdog
- Test runs on single test → Consider watchdog

**If in doubt, use the watchdog. It adds < 1 second overhead.**

---

## Watchdog Script Creation

If watchdog doesn't exist in a project, create it from global template:

### Windows
```powershell
Copy-Item "C:\Users\$env:USERNAME\.cursor\global-cursor-repo\scripts\cursor_run.ps1" `
    -Destination "scripts\cursor_run.ps1"
```

### Linux
```bash
cp ~/.cursor/global-cursor-repo/scripts/cursor_run.sh scripts/cursor_run.sh
chmod +x scripts/cursor_run.sh
```

The watchdog script should be included in ALL project setups automatically.

---

## Global Memory Integration

This protocol is reinforced by:

1. **Memory 10080999**: MANDATORY Command Watchdog Protocol
2. **User Rules**: Command Watchdog Protocol (CWP) section
3. **Project-level reasoning**: command-execution-safety-protocol.md
4. **This global workflow**: CRITICAL-Command-Watchdog-Protocol.md

All four layers MUST agree. If agent violates this protocol, it's a CRITICAL bug.

---

## Monitoring and Enforcement

### For AI Agents
- Review command execution logs after each milestone
- Count direct vs. watchdog executions
- Flag any long-running direct executions
- Learn from timeout patterns to improve timeout estimates

### For Users
- Check `.cursor/ai-logs/` for watchdog usage
- Review `last-commands.jsonl` for patterns
- Report violations to improve agent training
- Verify autonomous sessions used watchdog consistently

---

## Summary: The Non-Negotiable Rule

```
IF command could take > 5 seconds OR could hang
THEN use Command Watchdog Protocol
ELSE direct execution OK

IF in autonomous mode
THEN use watchdog for EVERYTHING > 5 seconds
NO EXCEPTIONS

IF watchdog doesn't exist
THEN create it from global template FIRST
THEN proceed with watchdog protection
```

**Violation of this protocol is a CRITICAL failure.**  
**It wastes hours of session time and defeats the purpose of autonomous operation.**

---

**Last Updated**: 2025-10-18  
**Next Review**: Every 30 days or after any hang incident  
**Enforcement**: MANDATORY across ALL projects and ALL sessions

