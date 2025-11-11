# Global Reasoning: Command Execution Patterns

**Purpose**: Guide AI agents on safe command execution across ALL projects  
**Created**: 2025-10-18 (after watchdog violation incident)  
**Applies To**: ALL platforms (Windows PowerShell, Linux Bash, macOS)  
**Status**: MANDATORY REASONING FRAMEWORK

---

## Core Reasoning Framework

### Question: Should I use the Command Watchdog Protocol?

```
START → Is command expected to take > 5 seconds?
         ├─ YES → Use watchdog (MANDATORY)
         └─ NO → Could it potentially hang?
                  ├─ YES → Use watchdog (MANDATORY)
                  └─ NO → Is this autonomous operation?
                           ├─ YES → Use watchdog (SAFER)
                           └─ NO → Direct execution OK
```

### Risk Assessment Matrix

| Command Category | Hang Risk | Duration Risk | Network Risk | Watchdog Required? |
|------------------|-----------|---------------|--------------|-------------------|
| npm build | HIGH | HIGH | MEDIUM | ✅ YES |
| npm install | MEDIUM | HIGH | HIGH | ✅ YES |
| npm test | MEDIUM | HIGH | LOW | ✅ YES |
| Database queries | MEDIUM | MEDIUM | LOW | ✅ IF > 5s |
| File transfers | LOW | HIGH | HIGH | ✅ YES |
| Git operations | MEDIUM | MEDIUM | MEDIUM | ✅ IF > 5s |
| Server startup | HIGH | MEDIUM | LOW | ✅ YES |
| Status checks | LOW | LOW | LOW | ❌ NO |
| File reads | LOW | LOW | LOW | ❌ NO |
| Echo/Write | NONE | NONE | NONE | ❌ NO |

**Decision Rule**: If ANY risk is HIGH, use watchdog. If 2+ risks are MEDIUM, use watchdog.

---

## Pattern Recognition: Commands That Have Caused Issues

### Historical Failures (Actual Incidents)

#### Incident 1: npm run build (2025-10-18)
- **Project**: Innovation Forge Website
- **Command**: `npm run build` (direct, no watchdog)
- **Result**: Hung for 1h55m, zero progress
- **Lesson**: Build commands ALWAYS need watchdog
- **Prevention**: Route through watchdog with 1800s timeout

#### Pattern: Package Installations
- **Commands**: `npm install`, `npm ci`, `yarn install`, `pnpm install`
- **Common Issues**: Network timeouts, peer dependency resolution loops, postinstall script hangs
- **Prevention**: Watchdog with 600-1200s timeout
- **Fallback**: Use `--no-optional` or `--production` flags

#### Pattern: Test Executions
- **Commands**: `npm test`, `npm run test:e2e`, `pytest`, `jest`
- **Common Issues**: Infinite test loops, browser/server not closing, memory leaks
- **Prevention**: Watchdog with 900-1800s timeout
- **Fallback**: Run specific test files instead of full suite

#### Pattern: Database Migrations
- **Commands**: `npx prisma migrate`, `psql -f migration.sql`, `sequelize db:migrate`
- **Common Issues**: Lock waits, transaction deadlocks, large data migrations
- **Prevention**: Watchdog with 600-1800s timeout
- **Fallback**: Break large migrations into smaller chunks

---

## Reasoning by Platform

### Windows PowerShell

#### Context
- Default shell in Windows environments
- Uses `Stop-Process` for termination
- Has different timeout/interrupt behavior than Unix

#### Command Patterns
```powershell
# High-risk pattern (MUST use watchdog)
npm run build              # Can hang on compilation errors
npm install                # Network/dependency issues
npm test                   # Browser/server cleanup issues
docker build               # Layer caching, network pulls
```

#### Watchdog Template
```powershell
if (-not (Test-Path "scripts/cursor_run.ps1")) {
    Write-Error "Watchdog missing - create from global template"
    Copy-Item "C:\Users\$env:USERNAME\.cursor\global-cursor-repo\scripts\cursor_run.ps1" `
        -Destination "scripts\cursor_run.ps1"
}

pwsh -File scripts/cursor_run.ps1 `
    -TimeoutSec <timeout> `
    -Label "<descriptive-label>" `
    -- <actual-command>
```

### Linux Bash

#### Context
- Default shell in Linux/Ubuntu environments
- Uses `kill -9` (SIGKILL) for forced termination
- Better signal handling than Windows

#### Command Patterns
```bash
# High-risk pattern (MUST use watchdog)
npm run build              # Compilation hangs
npm install                # Network issues
./scripts/deploy.sh        # Multi-step deployments
tar -xzf large-file.tar.gz # Large file extraction
```

#### Watchdog Template
```bash
if [ ! -f "scripts/cursor_run.sh" ]; then
    echo "Watchdog missing - create from global template"
    cp ~/.cursor/global-cursor-repo/scripts/cursor_run.sh scripts/cursor_run.sh
    chmod +x scripts/cursor_run.sh
fi

bash scripts/cursor_run.sh \
    --timeout <timeout> \
    --label "<descriptive-label>" \
    -- <actual-command>
```

---

## Autonomous Mode: Elevated Safety Requirements

### Reasoning
When user requests "full autonomy", "work on your own", "proceed independently":
- User is NOT watching the session
- Hours could pass before user checks progress
- ANY hang wastes significant time
- Recovery must be automatic

### Elevated Rules for Autonomous Mode

1. **Use watchdog for EVERYTHING > 5 seconds** (no exceptions)
2. **Set generous timeouts** (2x normal expected duration)
3. **NEVER retry twice** (if fails twice, document and stop)
4. **Verify watchdog exists BEFORE starting first milestone**
5. **Log ALL command results in milestone reports**
6. **Check for command completion within expected time**

### Autonomous Mode Checklist

Before starting ANY milestone in autonomous mode:

```
✅ Pre-Session Setup
   [ ] Verify watchdog script exists
   [ ] Review command list for milestone
   [ ] Estimate timeout for each command
   [ ] Plan error handling for each command
   [ ] Define success criteria

✅ During Execution
   [ ] Use watchdog for all commands > 5s
   [ ] Monitor for timeout/failure patterns
   [ ] Log results to milestone report
   [ ] Never retry without changes
   [ ] Stop after 2 failures on same command

✅ Post-Execution
   [ ] Review command logs
   [ ] Document any timeouts/failures
   [ ] Update timeout estimates based on actuals
   [ ] Report issues to user before next milestone
```

---

## Timeout Selection Reasoning

### Small Commands (< 5 seconds expected)
- **Direct execution OK** (no watchdog needed)
- Examples: `ls`, `pwd`, `cat small-file.txt`
- Reasoning: Overhead of watchdog > benefit

### Medium Commands (5-60 seconds expected)
- **Timeout: 120 seconds** (2x maximum expected)
- Examples: TypeScript compile, small test suite, quick query
- Reasoning: Allow buffer for slower systems

### Large Commands (1-15 minutes expected)
- **Timeout: 900-1800 seconds** (15-30 minutes)
- Examples: npm build, npm install, full test suite
- Reasoning: Build complexity varies, need generous buffer

### Very Large Commands (15-30 minutes expected)
- **Timeout: 1800-3600 seconds** (30-60 minutes)
- Examples: Monorepo builds, large file transfers, database backups
- Reasoning: Legitimate operations can take this long

### Unknown Duration
- **Default: 1800 seconds** (30 minutes)
- Reasoning: Safe default that catches most hangs
- Can adjust based on logs after first run

---

## Error Pattern Recognition

### Pattern 1: Immediate Failure (Exit Code 1-10, Duration < 5s)
**Reasoning**: Configuration error, missing dependency, wrong path
**Action**: Fix configuration, verify dependencies, retry ONCE
**Example**: `Error: Cannot find module 'next'` → Run `npm install`

### Pattern 2: Timeout (Exit Code 124, Duration = Timeout)
**Reasoning**: Command legitimately slow OR stuck
**Action**: Check logs for progress, increase timeout if making progress
**Example**: Build logs show 90% complete → Increase timeout to 2400s

### Pattern 3: Force Killed (Exit Code 137, Duration = Timeout + Grace Period)
**Reasoning**: Command completely stuck, didn't respond to SIGINT/SIGTERM
**Action**: Investigate root cause, fix before retry
**Example**: Deadlock in database migration → Fix migration SQL

### Pattern 4: Intermittent (Success → Fail → Success)
**Reasoning**: Network issues, race conditions, external dependency problems
**Action**: Add retry logic with exponential backoff (but max 1 retry total)
**Example**: npm install fails on network timeout → Retry once

### Pattern 5: Consistent Failure (Fails twice with same error)
**Reasoning**: Fundamental issue that won't resolve with retry
**Action**: STOP retrying, document issue, request user input
**Example**: TypeScript compilation error → Fix code, don't retry same build

---

## Integration with Global Systems

### Memory System
- **Memory 10080999**: Mandatory watchdog protocol
- **This Document**: Reasoning framework for when/why/how

### Workflow System
- **CRITICAL-Command-Watchdog-Protocol.md**: Step-by-step procedures
- **This Document**: Strategic thinking behind procedures

### History System
- **2025-10-18-watchdog-violation-incident.md**: What happened when protocol violated
- **This Document**: How to prevent similar incidents

---

## Decision Flowchart for Complex Scenarios

### Scenario: Building on Remote Server

```
Question: Should I build locally or on server?

├─ Can I build locally?
│  ├─ YES: Build locally (safer, faster feedback)
│  │     → Use watchdog with 1800s timeout
│  │     → Upload .next folder to server
│  └─ NO: Must build on server
│        → SSH to server
│        → Use watchdog with 2400s timeout (remote slower)
│        → Monitor SSH connection stability

Result: Local build preferred when possible
```

### Scenario: Package Installation Failing

```
Question: npm install failed with timeout - what next?

├─ Check logs: Any progress made?
│  ├─ YES (90% complete): Increase timeout to 1800s, retry once
│  └─ NO (stuck at 0%): Network or config issue
│        ├─ Check: Can I access npm registry?
│        │  ├─ YES: Dependency issue, check package.json
│        │  └─ NO: Network issue, fix connection
│        └─ Try: npm install --verbose --loglevel=silly
│              → Use watchdog with 1200s timeout

Result: Diagnose before retry, don't blindly increase timeout
```

### Scenario: Test Suite Running Forever

```
Question: Tests exceeded 1800s timeout - what's wrong?

├─ Check logs: Which test(s) running?
│  ├─ Stuck on specific test: Infinite loop or waiting for resource
│  │     → Run that test in isolation with debugger
│  │     → Fix test or mark as skipped
│  └─ Making progress: Just really slow
│        → Increase timeout to 3600s
│        → OR parallelize tests: npm test -- --maxWorkers=4

Result: Isolate problem, don't just increase timeout
```

---

## Future Improvements

### Proposed Enhancements

1. **Automatic Timeout Estimation**
   - Track historical command durations
   - ML model to predict timeout based on project size, file count, etc.
   - Auto-adjust timeouts based on past runs

2. **Progress Detection**
   - Parse command output for progress indicators (10%, 50%, 90%)
   - Auto-extend timeout if making progress
   - Alert if no progress for 5 minutes

3. **Resource Monitoring**
   - Track CPU/memory usage during command
   - Detect resource exhaustion before hang
   - Suggest optimization if resource bottlenecked

4. **Smart Retry Logic**
   - Classify errors (transient vs. permanent)
   - Auto-retry transient errors with backoff
   - Never retry permanent errors

---

## Summary: Reasoning Principles

1. **Safety First**: When in doubt, use watchdog
2. **Measure, Don't Guess**: Base timeouts on data, not assumptions
3. **Learn from Failures**: Every timeout teaches optimal duration
4. **Autonomous = Extra Safety**: Not watching requires more protection
5. **Two Failures = Stop**: Never infinite loop on same command
6. **Document Everything**: Logs enable intelligent decisions

**The watchdog is not overhead - it's insurance against wasted time.**

---

**Created**: 2025-10-18  
**Last Updated**: 2025-10-18  
**Applies To**: ALL projects, ALL platforms, ALL AI agents  
**Status**: ACTIVE REASONING FRAMEWORK

