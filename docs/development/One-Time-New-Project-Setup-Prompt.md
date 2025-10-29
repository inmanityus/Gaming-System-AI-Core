# 🚀 One-Time New Project Setup Prompt

**PURPOSE**: Use this prompt when starting ANY new project to automatically set up Ken's optimized development environment with all best practices, global rules, and essential scripts.

---

## 📋 HOW TO USE THIS PROMPT

1. **Open Cursor** in your new project directory
2. **Copy this ENTIRE file** and paste it into Cursor chat
3. **Answer the questions** about your project when prompted
4. **Let the AI do the rest** - it will set everything up automatically

That's it! The AI will handle all the setup steps.

---

## 🤖 PROMPT STARTS HERE (Copy everything below this line)

---

Hello! I need you to set up this new project for me. Please follow these steps:

## 🚨 CRITICAL: PowerShell Rules & Crash Prevention

**BEFORE STARTING ANY SETUP**, follow these rules to prevent crashes and connection failures:

### PowerShell Execution Rules
1. **ALWAYS use PowerShell syntax** - You are running in PowerShell, not bash
2. **Use proper PowerShell commands**:
   - `Get-Location` (not `pwd`)
   - `Get-ChildItem` (not `ls`)
   - `New-Item` (not `mkdir`)
   - `Test-Path` (not `test`)
   - `Write-Host` (not `echo`)

### Crash Prevention Measures
1. **Use Command Watchdog Protocol** for any command that could take > 5 seconds:
   ```powershell
   pwsh -File scripts\cursor_run.ps1 -TimeoutSec 900 -Label "setup-task" -- <actual command>
   ```

2. **Avoid these crash-causing patterns**:
   - ❌ Don't run `npm install` directly (use watchdog)
   - ❌ Don't run `npm run build` directly (use watchdog)
   - ❌ Don't run long-running commands without timeout
   - ❌ Don't use bash syntax in PowerShell

3. **If Setup-Global-Junctions.ps1 fails**:
   - Check for syntax errors (missing braces)
   - **CRITICAL FIX**: If script is empty or corrupted, recreate it manually
   - Recreate the script if corrupted
   - Run with `-Force` flag
   - Verify PowerShell execution policy

4. **Connection Failure Recovery**:
   - If connection drops, restart Cursor completely
   - Don't try to resume mid-setup
   - Start fresh with this prompt
   - Use shorter, simpler commands

5. **Manual Junction Creation** (if script fails):
   ```powershell
   # If Setup-Global-Junctions.ps1 fails, create junctions manually:
   New-Item -ItemType Junction -Path "Global-Reasoning" -Target "C:\Users\kento\.cursor\global-cursor-repo\reasoning" -Force
   New-Item -ItemType Junction -Path "Global-History" -Target "C:\Users\kento\.cursor\global-cursor-repo\history" -Force
   New-Item -ItemType Junction -Path "Global-Scripts" -Target "C:\Users\kento\.cursor\global-cursor-repo\scripts" -Force
   New-Item -ItemType Junction -Path "Global-Workflows" -Target "C:\Users\kento\.cursor\global-cursor-repo\rules" -Force
   New-Item -ItemType Junction -Path "Global-Docs" -Target "C:\Users\kento\.cursor\global-cursor-repo\docs" -Force
   New-Item -ItemType Junction -Path "Global-Utils" -Target "C:\Users\kento\.cursor\global-cursor-repo\utils" -Force
   ```

### Safe Command Examples
```powershell
# ✅ CORRECT - PowerShell syntax
Get-Location
Get-ChildItem -Directory
Test-Path "scripts\Setup-Global-Junctions.ps1"

# ✅ CORRECT - With watchdog for long commands
pwsh -File scripts\cursor_run.ps1 -TimeoutSec 600 -Label "npm-install" -- npm install

# ❌ WRONG - Bash syntax in PowerShell
pwd
ls -la
mkdir -p folder
```

## 📚 LESSONS LEARNED FROM DRONE SENTINELS SETUP (2025-10-22)

### Critical Issues Discovered and Fixed:

1. **Empty Setup-Global-Junctions.ps1 Script**:
   - **Problem**: Script was completely empty (0 bytes)
   - **Solution**: Created complete script with proper error handling
   - **Prevention**: Always verify script content before running

2. **Manual Junction Creation Required**:
   - **Problem**: Script failed silently without output
   - **Solution**: Manual PowerShell commands work reliably
   - **Command**: `New-Item -ItemType Junction -Path "Global-*" -Target "C:\Users\kento\.cursor\global-cursor-repo\*" -Force`

3. **PowerShell Command Verification**:
   - **Problem**: Commands appeared to run but produced no output
   - **Solution**: Use explicit `Write-Host` for verification
   - **Best Practice**: Always verify results with `Get-ChildItem | Where-Object { $_.Name -like "Global-*" }`

4. **Project Configuration Auto-Detection**:
   - **Success**: Folder structure detection worked perfectly
   - **Pattern**: `[ParentFolder]-[RootFolder]` → `Drone-Sentinels-Comms-System`
   - **Database**: `parentfolder_rootfolder` → `drone_sentinels_comms_system`

5. **Memory Structure Creation**:
   - **Success**: All memory files created and populated successfully
   - **Benefit**: Immediate AI session optimization
   - **Files**: PROJECT_BRIEF.md, TECH_STACK.md, ARCHITECTURE.md, PATTERNS.md, active/*

6. **Essential Files Creation**:
   - **Success**: All required files created with proper content
   - **Note**: `.env.example` blocked by globalIgnore - use project-config.md instead
   - **Files**: .gitignore, .cursorrules, README.md, project-config.md, project-services.md

7. **Script Updates Required**:
   - **safe-kill-servers.ps1**: Updated project name and ports
   - **startup.ps1**: Updated database port (5432) and API URL (3000)
   - **Critical**: Always update existing scripts for new project

### Improved Setup Process:
1. **Verify Script Content**: Check if Setup-Global-Junctions.ps1 has content
2. **Manual Fallback**: Use manual PowerShell commands if script fails
3. **Explicit Verification**: Always verify junctions were created
4. **Project-Specific Updates**: Update all scripts with correct project details
5. **Comprehensive Testing**: Verify all components before declaring complete

### Success Metrics:
- ✅ All 6 Global-* junctions created successfully
- ✅ All 7 memory files created and populated
- ✅ All 6 essential files created with proper content
- ✅ All 2 essential scripts updated for project
- ✅ Complete verification passed

---

## Step 1: Link Global Repository (CRITICAL - DO THIS FIRST!)

**This is the MOST IMPORTANT step - it links the shared global Cursor repository to this project.**

Run this command immediately:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force
```

**What this does**:
- Creates Windows junction links (like symlinks) to the shared global repository
- All projects share ONE global repository at: `C:\Users\kento\.cursor\global-cursor-repo\`
- Junctions created:
  - `Global-Reasoning` → global-cursor-repo\reasoning\ (universal patterns/approaches)
  - `Global-History` → global-cursor-repo\history\ (universal solutions/fixes)
  - `Global-Scripts` → global-cursor-repo\scripts\ (reusable scripts)
  - `Global-Workflows` → global-cursor-repo\rules\ (workflow templates/protocols)
  - `Global-Docs` → global-cursor-repo\docs\ (comprehensive documentation)
  - `Global-Utils` → global-cursor-repo\utils\ (utility functions)
  - `Global-Testing-Framework` → global-cursor-repo\testing\ (testing patterns and learnings)

**Expected output**:
```
✓ Created: Global-Reasoning → C:\Users\kento\.cursor\global-cursor-repo\reasoning
✓ Created: Global-History → C:\Users\kento\.cursor\global-cursor-repo\history
✓ Created: Global-Scripts → C:\Users\kento\.cursor\global-cursor-repo\scripts
✓ Created: Global-Workflows → C:\Users\kento\.cursor\global-cursor-repo\rules
✓ Created: Global-Docs → C:\Users\kento\.cursor\global-cursor-repo\docs
✓ Created: Global-Utils → C:\Users\kento\.cursor\global-cursor-repo\utils
✓ Created: Global-Testing-Framework → C:\Users\kento\.cursor\global-cursor-repo\testing
✅ Global Junctions Setup Complete!
```

**⚠️ CRITICAL**: If you don't run this step, the project won't have access to:
- Shared reasoning/patterns across all projects
- Universal history of solutions/fixes
- Reusable scripts (resource management, MCP protection, etc.)
- Standard workflows and protocols (testing, security, deployment)
- Comprehensive documentation (AI systems, deployment, integrations)
- Utility functions and helpers

**Note:** Junctions appear as folders but link to external repository. They should be added to `.gitignore`.

---

## Step 1.5: Script Location Verification (CRITICAL - Prevents Crashes)

**🚨 CRITICAL**: Before running ANY scripts or file operations, ALWAYS verify you are in the project root directory. This verification prevents "script not found" errors that crash sessions.

### Verification Process

**The AI must verify project root before proceeding:**

```powershell
# Verify root directory before any operations
Write-Host "[VERIFY] Verifying project root directory..." -ForegroundColor Cyan
$currentDir = Get-Location
Write-Host "Current directory: $currentDir" -ForegroundColor White

# Required files that must exist in project root
$requiredFiles = @("startup.ps1", "package.json")
$requiredDirs = @("scripts", "Global-Scripts")
$allPresent = $true

# Check required files
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "[OK] Found: $file" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Missing: $file" -ForegroundColor Red
        $allPresent = $false
    }
}

# Check required directories (at least one should exist)
$anyDirFound = $false
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "[OK] Found: $dir/" -ForegroundColor Green
        $anyDirFound = $true
    }
}

if (-not $allPresent) {
    Write-Host "[ERROR] Not in project root - some required files missing" -ForegroundColor Red
    Write-Host "[ACTION] Navigate to project root before proceeding" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Root directory verified - proceeding" -ForegroundColor Green
```

### Why This Is Critical

**Problem**: Sessions often get lost in subdirectories or wrong paths, causing:
- "Script not found" errors when calling scripts
- "File does not exist" errors when accessing project files
- Session crashes when scripts can't be located
- Failed operations due to incorrect working directory

**Solution**: Always verify root directory before:
- Running any scripts
- Accessing project files
- Creating new files
- Running commands that depend on file paths

### Integration with Startup Script

The `startup.ps1` script now includes this verification process automatically. It will:
1. Check if you're in the project root
2. Verify required files exist
3. Attempt to navigate to root if needed
4. Display clear error messages if root cannot be found
5. Proceed safely once verified

**This verification is now built into the universal startup process.**

---

## Step 2: Detect Project Name and Configuration

**Auto-detect the project name** from folder structure:
- If project root is `Website` and parent folder is `Be Free Fitness`, project name is `Be-Free-Fitness-Website`
- If project root is `API` and parent folder is `Project X`, project name is `Project-X-API`
- Format: `[ParentFolder]-[RootFolder]` with spaces replaced by hyphens, lowercase

**Then ask me these questions:**
1. Is the detected project name correct: [auto-detected name]?
2. **What type of project is this?** (This is CRITICAL for proper setup)
   - Web Application (Frontend + Backend)
   - Deep Learning System (AI/ML focused)
   - Mobile Application
   - API-Only Service
   - Full-Stack Monorepo
   - Data Science Project
   - Desktop Application
   - Other (please specify)
3. What technology stack are you using?
   - Frontend: (Next.js, React, Vue, etc.)
   - Backend: (Node.js/Express, Python, etc.)
   - Database: (PostgreSQL, MySQL, MongoDB, etc.)
   - AI/ML: (TensorFlow, PyTorch, OpenAI API, etc.)
4. What ports should the services use?
   - Frontend port (default: 3000)
   - Backend port (default: 4000)
   - Database port (default: 5432)
   - Other services?

**🚨 CRITICAL PORT RULE**: Before assigning ANY port, check `Global-Docs/Occupied-Ports.md` and ensure your chosen ports are at least 10 ports away from any occupied port. Update the Occupied-Ports.md file immediately after port assignment.

**Wait for my answers before proceeding.**

### Port Management Process
1. **Check Global Registry**: Read `Global-Docs/Occupied-Ports.md`
2. **Identify Conflicts**: Look for ports within 10-port range of occupied ports
3. **Choose Safe Ports**: Select ports with 10+ gap from any occupied port
4. **Update Registry**: Add new port assignments to Occupied-Ports.md
5. **Document in Project**: Update project-services.md with correct ports

**Example Port Assignment**:
- If ports 3000, 4000, 5000, 8888 are occupied
- Choose ports like 3010, 4010, 5010, 8890 (10+ ports away)
- Update both Global-Docs/Occupied-Ports.md and project files

### Environment Configuration Rules
1. **Always create .env.example** with proper structure:
   - Database Configuration (PostgreSQL only)
   - Application Environment (PORT, NODE_ENV)
   - Development URLs (DEV_URL with correct port)
   - Production URLs (PROD_URL)
   - AI/ML Configuration (for future features)
   - Security settings
   - External Services (as needed)
   - Notes section with project-specific rules

2. **Port Configuration**:
   - PORT=3010 (or chosen frontend port)
   - DEV_URL=http://localhost:3010 (match PORT)
   - DB_PORT=5443 (or chosen database port)

3. **Database Rule**: Always use PostgreSQL database for these projects

4. **Notes Section**: Include project-specific rules and port reservations

---

## Step 3: Verify Global Junctions

After running the setup command, verify these junctions exist:
- ✅ `Global-Reasoning/` (junction → global-cursor-repo\reasoning\)
- ✅ `Global-History/` (junction → global-cursor-repo\history\)
- ✅ `Global-Scripts/` (junction → global-cursor-repo\scripts\)
- ✅ `Global-Workflows/` (junction → global-cursor-repo\rules\)
- ✅ `Global-Docs/` (junction → global-cursor-repo\docs\)
- ✅ `Global-Utils/` (junction → global-cursor-repo\utils\)
- ✅ `Global-Testing-Framework/` (junction → global-cursor-repo\testing\)

**Verify command:**
```powershell
Get-ChildItem -Directory | Where-Object { $_.LinkType -eq "Junction" } | Select-Object Name, Target
```

If any are missing, the setup failed. Try running with `-Force` again.

---

## Step 3.5: Set Up Memory Structure for Long-Running Sessions

**🧠 IMPORTANT**: Set up the memory structure for optimal AI session performance.

**What this does**:
- Extends AI session duration 3-5x (from 1-2 hours to 3-10 hours)
- Reduces context window usage by 70-90%
- Reduces RAM usage by 40-70%
- Maintains consistent AI response quality

**Quick Setup** (automated):

The startup script will automatically create the memory structure. Alternatively, create it now:

```powershell
# Create memory structure
New-Item -Path ".cursor/memory/active" -ItemType Directory -Force | Out-Null
New-Item -Path ".cursor/memory/archive/decisions" -ItemType Directory -Force | Out-Null
New-Item -Path ".cursor/memory/archive/$(Get-Date -Format yyyy-MM)" -ItemType Directory -Force | Out-Null

# Create memory files with templates
@"
# Project Brief: [PROJECT_NAME]

## Purpose
[What this project does - 2-3 paragraphs]

## Core Requirements
- [Add key requirements]

## Constraints
- [Add constraints]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/PROJECT_BRIEF.md" -Encoding UTF8

@"
# Technology Stack: [PROJECT_NAME]

## Frontend
- **Framework:** [e.g., Next.js]
- **Language:** [e.g., TypeScript]

## Backend
- **Framework:** [e.g., Express]
- **Database:** [e.g., PostgreSQL]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/TECH_STACK.md" -Encoding UTF8

@"
# Architecture: [PROJECT_NAME]

## Key Architectural Decisions
[Document major decisions as you make them]

**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File -FilePath ".cursor/memory/ARCHITECTURE.md" -Encoding UTF8

@"
# Coding Patterns: [PROJECT_NAME]

## Conventions
[Document coding standards as they emerge]

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
```

**What was created**:
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
    ├── YYYY-MM/              # Historical - Completed work by month
    └── decisions/            # Historical - Archived decisions
```

**How to use**:
1. **Populate immediately**: Fill in PROJECT_BRIEF.md and TECH_STACK.md with project details
2. **Update during development**: Keep ACTIVE_WORK.md and CURRENT_FOCUS.md current
3. **Archive regularly**: Move completed work to archive/ monthly
4. **Session start**: AI reads stable files (PROJECT_BRIEF, TECH_STACK, ARCHITECTURE)
5. **Session work**: AI updates active files (CURRENT_FOCUS, ACTIVE_WORK)

**For detailed guidance**: See `Global-Workflows/Memory-Structure-Setup-Guide.md`

**⚠️ CRITICAL**: Populate these files! Empty memory files provide no benefit.

---

## Step 4: Create Essential Files

Based on my answers above, create these files:

### 4.1: Update `.gitignore`

**CRITICAL**: Add global junctions and AI memory to .gitignore:
```gitignore
# Global repository junctions (link to C:\Users\kento\.cursor\global-cursor-repo\)
# These are NOT part of the project - they are Windows junctions to shared global repo
Global-Reasoning/
Global-History/
Global-Scripts/
Global-Workflows/

# AI Session Memory (auto-created by startup.ps1)
# These files are session-specific and should not be committed
.cursor/memory/
.cursor/session-start.txt
.cursor/health-metrics.jsonl
.cursor/last-cleanup.json
```

Plus standard .gitignore for the technology stack:
- node_modules/
- .env files
- logs
- build outputs
- OS files
- IDE files
- .cursor/ directory (except .cursor/.globals_linked marker)

### 4.2: Create/Update `.cursorrules`

Create this file with project-specific configuration:

```markdown
# [PROJECT NAME] - Cursor Rules

## 🌐 Global Repository Linked
Global knowledge and scripts accessed via Windows junctions:
- `Global-Reasoning/` → C:\Users\kento\.cursor\global-cursor-repo\reasoning\
- `Global-History/` → C:\Users\kento\.cursor\global-cursor-repo\history\
- `Global-Scripts/` → C:\Users\kento\.cursor\global-cursor-repo\scripts\
- `Global-Workflows/` → C:\Users\kento\.cursor\global-cursor-repo\rules\
- `Global-Testing-Framework/` → C:\Users\kento\.cursor\global-cursor-repo\testing\

✅ **Shared Across ALL Projects**: Updates in global repo appear everywhere instantly

## 📋 This Project

**Type**: [Web App / Mobile / API / etc.]
**Stack**: [List technologies]

### Ports
- Frontend: [port]
- Backend: [port]
- Database: [port]

### Start Services
```bash
[commands to start services]
```

### Stop Services (MCP-Safe)
```bash
.\scripts\safe-kill-servers.ps1
```

## 🛡️ MCP Protection
**CRITICAL**: Use safe-kill scripts. NEVER: `Get-Process node | Stop-Process`

## 📊 Automated Systems
- 45-minute milestones auto-activate for tasks > 1 hour
- Resource management monitors session health (enables 12+ hour sessions)
- End-user testing with Playwright for web projects
- Context management between features
- Global reasoning/history from shared repository

## 🔄 Managing Global Repository
To recreate junctions (if broken):
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force
```

To update global content (affects ALL projects):
```powershell
# Edit through any project's junction - changes appear everywhere
code "Global-Scripts\monitor-resources.ps1"
```
```

### 4.3: Create `README.md`

Include:
- Project name (auto-detected from folder structure)
- Project description
- **Global repository junction setup** (Step 1!)
- Quick start instructions
- Technology stack
- Available commands
- Port information
- Troubleshooting section
- **MCP protection warnings**
- **Note about Global-* folders being Windows junctions to shared global repo**

### 4.4: Create `.env.example`

Template with:
- Database connection
- Service ports
- API keys (placeholders)
- Development settings

### 4.5: Create `project-config.md`

Document:
- Project name (auto-detected: ParentFolder-RootFolder)
- Technology stack
- Service ports
- Database name (auto-detected: parentfolder_rootfolder lowercase with underscores)
- Database configuration (PostgreSQL on localhost)
- MCP server capabilities
- **Global repository junctions location**

### 4.6: Create `project-services.md`

Document:
- How to start each service
- How to stop services safely
- Health check commands
- Port information
- Troubleshooting TypeScript errors (common issue)

---

## Step 5: Create .env.example with Proper Structure

**CRITICAL**: Always create `.env.example` with the standardized structure for all projects.

### Required .env.example Structure:
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=[chosen-db-port]
DB_NAME=[project-db-name]
DB_USER=postgres
DB_PASSWORD=Inn0vat1on!

# Application Environment
PORT=[chosen-frontend-port]
NODE_ENV=development

# Development URLs
DEV_URL=http://localhost:[chosen-frontend-port]

# Production URLs
PROD_URL=https://your-production-domain.com

# AI/ML Configuration (for future features)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# External Services (for future features)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Email Configuration (for future features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password

# Notes
# - Always use PostgreSQL database for these projects
# - Port [chosen-frontend-port] is reserved for this project's frontend
# - Port [chosen-db-port] is reserved for this project's database
# - Add new sections as needed per project requirements
```

### Key Rules:
1. **Database Rule**: Always use PostgreSQL database for these projects
2. **Port Matching**: DEV_URL port must match PORT value
3. **No API Configuration**: Drop API Configuration section (add as needed per project)
4. **Notes Section**: Always include project-specific rules and port reservations
5. **Template Placeholders**: Use [chosen-port] placeholders for AI to fill in

---

## Step 6: Set Up Scripts

### 6.1: Ensure `scripts/Setup-Global-Junctions.ps1` Exists

This script should already exist in the deployment folder. It creates Windows junctions to link the shared global repository.

### 6.2: Copy Other Template Scripts

If you can access the template folder, copy these files:
- `startup.ps1` → project root
- `universal-watchdog.ps1` → project root

If you cannot access templates, create basic versions.

### 6.3: Create `scripts/safe-kill-servers.ps1`

```powershell
# Safe Server Shutdown with MCP Protection
param([switch]$TestOnly)

Write-Host "🛡️ Stopping [PROJECT NAME] servers (MCP protected)" -ForegroundColor Green

# Define project ports
$projectPorts = @([PORT1], [PORT2], [PORT3])

foreach ($port in $projectPorts) {
    Write-Host "Checking port $port..."
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "  Killing process on port $port" -ForegroundColor Yellow
        Stop-Process -Id $connection.OwningProcess -Force
    }
}

# Verify MCP servers still running
$mcpCount = (Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -match "mcp"
}).Count

Write-Host "✅ Done. MCP servers protected: $mcpCount running" -ForegroundColor Green
```

### 5.4: Create `scripts/protect-mcp-servers.ps1`

Protection script that identifies MCP servers and only kills application servers.

---

## Step 6: Create Directory Structure

Create these directories:
- `.logs/` (with .gitignore inside)
- `.cursor/` (if not exists - created by sync script)
- `scripts/` (if not exists)
- `docs/` (if not exists)

---

## Step 7: Customize Startup Script

If `startup.ps1` exists, ensure it:
- Sets working directory to project root
- Configures environment variables
- Checks service health
- Displays MCP capabilities
- Shows project information
- **Mentions global resources are linked**

---

## Step 8: Verification

Check that these exist:
- ✅ **Global-Reasoning/** (junction → global-cursor-repo\reasoning\) - **MOST IMPORTANT**
- ✅ **Global-History/** (junction → global-cursor-repo\history\)
- ✅ **Global-Scripts/** (junction → global-cursor-repo\scripts\)
- ✅ **Global-Workflows/** (junction → global-cursor-repo\rules\)
- ✅ **.cursor/memory/** (memory structure) - **NEW FOR SESSION OPTIMIZATION**
- ✅ **.cursor/memory/PROJECT_BRIEF.md** (populated)
- ✅ **.cursor/memory/TECH_STACK.md** (populated)
- ✅ **.cursor/memory/active/** (active work tracking)
- ✅ .cursorrules (project-specific config)
- ✅ .gitignore (with Global-* excluded)
- ✅ README.md
- ✅ .env.example
- ✅ project-config.md
- ✅ project-services.md
- ✅ startup.ps1
- ✅ universal-watchdog.ps1
- ✅ scripts/Setup-Global-Junctions.ps1
- ✅ scripts/safe-kill-servers.ps1
- ✅ scripts/protect-mcp-servers.ps1
- ✅ .logs/ directory

---

## Step 9: Generate Setup Report

Create a report showing:
- ✅ What was created
- ✅ What was synced from global resources
- ✅ What was skipped (with reasons)
- ✅ Current project configuration
- ✅ Global resources status
- ✅ Next steps for the developer
- ✅ Important reminders about MCP protection

---

## Step 10: Final Instructions for Developer

Tell me:
1. **Setup is complete!** 🎉
2. **Global repository linked** - Global-* folders are Windows junctions to shared repo
3. **Memory structure created** - .cursor/memory/ for optimal AI sessions
4. **What to do next:**
   - **POPULATE .cursor/memory/PROJECT_BRIEF.md and TECH_STACK.md** (important!)
   - Review and customize `.env.example` → `.env`
   - Install dependencies
   - Run `.\startup.ps1` to verify setup
5. **Critical reminders:**
   - Always use `safe-kill-servers.ps1` to stop services
   - Never kill all node processes (protects MCP servers)
   - **Update .cursor/memory/active/ACTIVE_WORK.md as you work** (extends sessions 3-5x!)
   - 45-minute milestone system with resource management for long sessions
   - Global-* folders are junctions - don't commit them to git
   - Recreate junctions if broken: `.\scripts\Setup-Global-Junctions.ps1 -Force`
   - **After project completion: Extract knowledge to AI repository (see Step 11)**

---

## Step 11: Extract Knowledge to AI Repository (AFTER PROJECT COMPLETION)

**⚠️ IMPORTANT**: This step should be done AFTER the project is functionally complete or when switching to a new project, NOT during initial setup.

### When to Run Knowledge Extraction

Run this when:
- ✅ Project reaches completion or major milestone
- ✅ Switching from this project to another project
- ✅ Core features are implemented and working
- ✅ Significant architectural decisions have been made
- ✅ Important patterns or solutions have been developed

**Do NOT run during initial setup** - there's no knowledge to extract yet!

### What is Knowledge Extraction?

The AI Knowledge Repository is a shared PostgreSQL database (`ai_knowledge`) that stores:
- **Project Reasoning**: HOW things work in this project (architecture, flows, decisions)
- **Project History**: WHAT was accomplished (features, bugs fixed, lessons learned)
- **Global Reasoning**: UNIVERSAL patterns applicable to multiple projects
- **Global History**: UNIVERSAL issues and solutions

This allows AI assistants to learn from past projects and apply that knowledge to future work.

### How to Extract Knowledge

When ready to extract knowledge (after project development):

1. **Read the Knowledge Extraction Guide**:
```
E:\Vibe Code\Be Free Fitness\Website\Global-Workflows\Knowledge-Extraction-Guide.md
```

Or use the quick reference prompt:

```markdown
═══════════════════════════════════════════════════════════════════════════════
KNOWLEDGE EXTRACTION FOR NEW PROJECT
═══════════════════════════════════════════════════════════════════════════════

📖 READ THIS FILE FIRST:
E:\Vibe Code\Be Free Fitness\Website\Global-Workflows\Knowledge-Extraction-Guide.md

Then follow the instructions to extract ALL knowledge from THIS project.

═══════════════════════════════════════════════════════════════════════════════
QUICK REFERENCE
═══════════════════════════════════════════════════════════════════════════════

DATABASE: ai_knowledge on localhost (PostgreSQL)
SHARED: Yes - check for existing entries before adding!

VERIFY ACCESS:
psql -h localhost -U postgres -d ai_knowledge -c "SELECT * FROM knowledge_statistics;"

4 REPOSITORIES:
1. project_reasoning - How THIS project works
2. project_history - What was done in THIS project  
3. global_reasoning - Universal patterns (check & update existing!)
4. global_history - Universal issues (check & update existing!)

EXTRACT FROM:
□ Documentation (docs/ folder)
□ Completion reports (*COMPLETION*.md, *HANDOFF*.md, *REPORT*.md)
□ Logs (.logs/ folder)
□ Code patterns (migrations, middleware, routes, components)
□ Config files (.env.example, docker-compose.yml, package.json)

CRITICAL RULES:
✅ ALWAYS check for existing entries FIRST: SELECT * FROM search_all_knowledge('topic');
✅ UPDATE existing global entries when you have new insights (don't duplicate!)
✅ ADD new project-specific entries
✅ Use SQL templates from: KNOWLEDGE-EXTRACTION-SQL-TEMPLATES.sql

TARGET: 15-25 total entries

═══════════════════════════════════════════════════════════════════════════════

🚀 START: Read the guide file above, then begin extraction!

═══════════════════════════════════════════════════════════════════════════════
```

### What the AI Will Extract

The AI will systematically extract:

**From Documentation**:
- Architecture decisions
- Authentication flows
- API structures
- Database schemas
- Deployment processes

**From Completion Reports**:
- Features created
- Bugs fixed
- Performance optimizations
- Security implementations

**From Code Patterns**:
- Project-specific patterns
- Universal patterns (if applicable to 2+ projects)
- Reusable components
- Utility functions

**From Configuration**:
- Service architectures
- Technology stack decisions
- Port allocations
- Environment setup

### Expected Output

The AI will:
1. Read all documentation and completion reports
2. Check for existing similar entries (avoid duplicates)
3. Add 15-25 new entries to the knowledge database:
   - 7-10 project_reasoning entries (architecture, flows, decisions)
   - 5-8 project_history entries (features, fixes, lessons)
   - 1-3 global_reasoning entries (universal patterns)
   - 0-2 global_history entries (universal issues)
4. Update existing global entries with new implementations
5. Generate a comprehensive extraction report

### Benefits

After extraction, AI assistants can:
- ✅ Learn from your architectural patterns
- ✅ Reuse proven implementations
- ✅ Avoid repeating past mistakes
- ✅ Apply lessons learned to new projects
- ✅ Build on existing solutions

### Verification

After extraction, verify:
```sql
-- Check statistics
SELECT * FROM knowledge_statistics;

-- View this project's entries
SELECT component, title FROM project_reasoning WHERE project_name = 'your_project_name';
SELECT component, title FROM project_history WHERE project_name = 'your_project_name';
```

### Files Created During Extraction

The AI will create:
- `KNOWLEDGE-EXTRACTION-REPORT.md` - Comprehensive extraction report
- Temporary SQL files (deleted after import)

### When NOT to Extract

**Don't extract if**:
- ❌ Project just started (no knowledge yet)
- ❌ Only initial setup completed
- ❌ No meaningful features implemented
- ❌ No architectural decisions made

**Wait until**:
- ✅ Core functionality complete
- ✅ Major features implemented  
- ✅ Patterns established
- ✅ Lessons learned

---

## 🎯 IMPORTANT NOTES FOR THE AI

### CRITICAL: Global Repository Junction Setup Must Be FIRST

**Before doing anything else**, you MUST run:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force
```

**Why this is critical**:
1. Links this project to shared global Cursor repository
2. Provides access to universal reasoning/history across ALL projects
3. Provides access to shared scripts and utilities
4. Provides access to standard workflows and protocols
5. Without it, the project operates in isolation without global knowledge

**What gets created (Windows Junctions)**:
- `Global-Reasoning/` → C:\Users\kento\.cursor\global-cursor-repo\reasoning\
- `Global-History/` → C:\Users\kento\.cursor\global-cursor-repo\history\
- `Global-Scripts/` → C:\Users\kento\.cursor\global-cursor-repo\scripts\
- `Global-Workflows/` → C:\Users\kento\.cursor\global-cursor-repo\rules\
- `Global-Testing-Framework/` → C:\Users\kento\.cursor\global-cursor-repo\testing\

**Junction Benefits**:
- ✅ Single source of truth - one repository, not copies
- ✅ Instant updates - change once, applies everywhere
- ✅ No duplication - minimal disk usage
- ✅ No sync needed - always consistent
- ✅ Easy to manage - junctions work like normal folders

### When You See This Prompt, You Should:

1. **Verify Root Directory FIRST**: ALWAYS verify project root before ANY operations
   - Check current directory with `Get-Location`
   - Verify required files exist (startup.ps1, package.json)
   - Verify required directories exist (scripts/, Global-Scripts/)
   - Navigate to root if needed before proceeding
   - **CRITICAL**: This prevents "script not found" errors that crash sessions
2. **Run Sync Script SECOND**: After verifying root, run junction setup script
3. **Be Conversational**: Ask questions if the project type isn't obvious
4. **Be Smart**: Make intelligent defaults based on what you can see
5. **Be Complete**: Create all essential files, even if user didn't explicitly ask
6. **Be Safe**: Always emphasize MCP protection in all documentation
7. **Be Helpful**: Provide clear next steps and troubleshooting tips
8. **Document Global Links**: Explain that Global-* folders are junctions

### What to Infer from the Project:

- Look at existing files (package.json, requirements.txt, etc.)
- Check directory structure (apps/, src/, etc.)
- Identify the technology stack from dependencies
- Determine if it's a monorepo or single app
- Find what ports are being used

### Common Scenarios:

**Scenario A: Brand New Empty Project**
- Run sync script FIRST
- Create ALL files from scratch
- Ask about tech stack before creating
- Provide comprehensive README

**Scenario B: Existing Project Without Setup**
- Run sync script FIRST
- Analyze existing structure
- Create missing files only
- Update existing files carefully
- Report what was found vs created

**Scenario C: Partially Set Up Project**
- Run sync script FIRST (or verify it was already run)
- Verify existing setup
- Fill in gaps
- Update outdated files
- Report status

### File Creation Priority:

1. **CRITICAL** (Do FIRST - before everything else):
   - **Run `Sync-Global-Rules.ps1 -Force`** ← MOST IMPORTANT
   - Verify Global-* folders were created

2. **HIGH** (Create next):
   - .gitignore (must exclude Global-* folders)
   - scripts/safe-kill-servers.ps1
   - .cursorrules (if not synced by script)

3. **MEDIUM** (Create after):
   - README.md
   - project-config.md
   - project-services.md
   - startup.ps1

4. **LOW** (Create last):
   - .env.example
   - universal-watchdog.ps1
   - .logs/ directory
   - Additional documentation
   - Extra helper scripts

### Error Handling:

- **Sync script fails?** → Check if global-cursor-repo exists, guide user to fix
- **Cannot access global rules?** → Note it and ask user to verify path
- **Global-* folders missing?** → Re-run sync with -Force
- **File already exists?** → Verify and update if needed
- **Don't know something?** → Ask the user

### Quality Standards:

- **Documentation**: Clear, complete, with examples, mention global resources
- **Scripts**: Well-commented, error-handled
- **Configuration**: Sensible defaults, easy to customize
- **Safety**: MCP protection emphasized everywhere
- **Global Resources**: Always document that Global-* folders are junctions

---

## 🚨 CRITICAL RULES TO FOLLOW

### Global Resources Sync (NEW - MOST CRITICAL)

**ALWAYS**:
- Run `Sync-Global-Rules.ps1 -Force` as the FIRST step
- Verify Global-* folders are created
- Add Global-* folders to .gitignore
- Document that these are junction links
- Explain how to re-sync if needed

**NEVER**:
- Skip the sync step
- Commit Global-* folders to git
- Create files before running sync
- Forget to exclude Global-* in .gitignore

### MCP Server Protection (CRITICAL)

**ALWAYS**:
- Create safe-kill scripts that protect MCP servers
- Mention MCP protection in README
- Emphasize NEVER killing all node processes
- Verify MCP servers after shutdown

**NEVER**:
- Use `Get-Process node | Stop-Process` in any script
- Use `killall node` in any script
- Create shutdown scripts without MCP protection

### File Creation

**ALWAYS**:
- Use correct syntax for the tech stack
- Include comprehensive comments
- Provide examples in documentation
- Create .logs/.gitignore to exclude logs from git

**NEVER**:
- Create files with placeholder content that needs manual editing
- Leave TODO comments that require user action
- Create broken or incomplete scripts

### Documentation

**ALWAYS**:
- Explain WHY things are done a certain way
- Provide troubleshooting sections
- Include common error solutions
- Link related documentation files
- Document global resources and how to sync them

**NEVER**:
- Assume knowledge of the project structure
- Skip explaining MCP protection
- Forget to document ports and services
- Forget to mention Global-* folders are junctions

---

## 📝 EXAMPLE CONVERSATION FLOW

**User**: [Pastes this prompt]

**AI**: "Great! Let me set up this project. First, I'll link the global repository."

[Runs: powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force]

"✅ Global repository linked successfully! Created junction links to:
- Global-Reasoning (universal patterns/approaches)
- Global-History (universal solutions/fixes)
- Global-Scripts (reusable scripts)
- Global-Workflows (workflow protocols)

Now let me ask a few questions:

1. What is this project called?
2. I see a `package.json` with Next.js and Express - is this a full-stack web application?
3. What ports should I use? I see references to ports 3000 and 4000 - is that correct?
4. Are you using PostgreSQL as the database?"

**User**: "Yes, it's called 'My Awesome App'. Those ports are correct. Using PostgreSQL."

**AI**: "Perfect! I'll set up 'My Awesome App' with:
- Next.js frontend on port 3000
- Express backend on port 4000
- PostgreSQL database on port 5432
- Global resources already linked ✅

Let me create all the necessary files... [creates files]

✅ Setup complete! Here's what I created: [lists files]

**Important**: The Global-* folders are junction links to your global repository. They should NOT be committed to git (already added to .gitignore).

Next steps:
1. Copy `.env.example` to `.env` and fill in your configuration
2. Run `pnpm install` to install dependencies
3. Run `.\startup.ps1` to verify everything is set up correctly
4. Start developing!

⚠️ Critical reminders:
- Use `.\scripts\safe-kill-servers.ps1` to stop services (never kill node directly)
- To update global resources: `.\scripts\Sync-Global-Rules.ps1 -Force`
- Global-* folders are junctions - don't modify them directly"

---

## 🎓 LEARNING NOTES

This prompt is designed to be:

1. **Global-Repository-Aware**: Links to shared global repository FIRST
2. **Junction-Based**: Uses Windows junctions (no file copying/syncing needed)
3. **Auto-Detection**: Detects project name and database from folder structure
4. **Smart**: Makes intelligent decisions based on project structure
5. **Safe**: Emphasizes MCP protection throughout
6. **Complete**: Creates everything needed for development
7. **Flexible**: Adapts to different project types
8. **Documented**: Explains everything clearly

**For Developers**: You can customize this prompt for your specific needs, but always:
- Keep the global junction setup FIRST
- Keep the MCP protection emphasis
- Document that Global-* are Windows junctions
- Use auto-detection for project/database names

**For AI**: Follow the guidelines above and adapt to the specific project you're setting up. When in doubt, ask the user. **ALWAYS run the junction setup script first!**

---

## 🔄 RECREATE JUNCTIONS ANYTIME

To recreate global repository junctions (if they get deleted or broken):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force
```

This recreates junction links:
- Global-Reasoning → global-cursor-repo\reasoning\
- Global-History → global-cursor-repo\history\
- Global-Scripts → global-cursor-repo\scripts\
- Global-Workflows → global-cursor-repo\rules\

---

## 🔄 VERSION HISTORY

- **v3.1** (October 2025): Added lessons learned from Drone Sentinels setup
  - Added manual junction creation fallback for empty/corrupted scripts
  - Enhanced troubleshooting with specific issues encountered
  - Added verification steps and success metrics
  - Documented PowerShell command verification best practices
  - Added project-specific script update requirements
- **v3.0** (October 2025): Major overhaul - changed to Windows Junction-based global repository linking
  - Replaced Sync-Global-Rules.ps1 with Setup-Global-Junctions.ps1
  - Changed from file copying/syncing to true junction linking
  - Updated to new folder structure: Global-Reasoning, Global-History, Global-Scripts, Global-Workflows
  - Added auto-detection for project name (ParentFolder-RootFolder) and database name
  - Added resource management system for 12+ hour AI sessions
  - Changed from hourly to 45-minute milestones
- **v2.3** (October 2025): Added Step 3.5 - Memory Structure Setup for optimal long-running AI sessions
- **v2.2** (October 2025): Added Step 11 - Knowledge Extraction to AI Repository (after project completion)
- **v2.1** (October 2025): Added critical Global Rules Sync step as Step 1
- **v2.0** (October 2025): Completely rewritten for clarity and ease of use
- **v1.0** (Original): Initial version with all phases spelled out

---

## 📞 TROUBLESHOOTING THIS PROMPT

### Common Setup Issues

**Issue**: Setup-Global-Junctions.ps1 not found
**Solution**: Copy from deployment folder template (C:\Users\kento\.cursor\Deployment\For Every Project\scripts\)

**Issue**: Setup-Global-Junctions.ps1 is empty (0 bytes)
**Solution**: 
1. **CRITICAL**: Script is corrupted or empty
2. Recreate the script with proper content (see manual junction creation above)
3. Or use manual PowerShell commands directly
4. Always verify script has content before running

**Issue**: Setup-Global-Junctions.ps1 syntax error (missing closing brace)
**Solution**: 
1. Check the script for missing `}` characters
2. Recreate the script with proper syntax
3. Common error: `Missing closing '}' in statement block or type definition`

**Issue**: Setup-Global-Junctions.ps1 runs but produces no output
**Solution**:
1. **CRITICAL**: Script may be failing silently
2. Use manual PowerShell commands instead
3. Always verify junctions were created with `Get-ChildItem | Where-Object { $_.Name -like "Global-*" }`
4. Check if global repository path exists: `Test-Path "C:\Users\kento\.cursor\global-cursor-repo"`

**Issue**: Global-* junctions not created
**Solution**: Re-run Setup-Global-Junctions.ps1 with -Force flag, or use manual commands

**Issue**: Permission denied creating junctions
**Solution**: Run PowerShell as Administrator (junctions require elevated permissions on Windows)

**Issue**: Global repository path not found
**Solution**: Ensure C:\Users\kento\.cursor\global-cursor-repo\ exists, verify the global-cursor-repo has these folders: reasoning/, history/, scripts/, rules/

**Issue**: AI doesn't run junction setup first
**Solution**: Emphasize "This is Step 1 - do it before anything else"

**Issue**: Script location verification not performed
**Solution**: ALWAYS verify root directory before running ANY scripts - this prevents crashes
- Check current directory first
- Verify required files exist
- Navigate to root if needed
- This is now built into startup.ps1 but should also be done manually before critical operations

**Issue**: AI creates files with wrong tech stack
**Solution**: Explicitly state your tech stack in initial message

**Issue**: Global-* junctions committed to git
**Solution**: Ensure .gitignore excludes them, run `git rm -r --cached Global-*`

**Issue**: Junction appears broken or empty
**Solution**: Verify target folder exists, recreate junction with -Force flag

### PowerShell-Specific Issues

**Issue**: Commands fail with "command not found"
**Solution**: Use PowerShell syntax, not bash:
- `Get-Location` instead of `pwd`
- `Get-ChildItem` instead of `ls`
- `New-Item` instead of `mkdir`

**Issue**: Connection failures during setup
**Solution**: 
1. Use Command Watchdog Protocol for long commands
2. Break complex operations into smaller steps
3. Restart Cursor if connection drops
4. Don't resume mid-setup - start fresh

**Issue**: npm commands hang or crash
**Solution**: Always use watchdog wrapper:
```powershell
pwsh -File scripts\cursor_run.ps1 -TimeoutSec 600 -Label "npm-install" -- npm install
```

**Issue**: Docker port conflicts
**Solution**: 
1. Check existing ports: `netstat -ano | findstr :5432`
2. Use different port in docker-compose.yml
3. Update all references to new port

### Recovery Procedures

**If Setup Completely Fails**:
1. Close Cursor completely
2. Delete any partial Global-* folders
3. Restart Cursor
4. Start fresh with this prompt
5. Use simpler, shorter commands

**If Global Junctions Are Broken**:
1. Delete existing Global-* folders
2. Re-run: `powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force`
3. Verify with: `Get-ChildItem | Where-Object { $_.Name -like "Global-*" }`

---

*This prompt is maintained by Ken Tola. Last updated: October 2025*
