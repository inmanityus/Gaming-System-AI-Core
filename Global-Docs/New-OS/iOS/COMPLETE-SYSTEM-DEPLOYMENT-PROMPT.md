# Complete Cursor IDE Advanced Development System - macOS Deployment

**Single comprehensive prompt to deploy the entire system on macOS.**

---

## Prerequisites

Before using this prompt, you MUST have completed:

- ✅ **A-LIST-OF-REQUIRED-SOFTWARE.md** - All software installed
- ✅ **$HOME/.cursor/.env created** - With ALL API keys and actual values
- ✅ **PostgreSQL configured** - With `.pgpass` file
- ✅ **Docker Desktop running** - Fully started
- ✅ **AWS CLI configured** - With valid credentials

---

## 📋 COPY THIS ENTIRE PROMPT INTO CURSOR IDE

```prompt
# CURSOR IDE ADVANCED DEVELOPMENT SYSTEM - MACOS DEPLOYMENT

I have completed all software installation on macOS and configured my .env file with all actual values. Please deploy the complete Cursor IDE Advanced Development System with all 20+ advanced features.

## My Environment Details

**Operating System:** macOS (zsh shell)
**Home Directory:** $HOME
**Shell:** zsh (default macOS shell)
**PostgreSQL:** localhost:5432, user: postgres
**Docker:** Docker Desktop running
**Node.js:** v20.x LTS with npm, tsx, pm2
**AWS CLI:** Configured with credentials
**Homebrew:** Installed (Apple Silicon: /opt/homebrew/ or Intel: /usr/local/)
**Cursor IDE:** Installed at /Applications/Cursor.app

## Environment Variables Configuration

My $HOME/.cursor/.env file is ALREADY CONFIGURED with actual values for:

**MCP Server API Keys:**
```bash
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
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=my_actual_postgres_password
```

**AWS Configuration:**
```bash
AWS_ACCESS_KEY_ID=AKIA2DZSOUO2K5EI4QWR
AWS_SECRET_ACCESS_KEY=my_actual_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
```

**SMTP Configuration:**
```bash
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
```bash
NODE_ENV=development
NEXT_PUBLIC_BASE_URL=http://localhost:3000
```

**IMPORTANT:** My .env file already contains all these values with actual API keys and passwords. USE THE EXISTING FILE - do not overwrite it.

## Deployment Requirements

Please create the COMPLETE system structure with ALL of the following:

### 1. Global Repository Structure ($HOME/.cursor/global-cursor-repo/)

Create the complete global repository with these folders and contents:

**rules/** - All global development rules (create as .md or .mdc files):
- session-handoff-protocol.md - Automatic handoff document generation
- hourly-milestone-system.mdc - 45-minute milestone tracking
- autonomous-development-protocol.mdc - AI autonomous work
- command-watchdog-protocol.mdc - Command timeout protection
- aggressive-resource-management.mdc - Session resource cleanup
- peer-coding-protocol.mdc - Multi-AI code review
- pairwise-testing-protocol.mdc - Tester + Reviewer AI pair
- multi-model-collaboration.mdc - Multi-AI collaboration
- end-user-testing.mdc - Playwright end-user testing
- context-cache-management.mdc - Context clearing rules
- mcp-server-protection.mdc - Protect MCP servers from shutdown
- security-review-protocol.mdc - Monthly security audits
- auto-documentation-generation.md - Auto-generate docs for complex components
- postgres-defaults.mdc - PostgreSQL connection defaults
- git-commit-policy.mdc - Automatic git commits
- workflow-integration.mdc - Workflow activation rules
- mcp-server-integration.mdc - MCP server usage rules

**workflows/** - All automation workflows:
- Autonomous-Development-Protocol.md
- Pairwise-Comprehensive-Testing.md
- Memory-Structure-Setup-Guide.md
- Aggressive-Resource-Management.md
- Session-Handoff-Protocol.md
- Command-Watchdog-Protocol.md
- deploy_to_aws_linux_server.md
- provision_aws_linux_server.md
- visually_test_apps.md
- test-driven-development.md
- Shutterstock-Automation-Workflow.md
- workflow-registry.json (JSON file listing all workflows)

**scripts/** - All utility scripts (macOS-compatible .sh scripts):
- resource-cleanup.sh (run after 45-min milestones)
- emergency-flush.sh (aggressive cleanup when session struggling)
- monitor-resources.sh (track session health)
- extract-facts.py (compress logs to facts)
- cursor_run.sh (watchdog script for command protection)
- safe-kill-servers.sh (kill app servers, protect MCPs)
- sync-global-rules.sh (sync rules to project)

**docs/** - All technical documentation:
- Peer-Coding.md
- End-User-Testing.md
- Context-Cache-Management.md
- Collaborate-With-Other-Models.md
- Cybersecurity-Review-Protocol.md
- MCP-Server-Protection.md
- Passwordless-Authentication-Guide.md
- COMPLEX-TASK-COLLABORATION-GUIDE.md
- AI-COLLABORATIVE-AUTHORING-SYSTEM.md
- EXA-MCP-SERVER-SETUP.md
- PERPLEXITY-ASK-MCP-SERVER-SETUP.md
- SYSTEMD-DAEMON-SETUP.md
- AWS-SES-EMAIL-INTEGRATION.md
- MULTI-TENANT-DEPLOYMENT.md

**history/** - Global knowledge history:
- README.md (explaining global history system)
- resolutions/ folder (common problems and solutions)
- milestones/ folder (universal project phase patterns)
- lessons/ folder (validated insights)

**reasoning/** - Global reasoning patterns:
- README.md (explaining global reasoning system)
- Template files for architectural decisions and patterns

**docker-templates/** - Pre-configured Docker templates:
- docker-compose.yml (full stack with PostgreSQL, Redis, MinIO)
- docker-compose.dev.yml (development overrides)
- Dockerfile.api (backend API template)
- Dockerfile.frontend (frontend app template)
- PostgreSQL init scripts
- Redis configuration
- MinIO configuration (S3-compatible storage)
- Postfix configuration (email server)

**utils/** - Shared utility functions:
- README.md (explaining utils system)
- Common helper functions and shared code

### 2. MCP Server Configuration ($HOME/.cursor/mcp.json)

Create mcp.json with properly configured MCP servers for macOS using absolute paths.

**CRITICAL REQUIREMENTS:**
- Use environment variables from $HOME/.cursor/.env
- Use absolute paths compatible with macOS
- For Apple Silicon Macs: Homebrew is at /opt/homebrew/
- For Intel Macs: Homebrew is at /usr/local/
- Detect and use appropriate paths
- All MCP servers must load environment variables

**Required MCP Servers:**

1. **Apify** - Web automation
```json
{
  "command": "npx",
  "args": ["-y", "@apify/mcp-server-apify"],
  "env": {
    "APIFY_API_TOKEN": "${APIFY_API_TOKEN}"
  }
}
```

2. **Exa** - AI-optimized search
```json
{
  "command": "npx",
  "args": ["-y", "@exa/mcp-server-exa"],
  "env": {
    "EXA_API_KEY": "${EXA_API_KEY}"
  }
}
```

3. **OpenRouter** - Advanced AI models
```json
{
  "command": "npx",
  "args": ["-y", "@openrouter/mcp-server"],
  "env": {
    "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
  }
}
```

4. **Perplexity** - Contextual Q&A
5. **Playwright** - Browser automation
6. **Ref** - Documentation search
7. **Stripe** - Payment systems (optional)
8. **Sequential Thinking** - Complex problem decomposition

**Load all environment variables from $HOME/.cursor/.env for each MCP server.**

### 3. Cursor IDE Configuration

Create the following configuration files:

**$HOME/.cursor/settings.json** - IDE settings:
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
  "terminal.integrated.defaultProfile.osx": "zsh"
}
```

**$HOME/.cursor/argv.json** - Cursor arguments (if needed)

### 4. Shell Integration (~/.zshrc)

Update ~/.zshrc to load Cursor environment variables:

```bash
# Add this at the end of ~/.zshrc (if not already present)
if [ -f "$HOME/.cursor/.env" ]; then
    export $(grep -v '^#' "$HOME/.cursor/.env" | xargs)
fi
```

Then reload:
```bash
source ~/.zshrc
```

### 5. Project Template System ($HOME/.cursor/Deployment/For Every Project/)

Create complete project template folder with:

**Core Files:**
- **startup.sh** - macOS version with zsh compatibility, executable (chmod +x)
  * Checks for PostgreSQL, Docker, Node.js
  * Loads .env file
  * Creates symbolic links to Global-* folders
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

**Scripts folder (scripts/):**
- automated-setup.sh (macOS version, executable)
- sync-global-rules.sh (executable)
- cursor_run.sh (watchdog, executable)
- safe-kill-servers.sh (executable)
- resource-cleanup.sh (executable)
- emergency-flush.sh (executable)
- monitor-resources.sh (executable)
- extract-facts.py (Python script)

**CRITICAL:** All .sh scripts MUST be made executable:
```bash
chmod +x startup.sh
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;
```

**Memory Structure Templates:**
- .cursor/memory/ folder with template files:
  * PROJECT_BRIEF.md
  * TECH_STACK.md
  * ARCHITECTURE.md
  * PATTERNS.md
  * ACTIVE_WORK.md
  * CURRENT_FOCUS.md
  
- .project-memory/history/ folder structure
- .project-memory/reasoning/ folder structure
- README.md files explaining each memory tier

### 6. Startup Script (startup.sh) - macOS Version

Create startup.sh that:

1. **Environment Detection:**
   - Detect Apple Silicon vs Intel Mac
   - Identify shell (zsh vs bash)
   - Check macOS version
   
2. **Software Verification:**
   - PostgreSQL running (check with `brew services list`)
   - Docker Desktop running (check with `docker ps`)
   - Node.js/npm/tsx/pm2 available
   - Git available
   
3. **Environment Loading:**
   - Load variables from project .env
   - Load global variables from $HOME/.cursor/.env
   - Export all variables to current shell
   
4. **Symbolic Link Creation:**
   - Global-Rules → $HOME/.cursor/global-cursor-repo/rules
   - Global-Workflows → $HOME/.cursor/global-cursor-repo/workflows
   - Global-Scripts → $HOME/.cursor/global-cursor-repo/scripts
   - Global-Docs → $HOME/.cursor/global-cursor-repo/docs
   - Global-Utils → $HOME/.cursor/global-cursor-repo/utils
   - Global-History → $HOME/.cursor/global-cursor-repo/history
   - Global-Reasoning → $HOME/.cursor/global-cursor-repo/reasoning
   
5. **Memory Structure Setup:**
   - Create .cursor/memory/ if missing
   - Create .project-memory/history/ if missing
   - Create .project-memory/reasoning/ if missing
   - Populate with template files
   
6. **Service Verification:**
   - Test PostgreSQL connection using .pgpass
   - Verify Docker is responsive
   - Check MCP servers in $HOME/.cursor/mcp.json
   
7. **Watchdog Setup:**
   - Copy cursor_run.sh from Global-Scripts if missing
   - Make executable (chmod +x)
   
8. **Completion:**
   - Display verification checklist
   - Show next steps
   - Mark startup as complete

**CRITICAL macOS Requirements:**
- Use zsh syntax (not bash-specific)
- Use `#!/usr/bin/env zsh` shebang
- Use macOS-compatible commands (brew services, open, etc.)
- Handle Apple Silicon vs Intel paths
- Use $HOME not ~/ for reliability
- All paths must be absolute

### 7. Documentation

Create comprehensive documentation:

**$HOME/.cursor/Deployment/README.md:**
- Complete deployment guide for macOS
- Software installation instructions
- Configuration steps
- Troubleshooting guide
- macOS-specific notes

**$HOME/.cursor/Deployment/For Every Project/README.md:**
- Project setup guide
- How to use startup.sh
- How to create new projects
- How to use advanced features

### 8. Verification

After creating everything, verify:

```bash
# Global repository structure
ls -la $HOME/.cursor/global-cursor-repo/
# Should show: rules/, workflows/, scripts/, docs/, history/, reasoning/, utils/, docker-templates/

# Project template
ls -la "$HOME/.cursor/Deployment/For Every Project/"
# Should show: startup.sh, project-config.md, scripts/, .env.template, etc.

# MCP configuration
cat $HOME/.cursor/mcp.json | jq .
# Should show properly configured MCP servers

# Environment variables (verify existing file not overwritten)
grep -v "^#" $HOME/.cursor/.env | head -10
# Should show MY existing API keys and values

# Shell integration
grep "cursor/.env" ~/.zshrc
# Should show environment variable loading command

# Script permissions
ls -l "$HOME/.cursor/Deployment/For Every Project/startup.sh"
# Should show: -rwxr-xr-x (executable)
```

## Final Steps

After deployment:

1. **Test Project Creation:**
```bash
mkdir -p ~/Projects/TestCompany/TestProject
cd ~/Projects/TestCompany/TestProject
cp -r "$HOME/.cursor/Deployment/For Every Project/"* .
chmod +x startup.sh
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;
./startup.sh
```

2. **Launch Cursor:**
```bash
open -a Cursor .
```

3. **Test in Cursor:**
```
Please run your startup process
```

## Success Criteria

I should have:
- ✅ Complete global-cursor-repo structure at $HOME/.cursor/
- ✅ All 20+ advanced features available
- ✅ MCP servers configured for macOS with proper paths
- ✅ Project template ready for use
- ✅ Symbolic links to Global-* folders working
- ✅ Memory structure implemented
- ✅ All scripts executable (chmod +x)
- ✅ Environment variables loaded in zsh
- ✅ PostgreSQL and Docker integration working
- ✅ My existing .env file preserved (not overwritten)

## macOS-Specific Requirements

- Use zsh syntax (default macOS shell since Catalina)
- Handle Apple Silicon (/opt/homebrew/) vs Intel (/usr/local/) Homebrew paths
- Use macOS-compatible commands:
  * `brew services list` (not systemctl)
  * `open -a` (not xdg-open)
  * `killall` (process management)
- Use absolute paths with $HOME variable
- All .sh scripts must have +x permissions
- Use `#!/usr/bin/env zsh` shebang
- Test on current macOS version

## Critical Notes

1. **DO NOT OVERWRITE** my $HOME/.cursor/.env file - it already contains all my actual API keys and passwords
2. **USE ABSOLUTE PATHS** with $HOME variable, not relative paths or ~/
3. **MAKE SCRIPTS EXECUTABLE** - All .sh files need chmod +x
4. **DETECT ARCHITECTURE** - Handle Apple Silicon vs Intel differences
5. **USE ZSH** - Default macOS shell, not bash
6. **LOAD MY ENV** - MCP servers must use environment variables from my .env file

Please proceed with the complete deployment and let me know when I can start creating projects!
```

---

## After Deployment

Once the AI completes the deployment, you're ready to create your first real project!

### Create Your First Project

```bash
# Create project directory
mkdir -p ~/Projects/MyCompany/MyFirstProject
cd ~/Projects/MyCompany/MyFirstProject

# Copy template
cp -r "$HOME/.cursor/Deployment/For Every Project/"* .

# Make scripts executable
chmod +x startup.sh
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;

# Customize project config
nano project-config.md

# Run startup
./startup.sh

# Launch Cursor
open -a Cursor .
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

You now have the complete Cursor IDE Advanced Development System running on macOS with:

- ✅ Autonomous development (10x faster)
- ✅ Memory structure (3-5x longer sessions)
- ✅ Peer-based coding (90% fewer bugs)
- ✅ Pairwise testing (100% coverage)
- ✅ Multi-model collaboration
- ✅ Session handoffs (seamless transitions)
- ✅ Resource management (12+ hour sessions)
- ✅ MCP servers (extended AI capabilities)
- ✅ Docker templates (consistent environments)
- ✅ AWS deployment automation
- ✅ Security reviews
- ✅ Auto-documentation
- ✅ And 8+ more features!

**Happy coding on Mac!** 🚀

