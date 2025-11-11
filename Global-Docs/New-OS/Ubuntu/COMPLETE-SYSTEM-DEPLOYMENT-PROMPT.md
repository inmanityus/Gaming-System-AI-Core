# Complete Cursor IDE Advanced Development System - Ubuntu Deployment

**Single comprehensive prompt to deploy the entire system on Ubuntu Linux.**

---

## Prerequisites

Before using this prompt, you MUST have completed:

- ✅ **A-LIST-OF-REQUIRED-SOFTWARE.md** - All software installed
- ✅ **API Keys obtained** - Stored in `$HOME/api-keys-temp.txt`
- ✅ **PostgreSQL configured** - With `.pgpass` file
- ✅ **Docker running** - User added to docker group
- ✅ **AWS CLI configured** - With valid credentials

---

## 📋 COPY THIS ENTIRE PROMPT INTO CURSOR IDE

```prompt
# CURSOR IDE ADVANCED DEVELOPMENT SYSTEM - UBUNTU DEPLOYMENT

I have completed all software installation on Ubuntu Linux and I need you to deploy the complete Cursor IDE Advanced Development System with all 20+ advanced features.

## My Environment Details

**Operating System:** Ubuntu Linux (bash shell)
**Home Directory:** $HOME
**Shell:** bash
**PostgreSQL:** localhost:5432, user: postgres
**Docker:** Installed and running
**Node.js:** v20.x LTS with npm, tsx, pm2
**AWS CLI:** Configured with credentials
**Cursor IDE:** Installed at $HOME/Applications/cursor.AppImage

## API Keys

I have the following API keys ready (stored in $HOME/api-keys-temp.txt):
- APIFY_API_TOKEN
- EXA_API_KEY
- OPENROUTER_API_KEY
- PERPLEXITY_API_KEY
- REF_API_KEY
- STRIPE_SECRET_KEY (optional)
- GEMINI_API_KEY (optional)
- OPENAI_API_KEY (optional)

## Deployment Requirements

Please create the COMPLETE system structure with ALL of the following:

### 1. Global Repository Structure ($HOME/.cursor/global-cursor-repo/)

Create the complete global repository with these folders and contents:

**rules/** - All global development rules:
- session-handoff-protocol.md
- hourly-milestone-system.mdc
- autonomous-development-protocol.mdc
- command-watchdog-protocol.mdc
- aggressive-resource-management.mdc
- peer-coding-protocol.mdc
- pairwise-testing-protocol.mdc
- multi-model-collaboration.mdc
- end-user-testing.mdc
- context-cache-management.mdc
- mcp-server-protection.mdc
- security-review-protocol.mdc
- auto-documentation-generation.md
- postgres-defaults.mdc
- git-commit-policy.mdc
- workflow-integration.mdc
- mcp-server-integration.mdc

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
- workflow-registry.json

**scripts/** - All utility scripts (with .sh extension for Ubuntu):
- resource-cleanup.sh
- emergency-flush.sh
- monitor-resources.sh
- extract-facts.py
- cursor_run.sh (watchdog script)
- safe-kill-servers.sh
- sync-global-rules.sh

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
- Create initial README.md explaining the global history system
- Template files for resolutions/, milestones/, lessons/

**reasoning/** - Global reasoning patterns:
- Create initial README.md explaining the global reasoning system
- Template files for architectural decisions and patterns

**docker-templates/** - Pre-configured Docker templates:
- docker-compose.yml
- docker-compose.dev.yml
- Dockerfile.api
- Dockerfile.frontend
- PostgreSQL init scripts
- Redis configuration
- MinIO configuration

**utils/** - Shared utility functions:
- Create README.md explaining the utils system
- Common helper functions

### 2. Environment Configuration ($HOME/.cursor/.env)

Read my API keys from $HOME/api-keys-temp.txt and create $HOME/.cursor/.env with:

```bash
# MCP Server API Keys
APIFY_API_TOKEN=<from temp file>
EXA_API_KEY=<from temp file>
OPENROUTER_API_KEY=<from temp file>
PERPLEXITY_API_KEY=<from temp file>
REF_API_KEY=<from temp file>
STRIPE_SECRET_KEY=<from temp file if exists>
GEMINI_API_KEY=<from temp file if exists>
OPENAI_API_KEY=<from temp file if exists>

# Database Configuration (Global Defaults)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<read from ~/.pgpass if available>

# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
```

Then secure the file:
```bash
chmod 0600 $HOME/.cursor/.env
```

### 3. MCP Server Configuration ($HOME/.cursor/mcp.json)

Create mcp.json with properly configured MCP servers for Ubuntu using absolute paths with $HOME variable:

**Required MCP Servers:**
- Apify (web automation)
- Exa (AI search)
- OpenRouter (AI models)
- Perplexity (Q&A)
- Playwright (browser automation)
- Ref (documentation)
- Stripe (optional)

**Critical:** All paths MUST use absolute paths with environment variables (not hardcoded usernames).

Example structure:
```json
{
  "mcpServers": {
    "apify": {
      "command": "npx",
      "args": ["-y", "@apify/mcp-server-apify"],
      "env": {
        "APIFY_API_TOKEN": "${APIFY_API_TOKEN}"
      }
    }
  }
}
```

Load environment variables from $HOME/.cursor/.env for each MCP server.

### 4. Cursor IDE Configuration

Create the following configuration files:

**$HOME/.cursor/settings.json** - IDE settings optimized for development
**$HOME/.cursor/argv.json** - Cursor arguments

### 5. Project Template System ($HOME/.cursor/Deployment/For Every Project/)

Create complete project template folder with:

**Core Files:**
- startup.sh (Ubuntu version with bash, executable)
- project-config.md (template)
- .env.template (project environment variables)
- .gitignore (comprehensive)
- README.md (project template)
- package.json (template with common dependencies)
- tsconfig.json (TypeScript configuration)
- docker-compose.yml (from templates)

**Scripts folder (scripts/):**
- automated-setup.sh (Ubuntu version)
- sync-global-rules.sh
- cursor_run.sh (watchdog)
- safe-kill-servers.sh
- All resource management scripts (.sh versions)

All .sh scripts must be made executable:
```bash
chmod +x startup.sh
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;
```

**Memory Structure Templates:**
- .cursor/memory/ folder with template files
- .project-memory/history/ folder structure
- .project-memory/reasoning/ folder structure

### 6. Shell Integration

Update my ~/.bashrc to load Cursor environment variables:

```bash
# Add at end of ~/.bashrc
if [ -f "$HOME/.cursor/.env" ]; then
    export $(grep -v '^#' "$HOME/.cursor/.env" | xargs)
fi
```

Then reload: `source ~/.bashrc`

### 7. Startup Script (startup.sh)

Create a comprehensive startup.sh for projects that:
- Checks for required software (PostgreSQL, Docker, Node.js)
- Loads environment variables from .env
- Creates symbolic links to Global-* folders:
  * Global-Rules → $HOME/.cursor/global-cursor-repo/rules
  * Global-Workflows → $HOME/.cursor/global-cursor-repo/workflows
  * Global-Scripts → $HOME/.cursor/global-cursor-repo/scripts
  * Global-Docs → $HOME/.cursor/global-cursor-repo/docs
  * Global-Utils → $HOME/.cursor/global-cursor-repo/utils
  * Global-History → $HOME/.cursor/global-cursor-repo/history
  * Global-Reasoning → $HOME/.cursor/global-cursor-repo/reasoning
- Sets up memory structure (.cursor/memory/, .project-memory/)
- Verifies PostgreSQL connection
- Checks Docker status
- Creates watchdog script if missing
- Verifies all systems operational

**Critical:** Must be bash-compatible, use Unix paths (forward slashes), and set executable permissions.

### 8. Memory Structure Implementation

Implement the three-tier memory system:

**Session Memory (.cursor/memory/):**
- PROJECT_BRIEF.md
- TECH_STACK.md
- ARCHITECTURE.md
- PATTERNS.md
- ACTIVE_WORK.md
- CURRENT_FOCUS.md

**Project Memory (.project-memory/):**
- history/ folder (completed work)
- reasoning/ folder (business logic)
- README.md explaining system

**Global Memory (already created):**
- global-cursor-repo/history/
- global-cursor-repo/reasoning/

### 9. Documentation

Create comprehensive documentation:

**$HOME/.cursor/Deployment/README.md** - Complete deployment guide for Ubuntu
**$HOME/.cursor/Deployment/For Every Project/README.md** - Project setup guide

### 10. Verification

After creating everything, verify:

```bash
# Global repository structure
ls -la $HOME/.cursor/global-cursor-repo/

# Project template
ls -la "$HOME/.cursor/Deployment/For Every Project/"

# MCP configuration
cat $HOME/.cursor/mcp.json | jq .

# Environment variables
grep -v "^#" $HOME/.cursor/.env

# Shell integration
grep "cursor/.env" ~/.bashrc
```

## Final Steps

After deployment:

1. Securely delete API keys temp file:
```bash
shred -u $HOME/api-keys-temp.txt
```

2. Test project creation:
```bash
mkdir -p ~/Projects/TestCompany/TestProject
cd ~/Projects/TestCompany/TestProject
cp -r "$HOME/.cursor/Deployment/For Every Project/"* .
chmod +x startup.sh
find scripts/ -name "*.sh" -type f -exec chmod +x {} \;
./startup.sh
```

3. Launch Cursor in test project:
```bash
~/Applications/cursor.AppImage .
```

4. Test with AI:
```
Please run your startup process
```

## Success Criteria

I should have:
- ✅ Complete global-cursor-repo structure at $HOME/.cursor/
- ✅ All 20+ advanced features available
- ✅ MCP servers configured and ready
- ✅ Project template ready for use
- ✅ Symbolic links to Global-* folders working
- ✅ Memory structure implemented
- ✅ All scripts executable
- ✅ Environment variables loaded in shell
- ✅ PostgreSQL and Docker integration working

## Notes

- Use bash syntax (not PowerShell)
- Use Unix paths (forward slashes)
- Use $HOME not ~/ in scripts for reliability
- All .sh scripts must be chmod +x
- All paths must be absolute with $HOME variable
- Load environment variables from $HOME/.cursor/.env
- Follow Linux best practices

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

# Run startup
./startup.sh

# Launch Cursor
~/Applications/cursor.AppImage .
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

You now have the complete Cursor IDE Advanced Development System running on Ubuntu Linux with:

- ✅ Autonomous development (10x faster)
- ✅ Memory structure (3-5x longer sessions)
- ✅ Peer-based coding (90% fewer bugs)
- ✅ Pairwise testing (100% coverage)
- ✅ Multi-model collaboration
- ✅ Session handoffs (seamless transitions)
- ✅ Resource management (12+ hour sessions)
- ✅ And 13+ more advanced features!

**Happy coding!** 🚀

