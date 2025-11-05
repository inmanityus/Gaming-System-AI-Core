# MCP Server Protection System

## Overview

MCP (Model Context Protocol) servers are Node.js processes that power Cursor's AI features. They should **NEVER** be killed during development as this breaks AI functionality and requires restarting Cursor.

## Problem

Traditional `Get-Process -Name "node" | Stop-Process -Force` commands kill **ALL** Node.js processes, including:
- ✅ Application servers (API, Web) - OK to kill
- ❌ MCP servers - NEVER kill these!

## Solution

We've created a comprehensive MCP protection system:

### 1. Protection Script: `scripts/protect-mcp-servers.ps1`

**Functions:**
- `Get-MCPServerProcesses` - Identifies MCP server PIDs
- `Stop-ApplicationServersOnly` - Safely kills only app servers
- `Test-MCPProtection` - Tests the protection system

**How it works:**
```powershell
# Identifies MCP servers by command line patterns:
- "mcp" in command line
- "@modelcontextprotocol" in command line
- "npx" without npm/pnpm/next/nodemon
```

### 2. Safe Shutdown Script: `scripts/safe-kill-servers.ps1`

**Usage:**
```powershell
# Stop only application servers (API + Web)
.\scripts\safe-kill-servers.ps1

# Also stop database
.\scripts\safe-kill-servers.ps1 -IncludeDatabase

# Test MCP protection without killing anything
.\scripts\safe-kill-servers.ps1 -TestOnly
```

### 3. Integration with Startup

The `startup.ps1` script now imports MCP protection functions automatically.

## Best Practices

### ✅ DO:
```powershell
# Import protection first
. ".\scripts\protect-mcp-servers.ps1"

# Use safe shutdown
Stop-ApplicationServersOnly

# Or use the wrapper script
.\scripts\safe-kill-servers.ps1
```

### ❌ DON'T:
```powershell
# NEVER do this (kills MCP servers!)
Get-Process -Name "node" | Stop-Process -Force

# NEVER do this (same problem)
Stop-Process -Name "node" -Force
```

## Identifying MCP Servers

### Manual Check:
```powershell
Get-Process -Name "node" | ForEach-Object {
    $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    if ($cmd -match "mcp") {
        Write-Host "MCP Server: PID $($_.Id)"
        Write-Host "  $cmd"
    }
}
```

### Using Our Script:
```powershell
. ".\scripts\protect-mcp-servers.ps1"
Test-MCPProtection
```

## Troubleshooting

### If MCP Servers Get Killed:
1. **Restart Cursor** - Only way to restart MCP servers
2. **Check scripts** - Make sure you're using the safe shutdown functions
3. **Update patterns** - If new MCP servers aren't detected, update patterns in `protect-mcp-servers.ps1`

### If Application Servers Won't Stop:
1. Check if they're being misidentified as MCP servers
2. Add more specific patterns to the kill logic
3. Use Task Manager as last resort (but avoid MCP server PIDs!)

## Testing

Test the protection system anytime:
```powershell
.\scripts\safe-kill-servers.ps1 -TestOnly
```

This will show:
- How many MCP servers are detected
- Their PIDs
- Total Node.js processes

## Future Improvements

1. **Process naming** - Ask Cursor team about MCP server naming patterns
2. **Port detection** - Identify MCP servers by port numbers
3. **Config file** - Store known MCP server PIDs in a file
4. **Auto-refresh** - Periodically update MCP server list

## Emergency Recovery

If you accidentally kill MCP servers:
1. Save all your work
2. Close Cursor completely
3. Restart Cursor
4. Wait for MCP servers to initialize (~30 seconds)
5. Resume development

---

**Remember:** When in doubt, **DON'T** kill all Node processes. Use the safe shutdown script!





