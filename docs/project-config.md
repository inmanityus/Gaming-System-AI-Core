# Gaming System AI Core - Project Configuration

## Project Details

- **Name**: Gaming-System-AI-Core
- **Type**: Deep Learning System (AI/ML focused)
- **Stack**: Next.js 15, React 19, TypeScript, ESLint
- **Purpose**: AI-powered gaming system core with deep learning capabilities

## Database Configuration

- **Host**: localhost
- **Port**: 5443 (PostgreSQL Docker container)
- **Database**: gaming_system_ai_core (auto-detected from folder structure)
- **User**: postgres (default)
- **Password**: Inn0vat1on! (default for development - CHANGE FOR PRODUCTION)

## Service Ports

- **Frontend**: 3000 (Next.js dev server - configurable via PORT env var)
- **Database**: 5443 (PostgreSQL Docker container)

## MCP Server Capabilities

These are available across ALL projects via Cursor:

### **Apify** - Web Automation & Data Extraction
- **Purpose**: Log into other websites and services
- **Capabilities**: Web scraping, form automation, login automation
- **Use Cases**: Testing external integrations, data extraction, automated workflows

### **AWS Labs (awslabs.*)** - Cloud Infrastructure Management
- **Purpose**: Interact with AWS Cloud services
- **Capabilities**: EC2, VPC, security groups, key pairs, volumes
- **Use Cases**: Infrastructure provisioning, server management, cloud deployment

### **Exa** - Superior Programmer-Oriented Search
- **Purpose**: Advanced search for developers
- **Capabilities**: Code examples, API documentation, technical solutions
- **Use Cases**: Finding implementation examples, researching libraries

### **OpenRouter AI** - Advanced AI Model Access
- **Purpose**: Access to multiple AI models beyond Claude
- **Capabilities**: GPT-4, Gemini, specialized models
- **Use Cases**: Complex problem solving, peer review, alternative perspectives

### **Perplexity Ask** - Contextualized Q&A
- **Purpose**: Highly contextualized answers
- **Capabilities**: Real-time web search, technical explanations
- **Use Cases**: Current events, latest documentation, technology updates

### **Ref** - Documentation Search
- **Purpose**: In-depth search for documentation
- **Capabilities**: Framework docs, API references, user manuals
- **Use Cases**: Understanding libraries, finding configuration options

### **Playwright** - Browser Automation
- **Purpose**: Comprehensive web browser control
- **Capabilities**: UI automation, end-user testing, screenshots
- **Use Cases**: Automated testing, web scraping, UI verification

### **Sequential Thinking** - Complex Task Breakdown
- **Purpose**: Break complex efforts into series of tasks
- **Capabilities**: Task decomposition, milestone planning
- **Use Cases**: Large features, refactoring, complex implementations

### **Stripe** - Payment System Integration
- **Purpose**: Credit card payment system access
- **Capabilities**: Create customers, products, subscriptions, invoices
- **Use Cases**: Payment processing, billing, subscription management

## Global Repository Junctions

This project links to the shared global Cursor repository via Windows junctions:

- `Global-Reasoning/` → C:\Users\kento\.cursor\global-cursor-repo\reasoning\
- `Global-History/` → C:\Users\kento\.cursor\global-cursor-repo\history\
- `Global-Scripts/` → C:\Users\kento\.cursor\global-cursor-repo\scripts\
- `Global-Workflows/` → C:\Users\kento\.cursor\global-cursor-repo\rules\
- `Global-Docs/` → C:\Users\kento\.cursor\global-cursor-repo\docs\
- `Global-Utils/` → C:\Users\kento\.cursor\global-cursor-repo\utils\

**Note**: These are Windows junction links, not actual project folders. They provide access to universal knowledge and scripts shared across all projects.

## Environment Variables

Create a `.env` file in the project root with:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5443
DB_NAME=gaming_system_ai_core
DB_USER=postgres
DB_PASSWORD=Inn0vat1on!

# Application Environment
PORT=3000
NODE_ENV=development

# Development URLs
DEV_URL=http://localhost:3000

# Production URLs
PROD_URL=https://your-production-domain.com

# AI/ML Configuration (for future features)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Notes
# - Always use PostgreSQL database for these projects
# - Port 3000 is reserved for this project's frontend
# - Port 5443 is reserved for this project's database
# - Add new sections as needed per project requirements
```

## Project Structure

```
Gaming-System-AI-Core/
├── .cursor/              # AI session memory
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── models/               # Deep learning models (future)
├── data/                 # Training and test datasets (future)
├── notebooks/            # Jupyter notebooks for experimentation (future)
├── Global-Reasoning/     # Junction → global reasoning
├── Global-History/       # Junction → global history
├── Global-Scripts/       # Junction → global scripts
├── Global-Workflows/     # Junction → global workflows
├── Global-Docs/          # Junction → global docs
├── Global-Utils/         # Junction → global utils
├── .env                  # Environment variables (git-ignored)
├── .gitignore           # Git exclusions
├── .cursorrules         # Project-specific rules
├── startup.ps1          # Session startup script
├── package.json         # Dependencies
└── README.md            # Project documentation
```

## Getting Started

1. **Link Global Repository**: 
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\Setup-Global-Junctions.ps1" -Force
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Setup Environment**:
   ```bash
   # Copy .env.example to .env and fill in your configuration
   cp .env.example .env
   ```

4. **Start Services**:
   ```bash
   # Start development server
   npm run dev

   # Start PostgreSQL database (if using Docker)
   docker-compose up -d
   ```

5. **Run Startup Script**:
   ```powershell
   .\startup.ps1
   ```

---

*This file was generated during project setup. Customize as needed for your specific project.*
