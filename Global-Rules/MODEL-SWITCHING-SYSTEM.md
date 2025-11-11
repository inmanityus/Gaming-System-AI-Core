# Model Switching System for Rule Violations

## Overview
This system automatically monitors AI model compliance with mandatory session requirements and switches to alternative models when violations are detected.

## Model Switching Command

### Usage
Type `/switch-model <reason>` to manually switch models or trigger automatic switching.

### Examples
- `/switch-model "watchdog violation"` - Switch due to watchdog command violation
- `/switch-model "peer coding skipped"` - Switch due to peer coding violation
- `/switch-model "testing incomplete"` - Switch due to testing violation
- `/switch-model "knowledge not saved"` - Switch due to knowledge saving violation

## Automatic Model Switching Triggers

### Critical Violations (Immediate Switch)
1. **Watchdog Command Violation**
   - Command executed without `universal-watchdog.ps1` protection
   - System call, remote call, MCP server call without timeout protection
   - Database operation without watchdog wrapper

2. **Peer Coding Violation**
   - Code used without peer review process
   - Code deployed without second model approval
   - Code modified without final inspection

3. **Testing Violation**
   - Testing skipped or incomplete
   - Tests not passing 100%
   - Frontend testing without Playwright
   - Test coverage less than 100%

4. **Knowledge Saving Violation**
   - Learning not saved to memory systems
   - Discovery not documented
   - Solution not archived

5. **Resource Management Violation**
   - Resource cleanup not performed
   - Session health not monitored
   - Memory optimization ignored

6. **Completion Standard Violation**
   - Partial completion reported as "done"
   - "Core functionality completed" reported
   - "Minor bugs remaining" accepted

## Model Hierarchy and Fallback

### Primary Models (In Order of Preference)
1. **Claude Sonnet 4.5** - Primary model for complex tasks
2. **GPT-4** - Secondary model for peer review
3. **Gemini 2.5 Flash** - Tertiary model for testing
4. **DeepSeek Coder** - Fallback model for coding tasks

### Switching Logic
- **First Violation**: Warning logged, model continues
- **Second Violation**: Switch to next model in hierarchy
- **Third Violation**: Switch to tertiary model
- **Fourth Violation**: Switch to fallback model
- **Fifth Violation**: Session termination with handoff

## Implementation

### Model Switching Script
```powershell
# Global-Scripts/switch-model.ps1
param(
    [string]$Reason,
    [string]$ViolationType,
    [switch]$Force
)

# Model hierarchy
$modelHierarchy = @(
    "Claude Sonnet 4.5",
    "GPT-4", 
    "Gemini 2.5 Flash",
    "DeepSeek Coder"
)

# Get current model and violation count
$currentModel = $env:CURSOR_CURRENT_MODEL
$violationCount = $env:CURSOR_MODEL_VIOLATIONS

# Determine next model
$currentIndex = $modelHierarchy.IndexOf($currentModel)
if ($currentIndex -eq -1) { $currentIndex = 0 }

if ($violationCount -ge 4) {
    Write-Host "CRITICAL: Maximum violations reached. Terminating session." -ForegroundColor Red
    # Create handoff document
    # Terminate session
} else {
    $nextModel = $modelHierarchy[$currentIndex + 1]
    Write-Host "SWITCHING MODEL: $currentModel → $nextModel" -ForegroundColor Yellow
    Write-Host "Reason: $Reason" -ForegroundColor Yellow
    Write-Host "Violation Type: $ViolationType" -ForegroundColor Yellow
    
    # Update environment variables
    $env:CURSOR_CURRENT_MODEL = $nextModel
    $env:CURSOR_MODEL_VIOLATIONS = $violationCount + 1
    
    # Log violation
    $logEntry = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        PreviousModel = $currentModel
        NewModel = $nextModel
        Reason = $Reason
        ViolationType = $ViolationType
        ViolationCount = $violationCount + 1
    }
    
    $logPath = ".logs/model-switching/$(Get-Date -Format 'yyyy-MM-dd').json"
    New-Item -ItemType Directory -Force -Path (Split-Path $logPath)
    $logEntry | ConvertTo-Json | Add-Content $logPath
}
```

### Violation Detection Script
```powershell
# Global-Scripts/detect-violations.ps1
param(
    [string]$Command,
    [string]$Context
)

$violations = @()

# Check for watchdog violation
if ($Command -notmatch "universal-watchdog\.ps1" -and 
    ($Command -match "(system|remote|mcp|database|file)" -or 
     $Command -match "(npm|pnpm|yarn|git|docker)")) {
    $violations += "WATCHDOG_VIOLATION"
}

# Check for peer coding violation
if ($Context -match "code.*without.*review" -or 
    $Context -match "deploy.*without.*approval") {
    $violations += "PEER_CODING_VIOLATION"
}

# Check for testing violation
if ($Context -match "test.*skip" -or 
    $Context -match "test.*incomplete" -or
    $Context -match "test.*fail") {
    $violations += "TESTING_VIOLATION"
}

# Check for knowledge saving violation
if ($Context -match "learning.*not.*save" -or 
    $Context -match "discovery.*not.*document") {
    $violations += "KNOWLEDGE_SAVING_VIOLATION"
}

# Check for completion violation
if ($Context -match "core.*functionality.*complete" -or 
    $Context -match "95.*done" -or
    $Context -match "minor.*bug") {
    $violations += "COMPLETION_VIOLATION"
}

return $violations
```

## Integration with Existing System

### Startup Process Integration
```powershell
# Add to startup.ps1
Write-Host "Loading Model Switching System..." -ForegroundColor Green
if (Test-Path "Global-Scripts\switch-model.ps1") {
    Write-Host "✓ Model Switching System: ACTIVE" -ForegroundColor Green
    Write-Host "  → Automatic model switching on rule violations" -ForegroundColor White
    Write-Host "  → Model hierarchy: Claude → GPT-4 → Gemini → DeepSeek" -ForegroundColor White
    Write-Host "  → Violation tracking and logging enabled" -ForegroundColor White
} else {
    Write-Host "WARNING: Model switching system not found" -ForegroundColor Yellow
}

# Initialize model tracking
$env:CURSOR_CURRENT_MODEL = "Claude Sonnet 4.5"
$env:CURSOR_MODEL_VIOLATIONS = 0
```

### Command File Integration
Add to all command files:
```markdown
### 🔄 **MODEL SWITCHING - MANDATORY**
- **Rule**: Model will be automatically switched if rules are violated
- **Triggers**: Watchdog violations, peer coding violations, testing violations, knowledge saving violations, completion violations
- **Process**: First violation = warning, Second = switch to GPT-4, Third = switch to Gemini, Fourth = switch to DeepSeek, Fifth = session termination
- **Enforcement**: Automatic switching with violation logging
```

## Monitoring and Logging

### Violation Log Format
```json
{
  "timestamp": "2025-01-17 14:30:25 UTC",
  "previousModel": "Claude Sonnet 4.5",
  "newModel": "GPT-4",
  "reason": "watchdog violation",
  "violationType": "WATCHDOG_VIOLATION",
  "violationCount": 2,
  "command": "npm run build",
  "context": "Build command executed without watchdog protection"
}
```

### Session Handoff Document
When maximum violations are reached:
```markdown
# SESSION TERMINATION - MODEL SWITCHING EXHAUSTED

## Termination Reason
Maximum model violations reached (5 violations). All models in hierarchy have violated mandatory session requirements.

## Violation History
1. Violation 1: Watchdog command violation
2. Violation 2: Peer coding violation  
3. Violation 3: Testing violation
4. Violation 4: Knowledge saving violation
5. Violation 5: Completion standard violation

## Current State
- Task: [Current task description]
- Progress: [Current progress]
- Files Modified: [List of modified files]
- Issues Remaining: [List of remaining issues]

## Recovery Instructions
1. Review violation log: `.logs/model-switching/[date].json`
2. Identify root cause of violations
3. Restart session with corrected approach
4. Ensure all mandatory requirements are followed
```

## Success Criteria

### Model Switching is Working When:
- ✅ Violations are automatically detected
- ✅ Models are switched according to hierarchy
- ✅ Violations are logged with timestamps
- ✅ Session terminates after maximum violations
- ✅ Handoff document is created for recovery
- ✅ All command files include switching rules
- ✅ Startup process initializes switching system

## Critical Rules Summary

1. **AUTOMATIC DETECTION**: System automatically detects rule violations
2. **HIERARCHICAL SWITCHING**: Models switched in predefined order
3. **VIOLATION LOGGING**: All violations logged with context
4. **SESSION TERMINATION**: Maximum violations result in session termination
5. **HANDOFF PREPARATION**: Complete handoff document created for recovery
6. **INTEGRATION**: System integrated into all command files and startup process

**FAILURE TO FOLLOW MANDATORY REQUIREMENTS RESULTS IN AUTOMATIC MODEL SWITCHING**
