# Universal Startup Rule for Cursor AI Sessions

## 🚨 MANDATORY STARTUP PROCESS 🚨

**CRITICAL**: At the beginning of EVERY Cursor session, you MUST run the universal startup script:

```powershell
pwsh -ExecutionPolicy Bypass -File "startup.ps1"
```

**FAILURE TO FOLLOW THIS STARTUP PROCESS WILL RESULT IN:**
- Command timeout issues
- Database connectivity problems
- Service management conflicts
- MCP server destruction
- Environment configuration errors

## What the Startup Script Does

1. **Environment Setup**: Sets working directory and environment variables
2. **Docker Check**: Verifies Docker availability (required for this project)
3. **Git Repository**: Checks Git repository status and identifies untracked files
4. **Service Health**: Checks API, Web, Database, and MailHog server status
5. **Watchdog Creation**: Creates universal-watchdog.ps1 for command execution
6. **MCP Protection**: Sets up MCP server protection commands
7. **Database Connection**: Verifies PostgreSQL connectivity

## Command Execution Rules

**ALWAYS use the universal watchdog for commands:**
```powershell
pwsh -ExecutionPolicy Bypass -File "universal-watchdog.ps1" -TimeoutSec 900 -Label "<action>" -- <command>
```

**NEVER use -W switch** when running PostgreSQL commands

## MCP Server Protection

**CRITICAL**: NEVER kill all Node.js processes - this will destroy MCP servers!

**Use this command to stop only application servers:**
```powershell
Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object { try { $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine; if ($cmdLine -and ($cmdLine -match "npm|pnpm|nodemon|ts-node|next|vite|webpack|express|fastify")) { Write-Host "Killing application server process $($_.Id)"; Stop-Process -Id $_.Id -Force } } catch { Write-Host "Preserving process $($_.Id) (likely MCP server)" } }
```

## MCP Server Capabilities

### **Apify** - Web Automation & Data Extraction
- **Purpose**: Log into other websites and services
- **Use For**: Web scraping, form automation, login automation, testing external integrations

### **AWS Labs (awslabs.*)** - Cloud Infrastructure Management  
- **Purpose**: Interact with AWS Cloud services, servers, networks
- **Use For**: EC2 management, VPC configuration, security groups, infrastructure provisioning

### **Exa** - Superior Programmer-Oriented Search
- **Purpose**: Provides superior programmer-oriented search results
- **Use For**: Code context search, technical documentation, finding code examples

### **OpenRouter AI** - Advanced AI Model Access
- **Purpose**: Access stronger AI models for complex tasks and advanced thinking
- **Use For**: Complex analysis, advanced reasoning, model comparison

### **Perplexity Ask** - Contextualized Q&A
- **Purpose**: Provides highly contextualized answers for various questions
- **Use For**: Research tasks, fact-checking, contextual information gathering

### **Ref** - Documentation Search
- **Purpose**: In-depth search for documentation, configuration, and user manuals
- **Use For**: Finding documentation, configuration examples, setup guides

### **Playwright** - Browser Automation
- **Purpose**: Comprehensive control over web browser and UI automation
- **Use For**: End-to-end testing, UI automation, frontend validation, form testing

### **Sequential Thinking** - Complex Task Breakdown
- **Purpose**: Break complex efforts into series of tasks or steps
- **Use For**: Project planning, complex task analysis, multi-step problem solving

### **Stripe** - Payment System Integration
- **Purpose**: Access to Stripe credit card payment system
- **Use For**: Payment integration, subscription handling, financial transactions

## Project Requirements

### Docker Requirements
- **Docker Desktop**: Required (Windows/macOS) or Docker Engine (Linux)
- **Services**: PostgreSQL, Redis, MinIO, MailHog
- **Global Availability**: May run globally on Linux machines

### Git Repository Requirements
- **Local Repository**: Required (.git folder must exist)
- **Clean Repository**: Only include files necessary to run the project
- **Constant Exclusion**: Exclude unnecessary files when folders themselves are not excluded
- **Production Ready**: Maintain minimal, production-ready file set

### Email Formatting Protection
- **CRITICAL**: Any changes must never interfere with email formatting functionality
- **Testing**: Always test email functionality after modifications
- **Priority**: Email formatting issues must be fixed immediately
- **Review**: Consider email functionality when refactoring code

## Service Management

Use commands from `project-services.md` for starting/stopping project services:
- **API Server**: Port 4000
- **Web Server**: Port 3000  
- **Database**: Port 5432
- **MailHog**: Port 8025

## Success Criteria

After running startup script, verify:
- ✅ Environment variables are set
- ✅ Docker availability confirmed
- ✅ Git repository status checked
- ✅ Service health checks completed
- ✅ PostgreSQL connectivity confirmed
- ✅ MCP protection command available
- ✅ Universal watchdog script created
- ✅ Startup marker created

---

*This rule ensures consistent, reliable operation of Cursor AI across all sessions with comprehensive MCP server understanding and project-specific requirements.*
