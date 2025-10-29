# Memory Structure Setup Guide
**For Long-Running AI Sessions with Optimal Context Management**

## 🎯 Purpose

This guide sets up a structured memory system that:
- Extends AI session duration 3-5x (from 1-2 hours to 3-10 hours)
- Reduces context window usage by 70-90%
- Reduces RAM usage by 40-70%
- Maintains consistent AI response quality throughout long sessions
- Provides fast session recovery after restarts

## 📁 Memory Structure Overview

```
.cursor/memory/
├── PROJECT_BRIEF.md          # Stable - What project does (rarely changes)
├── TECH_STACK.md             # Stable - Technologies and why (rarely changes)
├── ARCHITECTURE.md           # Stable - Patterns and decisions (rarely changes)
├── PATTERNS.md               # Stable - Coding standards (rarely changes)
├── active/
│   ├── CURRENT_FOCUS.md      # Volatile - Immediate task (updates constantly)
│   ├── ACTIVE_WORK.md        # Volatile - Current feature (updates frequently)
│   └── RECENT_DECISIONS.md   # Volatile - Last 2-3 milestones (updates frequently)
└── archive/
    ├── 2025-10/              # Historical - Completed work by month
    ├── 2025-11/
    └── decisions/            # Historical - Archived decisions
```

## 🚀 Quick Setup (5 Minutes)

### Step 1: Create Directory Structure

```powershell
# PowerShell (Windows)
mkdir -p .cursor/memory/active
mkdir -p .cursor/memory/archive/decisions
mkdir -p .cursor/memory/archive/$(Get-Date -Format yyyy-MM)

# Create core files
New-Item -Path .cursor/memory/PROJECT_BRIEF.md -ItemType File -Force
New-Item -Path .cursor/memory/TECH_STACK.md -ItemType File -Force
New-Item -Path .cursor/memory/ARCHITECTURE.md -ItemType File -Force
New-Item -Path .cursor/memory/PATTERNS.md -ItemType File -Force
New-Item -Path .cursor/memory/active/CURRENT_FOCUS.md -ItemType File -Force
New-Item -Path .cursor/memory/active/ACTIVE_WORK.md -ItemType File -Force
New-Item -Path .cursor/memory/active/RECENT_DECISIONS.md -ItemType File -Force
```

```bash
# Bash (Unix/Linux/Mac)
mkdir -p .cursor/memory/active
mkdir -p .cursor/memory/archive/decisions
mkdir -p .cursor/memory/archive/$(date +%Y-%m)

# Create core files
touch .cursor/memory/PROJECT_BRIEF.md
touch .cursor/memory/TECH_STACK.md
touch .cursor/memory/ARCHITECTURE.md
touch .cursor/memory/PATTERNS.md
touch .cursor/memory/active/CURRENT_FOCUS.md
touch .cursor/memory/active/ACTIVE_WORK.md
touch .cursor/memory/active/RECENT_DECISIONS.md
```

### Step 2: Populate Initial Content

#### PROJECT_BRIEF.md
```markdown
# Project Brief: [Project Name]

## Purpose
[What this project does - 2-3 paragraphs]

## Core Requirements
- [Key requirement 1]
- [Key requirement 2]
- [Key requirement 3]

## Constraints
- [Technical constraint 1]
- [Business constraint 1]

## Success Criteria
- [Metric 1]
- [Metric 2]

**Last Updated:** [Date]
```

#### TECH_STACK.md
```markdown
# Technology Stack: [Project Name]

## Frontend
- **Framework:** [e.g., Next.js 15]
- **Language:** [e.g., TypeScript]
- **Styling:** [e.g., Tailwind CSS 4.0]
- **Key Libraries:**
  - [Library 1] - [Why chosen]
  - [Library 2] - [Why chosen]

## Backend
- **Framework:** [e.g., Next.js API Routes]
- **Database:** [e.g., PostgreSQL 16]
- **Key Libraries:**
  - [Library 1] - [Why chosen]

## Infrastructure
- **Development:** [e.g., Docker Compose]
- **Production:** [e.g., Vercel / AWS]
- **Email:** [e.g., Nodemailer + MailHog for dev]

## Development Tools
- **Package Manager:** [e.g., npm]
- **Ports:**
  - App: [e.g., 3000]
  - Database: [e.g., 5432]
  - MailHog: [e.g., 8025]

**Last Updated:** [Date]
```

#### ARCHITECTURE.md
```markdown
# Architecture: [Project Name]

## Project Structure
[Brief overview of folder structure]

## Key Architectural Decisions

### Decision 1: [e.g., App Router vs Pages Router]
- **Choice:** [What was chosen]
- **Reason:** [Why chosen]
- **Impact:** [How it affects development]

### Decision 2: [e.g., Database Connection Pooling]
- **Choice:** [What was chosen]
- **Reason:** [Why chosen]
- **Impact:** [How it affects development]

## Patterns Used
- [Pattern 1] - [Where/Why]
- [Pattern 2] - [Where/Why]

## Data Flow
[Brief description of how data flows through the system]

**Last Updated:** [Date]
```

#### PATTERNS.md
```markdown
# Coding Patterns & Standards: [Project Name]

## File Naming
- Components: PascalCase (e.g., `UserProfile.tsx`)
- Utilities: camelCase (e.g., `formatDate.ts`)
- [Other conventions]

## Component Patterns
- [Pattern 1]
- [Pattern 2]

## Error Handling
[How errors are handled in this project]

## Testing Approach
[Testing strategy]

## Code Style
[Any project-specific style guidelines]

**Last Updated:** [Date]
```

#### active/CURRENT_FOCUS.md
```markdown
# Current Focus: [Task Name]
**Updated:** [Timestamp]

## What We're Working On
[Current task in 2-3 sentences]

## Current File/Component
[What we're working in]

## Goal
[What we're trying to achieve]

## Context Needed
- [File/info relevant to THIS task only]

## Status
[Current state, any blockers]
```

#### active/ACTIVE_WORK.md
```markdown
# Active Work: [Feature/Component]
**Last Updated:** [Timestamp]

## Current Feature
[Feature being developed in 2-3 sentences]

## Completed This Session
- [x] [Completed item 1]
- [x] [Completed item 2]

## In Progress
- [ ] [Current task]

## Next Steps
- [ ] [Next task 1]
- [ ] [Next task 2]

## Recent Decisions (Last 2-3 Milestones)
- [Decision 1] - [Date]
- [Decision 2] - [Date]

**Clear older decisions to archive/ folder**
```

#### active/RECENT_DECISIONS.md
```markdown
# Recent Decisions
**Last Updated:** [Timestamp]

## This Week
### [Date] - [Decision Title]
- **Context:** [Why decision was needed]
- **Decision:** [What was decided]
- **Impact:** [How it affects project]

## Last Week
### [Date] - [Decision Title]
- **Context:** [Why decision was needed]
- **Decision:** [What was decided]
- **Impact:** [How it affects project]

**Archive decisions older than 2 weeks to archive/decisions/**
```

### Step 3: Link to Startup Process

Add to your `startup.ps1` or startup script:

```powershell
# Check if memory structure exists, create if not
if (-not (Test-Path ".cursor/memory")) {
    Write-Host "🧠 Creating memory structure for optimal AI sessions..." -ForegroundColor Cyan
    
    # Create directories
    New-Item -Path ".cursor/memory/active" -ItemType Directory -Force | Out-Null
    New-Item -Path ".cursor/memory/archive/decisions" -ItemType Directory -Force | Out-Null
    New-Item -Path ".cursor/memory/archive/$(Get-Date -Format yyyy-MM)" -ItemType Directory -Force | Out-Null
    
    # Create files with templates
    @"
# Project Brief: $projectName

## Purpose
[Document what this project does]

## Core Requirements
- [Add requirements]

## Constraints
- [Add constraints]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PROJECT_BRIEF.md" -Encoding UTF8
    
    @"
# Technology Stack: $projectName

## Frontend
- **Framework:** [e.g., Next.js]
- **Language:** [e.g., TypeScript]

## Backend
- **Framework:** [e.g., Next.js API Routes]
- **Database:** [e.g., PostgreSQL]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/TECH_STACK.md" -Encoding UTF8
    
    @"
# Architecture: $projectName

## Key Architectural Decisions
[Document major decisions]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/ARCHITECTURE.md" -Encoding UTF8
    
    @"
# Coding Patterns: $projectName

## Conventions
[Document coding standards]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PATTERNS.md" -Encoding UTF8
    
    @"
# Current Focus
**Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## What We're Working On
[Update with current task]
"@ | Out-File -FilePath ".cursor/memory/active/CURRENT_FOCUS.md" -Encoding UTF8
    
    @"
# Active Work
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Current Feature
[Update with current feature]

## Next Steps
- [ ] [Add tasks]
"@ | Out-File -FilePath ".cursor/memory/active/ACTIVE_WORK.md" -Encoding UTF8
    
    @"
# Recent Decisions
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## This Week
[Add recent decisions]
"@ | Out-File -FilePath ".cursor/memory/active/RECENT_DECISIONS.md" -Encoding UTF8
    
    Write-Host "✅ Memory structure created!" -ForegroundColor Green
    Write-Host "📝 Please populate .cursor/memory/*.md files with project details" -ForegroundColor Yellow
}

# Display memory structure status
if (Test-Path ".cursor/memory/PROJECT_BRIEF.md") {
    $briefSize = (Get-Item ".cursor/memory/PROJECT_BRIEF.md").Length
    if ($briefSize -lt 100) {
        Write-Host "⚠️  Memory files need population - see .cursor/memory/" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Memory structure ready for optimal AI sessions" -ForegroundColor Green
    }
}
```

### Step 4: Add to .gitignore (REQUIRED)

**IMPORTANT**: Memory files are session-specific and should NOT be committed to git. They will be auto-created by `startup.ps1`.

Add this to your `.gitignore`:

```gitignore
# AI Session Memory (auto-created by startup.ps1)
# These files are session-specific and should not be committed
.cursor/memory/
```

**Why exclude the entire folder?**
- Memory files are AI session-specific
- Different developers have different active work
- Files are auto-created by startup.ps1 on any machine
- Volatile files change constantly
- Prevents git conflicts and noise

**Note**: If your team wants to share PROJECT_BRIEF.md and TECH_STACK.md, you can selectively include them:
```gitignore
# AI Session Memory
.cursor/memory/
# But keep stable documentation
!.cursor/memory/PROJECT_BRIEF.md
!.cursor/memory/TECH_STACK.md
!.cursor/memory/ARCHITECTURE.md
!.cursor/memory/PATTERNS.md
```

However, we recommend excluding everything - `startup.ps1` will recreate them automatically.

## 📖 Usage Patterns

### Session Start Routine

```markdown
AI, please read the following memory files to establish context:
1. .cursor/memory/PROJECT_BRIEF.md
2. .cursor/memory/TECH_STACK.md
3. .cursor/memory/ARCHITECTURE.md
4. .cursor/memory/active/ACTIVE_WORK.md

Then let's continue work on [current task].
```

### During Development

**Update CURRENT_FOCUS every task (5-15 min):**
```markdown
Update .cursor/memory/active/CURRENT_FOCUS.md:
- Task: Implement email validation
- File: auth-service.ts
- Goal: Validate format and check blocklist
```

**Update ACTIVE_WORK every milestone (30-60 min):**
```markdown
Update .cursor/memory/active/ACTIVE_WORK.md:
- Completed: Email validation
- In Progress: Email verification flow
- Next: Password reset
```

### Between Major Tasks (Context Clear)

```markdown
## Context Clear Point

Previous work: Completed user authentication system.
Relevant decisions: Using JWT tokens, 24hr expiry, refresh token strategy.
Current focus: Building admin dashboard.

Update .cursor/memory/active/ACTIVE_WORK.md with new focus.
Archive old decisions to .cursor/memory/archive/decisions/auth-decisions.md

All prior implementation details, error traces, and temporary context cleared.
```

### Session End Routine

```markdown
Before ending session:
1. Update .cursor/memory/active/ACTIVE_WORK.md with progress
2. Update .cursor/memory/active/RECENT_DECISIONS.md with any new decisions
3. If in middle of work, update .cursor/memory/active/CURRENT_FOCUS.md with exact state
4. Archive completed work to .cursor/memory/archive/YYYY-MM/
```

### Monthly Maintenance

```markdown
Monthly cleanup:
1. Review .cursor/memory/active/RECENT_DECISIONS.md
2. Move decisions older than 2 weeks to .cursor/memory/archive/decisions/
3. Create new archive folder: .cursor/memory/archive/YYYY-MM/
4. Review and update ARCHITECTURE.md if patterns changed
5. Update PROJECT_BRIEF.md if scope evolved
```

## 🎯 Benefits Tracking

### Metrics to Monitor

**Before Memory Structure:**
- Session duration: ___ hours
- Context window usage: ___%
- RAM usage: ___ GB
- Restarts per day: ___

**After Memory Structure (2 weeks):**
- Session duration: ___ hours
- Context window usage: ___%
- RAM usage: ___ GB
- Restarts per day: ___

**Expected Improvements:**
- Session duration: 3-5x increase
- Context usage: 70-90% reduction
- RAM usage: 40-70% reduction
- Restarts: 60-80% reduction

## 🔗 Related Resources

- **Global Rule:** `C:\Users\kento\.cursor\global-cursor-repo\rules\session-context-management.mdc`
- **Knowledge Base:** `ai_knowledge.global_reasoning` entries on context management
- **Setup Integration:** `One-Time-New-Project-Setup-Prompt.md`

## ❓ Troubleshooting

### Memory files not being used by AI

**Solution:** Explicitly mention files in prompts:
```markdown
@.cursor/memory/PROJECT_BRIEF.md @.cursor/memory/TECH_STACK.md 
Please use these memory files for context.
```

### Files getting stale

**Solution:** Set calendar reminder for monthly review, or add to milestone checklist.

### Too much in ACTIVE_WORK

**Solution:** Archive completed features to `archive/YYYY-MM/feature-name-completion.md` monthly.

### AI still has old context

**Solution:** Use explicit Context Clear Point statements more frequently (every 2-3 milestones).

---

## 🔒 File Integrity & Accuracy Guidelines

### Maintaining Accuracy

**Critical Rules:**
1. **Update timestamps** when modifying any memory file
2. **Review monthly** - Set recurring reminder to verify accuracy
3. **Archive outdated info** - Don't let stale data accumulate
4. **Single source of truth** - Memory files should match reality
5. **AI responsibility** - AI should maintain volatile files automatically

### Integrity Checks

**Quarterly Review Checklist:**
- [ ] PROJECT_BRIEF.md reflects current project scope
- [ ] TECH_STACK.md lists actual technologies in use
- [ ] ARCHITECTURE.md documents current patterns (not deprecated)
- [ ] PATTERNS.md matches current code conventions
- [ ] ACTIVE_WORK.md is up to date
- [ ] Archive folder organized by month
- [ ] No duplicate or contradictory information

### Automatic Maintenance

**What AI Should Do:**
- ✅ Update CURRENT_FOCUS.md every task
- ✅ Update ACTIVE_WORK.md every milestone
- ✅ Update RECENT_DECISIONS.md when decisions made
- ✅ Archive old decisions automatically
- ✅ Detect stale information and flag for review
- ✅ Maintain timestamp accuracy

**What Developer Should Do:**
- ✅ Review stable files monthly
- ✅ Update ARCHITECTURE.md when patterns change
- ✅ Update TECH_STACK.md when dependencies change
- ✅ Update PROJECT_BRIEF.md if scope evolves
- ✅ Clean archive folder annually

### Validation Commands

**Check file freshness:**
```powershell
# Show files older than 30 days
Get-ChildItem .cursor/memory/*.md | Where-Object { 
    $_.LastWriteTime -lt (Get-Date).AddDays(-30) 
} | Select-Object Name, LastWriteTime
```

**Verify file sizes (detect empty/incomplete):**
```powershell
# Show files smaller than 200 bytes
Get-ChildItem .cursor/memory -Recurse -File | Where-Object { 
    $_.Length -lt 200 
} | Select-Object FullName, Length
```

**Check for TODO/FIXME markers:**
```powershell
# Find placeholder text that needs updating
Get-ChildItem .cursor/memory -Recurse -File | Select-String "\[.*\]|\.\.\.|TODO|FIXME|PLACEHOLDER"
```

### Corruption Prevention

**Best Practices:**
- ✅ Use UTF-8 encoding for all files
- ✅ Avoid manual edits during AI sessions (let AI maintain)
- ✅ Use git to track changes in stable files (if not excluded)
- ✅ Keep backups of populated templates
- ✅ Don't copy-paste from other projects without updating

### Recovery Procedure

**If memory files become corrupted or inaccurate:**

1. **Backup existing files** (even if corrupt):
   ```powershell
   Copy-Item .cursor/memory .cursor/memory-backup-$(Get-Date -Format yyyyMMdd) -Recurse
   ```

2. **Delete corrupted files**:
   ```powershell
   Remove-Item .cursor/memory -Recurse -Force
   ```

3. **Recreate with startup script**:
   ```powershell
   .\startup.ps1
   ```

4. **Repopulate manually or use AI**:
   - Copy PROJECT_BRIEF from backup if it was accurate
   - Copy TECH_STACK from backup if it was accurate
   - Let AI analyze project and populate ARCHITECTURE and PATTERNS
   - Start fresh with ACTIVE_WORK and RECENT_DECISIONS

5. **Verify accuracy before continuing**:
   - Read each file
   - Confirm information is current and correct
   - Update timestamps

## 📝 Templates

### Context Clear Point Template
```markdown
## Context Clear Point - [Date/Time]

**Previous Work:** [1-sentence summary]
**Key Decisions:** [List retained decisions]
**Current Focus:** [What we're working on now]

**Actions:**
1. Update .cursor/memory/active/ACTIVE_WORK.md
2. Archive old decisions if > 2 weeks
3. Clear all prior implementation details from conversation

All temporary context cleared. Ready for fresh focus.
```

### Monthly Archive Template
```markdown
# [Feature Name] - Completion Summary
**Date:** [YYYY-MM-DD]
**Duration:** [X weeks]

## What Was Built
[Brief description]

## Key Decisions
- [Decision 1]
- [Decision 2]

## Files Modified
- [File 1]
- [File 2]

## Lessons Learned
- [Learning 1]
- [Learning 2]

## Next Steps (if any)
- [Item 1]
```

---

**This structure is now part of your global workflow system and integrates with startup automation!**

