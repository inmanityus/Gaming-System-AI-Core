# Required Software Installation Guide - Windows

**Complete installation guide for all software needed to run the Cursor IDE Advanced Development System on Windows 10/11.**

---

## 📋 Prerequisites

- Windows 10 or Windows 11
- Administrator access
- Internet connection
- At least 20GB free disk space

---

## Installation Order

**Install in this exact order to avoid dependency issues:**

1. System Updates & Essential Tools
2. PostgreSQL Database Server
3. WSL (Windows Subsystem for Linux)
4. Docker Desktop
5. Node.js & NPM
6. AWS CLI
7. Cursor IDE
8. MCP Server Dependencies

---

## 1. System Updates & Essential Tools

### Update Windows

```powershell
# Check for Windows Updates
Start-Process ms-settings:windowsupdate
```

Install all available updates and restart if needed.

### Install PowerShell 7 (Recommended)

```powershell
# Download and install PowerShell 7
winget install --id Microsoft.PowerShell --source winget
```

**Why:** PowerShell 7 is cross-platform and has better features than Windows PowerShell 5.1.

---

## 2. PostgreSQL Database Server

### Install PostgreSQL

**Download from:** https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

1. Download PostgreSQL 15.x for Windows
2. Run the installer
3. Use default settings
4. **IMPORTANT:** Remember your postgres password
5. Port: 5432 (default)
6. Install Stack Builder components: No

### Configure Automatic Login

```powershell
# Create pgpass file (Run in PowerShell)
$pgpassFile = Join-Path $env:APPDATA "postgresql\pgpass.conf"
New-Item -ItemType Directory -Force (Split-Path $pgpassFile) | Out-Null
"localhost:5432:*:postgres:YOUR_PASSWORD_HERE" | Out-File -FilePath $pgpassFile -Encoding ascii -NoNewline
```

**Replace `YOUR_PASSWORD_HERE` with your actual PostgreSQL password.**

### Test Connection

```powershell
psql -h localhost -p 5432 -U postgres -d postgres -w
```

If successful, you'll see the PostgreSQL prompt. Type `\q` to exit.

---

## 3. WSL (Windows Subsystem for Linux)

### Install WSL

```powershell
# Run PowerShell as Administrator
wsl --install
```

This will:
- Install WSL 2
- Install Ubuntu (default distribution)
- Prompt you to create a Linux username and password

**IMPORTANT: Restart your computer after installation.**

### Verify Installation

```powershell
wsl --list --verbose
```

---

## 4. Docker Desktop

### Install Docker Desktop

**Download from:** https://docs.docker.com/desktop/setup/install/windows-install/

1. Download Docker Desktop for Windows
2. Run the installer
3. **IMPORTANT:** Ensure "Use WSL 2 instead of Hyper-V" is checked
4. Complete installation
5. **Restart your computer**

### Launch Docker Desktop

Search for "Docker Desktop" in Start menu and launch it.

Wait for Docker to fully start (whale icon in system tray).

### Verify Installation

```powershell
docker --version
docker compose version
docker run hello-world
```

---

## 5. Node.js & NPM

### Install Node.js

**Download from:** https://nodejs.org/

1. Download Node.js 20.x LTS (Long Term Support)
2. Run the installer
3. Use all default settings
4. **Check the box:** "Automatically install the necessary tools"

### Verify Installation

```powershell
node --version
npm --version
```

### Install Global NPM Packages

```powershell
npm install -g typescript tsx npm-check-updates pm2
```

**Why:**
- `typescript` - TypeScript compiler
- `tsx` - Execute TypeScript files directly
- `npm-check-updates` - Update dependencies easily
- `pm2` - Process manager for Node.js applications

---

## 6. AWS CLI

### Install AWS CLI v2

**Download from:** https://awscli.amazonaws.com/AWSCLIV2.msi

1. Download the MSI installer
2. Run the installer
3. Use default settings
4. Complete installation

### Configure AWS CLI

```powershell
aws configure
```

**You will be prompted for:**
- **AWS Access Key ID:** (from your IAM user)
- **AWS Secret Access Key:** (from your IAM user)
- **Default region:** (e.g., `us-east-1`)
- **Default output format:** `json`

### Required AWS IAM Permissions

Your IAM user must have these policies attached:
- AdministratorAccess (or)
- AWSCloudFormationFullAccess
- IAMFullAccess
- CloudWatchLogsFullAccess
- AmazonS3FullAccess
- AmazonVPCFullAccess
- AmazonECS_FullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonBedrockFullAccess
- AmazonDynamoDBFullAccess
- AmazonSESFullAccess

### Verify AWS Configuration

```powershell
aws sts get-caller-identity
```

---

## 7. Cursor IDE

### Download Cursor IDE

Visit: https://cursor.com/

Download the Windows version.

### Install Cursor

1. Run the downloaded installer
2. Use default settings
3. Complete installation
4. Launch Cursor (optional - can wait)

### Required Subscription

You need a Cursor subscription:
- **Minimum:** Pro ($20/month)
- **Recommended:** Ultra (unlimited usage)

**Do NOT configure Cursor yet** - we'll handle that after global configuration deployment.

---

## 8. MCP Server Dependencies

### Install Required Node Packages Globally

```powershell
npm install -g `
  @modelcontextprotocol/server-playwright `
  @modelcontextprotocol/server-filesystem `
  @modelcontextprotocol/server-git
```

---

## 9. Obtain API Keys

Before proceeding, obtain API keys from these services:

### Critical Services (Required)

| Service | Purpose | URL |
|---------|---------|-----|
| **Apify** | Web automation & login handling | https://console.apify.com/settings/integrations |
| **Exa** | AI-optimized search engine | https://dashboard.exa.ai/api-keys |
| **OpenRouter** | Access to advanced AI models | https://openrouter.ai/settings/keys |

### Recommended Services

| Service | Purpose | URL |
|---------|---------|-----|
| **Perplexity** | Contextual Q&A and research | https://www.perplexity.ai/account/api/keys |
| **Ref** | Documentation search | https://ref.tools/dashboard |

### Optional Services

| Service | Purpose | URL |
|---------|---------|-----|
| **Stripe** | Payment system integration | https://dashboard.stripe.com/test/apikeys |
| **Gemini** | Google AI models | https://aistudio.google.com/app/apikey |
| **OpenAI** | GPT models (direct access) | https://platform.openai.com/api-keys |

### Save Your Keys Securely

Create a temporary file to store them:

```powershell
notepad $env:USERPROFILE\api-keys-temp.txt
```

Paste your keys in this format:

```
APIFY_API_TOKEN=your_token_here
EXA_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
REF_API_KEY=your_key_here
STRIPE_SECRET_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

**IMPORTANT:** Keep this file secure. You'll use it in the next steps.

---

## 10. Environment Variables Setup

### Global Environment Variables

These will be stored in `%UserProfile%\.cursor\.env` for use across all projects.

```powershell
# Create .cursor directory
New-Item -Path "$env:USERPROFILE\.cursor" -ItemType Directory -Force

# Create .env file
notepad "$env:USERPROFILE\.cursor\.env"
```

**Add your environment variables (BOTH KEYS AND VALUES):**

```bash
# MCP Server API Keys
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EXA_API_KEY=exa_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
REF_API_KEY=ref_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional API Keys
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database Configuration (Global Defaults)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password_here

# AWS Configuration (if not using AWS CLI)
AWS_ACCESS_KEY_ID=AKIA2DZSOUO2K5EI4QWR
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_DEFAULT_REGION=us-east-1

# SMTP Configuration (for development - MailHog)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_SECURE=false

# AWS SES Configuration (for production)
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
AWS_SES_SMTP_USER=your_ses_smtp_username
AWS_SES_SMTP_PASSWORD=your_ses_smtp_password

# Email Addresses
SMTP_FROM_EMAIL=noreply@yourdomain.com
DEFAULT_EMAIL=info@yourdomain.com
EMAIL_MODE=development

# Node Environment
NODE_ENV=development

# Base URLs
NEXT_PUBLIC_BASE_URL=http://localhost:3000
```

**NOTE:** Replace all `xxxxx` placeholders with your actual API keys and values.

Save and close the file.

---

## 11. Verification Checklist

Run these commands to verify all software is installed correctly:

```powershell
# PostgreSQL
psql -h localhost -U postgres -d postgres -c "SELECT version();"

# WSL
wsl --list --verbose

# Docker
docker --version
docker compose version
docker run hello-world

# Node.js & NPM
node --version
npm --version
tsx --version
pm2 --version

# AWS CLI
aws --version
aws sts get-caller-identity

# Git
git --version

# Cursor IDE
Test-Path "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe"
```

**All commands should return version information or successful output.**

---

## 12. Final Setup Steps

### Create Projects Directory

```powershell
New-Item -Path "$env:USERPROFILE\Projects" -ItemType Directory -Force
Set-Location "$env:USERPROFILE\Projects"
```

### Copy Global Configuration

**After this software installation is complete, copy the prompt below into Cursor IDE to deploy the global configuration and complete your setup.**

---

## 📋 COPY THIS PROMPT INTO CURSOR IDE

```prompt
I have completed all software installation on Windows 10/11. Please help me deploy the global Cursor configuration system:

1. Create the global-cursor-repo structure at %UserProfile%\.cursor\global-cursor-repo\
2. Populate it with all global rules, workflows, scripts, utilities, reasoning, and history
3. Configure MCP servers (mcp.json) for Windows with correct paths
4. Set up environment variable loading from %UserProfile%\.cursor\.env
5. Create the "For Every Project" template folder at %UserProfile%\.cursor\Deployment\For Every Project\
6. Include all necessary setup scripts (startup.ps1, automated-setup.ps1, etc.) for Windows
7. Create junction links to Global-* folders
8. Set up the memory structure system
9. Verify all systems are operational

My environment details:
- OS: Windows 10/11 (PowerShell)
- Home Directory: %UserProfile%
- PostgreSQL: localhost:5432
- Docker: Docker Desktop running
- WSL: Ubuntu installed
- Node.js: v20.x LTS
- AWS CLI: Configured
- API Keys: Stored in %UserProfile%\.cursor\.env (with actual values)

My complete .env file is already configured with:
- All MCP API keys (Apify, Exa, OpenRouter, Perplexity, Ref)
- PostgreSQL credentials
- AWS credentials (access key, secret key, region)
- SMTP settings (localhost for dev, SES for production)
- Email addresses
- Node environment settings
- Base URLs

Please proceed with the complete setup using my existing .env file and let me know when I can start creating my first project.
```

---

## 🎉 Next Steps

After running the prompt above in Cursor IDE:

1. **Wait for AI to complete global configuration**
2. **Verify setup is complete**
3. **Create your first project** using the "For Every Project" template
4. **Start developing** with all 20+ advanced features

---

## 🔧 Troubleshooting

### PostgreSQL Connection Issues

```powershell
# Check if PostgreSQL service is running
Get-Service postgresql-*

# Start PostgreSQL if stopped
Start-Service postgresql-x64-15

# Check pgpass.conf
Get-Content "$env:APPDATA\postgresql\pgpass.conf"
```

### Docker Desktop Issues

```powershell
# Verify Docker is running
docker ps

# If not running, start Docker Desktop manually
Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
```

### WSL Issues

```powershell
# Check WSL status
wsl --status

# Restart WSL
wsl --shutdown
wsl
```

### Node.js/NPM Issues

```powershell
# Clear NPM cache
npm cache clean --force

# Update NPM
npm install -g npm@latest
```

### AWS CLI Issues

```powershell
# Reconfigure AWS CLI
aws configure

# Check credentials
Get-Content "$env:USERPROFILE\.aws\credentials"

# Test connection
aws sts get-caller-identity
```

---

**Installation Complete!** 🚀

Now proceed to Cursor IDE and use the prompt above to complete your setup.

