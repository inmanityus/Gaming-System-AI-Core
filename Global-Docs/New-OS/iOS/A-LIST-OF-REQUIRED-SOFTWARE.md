# Required Software Installation Guide - macOS

**Complete installation guide for all software needed to run the Cursor IDE Advanced Development System on macOS (Apple Desktop/Laptop).**

---

## 📋 Prerequisites

- macOS 12 (Monterey) or later
- Administrator access (sudo privileges)
- Internet connection
- At least 20GB free disk space
- Apple Silicon (M1/M2/M3) or Intel processor

---

## Installation Order

**Install in this exact order to avoid dependency issues:**

1. Xcode Command Line Tools
2. Homebrew Package Manager
3. PostgreSQL Database Server
4. Docker Desktop for Mac
5. Node.js & NPM
6. AWS CLI
7. Cursor IDE
8. MCP Server Dependencies

---

## 1. Xcode Command Line Tools

### Install Command Line Tools

```bash
xcode-select --install
```

Click "Install" in the dialog that appears and agree to the license.

### Verify Installation

```bash
xcode-select -p
# Should output: /Library/Developer/CommandLineTools
```

**Why:** Required for building and compiling software packages.

---

## 2. Homebrew Package Manager

### Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Add Homebrew to PATH

**For Apple Silicon (M1/M2/M3):**
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**For Intel Macs:**
```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

### Verify Installation

```bash
brew --version
```

**Why:** Homebrew is the standard package manager for macOS, making software installation simple.

---

## 3. PostgreSQL Database Server

### Install PostgreSQL

```bash
brew install postgresql@15
```

### Start PostgreSQL Service

```bash
# Start PostgreSQL now
brew services start postgresql@15

# Verify it's running
brew services list | grep postgresql
```

### Set PostgreSQL Password

```bash
# Connect to PostgreSQL
psql postgres

# Set password for postgres user (in psql prompt)
ALTER USER postgres PASSWORD 'your_strong_password_here';

# Exit psql
\q
```

### Configure Automatic Login

Create a `.pgpass` file in your home directory:

```bash
# Create .pgpass file
echo "localhost:5432:*:postgres:your_password_here" > ~/.pgpass

# Set permissions (CRITICAL - must be 0600)
chmod 0600 ~/.pgpass
```

### Test Connection

```bash
psql -h localhost -U postgres -d postgres
```

If successful, you'll see the PostgreSQL prompt. Type `\q` to exit.

---

## 4. Docker Desktop for Mac

### Install Docker Desktop

```bash
brew install --cask docker
```

### Launch Docker Desktop

```bash
open /Applications/Docker.app
```

Or search for "Docker" in Spotlight (Cmd+Space).

**First Launch:**
- Docker Desktop will ask for permissions
- Grant all requested permissions
- Wait for Docker to start (whale icon in menu bar)

### Verify Installation

```bash
docker --version
docker compose version
docker run hello-world
```

---

## 5. Node.js & NPM

### Install Node.js (LTS version)

```bash
brew install node@20
```

### Link Node.js

```bash
brew link node@20
```

### Verify Installation

```bash
node --version
npm --version
```

### Install Global NPM Packages

```bash
npm install -g \
  typescript \
  tsx \
  npm-check-updates \
  pm2
```

**Why:**
- `typescript` - TypeScript compiler
- `tsx` - Execute TypeScript files directly
- `npm-check-updates` - Update dependencies easily
- `pm2` - Process manager for Node.js applications

---

## 6. AWS CLI

### Install AWS CLI v2

```bash
brew install awscli
```

### Verify Installation

```bash
aws --version
```

### Configure AWS CLI

```bash
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

```bash
aws sts get-caller-identity
```

---

## 7. Cursor IDE

### Download Cursor IDE

Visit: https://cursor.com/

Download the macOS version (`.dmg` file).

### Install Cursor

1. Open the downloaded `.dmg` file
2. Drag Cursor.app to Applications folder
3. Eject the disk image

### Launch Cursor

```bash
open /Applications/Cursor.app
```

Or search for "Cursor" in Spotlight (Cmd+Space).

### Required Subscription

You need a Cursor subscription:
- **Minimum:** Pro ($20/month)
- **Recommended:** Ultra (unlimited usage)

**Do NOT configure Cursor yet** - we'll handle that after global configuration deployment.

---

## 8. MCP Server Dependencies

### Install Required Node Packages Globally

```bash
npm install -g \
  @modelcontextprotocol/server-playwright \
  @modelcontextprotocol/server-filesystem \
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

```bash
nano ~/api-keys-temp.txt
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

These will be stored in `~/.cursor/.env` for use across all projects.

```bash
# Create .cursor directory
mkdir -p ~/.cursor

# Create .env file
nano ~/.cursor/.env
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

### Secure the .env File

```bash
chmod 0600 ~/.cursor/.env
```

### Load Environment Variables in Shell

Add to your shell profile (`~/.zshrc` for macOS default shell):

```bash
# Add this line to ~/.zshrc
echo 'export $(grep -v "^#" ~/.cursor/.env | xargs)' >> ~/.zshrc

# Reload shell configuration
source ~/.zshrc
```

---

## 11. Verification Checklist

Run these commands to verify all software is installed correctly:

```bash
# Xcode Command Line Tools
xcode-select -p

# Homebrew
brew --version

# PostgreSQL
psql -h localhost -U postgres -d postgres -c "SELECT version();"

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
ls -lh /Applications/Cursor.app
```

**All commands should return version information or successful output.**

---

## 12. Optional: Install Additional Tools

### iTerm2 (Better Terminal)

```bash
brew install --cask iterm2
```

### VS Code Extensions Export (for migration)

```bash
brew install --cask visual-studio-code
```

### GitHub CLI

```bash
brew install gh
```

### jq (JSON processor)

```bash
brew install jq
```

---

## 13. Final Setup Steps

### Create Projects Directory

```bash
mkdir -p ~/Projects
cd ~/Projects
```

### Copy Global Configuration

**After this software installation is complete, copy the prompt below into Cursor IDE to deploy the global configuration and complete your setup.**

---

## 📋 COPY THIS PROMPT INTO CURSOR IDE

```prompt
I have completed all software installation on macOS. Please help me deploy the global Cursor configuration system:

1. Create the global-cursor-repo structure at $HOME/.cursor/global-cursor-repo/
2. Populate it with all global rules, workflows, scripts, utilities, reasoning, and history
3. Configure MCP servers (mcp.json) for macOS with correct paths
4. Set up environment variable loading from $HOME/.cursor/.env
5. Create the "For Every Project" template folder at $HOME/.cursor/Deployment/For Every Project/
6. Include all necessary setup scripts (startup.sh, automated-setup.sh, etc.) adapted for macOS
7. Create symbolic links to Global-* folders
8. Set up the memory structure system
9. Verify all systems are operational

My environment details:
- OS: macOS (zsh shell)
- Home Directory: $HOME
- PostgreSQL: localhost:5432
- Docker: Docker Desktop running
- Node.js: v20.x LTS
- AWS CLI: Configured
- API Keys: Stored in $HOME/.cursor/.env (with actual values)

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

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@15

# Check .pgpass permissions
ls -la ~/.pgpass
# Should show: -rw------- (600 permissions)
```

### Docker Desktop Issues

```bash
# Restart Docker Desktop
killall Docker && open /Applications/Docker.app

# Check status
docker ps
```

### Homebrew Issues

```bash
# Update Homebrew
brew update

# Check for issues
brew doctor
```

### Node.js/NPM Issues

```bash
# Clear NPM cache
npm cache clean --force

# Update NPM
npm install -g npm@latest
```

### AWS CLI Issues

```bash
# Reconfigure AWS CLI
aws configure

# Check credentials
cat ~/.aws/credentials

# Test connection
aws sts get-caller-identity
```

### Shell Environment Issues

```bash
# Reload shell configuration
source ~/.zshrc

# Verify environment variables loaded
env | grep -E "APIFY|EXA|POSTGRES"
```

---

## 📝 macOS-Specific Notes

### Apple Silicon vs Intel

This guide works for both Apple Silicon (M1/M2/M3) and Intel Macs. Homebrew automatically installs appropriate versions.

**Homebrew Locations:**
- Apple Silicon: `/opt/homebrew/`
- Intel: `/usr/local/`

### Default Shell

macOS Catalina+ uses `zsh` by default (not bash). All instructions use `.zshrc`.

If you're using bash, replace `.zshrc` with `.bash_profile` or `.bashrc`.

### Security & Privacy

macOS may prompt for permissions when installing or running software:
- Grant "Full Disk Access" to Terminal/iTerm2 if requested
- Grant Docker Desktop all requested permissions
- Allow Cursor IDE to access files when prompted

---

**Installation Complete!** 🚀

Now proceed to Cursor IDE and use the prompt above to complete your setup.

