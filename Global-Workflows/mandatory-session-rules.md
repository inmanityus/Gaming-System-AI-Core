# Mandatory Session Rules

**Status**: ✅ **ACTIVE**  
**Enforcement**: **MANDATORY - No Exceptions**  
**Applies To**: ALL AI sessions across ALL projects

---

## 🚨 RULE 1: TIMER SERVICE - MANDATORY CONTINUOUS OPERATION

### Critical Requirement
**ALWAYS use the Timer Service continuously throughout the session to prevent being trapped by IDE stalls, command hangs, or system failures.**

### Why This Rule Exists
- **IDE Protection**: Timers are the sessions' ONLY defense against IDE stalls and system traps
- **Command Protection**: Prevents commands from hanging indefinitely
- **Session Continuity**: Ensures sessions remain responsive and can recover from failures
- **Resource Management**: Prevents resource leaks from orphaned processes

### Mandatory Implementation

#### 1. Timer Service Must Run Continuously
- Timer Service MUST start immediately after `/start-right` completes
- Timer Service MUST run throughout the entire session
- Timer Service MUST NOT be stopped until session shutdown (`/shutdown`)
- Timer Service MUST auto-renew at natural breakpoints (command completion, milestones)

#### 2. Timer Service Cleanup (Before Startup)
- **MANDATORY**: Clean up orphaned timers BEFORE starting new timer service
- **Script**: Run `scripts/cleanup-orphaned-timers-auto.ps1 -AutoClean`
- **When**: During startup process, before timer service initialization
- **Purpose**: Prevents multiple timer services from running simultaneously
- **What it cleans**:
  - Orphaned PowerShell background jobs (timer jobs)
  - Orphaned PowerShell processes (old sessions >2 hours old)
  - Orphaned timer marker files (`.cursor/timer-service.running` older than 2 hours)
  - Old session ID files

#### 3. Timer Service Configuration
- **Default Interval**: 10 minutes (600 seconds)
- **Extended Interval**: 15-60 minutes for long operations
- **Background Operation**: Runs asynchronously via PowerShell background job
- **Marker File**: Creates `.cursor/timer-service.running` to indicate active service
- **Session Tracking**: Stores session info in `.cursor/timer-session-id.txt`

#### 4. Timer Service Health Checks
- **Monitor Status**: Check `Test-Path '.cursor/timer-service.running'`
- **Check Jobs**: Verify with `Get-Job | Where-Object { $_.Name -like '*Timer*' }`
- **Check Processes**: Monitor for orphaned processes with `Get-Process -Name "pwsh","powershell"`
- **Frequency**: Check periodically during long sessions

### Integration Points

#### Startup (`/start-right`)
1. Run cleanup: `scripts/cleanup-orphaned-timers-auto.ps1 -AutoClean`
2. Start timer service via `Global-Workflows/startup-features/timer-service.ps1`
3. Verify timer service is running
4. Display timer service status in session window

#### Command Execution
- Timer service runs independently of commands
- Commands use watchdog wrapper for additional protection
- Timer service provides session-level protection
- Watchdog provides command-level protection

#### Milestone Completion
- Timer service auto-renews at milestone boundaries
- Extends timer duration for next milestone
- Updates marker file to show activity

#### Session Shutdown (`/shutdown`)
1. Stop timer service background job
2. Remove timer marker file
3. Clean up session ID file
4. Verify cleanup complete

### Forbidden Practices
- ❌ **NEVER** manually stop timer service during session
- ❌ **NEVER** run multiple timer services simultaneously
- ❌ **NEVER** skip timer service cleanup before startup
- ❌ **NEVER** bypass timer service initialization
- ❌ **NEVER** ignore orphaned timer cleanup

### Success Criteria
- ✅ Timer service starts immediately after `/start-right`
- ✅ Timer service runs continuously throughout session
- ✅ Timer service auto-renews at appropriate breakpoints
- ✅ No orphaned timer processes exist
- ✅ Timer marker file exists and is current
- ✅ Timer service cleanup completes before new service starts

---

## 🚨 RULE 2: WORK VISIBILITY - MANDATORY SESSION WINDOW DISPLAY

### Critical Requirement
**ALWAYS show your work in the Session Window. No silent operations allowed.**

### Why This Rule Exists
- **IDE Protection**: Visible work prevents IDE stalls by showing active progress
- **User Awareness**: Users can see what the AI is doing at all times
- **Debugging**: Visible output helps identify issues quickly
- **Trust**: Transparent operations build confidence in AI sessions

### Mandatory Implementation

#### 1. Startup Visibility
- **MUST** display current working directory
- **MUST** show startup script execution status
- **MUST** display service health check results
- **MUST** show timer service cleanup results
- **MUST** display timer service initialization status
- **MUST** show environment configuration status

#### 2. Command Execution Visibility
- **MUST** show command being executed
- **MUST** display progress indicators for long operations
- **MUST** show intermediate results
- **MUST** display error messages clearly
- **MUST** show completion status

#### 3. Directory Changes
- **MUST** display current directory when changing locations
- **MUST** show navigation confirmation
- **MUST** verify correct directory after navigation

#### 4. Service Operations
- **MUST** show service check results (database, web, API, MailHog)
- **MUST** display service status clearly
- **MUST** show service startup/shutdown actions

#### 5. Timer Operations
- **MUST** show timer cleanup results
- **MUST** display timer service startup status
- **MUST** show timer renewal events
- **MUST** display timer service health checks

#### 6. Progress Indicators
- **MUST** show milestone progress
- **MUST** display task completion status
- **MUST** show file operations (create, modify, delete)
- **MUST** display testing progress

### Output Requirements

#### Status Messages
```powershell
Write-Host "Current Directory: $(Get-Location)" -ForegroundColor White
Write-Host "Starting timer service cleanup..." -ForegroundColor Yellow
Write-Host "✅ Timer service cleanup complete" -ForegroundColor Green
Write-Host "⏳ Timer service initializing..." -ForegroundColor Cyan
Write-Host "✅ Timer service started (background job)" -ForegroundColor Green
```

#### Progress Indicators
```powershell
Write-Host "[1/5] Checking for orphaned jobs..." -ForegroundColor Yellow
Write-Host "[2/5] Checking for orphaned processes..." -ForegroundColor Yellow
Write-Host "[3/5] Checking timer markers..." -ForegroundColor Yellow
```

#### Error Display
```powershell
Write-Host "⚠️  Warning: Orphaned process detected" -ForegroundColor Yellow
Write-Host "❌ Error: Timer service failed to start" -ForegroundColor Red
```

### Forbidden Practices
- ❌ **NEVER** execute commands silently without output
- ❌ **NEVER** skip status messages during startup
- ❌ **NEVER** hide error messages
- ❌ **NEVER** suppress progress indicators
- ❌ **NEVER** run background operations without status updates

### Success Criteria
- ✅ All startup steps display status messages
- ✅ All commands show execution status
- ✅ All directory changes are displayed
- ✅ All service operations show results
- ✅ All timer operations display status
- ✅ Progress indicators shown for long operations
- ✅ Errors displayed clearly with context

---

## 🚨 RULE 3: RESULTS OUTPUT TIMER - MANDATORY ANTI-STALL PROTECTION

### Critical Requirement
**ALWAYS use a results output timer to prevent stalls when writing out results and milestones. This is a separate timer from the continuous Timer Service.**

### Why This Rule Exists
- **Stall Prevention**: Sessions commonly stall after writing out results, milestones, or completion summaries
- **Continuity Enforcement**: Ensures work continues automatically after outputting results
- **Automatic Recovery**: Timer prompt forces continuation if stall occurs
- **Master Timer Separation**: This timer is separate from the continuous Timer Service which must always run

### Mandatory Implementation

#### 1. Timer Activation (BEFORE Results Output)
- **MANDATORY**: Start a background timer IMMEDIATELY BEFORE writing out any results
- **Applies To**:
  - Results summaries from any effort
  - Next milestone plans
  - Completion summaries
  - Any output that doesn't require user feedback
- **NOT Applies To**: Outputs that require explicit user response/feedback
- **Purpose**: Protects against stall after results output

#### 2. Timer Deactivation (BEFORE Next Command)
- **MANDATORY**: Stop and remove the results output timer AFTER completing all results/next milestone
- **MANDATORY**: Stop timer BEFORE outputting the first command in the session window
- **Timing**: Must happen between results output completion and first new command
- **Cleanup**: Timer must be completely removed (not just stopped)

#### 3. Timer Behavior
- **Master Timer**: Continuous Timer Service (Rule 1) must already be running independently
- **Results Timer**: Separate, temporary timer only for results output protection
- **Stall Detection**: If timer isn't stopped before next command, it MUST prompt to continue work
- **Prompt Message**: Clear message asking if work should continue
- **Auto-Continue**: If no response, automatically continue after brief delay

#### 4. Timer Configuration
- **Interval**: 2-3 minutes (120-180 seconds) - enough to detect stalls but not too long
- **Background Operation**: Runs asynchronously via PowerShell background job
- **Marker File**: Optional marker (`.cursor/results-output-timer.running`) to track active state
- **Cleanup Required**: Timer job must be stopped AND removed

### Integration Points

#### Before Results Output
1. **Check**: Master Timer Service is running (verify `.cursor/timer-service.running`)
2. **Start**: Results output timer (background job)
3. **Verify**: Timer started successfully
4. **Output**: Write all results/summaries/milestones

#### After Results Output (BEFORE Next Command)
1. **Complete**: All results output finished
2. **Stop**: Results output timer (stop background job)
3. **Remove**: Timer job completely removed
4. **Verify**: Timer cleanup confirmed
5. **Continue**: Output first command of next work

#### Stall Detection
- **If Timer Still Running**: When attempting to output first command
- **Action**: Prompt with clear message: "Results output timer still active - continuing work automatically"
- **Auto-Continue**: Proceed with work after 5-second delay
- **Log**: Document stall detection and recovery

### Forbidden Practices
- ❌ **NEVER** forget to start timer before results output
- ❌ **NEVER** forget to stop timer before next command
- ❌ **NEVER** leave results timer running after output complete
- ❌ **NEVER** confuse results timer with master Timer Service
- ❌ **NEVER** skip timer if outputting results without user feedback

### Success Criteria
- ✅ Results output timer starts before every results/milestone output
- ✅ Results output timer stops before first next command
- ✅ Timer cleanup verified after each use
- ✅ Master Timer Service continues running independently
- ✅ No orphaned results timers exist
- ✅ Stall detection works if timer not stopped
- ✅ Automatic continuation after stall detection

### Example Flow
```powershell
# BEFORE writing results
$resultsTimer = Start-Job -ScriptBlock { Start-Sleep -Seconds 180 }
Write-Host "✅ Task completed..."
Write-Host "📋 Next milestone: ..."

# AFTER results complete, BEFORE next command
Stop-Job -Name $resultsTimer.Name -ErrorAction SilentlyContinue
Remove-Job -Name $resultsTimer.Name -ErrorAction SilentlyContinue
Write-Host "⏱️ Results timer stopped"

# NOW output first command of next work
Write-Host "Starting next task..."
```

---

## 🔄 Integration with Startup Process

### Startup Sequence (Mandatory Order)

1. **Root Directory Validation**
   - Display: Current directory location
   - Display: Verification result

2. **Timer Service Cleanup**
   - Run: `scripts/cleanup-orphaned-timers-auto.ps1 -AutoClean`
   - Display: Cleanup results
   - Display: Orphaned items found and cleaned

3. **Startup Script Execution**
   - Display: Startup script running
   - Display: Each startup feature loading

4. **Timer Service Initialization**
   - Display: Timer service initializing
   - Display: Timer service startup status
   - Display: Timer service verification

5. **Work Visibility Confirmation**
   - Display: All startup operations visible
   - Display: Session ready status

---

## 📋 Compliance Checklist

### Timer Service
- [ ] Cleanup script runs before timer service starts
- [ ] Timer service initializes after cleanup
- [ ] Timer service runs continuously
- [ ] Timer service auto-renews appropriately
- [ ] No orphaned timer processes exist
- [ ] Timer marker file is current

### Work Visibility
- [ ] Startup operations display in session window
- [ ] Commands show execution status
- [ ] Directory changes are displayed
- [ ] Service operations show results
- [ ] Progress indicators shown for long operations
- [ ] Errors displayed clearly

### Results Output Timer
- [ ] Results timer starts before every results/milestone output
- [ ] Results timer stops before first next command
- [ ] Timer cleanup verified after each use
- [ ] Master Timer Service continues running independently
- [ ] No orphaned results timers exist
- [ ] Stall detection works if timer not stopped

---

## 🚨 Enforcement

**These rules are MANDATORY and apply to ALL sessions.**

**Violation Consequences**:
- Session review for compliance
- Rule enforcement reminder
- Potential session termination if repeated violations

**Compliance Verification**:
- Startup logs checked for timer service cleanup
- Startup logs checked for work visibility
- Timer service status verified
- Session window output reviewed

---

**Last Updated**: 2025-11-03  
**Status**: ✅ Active  
**Enforcement**: Mandatory



