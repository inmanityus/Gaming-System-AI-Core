# MCP Server Protection Script
# This script identifies and protects MCP servers from being killed

<#
.SYNOPSIS
    Identifies MCP server processes and provides safe kill functions
.DESCRIPTION
    MCP (Model Context Protocol) servers run as Node.js processes but should
    NEVER be killed during development. This script helps identify them and
    provides safe alternatives for killing only application servers.
#>

function Get-MCPServerProcesses {
    <#
    .SYNOPSIS
        Gets all MCP server Node.js processes
    .OUTPUTS
        Array of process IDs for MCP servers
    #>
    
    $mcpProcessIds = @()
    
    Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            
            # Identify MCP servers by command line patterns
            if ($cmdLine -and (
                $cmdLine -match "mcp" -or
                $cmdLine -match "@modelcontextprotocol" -or
                $cmdLine -match "npx.*@" -or
                ($cmdLine -match "npx" -and $cmdLine -notmatch "npm|pnpm|nodemon|ts-node|next|vite|webpack")
            )) {
                $mcpProcessIds += $_.Id
                Write-Host "[MCP PROTECTION] Identified MCP server: PID $($_.Id)" -ForegroundColor Green
                Write-Host "  Command: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))..." -ForegroundColor Gray
            }
        } catch {
            # If we can't get command line, preserve the process to be safe
            Write-Host "[MCP PROTECTION] Could not inspect PID $($_.Id) - preserving as potential MCP server" -ForegroundColor Yellow
            $mcpProcessIds += $_.Id
        }
    }
    
    return $mcpProcessIds
}

function Stop-ApplicationServersOnly {
    <#
    .SYNOPSIS
        Stops only application Node.js servers, preserving MCP servers
    .DESCRIPTION
        This function kills npm/pnpm/next/nodemon processes while protecting MCP servers
    #>
    
    Write-Host "`n🛡️  MCP-SAFE SERVER SHUTDOWN`n" -ForegroundColor Cyan
    
    # Get MCP server PIDs first
    $mcpPids = Get-MCPServerProcesses
    
    if ($mcpPids.Count -gt 0) {
        Write-Host "✅ Protected $($mcpPids.Count) MCP server(s)`n" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No MCP servers detected (they may not be running)`n" -ForegroundColor Yellow
    }
    
    # Now kill only application servers
    $killedCount = 0
    Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object {
        $pid = $_.Id
        
        # Skip if this is an MCP server
        if ($mcpPids -contains $pid) {
            Write-Host "[MCP PROTECTION] Skipping MCP server: PID $pid" -ForegroundColor Green
            return
        }
        
        try {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $pid" -ErrorAction SilentlyContinue).CommandLine
            
            # Kill only application servers (npm, pnpm, next, nodemon, ts-node, vite, webpack)
            if ($cmdLine -and ($cmdLine -match "npm|pnpm|nodemon|ts-node|next|vite|webpack|express|fastify")) {
                Write-Host "[KILL] Application server: PID $pid" -ForegroundColor Red
                Write-Host "  Command: $($cmdLine.Substring(0, [Math]::Min(60, $cmdLine.Length)))..." -ForegroundColor Gray
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                $killedCount++
            } else {
                Write-Host "[PRESERVE] Unknown/other Node process: PID $pid (not an app server)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[PRESERVE] Could not inspect PID $pid - preserving to be safe" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n✅ Killed $killedCount application server(s)" -ForegroundColor Green
    Write-Host "✅ MCP servers remain protected`n" -ForegroundColor Green
}

function Test-MCPProtection {
    <#
    .SYNOPSIS
        Tests the MCP protection system
    #>
    
    Write-Host "`n🧪 MCP PROTECTION TEST`n" -ForegroundColor Cyan
    
    $mcpPids = Get-MCPServerProcesses
    
    Write-Host "`nFound $($mcpPids.Count) MCP server(s):" -ForegroundColor Cyan
    
    if ($mcpPids.Count -eq 0) {
        Write-Host "  ⚠️  No MCP servers detected!" -ForegroundColor Yellow
        Write-Host "  This could mean:" -ForegroundColor Yellow
        Write-Host "    1. MCP servers are not running" -ForegroundColor Gray
        Write-Host "    2. They're running but not detectable by our patterns" -ForegroundColor Gray
        Write-Host "    3. Cursor manages them separately`n" -ForegroundColor Gray
    } else {
        $mcpPids | ForEach-Object {
            $process = Get-Process -Id $_ -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "  ✅ PID: $_" -ForegroundColor Green
            }
        }
        Write-Host ""
    }
    
    Write-Host "Total Node.js processes: $((Get-Process -Name 'node' -ErrorAction SilentlyContinue).Count)" -ForegroundColor Cyan
    Write-Host ""
}

# Functions are now available globally when dot-sourced
# No need for Export-ModuleMember when using dot-sourcing (. script.ps1)

