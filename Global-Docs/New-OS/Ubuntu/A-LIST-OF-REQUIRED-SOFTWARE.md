# Required Software Installation Guide - Ubuntu/Linux

**Complete installation guide for all software needed to run the Cursor IDE Advanced Development System on Ubuntu Linux.**

---

## 📋 Prerequisites

- Ubuntu 20.04 LTS or later (or compatible Linux distribution)
- Sudo/root access
- Internet connection
- At least 20GB free disk space

---

## Installation Order

**Install in this exact order to avoid dependency issues:**

1. System Updates & Essential Tools
2. PostgreSQL Database Server
3. Docker & Docker Compose
4. Node.js & NPM
5. AWS CLI
6. Cursor IDE
7. MCP Server Dependencies

---

## 1. System Updates & Essential Tools

### Update System Packages

```bash
sudo apt update && sudo apt upgrade -y
```

### Install Essential Build Tools

```bash
sudo apt install -y \
  build-essential \
  curl \
  wget \
  git \
  ca-certificates \
  gnupg \
  lsb-release \
  software-properties-common \
  apt-transport-https
```

**Why:** These tools are required for building and installing other software packages.

---

## 2. PostgreSQL Database Server

### Install PostgreSQL

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Import repository signing key
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15
```

### Start PostgreSQL Service

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

### Set PostgreSQL Password

```bash
# Switch to postgres user
sudo -i -u postgres

# Set password for postgres user
psql -c "ALTER USER postgres PASSWORD 'YOUR_STRONG_PASSWORD_HERE';"

# Exit postgres user
exit
```

### Configure Automatic Login

Create a `.pgpass` file in your home directory:

```bash
# Create .pgpass file
echo "localhost:5432:*:postgres:YOUR_PASSWORD_HERE" > ~/.pgpass

# Set permissions (CRITICAL - must be 0600)
chmod 0600 ~/.pgpass
```

### Test Connection

```bash
psql -h localhost -U postgres -d postgres
```

If successful, you'll see the PostgreSQL prompt. Type `\q` to exit.

---

## 3. Docker & Docker Compose

### Install Docker

```bash
# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Add Your User to Docker Group

```bash
sudo usermod -aG docker $USER
```

**IMPORTANT:** Log out and log back in for group changes to take effect.

### Verify Installation

```bash
docker --version
docker compose version
docker run hello-world
```

---

## 4. Node.js & NPM

### Install Node.js (LTS version via NodeSource)

```bash
# Download and install Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

### Install Global NPM Packages

```bash
# Install essential global packages
sudo npm install -g \
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

## 5. AWS CLI

### Install AWS CLI v2

```bash
# Download AWS CLI installer
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip and install
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
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

## 6. Cursor IDE

### Download Cursor IDE

Visit: https://cursor.com/

Download the Linux AppImage version.

### Install Cursor

```bash
# Create applications directory
mkdir -p ~/Applications

# Move downloaded AppImage
mv ~/Downloads/cursor-*.AppImage ~/Applications/cursor.AppImage

# Make executable
chmod +x ~/Applications/cursor.AppImage

# Create desktop entry
cat > ~/.local/share/applications/cursor.desktop <<'EOF'
[Desktop Entry]
Name=Cursor IDE
Exec=$HOME/Applications/cursor.AppImage
Icon=cursor
Type=Application
Categories=Development;IDE;
EOF
```

### Launch Cursor

```bash
~/Applications/cursor.AppImage
```

Or search for "Cursor" in your application launcher.

### Required Subscription

You need a Cursor subscription:
- **Minimum:** Pro ($20/month)
- **Recommended:** Ultra (unlimited usage)

**Do NOT configure Cursor yet** - we'll handle that after global configuration deployment.

---

## 7. MCP Server Dependencies

### Install Required Node Packages Globally

```bash
# Install MCP server dependencies
cd ~
npm install -g \
  @modelcontextprotocol/server-playwright \
  @modelcontextprotocol/server-filesystem \
  @modelcontextprotocol/server-git
```

---

## 8. Obtain API Keys

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

## 9. Environment Variables Setup

### Global Environment Variables

These will be stored in `~/.cursor/.env` for use across all projects.

```bash
# Create .cursor directory
mkdir -p ~/.cursor

# Create .env file
nano ~/.cursor/.env
```

**Add your environment variables (KEYS ONLY - fill in your actual values):**

```bash
# MCP Server API Keys
APIFY_API_TOKEN=
EXA_API_KEY=
OPENROUTER_API_KEY=
PERPLEXITY_API_KEY=
REF_API_KEY=

# Optional API Keys
STRIPE_SECRET_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=

# Database Configuration (Global Defaults)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=

# AWS Configuration (if not using AWS CLI)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
```

### Load Environment Variables in Shell

Add to your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
# Add this line to ~/.bashrc
echo 'export $(grep -v "^#" ~/.cursor/.env | xargs)' >> ~/.bashrc

# Reload shell configuration
source ~/.bashrc
```

---

## 10. Verification Checklist

Run these commands to verify all software is installed correctly:

```bash
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
ls -lh ~/Applications/cursor.AppImage
```

**All commands should return version information or successful output.**

---

## 11. Final Setup Steps

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
I have completed all software installation on Ubuntu Linux. Please help me deploy the global Cursor configuration system:

1. Create the global-cursor-repo structure at $HOME/.cursor/global-cursor-repo/
2. Populate it with all global rules, workflows, scripts, utilities, reasoning, and history
3. Configure MCP servers (mcp.json) for Ubuntu with correct paths
4. Set up environment variable loading from $HOME/.cursor/.env
5. Create the "For Every Project" template folder at $HOME/.cursor/Deployment/For Every Project/
6. Include all necessary setup scripts (startup.sh, automated-setup.sh, etc.) adapted for Linux
7. Create symbolic links to Global-* folders
8. Set up the memory structure system
9. Verify all systems are operational

My environment details:
- OS: Ubuntu Linux
- Home Directory: $HOME
- PostgreSQL: localhost:5432
- Docker: Installed and running
- Node.js: v20.x LTS
- AWS CLI: Configured
- API Keys: Stored in $HOME/.cursor/.env

Please proceed with the complete setup and let me know when I can start creating my first project.
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
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check .pgpass permissions
ls -la ~/.pgpass
# Should show: -rw------- (600 permissions)
```

### Docker Permission Issues

```bash
# Add user to docker group (if not done)
sudo usermod -aG docker $USER

# Log out and log back in
# Or use: newgrp docker

# Verify
docker run hello-world
```

### Node.js/NPM Issues

```bash
# Clear NPM cache
npm cache clean --force

# Update NPM
sudo npm install -g npm@latest
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

---

**Installation Complete!** 🚀

Now proceed to Cursor IDE and use the prompt above to complete your setup.

