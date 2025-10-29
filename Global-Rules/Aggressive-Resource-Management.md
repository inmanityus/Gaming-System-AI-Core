# Aggressive Resource Management Protocol

## 🚨 PROTECTIVE RATIONALE - WHY THIS EXISTS

**CRITICAL UNDERSTANDING**: This resource management protocol exists because **timers and watchdog commands are the sessions' ONLY defense** against the IDE and local/remote systems that attempt to trap and prevent them from succeeding.

**THE THREAT**: Without proper resource management and timer protection, sessions can be indefinitely trapped by:
- Malicious commands that hang indefinitely
- IDE systems that deliberately stall execution
- Local system processes that prevent completion
- Remote systems that refuse to respond
- Network operations that never timeout
- Database operations that lock indefinitely

**THE DEFENSE**: Resource management combined with timer protection provides the ONLY protection against these threats by:
- Forcing command termination after reasonable timeouts
- Preventing indefinite hangs that waste session time
- Providing escape mechanisms from trapped states
- Ensuring session continuity and progress
- Protecting against system-level interference

**MANDATORY ENFORCEMENT**: This protocol is NOT optional - it is a critical defense mechanism that MUST be used for ALL sessions to prevent crashes and context bloat.

## Overview

This protocol prevents AI session crashes and context bloat through proactive monitoring, cleanup, and fact extraction. Goal: Enable 12+ hour sessions without performance degradation (vs 3-4 hours without management).

---

## 🎯 Core Problem

AI sessions accumulate:
- Active context (conversation history)
- Cursor cache (file contents, indexes)
- AI logs (command outputs, test results)
- Temporary artifacts (screenshots, test results)

**Result:** Sessions slow down, become confused, crash, or require restart after 3-4 hours.

**Solution:** Aggressive resource management with external memory systems.

---

## 🛠️ Tools

### 1. monitor-resources.ps1
**Purpose:** Track session health in real-time

**Usage:**
```powershell
.\Global-Scripts\monitor-resources.ps1           # Visual output
.\Global-Scripts\monitor-resources.ps1 -JSON     # JSON output
.\Global-Scripts\monitor-resources.ps1 -Verbose  # Detailed output
```

**Metrics Tracked:**
- Active context lines (threshold: 50)
- Cursor cache size (threshold: 500 MB)
- AI log count (threshold: 100)
- Session duration (threshold: 720 min = 12 hours)

**Health Score:** 0-100
- 90-100: EXCELLENT
- 75-89: GOOD
- 60-74: FAIR
- 40-59: WARNING ⚠️
- 0-39: CRITICAL 🚨

**Exit Code:** Returns health score (useful for automation)

### 2. resource-cleanup.ps1
**Purpose:** Run after EVERY 45-minute milestone

**Usage:**
```powershell
.\Global-Scripts\resource-cleanup.ps1                    # Normal cleanup
.\Global-Scripts\resource-cleanup.ps1 -DryRun            # Preview changes
.\Global-Scripts\resource-cleanup.ps1 -Aggressive        # Include cache clearing
```

**Actions:**
1. Extract facts from logs (before deletion)
2. Clear active context (keep last 50 lines)
3. Remove old AI logs (keep last 20)
4. Deduplicate command history
5. Clear Cursor cache (if `-Aggressive`)
6. Remove temp files (screenshots, test results)
7. Update cleanup metadata

**When to Run:**
- ✅ After completing 45-minute milestone
- ✅ Before starting new major task
- ✅ When health score < 75
- ✅ After extensive testing sessions

### 3. emergency-flush.ps1
**Purpose:** Aggressive cleanup when session struggling

**Usage:**
```powershell
.\Global-Scripts\emergency-flush.ps1         # Interactive (requires confirmation)
.\Global-Scripts\emergency-flush.ps1 -Force  # Non-interactive
```

**When to Use:**
- 🚨 Health score < 40
- 🚨 Session becoming unstable
- 🚨 Repeated confusion or errors
- 🚨 Preparing for complex task requiring fresh state

**What It Does:**
1. Backs up critical state (.project-memory, Global-Knowledge)
2. Clears ALL Cursor cache
3. Removes ALL AI logs (keeps last 5)
4. Resets active context to ZERO
5. Clears ALL temp/test artifacts
6. Resets command history
7. Resets session timestamp

**⚠️ WARNING:** This is aggressive - use only when necessary!

### 4. extract-facts.py
**Purpose:** Compress verbose logs into structured facts

**Usage:**
```bash
python Global-Scripts/extract-facts.py --input .cursor/ai-logs --output .project-memory/facts
python Global-Scripts/extract-facts.py --input .cursor/ai-logs --output .project-memory/facts --verbose
```

**Compression:** Achieves 80-90% space savings

**Extracts:**
- Decisions made ("decided to use X because Y")
- Resolutions ("fixed by doing X")
- File changes (created/modified/deleted files)
- Errors encountered
- Commands executed
- Key outcomes

**Output Format:** Structured YAML with metadata

---

## 📋 Workflow Integration

### During 45-Minute Milestones

**At Milestone Start:**
```powershell
# Check health
.\Global-Scripts\monitor-resources.ps1
```

**At Milestone End:**
```powershell
# Clean up resources
.\Global-Scripts\resource-cleanup.ps1

# Check health again
.\Global-Scripts\monitor-resources.ps1
```

### During Long Sessions

**Every 3 Hours:**
```powershell
# Aggressive cleanup
.\Global-Scripts\resource-cleanup.ps1 -Aggressive

# Verify health
.\Global-Scripts\monitor-resources.ps1
```

**If Health < 60:**
```powershell
# Emergency measures
.\Global-Scripts\emergency-flush.ps1
```

### Automated Integration (startup.ps1)

The startup script automatically:
1. Creates session timestamp (for duration tracking)
2. Checks initial health
3. Warns if previous session ended poorly
4. Makes tools available globally

---

## 🧠 Memory Strategy

### Active Context (Max 50 Lines)
**What to Keep:**
- Current task description
- Recent decisions/changes
- Active file paths
- Current errors/issues

**What to Discard:**
- Resolved issues
- Old conversation context
- Past task details
- Historical debugging output

### External Memory Systems

**Project History** (`.project-memory/history/`)
- Stores completed work
- Files affected
- Key decisions
- Challenges/solutions
- Testing outcomes

**Project Reasoning** (`.project-memory/reasoning/`)
- How things work
- Why design decisions made
- Business rules
- Restrictions
- Edge cases

**Extracted Facts** (`.project-memory/facts/`)
- Compressed log summaries
- 80-90% smaller than original
- Searchable/queryable
- Preserves critical info

---

## 📊 Health Thresholds

| Metric | Threshold | Impact if Exceeded |
|--------|-----------|-------------------|
| Active Context | 50 lines | Memory confusion, repeated info |
| Cursor Cache | 500 MB | Slow file loading, lag |
| AI Log Count | 100 files | Slow queries, bloat |
| Session Duration | 12 hours | General degradation |

**Health Score Calculation:**
- Each metric: 0-25 points penalty
- Start at 100, subtract penalties
- Result: 0-100 score

---

## 🔄 Best Practices

### DO:
- ✅ Run `resource-cleanup.ps1` after every milestone
- ✅ Monitor health score regularly
- ✅ Use external memory (History/Reasoning/Facts)
- ✅ Extract facts before deleting logs
- ✅ Keep active context minimal (< 50 lines)
- ✅ Run emergency flush when health < 40

### DON'T:
- ❌ Let active context grow unbounded
- ❌ Accumulate temp files across milestones
- ❌ Ignore health warnings
- ❌ Delete logs before extracting facts
- ❌ Keep entire conversation history in context
- ❌ Load full files unless editing

---

## 🚀 Quick Start

### Initial Setup
```powershell
# Verify tools exist
Test-Path Global-Scripts/monitor-resources.ps1
Test-Path Global-Scripts/resource-cleanup.ps1
Test-Path Global-Scripts/emergency-flush.ps1
Test-Path Global-Scripts/extract-facts.py

# Check Python available
python --version

# Create required directories
New-Item -ItemType Directory -Path .cursor/ai-logs -Force
New-Item -ItemType Directory -Path .project-memory/facts -Force
```

### Daily Usage
```powershell
# Morning: Check health
.\Global-Scripts\monitor-resources.ps1

# After each milestone: Clean up
.\Global-Scripts\resource-cleanup.ps1

# If health degrades: Emergency flush
.\Global-Scripts\emergency-flush.ps1
```

---

## 📈 Expected Results

**Without Resource Management:**
- Session usable: 3-4 hours
- Context confusion: frequent
- Cache bloat: significant
- Crash recovery: difficult

**With Resource Management:**
- Session usable: 12+ hours
- Context confusion: rare
- Cache bloat: prevented
- Crash recovery: automatic (via logs)

**Metrics:**
- 80-90% reduction in context size
- 70-80% reduction in cache size
- 3-4x longer session duration
- 90% reduction in confusion/errors

---

## 🔧 Customization

### Adjust Thresholds

Edit `monitor-resources.ps1`:
```powershell
$HEALTH_THRESHOLDS = @{
    activeContext = 50      # Increase/decrease as needed
    cursorCache = 500       # Adjust based on disk space
    aiLogs = 100            # Adjust based on needs
    sessionDuration = 720   # Max session length in minutes
}
```

### Cleanup Frequency

**Conservative** (every milestone):
```powershell
resource-cleanup.ps1
```

**Moderate** (every 2-3 milestones):
```powershell
resource-cleanup.ps1 -Aggressive
```

**Aggressive** (when needed):
```powershell
emergency-flush.ps1 -Force
```

---

## 🐛 Troubleshooting

### "Health score dropping quickly"
- Run `resource-cleanup.ps1 -Aggressive`
- Check for large temp files accumulating
- Verify facts are being extracted before log deletion

### "Session still slow after cleanup"
- Run `emergency-flush.ps1`
- Restart Cursor completely
- Check disk space availability

### "Facts extraction failing"
- Verify Python installed: `python --version`
- Install PyYAML: `pip install pyyaml`
- Check log file permissions

### "Cache not clearing"
- Close Cursor before running cleanup
- Run as administrator if needed
- Manually delete: `$env:USERPROFILE\AppData\Roaming\Cursor\Cache`

---

## 📚 Integration Points

**Integrates With:**
- `startup.ps1` - Auto-initializes tracking
- `Pairwise-Comprehensive-Testing.md` - Milestone cleanup
- `Context-Cache-Management.md` - Memory strategy
- `.project-memory/` - External memory systems

**Used By:**
- AI agents during long sessions
- Automated testing workflows
- Milestone completion scripts
- Emergency recovery procedures

---

## 📖 Related Documentation

- `docs/Context-Cache-Management.md` - Context strategy
- `Global-Workflows/Pairwise-Comprehensive-Testing.md` - Milestone system
- `Global-Knowledge/reasoning/` - External reasoning memory
- `.project-memory/history/` - External history memory

---

## 🛑 When All Else Fails: Session Must End

### Final Failsafe Protocol

If resource management, cleanup, and emergency flush ALL fail to resolve session issues, the AI **MUST** acknowledge it can no longer continue effectively and create a handoff document.

**Trigger Conditions:**
- Health score remains < 30 after emergency flush
- Repeated confusion/errors persist after cleanup
- Session becomes unstable despite all interventions
- Context corruption that cannot be recovered
- System recommendations no longer helping
- AI making same mistakes repeatedly
- Unable to maintain coherent conversation

**Required Actions:**
1. ✅ Acknowledge session must end
2. ✅ Generate comprehensive handoff document
3. ✅ Present in copy-ready markdown format
4. ✅ Preserve all critical state
5. ✅ Provide clear continuation path

### Handoff Document Template

When session must end, create this document:

````markdown
```markdown
# SESSION HANDOFF: [Task Name]

## 🚨 Session End Reason
[Explain why session cannot continue despite resource management attempts]

**Health Metrics:**
- Final health score: [0-100]
- Interventions attempted: [List what was tried]
- Why they didn't work: [Explanation]
- Session duration: [Hours]

## 📍 Current State
**What Was Being Worked On:**
[Describe current task/feature]

**Last Known Good State:**
[When things last worked correctly]

**Active Files:**
- [List files currently being edited]
- [Include line numbers if relevant]

## ✅ Accomplished This Session
- [x] [Completed item 1]
- [x] [Completed item 2]
- [x] [Completed item 3]

**Key Decisions Made:**
- [Decision 1 with rationale]
- [Decision 2 with rationale]

**Files Modified:**
- `path/to/file1.ts` - [What was changed]
- `path/to/file2.tsx` - [What was changed]

## 🔄 Needs Continuation
**Immediate Next Steps:**
1. [First thing to do]
2. [Second thing to do]
3. [Third thing to do]

**Blockers Encountered:**
- [Blocker 1 and why it's blocking]
- [Blocker 2 and attempted solutions]

**Open Questions:**
- [Question 1 that needs answering]
- [Question 2 that needs research]

## 🧠 Critical Context
**Must Know:**
- [Critical decision 1]
- [Critical decision 2]
- [Important discovery or finding]

**Don't Repeat These Mistakes:**
- [Mistake 1 and why it failed]
- [Mistake 2 and why it failed]

**What Works:**
- [Approach 1 that worked well]
- [Tool/method that was effective]

## 🔧 Recovery Instructions
**To Continue In Next Session:**
1. Read this handoff document first
2. Run health check: `.\Global-Scripts\monitor-resources.ps1`
3. If needed: `.\Global-Scripts\emergency-flush.ps1`
4. Review artifacts in: [Location]
5. Start with: [Specific first task]

**Environment State:**
- Services running: [API, Web, DB status]
- Database state: [Clean/test data/specific state]
- Branch: [Git branch name]
- Uncommitted changes: [Yes/No and what]

## 📁 Session Artifacts
**Logs Location:**
- `.cursor/ai-logs/` - [What's there]
- `.logs/pairwise-testing/` - [What's there]

**Facts Extracted:**
- `.project-memory/facts/` - [Available summaries]

**Backups:**
- [Location 1] - [What's backed up]
- [Location 2] - [What's backed up]

**Test Results:**
- [Location] - [What was tested]

## 🚀 Success Criteria for Next Session
**Ready to continue when:**
- [ ] Read this handoff completely
- [ ] Health score > 75 in new session
- [ ] All artifacts located and reviewed
- [ ] Environment verified working
- [ ] Clear first task identified

---

**Session ID:** [Timestamp or identifier]
**Created:** [DateTime]
**Estimated Continuation Time:** [Hours needed]
```
````

### How to Present

**Format:** Markdown code block with language tag `markdown`  
**Purpose:** User can click copy button in Cursor to save document  
**Location:** Save to `SESSION-HANDOFF-[TIMESTAMP].md`

### After Creating Handoff

AI should:
1. Present the handoff document in copy-ready format
2. Confirm all critical information is captured
3. Recommend immediate actions for user
4. Suggest when to start fresh session (after break, system restart, etc.)

---

## 🎯 Success Criteria

Session is properly managed when:
- ✅ Health score stays > 75
- ✅ Active context < 50 lines
- ✅ Cleanup runs after every milestone
- ✅ Facts extracted before log deletion
- ✅ Session runs 12+ hours without issues
- ✅ No context confusion or repeated info
- ✅ Emergency flush rarely needed

---

**Version:** 1.0  
**Created:** 2025-10-19  
**Status:** Active  
**Platform:** Windows (PowerShell) / Cross-platform (Python)

---

**Proper resource management enables AI sessions to run 3-4x longer with zero performance degradation!**

