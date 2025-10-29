# Gaming System AI Core - Project Services

## Service Overview

This document contains information about all project services, their ports, and management commands for the Gaming System AI Core project.

## Project Services

### 1. Frontend Server (Next.js)
- **Port**: 3000
- **Description**: Next.js development server for the Gaming System AI Core application
- **Startup Command**: 
  ```powershell
  npm run dev
  ```
- **Health Check Command**: 
  ```powershell
  try { $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host "Frontend Server: Healthy" } else { Write-Host "Frontend Server: Unhealthy - Status $($response.StatusCode)" } } catch { Write-Host "Frontend Server: Unresponsive - $($_.Exception.Message)" }
  ```
- **Shutdown Command**: 
  ```powershell
  .\scripts\safe-kill-servers.ps1
  ```

### 2. PostgreSQL Database
- **Port**: 5443
- **Description**: PostgreSQL database running in Docker container
- **Startup Command**: 
  ```powershell
  docker-compose up -d
  ```
- **Health Check Command**: 
  ```powershell
  psql -h localhost -U postgres -d gaming_system_ai_core -p 5443 -c "SELECT version();"
  ```
- **Shutdown Command**: 
  ```powershell
  docker-compose down
  ```

## Project Rules

## MCP Server Protection
**CRITICAL RULE**: NEVER kill Node.js processes except those listening on ports 3000-4999 (application servers only). MCP servers run on different ports and are shared across multiple Cursor IDEs. ONLY kill Node processes on ports 3000-4999. Use the safe-kill scripts provided.

### Safe Server Shutdown
Always use the provided script to safely shut down servers:
```powershell
.\scripts\safe-kill-servers.ps1
```

This script:
- Only kills processes on project-specific ports (3000, 5443)
- Protects MCP servers from accidental termination
- Verifies MCP servers are still running after shutdown

### Testing MCP Protection
To test if MCP servers are properly protected:
```powershell
.\scripts\safe-kill-servers.ps1 -TestOnly
```

---

*This document should be referenced at the start of each development session to ensure proper service management and adherence to project-specific rules.*
