# Shutdown Local Models Script
# Purpose: Stop all local AI model services (Ollama, etc.) after AWS deployment
# MANDATORY: Protects MCP servers from accidental termination
# Reference: .cursorrules - MCP Protection

param(
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== SHUTTING DOWN LOCAL MODELS ===" -ForegroundColor Yellow
Write-Host "MCP Protection: Active" -ForegroundColor Green
Write-Host ""

# Function to safely stop a process (protects MCP servers)
function Stop-ModelProcess {
    param(
        [string]$ProcessName,
        [string]$Description
    )
    
    Write-Host "Checking for $Description..." -ForegroundColor White
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        foreach ($proc in $processes) {
            try {
                # Check if it's an MCP server (protected)
                $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
                
                # MCP servers typically run with specific patterns
                if ($cmdLine -match "mcp|mcp-server|cursor.*mcp") {
                    Write-Host "  ⚠ Preserving MCP server process $($proc.Id)" -ForegroundColor Yellow
                    continue
                }
                
                # Check if it's an application server (safe to kill)
                if ($cmdLine -match "npm|pnpm|nodemon|ts-node|next|vite|webpack|express|fastify") {
                    Write-Host "  - Stopping application server process $($proc.Id)" -ForegroundColor Gray
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                }
                
                # Check if it's Ollama (local model service)
                if ($cmdLine -match "ollama|ollama serve") {
                    Write-Host "  ✓ Stopping Ollama process $($proc.Id)" -ForegroundColor Green
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                }
            } catch {
                Write-Host "  ⚠ Error checking process $($proc.Id): $_" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  ✓ No $Description processes found" -ForegroundColor Green
    }
}

# Stop Ollama
Write-Host "Step 1: Stopping Ollama..." -ForegroundColor Yellow
Stop-ModelProcess -ProcessName "ollama" -Description "Ollama"

# Stop any Python training processes (if running locally)
Write-Host ""
Write-Host "Step 2: Stopping Local Training Processes..." -ForegroundColor Yellow
$trainingProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    $cmdLine -match "srl|rlvr|train"
}

if ($trainingProcesses) {
    foreach ($proc in $trainingProcesses) {
        Write-Host "  - Stopping training process $($proc.Id)" -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  ✓ Local training processes stopped" -ForegroundColor Green
} else {
    Write-Host "  ✓ No local training processes found" -ForegroundColor Green
}

# Verify MCP servers are still running
Write-Host ""
Write-Host "Step 3: Verifying MCP Servers..." -ForegroundColor Yellow
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
$mcpServers = 0

foreach ($proc in $nodeProcesses) {
    try {
        $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdLine -match "mcp|mcp-server") {
            $mcpServers++
            Write-Host "  ✓ MCP server process $($proc.Id) preserved" -ForegroundColor Green
        }
    } catch {
        # Ignore errors
    }
}

if ($mcpServers -eq 0) {
    Write-Host "  ⚠ No MCP servers detected" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ $mcpServers MCP server(s) preserved" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== SHUTDOWN COMPLETE ===" -ForegroundColor Green
Write-Host "Local models stopped - all training now runs in AWS" -ForegroundColor Green
Write-Host "MCP servers preserved" -ForegroundColor Green
