# 🚫 No Summaries Until Work Complete - Global Rule

**Rule ID**: GLOBAL-NO-SUMMARIES  
**Applies To**: ALL projects  
**Enforcement**: MANDATORY  
**Added**: 2025-11-09

---

## THE RULE

**NO summaries, status updates, or substantial output to session window until ALL work is 100% completed.**

**Only show**:
- Ongoing commands
- Command results
- Brief progress indicators

**When work is 100% complete**: THEN write final comprehensive summary.

---

## WHY THIS RULE EXISTS

**Problem**: File acceptance dialogs block AI progress  
**Solution**: Minimize file creation during work, batch accept after changes  
**Benefit**: Uninterrupted autonomous work

---

## IMPLEMENTATION

### During Work:
```
✅ Show: Commands and results
✅ Show: "Continuing..." / "Working on X..."
❌ Hide: Comprehensive summaries
❌ Hide: Status reports
❌ Hide: Milestone reports (until end)
```

### After File Changes:
```powershell
# Run immediately after creating/editing files
pwsh -ExecutionPolicy Bypass -File "C:\Users\kento\.cursor\start-accept-burst.ps1"
```

### When 100% Complete:
```
✅ Write comprehensive final summary
✅ Include all accomplishments
✅ Document all issues found/fixed
✅ Provide complete status
```

---

## APPLIES TO ALL PROJECTS

This is a GLOBAL rule in Global-Rules/ folder.  
All AI agents across all projects must follow this.

---

**Effective**: Immediately  
**Enforcement**: Mandatory  
**Applies**: Globally

