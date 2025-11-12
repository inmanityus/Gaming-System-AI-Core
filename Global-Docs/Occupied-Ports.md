# Occupied Ports Registry - Windows Edition

**Purpose**: Maintain a list of all ports used across all projects on Windows to prevent conflicts  
**Last Updated**: 2025-11-05  
**Port Spacing Rule**: New ports must be at least 10 numbers away from any occupied port  
**Platform**: Windows 10/11 Native

***

## 🚨 Port Allocation Rules

1. **Minimum Spacing**: 10 ports between any two application servers
2. **Windows OS Services**: NEVER use ports occupied by Windows system services
3. **Infrastructure Ports**: Document all infrastructure ports (Docker, databases, PostgreSQL, etc.)
4. **Reserved Ranges**: Mark ranges as reserved when allocating a port
5. **Update Immediately**: All projects must update this file when claiming ports
6. **Check Before Allocating**: Always check this file before selecting a port
7. **Cursor Services**: Protect Cursor MCP servers and Timer Service ports

***

## 📋 Windows System Services (DO NOT USE - PROTECTED)

### Windows Core Services (Protected - Never Use)

- **135**: RPC Endpoint Mapper (svchost)
- **139**: NetBIOS Session Service (System)
- **445**: Microsoft-DS Active Directory (System)
- **5357**: Web Services for Devices (System)
- **49664-49682**: Windows Dynamic Port Range (System services)

### Windows Application Services (Protected - Never Use)

- **843**: Dropbox (73876)
- **2179**: Hyper-V Virtual Machine Management (vmms)
- **5040**: Windows Service (svchost)
- **7680**: Windows Service (svchost)

**Reserved Range**: 135-139, 445, 49664-50000 (Windows System Services)

***

## 🔧 Infrastructure Services (Shared Across Projects)

### Database Services

- **5432**: PostgreSQL (Primary database server)
- **5443**: WSL Relay (Windows Subsystem for Linux)
- **6432**: PgBouncer (Connection pooler)

**Reserved Range**: 5432-5450 (Database services)

### Docker Services

- **3001-3002**: Docker Backend (com.docker.backend)
- **6379**: Redis Cache (Docker container)
- **8000**: Docker Service (com.docker.backend)

**Reserved Range**: 3001-3002, 6379, 8000 (Docker infrastructure)

### AI Testing System (Body Broker QA)

**Project Location**: `E:\Vibe Code\Gaming System\AI Core\ai-testing-system`

- **8010**: Body Broker QA Orchestrator (FastAPI - validation reports)

**Reserved Range**: 8010 (QA Orchestrator API)

**Port Selection Rationale**:
- Port 8010 is 10 ports away from Docker (8000) - meets minimum spacing rule
- No conflicts with Windows system services
- No conflicts with other projects

### Email Services

- **1025**: MailHog SMTP (mailhog)
- **8025**: MailHog Web UI (mailhog)

**Reserved Range**: 1025, 8025 (Email testing services)

### Monitoring & Development Tools

- **8080**: Apache HTTP Server (httpd)
- **9323**: Node.js Service (node)
- **11434**: Ollama AI Service (ollama)
- **45623**: Node.js Service (node)
- **53517-53518**: Node.js Services (node)
- **62075**: Node.js Service (node)
- **59220**: Ollama App

**Reserved Range**: 8080, 9323, 11434, 45623, 53517-53518, 59220, 62075 (Development tools)

### Third-Party Applications (Protected - Never Use)

- **6463**: Discord
- **7679**: Google Drive File Stream
- **13333**: Razer Cortex
- **15292-15393**: Adobe Desktop Service
- **16494**: Adobe Desktop Service
- **19292**: Adobe Collab Sync
- **27036-27060**: Steam
- **39300**: OS Server
- **42050**: OneDrive Sync Service
- **43227**: MBAM Service (Malwarebytes)
- **46123**: iCUE (Corsair)
- **51201**: Chrome
- **55000**: Razer Cortex
- **60992**: iCUE Device Plugin Host
- **65411-65413**: Steam

**Reserved Range**: Various (Third-party applications - do not use)

***

## 📋 Project Port Registry

### Be Free Fitness (KEEP - Existing Project)

**Project Location**: `E:\Vibe Code\Be Free Fitness\Website`

#### Frontend Services (Node/React)

- **3000**: Be Free Fitness Web Frontend (Next.js)

#### Backend Services (Node/Express)

- **4000**: Be Free Fitness API Server

**Reserved Range**: 
- 3000 (Frontend - Be Free Fitness)
- 4000 (Backend API - Be Free Fitness)

**Note**: Port 3000 is currently occupied by Be Free Fitness. New projects must use ports 10+ away from 3000.

### Drone Sentinels Communications System

**Project Location**: `E:\Vibe Code\Drone Sentinels\Comms System`

#### Frontend Services (Next.js)

- **3010**: Drone Sentinels Web Frontend (Next.js dev server)

#### Database Services

- **5432**: PostgreSQL (Shared with other projects)

**Reserved Range**: 
- 3010 (Frontend - Drone Sentinels)
- 5432 (Database - Shared PostgreSQL)

**Port Selection Rationale**:
- Port 3010 is 10 ports away from Be Free Fitness (3000)
- Port 3010 is 9 ports away from Docker (3001-3002) - acceptable as Docker is infrastructure
- No conflicts with Windows system services
- No conflicts with Cursor services

***

## 🔍 Cursor Support Services (PROTECTED - NEVER USE)

### Cursor MCP Servers

Cursor uses Node.js processes for MCP (Model Context Protocol) servers. These are identified by:
- Command line containing "mcp" or "@modelcontextprotocol" or "npx"
- Process name: "node"
- Typically use dynamic ports

**Protection Rule**: NEVER kill Node.js processes that match MCP server patterns. Always use `safe-kill-servers.ps1` which protects MCP servers.

**Reserved Range**: Dynamic (MCP servers use ephemeral ports)

### Timer Service

The Timer Service for Cursor AI sessions runs as a background PowerShell job and does NOT use a network port. It uses:
- PowerShell background jobs
- File-based status tracking (`.cursor/ai-logs/timer-status.json`)

**Port Usage**: NONE (File-based only)

### Memory Construct Service

The Memory Construct service is file-based and does NOT use network ports. It uses:
- File-based rule storage (`.cursor/memory-construct/`)
- JSON configuration files

**Port Usage**: NONE (File-based only)

**Reserved Range**: N/A (File-based services only)

***

## 🔍 Port Availability Guide

### Available Port Ranges (10+ port spacing enforced)

#### Node.js Frontend Applications (3000-3999 range)

- ⚠️ **3003-3009**: Available but close to Be Free Fitness (3000) - not recommended
- ✅ **3011-3999**: Available for new Node.js frontend apps (recommended: 3010+)
- ✅ **3010**: ASSIGNED to Drone Sentinels Communications System

#### Node.js Backend/API Services (4000-4999 range)

- ⚠️ **4001-4009**: Available but close to Be Free Fitness API (4000) - not recommended
- ✅ **4010-4999**: Available for new Node.js backend/API services (recommended: 4010+)

#### Python/FastAPI Services (8000-8999 range)

- ⚠️ **8001-8009**: Available but close to Docker (8000) - not recommended
- ✅ **8010-8999**: Available for new Python/FastAPI services (recommended: 8010+)

#### Custom Services (9000-9999 range)

- ✅ **9000-9999**: Available for custom services (avoid 9000 if Docker uses it)

#### High Ports (10000+)

- ✅ **10000+**: Fully available for any service type (except those occupied by third-party apps)

***

## 📝 How to Add a New Project

When creating a new project:

1. **Check Available Ranges**: Review this file for available ports
2. **Check Windows Services**: Verify port is not used by Windows system services
3. **Check Cursor Services**: Verify port is not used by Cursor MCP servers
4. **Select Port**: Choose a port at least 10 numbers away from occupied ports
5. **Reserve Range**: If multiple services, reserve a range (e.g., 4010-4020)
6. **Update This File**: Add your project and ports to this registry
7. **Update Project Files**: Update .env.example, .cursorrules, server.ts, etc.
8. **Git Commit**: Commit this file immediately to prevent conflicts

***

## 🔧 Port Selection Examples

### Example 1: New Node.js Frontend

- Current Node.js frontend ports: 3000 (Be Free Fitness), 3010 (Drone Sentinels)
- Minimum spacing: 10 ports
- ✅ **Recommended**: 3020 or higher
- ❌ **Too close**: 3001-3009, 3011-3019

### Example 2: New Node.js Backend API

- Current Node.js backend ports: 4000 (Be Free Fitness)
- Minimum spacing: 10 ports
- ✅ **Recommended**: 4010 or higher
- ❌ **Too close**: 4001-4009

### Example 3: New Multi-Service Project

- Need 5 ports for microservices
- Current ranges: See above
- ✅ **Recommended**: Reserve 4010-4020 (10 ports) for backend services
- ✅ **Recommended**: Reserve 3020-3030 (10 ports) for frontend services
- Update both this file and project configs

### Example 4: Avoiding Windows System Ports

- Windows uses ports 49664-50000 for dynamic allocation
- ✅ **Recommended**: Use ports below 49000 or above 50000
- ❌ **Avoid**: Ports 49664-50000 (Windows system range)

***

## 🚨 Conflict Resolution

If two projects claim the same port:

1. **First Commit Wins**: Check git history of this file
2. **Earlier Timestamp**: If simultaneous commits, earlier timestamp wins
3. **Negotiate**: Contact other project owner if needed
4. **Update Loser**: Losing project must select new port and update
5. **Windows Service Conflicts**: If conflict with Windows service, project MUST change port (Windows services take priority)

***

## 🛡️ Cursor Service Protection Rules

### MCP Server Protection

**CRITICAL**: Cursor MCP servers use Node.js processes with dynamic ports. To protect them:

1. **Never kill all Node.js processes**: `Get-Process node | Stop-Process` is FORBIDDEN
2. **Always use safe-kill scripts**: Use `scripts/safe-kill-servers.ps1` which identifies MCP servers
3. **MCP Detection**: MCP servers are identified by command line patterns:
   - Contains "mcp"
   - Contains "@modelcontextprotocol"
   - Contains "npx"
4. **Verification**: After killing servers, verify MCP servers still running

### Timer Service Protection

The Timer Service does NOT use network ports. It is file-based only:
- Status file: `.cursor/ai-logs/timer-status.json`
- Log file: `.cursor/ai-logs/timer-service.log`
- Job ID file: `.cursor/ai-logs/timer-jobid.txt`

**No port conflicts possible** - Timer Service is file-based.

### Memory Construct Protection

The Memory Construct does NOT use network ports. It is file-based only:
- Configuration: `.cursor/memory-construct/enforcement-active.json`
- Rules memory: `.cursor/memory-construct/rules-memory.json`
- Enforcement log: `.cursor/memory-construct/enforcement-log.md`

**No port conflicts possible** - Memory Construct is file-based.

***

## 📚 Related Documentation

- **Port Selection Tool**: `Global-Scripts/select-available-port.ps1` (Windows PowerShell version)
- **Project Setup**: `One-Time-New-Project-Setup-Prompt.md` (in project root)
- **Cursor Rules**: `.cursorrules` (each project)
- **Safe Server Shutdown**: `scripts/safe-kill-servers.ps1` (each project)

***

## 🔍 Windows-Specific Port Considerations

### Windows Dynamic Port Range

Windows uses ports **49664-50000** for dynamic port allocation. These are automatically assigned by Windows and should NEVER be used by applications.

**Rule**: Avoid ports 49664-50000 for application services.

### Windows RPC Ports

Windows uses ports **135** and **139** for RPC and NetBIOS. These are system services and must be protected.

**Rule**: NEVER use ports 135, 139, or 445 (Windows system services).

### Windows Hyper-V Ports

Hyper-V uses various ports for virtual machine management. Port **2179** is used by Hyper-V Virtual Machine Management.

**Rule**: Avoid ports used by Hyper-V if running virtual machines.

### PowerShell Background Jobs

PowerShell background jobs (like Timer Service) do NOT use network ports. They are process-based only.

**Rule**: File-based services (PowerShell jobs, file watchers) do not need port reservations.

***

**Last Updated**: 2025-11-05  
**Maintainer**: Global AI Memory System  
**Format Version**: 2.0 (Windows Native)  
**Platform**: Windows 10/11

