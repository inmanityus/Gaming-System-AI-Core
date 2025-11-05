# Updated Git Policies - GitHub Push Mandatory
**Date**: January 29, 2025  
**Status**: ⚠️ **POLICY CHANGE** - All Git workflows updated

---

## 🚨 POLICY CHANGE SUMMARY

### Previous Policy
- ❌ "local only — never push"
- ❌ Commits stayed local only
- ❌ No GitHub integration

### NEW Policy (MANDATORY)
- ✅ **ALL commits MUST be pushed to GitHub**
- ✅ **Private repo auto-created if none exists**
- ✅ **GitHub push is part of every commit workflow**

---

## UPDATED WORKFLOWS

### 1. Standard Commit Workflow (UPDATED)

**OLD**:
```powershell
git add -A
git commit -m "chore(cursor): <summary> [chat:<topic>]"
# ❌ No push
```

**NEW**:
```powershell
git add -A
git commit -m "chore(cursor): <summary> [chat:<topic>]"
# ✅ ALWAYS push
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-push-to-github.ps1"
```

**Or use wrapper** (recommended):
```powershell
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-commit-and-push.ps1" -Message "chore(cursor): <summary> [chat:<topic>]"
```

---

### 2. Milestone Completion (UPDATED)

**Updated in**: `Global-Workflows/Autonomous-Development-Protocol.md`

```powershell
git add -A
git commit -m "chore(cursor): Milestone [N]: [Name] - [Brief description] [chat:milestone-[N]]"
# ✅ NEW: Always push
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-push-to-github.ps1"
```

---

### 3. Session Handoff (UPDATED)

**Updated in**: `Global-Workflows/session-handoff-protocol.md`

```powershell
git add .project-memory/history/SESSION-HANDOFF-[DATE].md
git add .cursor/memory/active/*.md
# ✅ NEW: Use wrapper that auto-pushes
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-commit-and-push.ps1" -Message "chore(cursor): session handoff for [date] - [brief description] [chat:session-handoff]"
```

---

### 4. Feature Completion (UPDATED)

**Updated in**: `Global-Workflows/FIXED-Autonomous-Completion-Protocol.md`

All completion checklists now include:
- ✅ Git commits made with proper messages
- ✅ **Git commits pushed to GitHub (private repo created if needed)** ⭐ **NEW**

---

## AUTO-REPO CREATION

### How It Works

If no GitHub remote exists:
1. ✅ Script checks GitHub CLI (`gh`)
2. ✅ Verifies authentication
3. ✅ Creates **PRIVATE** repository automatically
4. ✅ Connects local repo to GitHub
5. ✅ Pushes all commits

### Repository Details
- **Privacy**: Always PRIVATE
- **Naming**: Uses project directory name (sanitized)
- **Description**: Extracted from README or defaults

---

## GLOBAL SCRIPTS CREATED

### 1. `Global-Scripts/git-push-to-github.ps1`
- Pushes to GitHub
- Creates private repo if needed
- Handles authentication

### 2. `Global-Scripts/git-commit-and-push.ps1`
- Wrapper: commit + push in one command
- Easier to use
- Recommended for new workflows

---

## UPDATED FILES

### Global Workflows (Updated)
- ✅ `Global-Workflows/git-with-github-push.mdc` - **NEW** comprehensive rule
- ✅ `Global-Workflows/Autonomous-Development-Protocol.md`
- ✅ `Global-Workflows/FIXED-Autonomous-Development-Protocol.md`
- ✅ `Global-Workflows/FIXED-Autonomous-Completion-Protocol.md`
- ✅ `Global-Workflows/session-handoff-protocol.md`
- ✅ `Global-Workflows/autonomous-completion-protocol.mdc`

### Global Scripts (Created)
- ✅ `Global-Scripts/git-push-to-github.ps1`
- ✅ `Global-Scripts/git-commit-and-push.ps1`

---

## ENFORCEMENT

### Where This Applies

✅ **ALL Projects** - Universal rule  
✅ **Project-level commits**  
✅ **Global workflow commits**  
✅ **Session handoffs**  
✅ **Milestone completions**  
✅ **Feature completions**

### Violation Handling

If commit made without push:
- Script should detect and push automatically
- Warning displayed if push fails
- Manual intervention required if GitHub setup incomplete

---

## MIGRATION GUIDE

### For Existing Projects

1. **Check if GitHub remote exists**:
   ```powershell
   git remote -v
   ```

2. **If no remote**, push will auto-create repo:
   ```powershell
   pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-push-to-github.ps1"
   ```

3. **For future commits**, use new workflow:
   ```powershell
   pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-commit-and-push.ps1" -Message "chore(cursor): <message> [chat:<topic>]"
   ```

---

## EXAMPLES

### Standard Workflow
```powershell
# Before (OLD - NO LONGER VALID):
git add -A
git commit -m "message"
# ❌ Stops here

# After (NEW - MANDATORY):
git add -A
git commit -m "chore(cursor): message [chat:topic]"
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-push-to-github.ps1"
# ✅ Always pushes
```

### Using Wrapper (EASIEST)
```powershell
# One command does everything:
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-commit-and-push.ps1" -Message "chore(cursor): message [chat:topic]"
```

---

## SECURITY REMINDER

✅ **Still Protected**:
- `.env` files NEVER committed (`.gitignore`)
- Sensitive data excluded
- Private repos only
- API keys never exposed

---

## SUMMARY

**Policy Change**: From "local only" to "push to GitHub always"

**Implementation**:
- ✅ New global script: `git-push-to-github.ps1`
- ✅ New wrapper: `git-commit-and-push.ps1`
- ✅ Updated all workflow documents
- ✅ Auto-repo creation for new projects
- ✅ Always creates PRIVATE repos

**Status**: ✅ **ACTIVE** - All Git workflows updated

---

**Next**: All future commits will automatically push to GitHub

