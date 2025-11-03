# Safe Server Shutdown with MCP Protection
# Gaming System AI Core
param([switch]$TestOnly)

Write-Host "[PROTECT] Stopping Gaming System AI Core servers (MCP protected)" -ForegroundColor Green

# Define project ports
$projectPorts = @(3000, 5443, 8000)

foreach ($port in $projectPorts) {
    Write-Host "Checking port $port..."
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "  Killing process on port $port" -ForegroundColor Yellow
        if (-not $TestOnly) {
            Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

# Verify MCP servers still running
$mcpCount = (Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdLine -and ($cmdLine -match "mcp|@modelcontextprotocol|npx")) {
            return $true
        }
    } catch {
        # If we can't get command line, assume it's an MCP server
        return $true
    }
    return $false
}).Count

if ($TestOnly) {
    Write-Host "[OK] Test mode - no processes were killed" -ForegroundColor Green
} else {
    Write-Host "[OK] Done. MCP servers protected: $mcpCount running" -ForegroundColor Green
}

# Additional safety check - warn if we killed too many node processes
$remainingNodeProcesses = (Get-Process node -ErrorAction SilentlyContinue).Count
if ($remainingNodeProcesses -lt 3) {
    Write-Host "[WARNING] Only $remainingNodeProcesses Node.js processes remaining" -ForegroundColor Yellow
    Write-Host "   This might indicate MCP servers were affected" -ForegroundColor Yellow
    Write-Host "   If Cursor AI features stop working, restart Cursor completely" -ForegroundColor Yellow
}