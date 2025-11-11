# Complete Cursor IDE Advanced Development System - Windows Deployment

**Single comprehensive prompt to deploy the entire system on Windows 10/11.**

---

## Prerequisites

Before using this prompt, you MUST have completed:

- ✅ **A-LIST-OF-REQUIRED-SOFTWARE.md** - All software installed
- ✅ **%UserProfile%\.cursor\.env created** - With ALL API keys and actual values
- ✅ **PostgreSQL configured** - With `pgpass.conf` file
- ✅ **Docker Desktop running** - Fully started
- ✅ **WSL installed** - Ubuntu distribution
- ✅ **AWS CLI configured** - With valid credentials

---

## 📋 COPY THIS ENTIRE PROMPT INTO CURSOR IDE

```prompt
# CURSOR IDE ADVANCED DEVELOPMENT SYSTEM - WINDOWS DEPLOYMENT

I have completed all software installation on Windows 10/11 and configured my .env file with all actual values. Please deploy the complete Cursor IDE Advanced Development System with all 20+ advanced features.

## My Environment Details

**Operating System:** Windows 10/11 (PowerShell 7)
**Home Directory:** %UserProfile%
**Shell:** PowerShell
**PostgreSQL:** localhost:5432, user: postgres
**Docker:** Docker Desktop running
**WSL:** Ubuntu installed
**Node.js:** v20.x LTS with npm, tsx, pm2
**AWS CLI:** Configured with credentials
**Cursor IDE:** Installed at %LocalAppData%\Programs\Cursor\Cursor.exe

## Environment Variables Configuration

My %UserProfile%\.cursor\.env file is ALREADY CONFIGURED with actual values for:

**MCP Server API Keys:**
```
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EXA_API_KEY=exa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
REF_API_KEY=ref_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Database Configuration:**
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=my_actual_postgres_password
```

**AWS Configuration:**
```
AWS_ACCESS_KEY_ID=AKIA2DZSOUO2K5EI4QWR
AWS_SECRET_ACCESS_KEY=my_actual_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

**SMTP Configuration:**
```
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_SECURE=false
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
AWS_SES_SMTP_USER=my_ses_username
AWS_SES_SMTP_PASSWORD=my_ses_password
SMTP_FROM_EMAIL=noreply@mydomain.com
DEFAULT_EMAIL=info@mydomain.com
EMAIL_MODE=development
```

**Other Configuration:**
```
NODE_ENV=development
NEXT_PUBLIC_BASE_URL=http://localhost:3000
```

**IMPORTANT:** My .env file already contains all these values with actual API keys and passwords. USE THE EXISTING FILE - do not overwrite it.

## Deployment Requirements

Please create the COMPLETE system structure with ALL of the following:

### 1. Global Repository Structure (%UserProfile%\.cursor\global-cursor-repo\)

Create the complete global repository with these folders and contents:

**rules/** - All global development rules (create as .md or .mdc files)
**workflows/** - All automation workflows
**scripts/** - All utility scripts (PowerShell .ps1 versions)
**docs/** - All technical documentation
**history/** - Global knowledge history
**reasoning/** - Global reasoning patterns
**docker-templates/** - Pre-configured Docker templates
**utils/** - Shared utility functions

### 2. MCP Server Configuration (%UserProfile%\.cursor\mcp.json)

Create mcp.json with properly configured MCP servers for Windows using absolute paths.

**CRITICAL REQUIREMENTS:**
- Use environment variables from %UserProfile%\.cursor\.env
- Use Windows absolute paths with %UserProfile%
- For WSL-based MCP servers, use wsl.exe command
- All MCP servers must load environment variables

**Required MCP Servers:**
1. Apify - Web automation
2. Exa - AI-optimized search
3. OpenRouter - Advanced AI models
4. Perplexity - Contextual Q&A
5. Playwright - Browser automation
6. Ref - Documentation search
7. Stripe - Payment systems (optional)
8. Sequential Thinking - Complex problem decomposition

**Load all environment variables from %UserProfile%\.cursor\.env for each MCP server.**

### 3. Cursor IDE Configuration

Create the following configuration files:

**%UserProfile%\.cursor\settings.json** - IDE settings:
```json
{
  "cursor.general.enableAutoUpdate": true,
  "editor.fontSize": 14,
  "editor.tabSize": 2,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true,
    "source.organizeImports": true
  },
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "git.autofetch": true,
  "git.enableSmartCommit": true,
  "terminal.integrated.defaultProfile.windows": "PowerShell"
}
```

**%UserProfile%\.cursor\argv.json** - Cursor arguments (if needed)

### 4. Project Template System (%UserProfile%\.cursor\Deployment\For Every Project\)

Create complete project template folder with:

**Core Files:**
- **startup.ps1** - Windows PowerShell version
  * Checks for PostgreSQL, Docker, Node.js
  * Loads .env file
  * Creates junction links to Global-* folders (use mklink /J or New-Item -ItemType Junction)
  * Sets up memory structure
  * Verifies all services
  * Creates watchdog script if missing
  
- **project-config.md** - Template for project configuration
- **.env.template** - Template for project-specific environment variables
- **.gitignore** - Comprehensive gitignore file
- **README.md** - Project template README
- **package.json** - Template with common dependencies
- **tsconfig.json** - TypeScript configuration
- **docker-compose.yml** - From docker-templates/

**Scripts folder (scripts\):**
- automated-setup.ps1 (Windows version)
- sync-global-rules.ps1
- cursor_run.ps1 (watchdog - PowerShell version)
- safe-kill-servers.ps1
- resource-cleanup.ps1
- emergency-flush.ps1
- monitor-resources.ps1
- extract-facts.py (Python script)

**Memory Structure Templates:**
- .cursor\memory\ folder with template files:
  * PROJECT_BRIEF.md
  * TECH_STACK.md
  * ARCHITECTURE.md
  * PATTERNS.md
  * ACTIVE_WORK.md
  * CURRENT_FOCUS.md
  
- .project-memory\history\ folder structure
- .project-memory\reasoning\ folder structure
- README.md files explaining each memory tier

### 5. Startup Script (startup.ps1) - Windows Version

Create startup.ps1 that:

1. **Environment Detection:**
   - Detect Windows version
   - Identify PowerShell version
   - Check if running as Administrator (warn if needed)
   
2. **Software Verification:**
   - PostgreSQL service running (check with Get-Service)
   - Docker Desktop running (check with docker ps)
   - Node.js/npm/tsx/pm2 available
   - Git available
   - WSL available
   
3. **Environment Loading:**
   - Load variables from project .env
   - Load global variables from %UserProfile%\.cursor\.env
   - Set environment variables for current session
   
4. **Junction Link Creation (NOT Symbolic Links):**
   Use `cmd /c mklink /J` or `New-Item -ItemType Junction` to create:
   - Global-Rules → %UserProfile%\.cursor\global-cursor-repo\rules
   - Global-Workflows → %UserProfile%\.cursor\global-cursor-repo\workflows
   - Global-Scripts → %UserProfile%\.cursor\global-cursor-repo\scripts
   - Global-Docs → %UserProfile%\.cursor\global-cursor-repo\docs
   - Global-Utils → %UserProfile%\.cursor\global-cursor-repo\utils
   - Global-History → %UserProfile%\.cursor\global-cursor-repo\history
   - Global-Reasoning → %UserProfile%\.cursor\global-cursor-repo\reasoning
   
5. **Memory Structure Setup:**
   - Create .cursor\memory\ if missing
   - Create .project-memory\history\ if missing
   - Create .project-memory\reasoning\ if missing
   - Populate with template files
   
6. **Service Verification:**
   - Test PostgreSQL connection using pgpass.conf
   - Verify Docker is responsive
   - Check MCP servers in %UserProfile%\.cursor\mcp.json
   
7. **Watchdog Setup:**
   - Copy cursor_run.ps1 from Global-Scripts if missing
   
8. **Completion:**
   - Display verification checklist
   - Show next steps
   - Mark startup as complete (.cursor\startup-complete.marker)

**CRITICAL Windows Requirements:**
- Use PowerShell syntax
- Use Windows paths with backslashes
- Use %UserProfile% not $HOME
- Use Get-Service, Start-Process, etc.
- Use cmd /c mklink /J for junction links (NOT New-Item -ItemType SymbolicLink which requires admin)
- All paths must be absolute with %UserProfile% variable

### 6. Documentation

Create comprehensive documentation:

**%UserProfile%\.cursor\Deployment\README.md:**
- Complete deployment guide for Windows
- Software installation instructions
- Configuration steps
- Troubleshooting guide
- Windows-specific notes

**%UserProfile%\.cursor\Deployment\For Every Project\README.md:**
- Project setup guide
- How to use startup.ps1
- How to create new projects
- How to use advanced features

### 7. Verification

After creating everything, verify:

```powershell
# Global repository structure
Get-ChildItem "$env:USERPROFILE\.cursor\global-cursor-repo\"
# Should show: rules\, workflows\, scripts\, docs\, history\, reasoning\, utils\, docker-templates\

# Project template
Get-ChildItem "$env:USERPROFILE\.cursor\Deployment\For Every Project\"
# Should show: startup.ps1, project-config.md, scripts\, .env.template, etc.

# MCP configuration
Get-Content "$env:USERPROFILE\.cursor\mcp.json" | ConvertFrom-Json
# Should show properly configured MCP servers

# Environment variables (verify existing file not overwritten)
Get-Content "$env:USERPROFILE\.cursor\.env" | Select-Object -First 10
# Should show MY existing API keys and values
```

## Final Steps

After deployment:

1. **Test Project Creation:**
```powershell
New-Item -Path "$env:USERPROFILE\Projects\TestCompany\TestProject" -ItemType Directory -Force
Set-Location "$env:USERPROFILE\Projects\TestCompany\TestProject"
Copy-Item -Path "$env:USERPROFILE\.cursor\Deployment\For Every Project\*" -Destination . -Recurse -Force
.\startup.ps1
```

2. **Launch Cursor:**
```powershell
& "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe" .
```

3. **Test in Cursor:**
```
Please run your startup process
```

## Success Criteria

I should have:
- ✅ Complete global-cursor-repo structure at %UserProfile%\.cursor\
- ✅ All 20+ advanced features available
- ✅ MCP servers configured for Windows with proper paths
- ✅ Project template ready for use
- ✅ Junction links to Global-* folders working
- ✅ Memory structure implemented
- ✅ All scripts in PowerShell (.ps1)
- ✅ PostgreSQL and Docker integration working
- ✅ My existing .env file preserved (not overwritten)

## Windows-Specific Requirements

- Use PowerShell syntax (not bash)
- Handle Windows paths with backslashes
- Use Windows-compatible commands:
  * `Get-Service` (not systemctl)
  * `Start-Process` (not open)
  * `Get-Process`, `Stop-Process` (process management)
- Use absolute paths with %UserProfile% variable
- Use `cmd /c mklink /J` for junction links (doesn't require admin)
- Test on Windows 10/11

## Critical Notes

1. **DO NOT OVERWRITE** my %UserProfile%\.cursor\.env file - it already contains all my actual API keys and passwords
2. **USE ABSOLUTE PATHS** with %UserProfile% variable, not relative paths
3. **USE JUNCTION LINKS** (mklink /J) not symbolic links (which require admin)
4. **USE POWERSHELL** - All scripts must be .ps1 format
5. **LOAD MY ENV** - MCP servers must use environment variables from my .env file

Please proceed with the complete deployment and let me know when I can start creating projects!
```

---

## After Deployment

Once the AI completes the deployment, you're ready to create your first real project!

### Create Your First Project

```powershell
# Create project directory
New-Item -Path "$env:USERPROFILE\Projects\MyCompany\MyFirstProject" -ItemType Directory -Force
Set-Location "$env:USERPROFILE\Projects\MyCompany\MyFirstProject"

# Copy template
Copy-Item -Path "$env:USERPROFILE\.cursor\Deployment\For Every Project\*" -Destination . -Recurse -Force

# Customize project config
notepad project-config.md

# Run startup
.\startup.ps1

# Launch Cursor
& "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe" .
```

### In Cursor IDE

```prompt
Please run your startup process
```

Then start building:

```prompt
I want to build [describe your project]. Let's start with [first feature].
```

The AI will use all 20+ advanced features to guide you through development!

---

## 🎉 You're All Set!

You now have the complete Cursor IDE Advanced Development System running on Windows with all 20+ advanced features!

**Happy coding on Windows!** 🚀

