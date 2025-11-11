# Context Window Monitoring - Global Rule

## Overview

This global rule automatically monitors context window size throughout AI sessions and triggers cleanup/handoff when the context exceeds 60% of maximum capacity. This rule is integrated into the shared startup process used by all projects.

## 🚨 CRITICAL RULE - MANDATORY ENFORCEMENT

### **CONTEXT WINDOW THRESHOLD - 60% RULE**

**RULE**: When context window size exceeds 60% of maximum capacity, MANDATORY actions MUST be taken automatically.

## Enforcement Process

### **Step 1: Continuous Monitoring**
- System continuously monitors context window size throughout the session
- Monitoring runs as a background process initialized during startup
- Check interval: Every 5 minutes (300 seconds)
- Monitoring never stops during active session

### **Step 2: Threshold Detection (≥ 60%)**
When context exceeds 60% threshold:
- **IMMEDIATE ACTION**: Execute `/clean-session` command automatically
- **NO DELAY**: Cleanup happens immediately, no waiting for user
- **NO EXCEPTIONS**: This rule applies to ALL sessions, ALL projects
- **NO USER INPUT REQUIRED**: System enforces automatically

### **Step 3: Post-Cleanup Verification**
After `/clean-session` completes:
- **Check Context Again**: Verify context window size after cleanup
- **If Still ≥ 60%**: Execute `/handoff` command immediately
- **Session Transfer**: Create handoff document and transfer to new session
- **NO DELAY**: Handoff happens immediately if threshold still exceeded

## Threshold Levels

- **< 60%**: Normal operation, continue monitoring
- **≥ 60%**: Trigger `/clean-session` immediately
- **Still ≥ 60% after cleanup**: Trigger `/handoff` immediately

## Integration Points

### **Startup Integration**
- **Feature File**: `Global-Workflows/startup-features/context-window-monitor.ps1`
- **Initialization**: Runs automatically during startup process
- **Function**: `Initialize-ContextWindowMonitor`
- **Status**: Active in all projects using shared startup

### **Cleanup Integration**
- **Command**: `/clean-session`
- **Trigger**: Automatic when context ≥ 60%
- **Process**: Executes full cleanup including memory construct reset
- **Verification**: Checks context after cleanup completes

### **Handoff Integration**
- **Command**: `/handoff`
- **Trigger**: Automatic if context still ≥ 60% after cleanup
- **Process**: Creates handoff document and transfers session
- **Purpose**: Prevents session instability from excessive context

## Implementation Details

### **Monitoring Script**
- **Location**: `.cursor/context-window-monitor.ps1`
- **Execution**: Background PowerShell job
- **Interval**: 5 minutes (300 seconds)
- **Marker File**: `.cursor/context-monitor.running`
- **Last Check File**: `.cursor/context-last-check.json`

### **Trigger Files**
- **Cleanup Trigger**: `.cursor/trigger-clean-session.flag`
- **Handoff Trigger**: `.cursor/trigger-handoff.flag`
- **Cleanup Complete**: `.cursor/cleanup-complete.flag`

### **Rules File**
- **Location**: `.cursor/context-window-rules.md`
- **Purpose**: Documents monitoring rules and thresholds
- **Reference**: Used for rule enforcement and documentation

## Enforcement Characteristics

### **MANDATORY**
- This rule is NON-NEGOTIABLE
- Applies to ALL sessions, ALL projects
- No exceptions allowed

### **AUTOMATIC**
- No user approval required
- System enforces automatically
- No manual intervention needed

### **IMMEDIATE**
- No delays allowed
- Actions happen immediately when threshold exceeded
- No waiting for user input

### **CONTINUOUS**
- Monitoring never stops during session
- Background process runs throughout session
- Checks happen every 5 minutes

## Purpose

- **Prevents Context Bloat**: Stops context from growing too large
- **Maintains Session Stability**: Prevents crashes from excessive context
- **Ensures Optimal Performance**: Keeps context at manageable levels
- **Automatic Management**: No manual intervention required

## Success Criteria

- ✅ Context monitor initialized during startup
- ✅ Background monitoring process running
- ✅ Threshold detection working correctly
- ✅ `/clean-session` triggered automatically at 60%
- ✅ `/handoff` triggered automatically if still > 60% after cleanup
- ✅ Monitoring continues throughout session
- ✅ Rules file created and accessible
- ✅ Trigger files created when thresholds exceeded

## Critical Reminders

**MANDATORY**:
- ✅ Context monitoring MUST be active in all sessions
- ✅ Cleanup MUST trigger automatically at 60% threshold
- ✅ Handoff MUST trigger if context still > 60% after cleanup
- ✅ Monitoring MUST continue throughout entire session
- ✅ NO exceptions to threshold enforcement

**FORBIDDEN**:
- ❌ Disabling context monitoring
- ❌ Ignoring threshold violations
- ❌ Delaying cleanup/handoff actions
- ❌ Requiring user approval for threshold actions
- ❌ Stopping monitoring during session

## Related Commands

- **`/clean-session`**: Executed automatically when context ≥ 60%
- **`/handoff`**: Executed automatically if context still ≥ 60% after cleanup
- **`/use-memory-construct`**: Used during cleanup to reset memory constructs
- **`/start-right`**: Initializes context monitoring during startup

## Technical Notes

### **Context Measurement**
- Current implementation uses file-based heuristics
- Future enhancement: Use actual Cursor API context measurement
- Indicators: Active files, log files, memory files

### **Background Job**
- Runs as PowerShell background job
- Job ID saved to `.cursor/context-monitor-job-id.txt`
- Can be monitored via `Get-Job` command

### **Error Handling**
- Monitoring continues even if errors occur
- Errors logged but don't stop monitoring
- Automatic retry on next check interval

---

**This rule is integrated into the shared startup process and applies to ALL projects automatically.**

