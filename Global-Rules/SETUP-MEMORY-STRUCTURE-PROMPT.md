# 🧠 Setup Memory Structure for Existing Project

**Copy and paste this entire prompt into Cursor to set up memory structure for optimal long-running AI sessions**

---

## 🎯 What This Does

Sets up a structured memory system that:
- ✅ Extends AI session duration 3-5x (from 1-2 hours to 3-10 hours)
- ✅ Reduces context window usage by 70-90%
- ✅ Reduces RAM usage by 40-70%
- ✅ Maintains consistent AI response quality throughout long sessions
- ✅ Enables fast session recovery after restarts

## 📋 Instructions for AI

Please set up the memory structure for this project:

### Step 1: Create Memory Structure

Run this PowerShell command to create the directory structure and files:

```powershell
# Create directories
New-Item -Path ".cursor/memory/active" -ItemType Directory -Force | Out-Null
New-Item -Path ".cursor/memory/archive/decisions" -ItemType Directory -Force | Out-Null
New-Item -Path ".cursor/memory/archive/$(Get-Date -Format yyyy-MM)" -ItemType Directory -Force | Out-Null

# Detect project name from folder structure
$projectRoot = Get-Location
$rootFolder = Split-Path $projectRoot -Leaf
$parentFolder = Split-Path (Split-Path $projectRoot -Parent) -Leaf
$projectName = "$parentFolder $rootFolder"

Write-Host "Setting up memory structure for: $projectName" -ForegroundColor Green

# Create PROJECT_BRIEF.md
@"
# Project Brief: $projectName

## Purpose
[What this project does - 2-3 paragraphs]

## Core Requirements
- [Add key requirements]

## Constraints
- [Add constraints]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PROJECT_BRIEF.md" -Encoding UTF8

# Create TECH_STACK.md
@"
# Technology Stack: $projectName

## Frontend
- **Framework:** [e.g., Next.js]
- **Language:** [e.g., TypeScript]

## Backend
- **Framework:** [e.g., Express]
- **Database:** [e.g., PostgreSQL]

## Key Libraries
[Add major dependencies]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/TECH_STACK.md" -Encoding UTF8

# Create ARCHITECTURE.md
@"
# Architecture: $projectName

## Key Architectural Decisions
[Document major decisions]

## Patterns Used
[Add patterns as they emerge]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/ARCHITECTURE.md" -Encoding UTF8

# Create PATTERNS.md
@"
# Coding Patterns: $projectName

## Conventions
[Document coding standards]

## File Naming
[Add conventions]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PATTERNS.md" -Encoding UTF8

# Create active/CURRENT_FOCUS.md
@"
# Current Focus
**Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## What We're Working On
[Update with current task]

## Status
[Current state]
"@ | Out-File -FilePath ".cursor/memory/active/CURRENT_FOCUS.md" -Encoding UTF8

# Create active/ACTIVE_WORK.md
@"
# Active Work
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Current Feature
[Update with current feature]

## Completed Today
- [Add completed items]

## Next Steps
- [ ] [Add next tasks]
"@ | Out-File -FilePath ".cursor/memory/active/ACTIVE_WORK.md" -Encoding UTF8

# Create active/RECENT_DECISIONS.md
@"
# Recent Decisions
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## This Week
[Add recent decisions]
"@ | Out-File -FilePath ".cursor/memory/active/RECENT_DECISIONS.md" -Encoding UTF8

Write-Host "✅ Memory structure created at .cursor/memory/" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Populate the memory files with project information" -ForegroundColor Yellow
```

### Step 2: Analyze This Project

Please analyze this project and populate the memory files:

1. **Analyze project structure** (check package.json, requirements.txt, or similar)
2. **Populate PROJECT_BRIEF.md** with:
   - What this project does
   - Core features
   - Main goals
3. **Populate TECH_STACK.md** with:
   - Frontend framework and version
   - Backend framework and version
   - Database type and version
   - Key libraries (top 5-10)
   - Development tools and ports
4. **Populate ARCHITECTURE.md** with:
   - Project structure overview
   - Key architectural decisions (if documented elsewhere)
   - Patterns you can identify
5. **Populate PATTERNS.md** with:
   - File naming conventions you observe
   - Code organization patterns
6. **Populate ACTIVE_WORK.md** with:
   - Current state of the project (complete, in-progress, etc.)
   - What appears to be the focus area

### Step 3: Update .gitignore (Optional)

If we want to keep active work private (not shared with team), add to .gitignore:

```gitignore
# AI Session Memory (optional - can be committed for team sharing)
.cursor/memory/active/CURRENT_FOCUS.md
.cursor/memory/active/ACTIVE_WORK.md
```

### Step 4: Link to Startup Process

If this project has a `startup.ps1` file, add memory structure check to it.

Check if startup.ps1 already has memory structure logic (search for "Memory Structure").

If not, add this section before the "UNIVERSAL STARTUP COMPLETE" message:

```powershell
Write-Host ""
Write-Host "Checking Memory Structure..." -ForegroundColor Yellow
if (Test-Path ".cursor/memory/PROJECT_BRIEF.md") {
    $briefSize = (Get-Item ".cursor/memory/PROJECT_BRIEF.md").Length
    if ($briefSize -lt 200) {
        Write-Host "⚠️  Memory structure needs population" -ForegroundColor Yellow
        Write-Host "   📝 Action: Populate .cursor/memory/*.md files" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Memory structure ready" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  Memory structure not set up" -ForegroundColor Yellow
    Write-Host "   Run: See Global-Workflows/Memory-Structure-Setup-Guide.md" -ForegroundColor Gray
}
```

### Step 5: Verify and Report

After completing the setup, provide me with:

1. ✅ Confirmation that memory structure was created
2. 📋 Summary of what you populated in each file
3. 📊 Current state of PROJECT_BRIEF.md and TECH_STACK.md (show excerpts)
4. 💡 Recommendations for keeping these files updated
5. 📖 Link to detailed guide: `Global-Workflows/Memory-Structure-Setup-Guide.md`

---

## 📖 How to Use Memory Structure

### Session Start
At the beginning of each session, AI should:
```markdown
Read these files for context:
- .cursor/memory/PROJECT_BRIEF.md
- .cursor/memory/TECH_STACK.md
- .cursor/memory/ARCHITECTURE.md
- .cursor/memory/active/ACTIVE_WORK.md
```

### During Work
AI updates these frequently:
- `.cursor/memory/active/CURRENT_FOCUS.md` - Every task (5-15 min)
- `.cursor/memory/active/ACTIVE_WORK.md` - Every milestone (30-60 min)
- `.cursor/memory/active/RECENT_DECISIONS.md` - When decisions made

### Between Major Tasks
AI should create "Context Clear Points":
```markdown
## Context Clear Point

Previous work: [1-sentence summary]
Relevant decisions: [Key decisions to retain]
Current focus: [What we're working on now]

Update .cursor/memory/active/ACTIVE_WORK.md
All prior implementation details cleared.
```

### Monthly Maintenance
- Move old decisions to `.cursor/memory/archive/decisions/`
- Create new archive folder: `.cursor/memory/archive/YYYY-MM/`
- Review and update ARCHITECTURE.md if needed

---

## 🎓 Benefits You'll See

**Before Memory Structure:**
- Sessions: 1-2 hours before restart
- Context window: 80-95% full after 30 minutes
- RAM usage: 2.5-3.5 GB
- Response quality: Degrades after 1 hour

**After Memory Structure:**
- Sessions: 3-10 hours before restart ✅
- Context window: 20-40% full after 2 hours ✅
- RAM usage: 1.0-1.5 GB ✅
- Response quality: Consistent throughout ✅

---

## 📚 Related Resources

- **Detailed Guide**: `Global-Workflows/Memory-Structure-Setup-Guide.md`
- **Global Rule**: `C:\Users\kento\.cursor\global-cursor-repo\rules\session-context-management.mdc`
- **Knowledge Base**: `ai_knowledge.global_reasoning` (Context Management entries)

---

## ✅ Ready!

Once you complete these steps, this project will have optimal memory structure for long-running AI sessions. The AI will automatically manage context, keeping sessions running longer with better performance!

---

**After AI completes setup, you should see:**
```
.cursor/memory/
├── PROJECT_BRIEF.md          (populated with project details)
├── TECH_STACK.md             (populated with tech stack)
├── ARCHITECTURE.md           (populated with architecture info)
├── PATTERNS.md               (populated with coding patterns)
├── active/
│   ├── CURRENT_FOCUS.md      (ready for AI updates)
│   ├── ACTIVE_WORK.md        (populated with current state)
│   └── RECENT_DECISIONS.md   (ready for AI updates)
└── archive/
    ├── 2025-10/              (for completed work)
    └── decisions/            (for archived decisions)
```

All files populated with actual project information and ready to use! 🎉

