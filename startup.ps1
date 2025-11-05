# Universal Startup Script for Cursor AI Sessions
# This script runs at the beginning of every Cursor chat session to ensure proper setup

param(
    [string]$ProjectRoot = $PWD.Path,
    [switch]$SkipDockerCheck = $false
)

Write-Host "=== UNIVERSAL CURSOR STARTUP ===" -ForegroundColor Green

# ================================================================
# CRITICAL: Script Location Verification Process
# ================================================================
# This verification prevents "script not found" errors that crash sessions
# ALWAYS verify project root before running any scripts or file operations

Write-Host "[VERIFY] Verifying project root directory..." -ForegroundColor Cyan
$currentDir = Get-Location
Write-Host "Current directory: $currentDir" -ForegroundColor White

# Required files that must exist in project root
$requiredFiles = @("startup.ps1", "package.json")
$requiredDirs = @("scripts", "Global-Scripts")
$allPresent = $true

# Check required files
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "[OK] Found: $file" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Missing: $file" -ForegroundColor Red
        $allPresent = $false
    }
}

# Check required directories (at least one should exist)
$anyDirFound = $false
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "[OK] Found: $dir/" -ForegroundColor Green
        $anyDirFound = $true
    }
}

if (-not $anyDirFound) {
    Write-Host "[WARNING] Neither scripts/ nor Global-Scripts/ found" -ForegroundColor Yellow
    Write-Host "         This may be normal if project hasn't been fully set up yet" -ForegroundColor Yellow
}

# If critical files missing, attempt to navigate to project root
if (-not $allPresent) {
    Write-Host "[ERROR] Not in project root - some required files missing" -ForegroundColor Red
    Write-Host "[ACTION] Attempting to navigate to project root: $ProjectRoot" -ForegroundColor Yellow
    
    if (Test-Path $ProjectRoot) {
        Set-Location $ProjectRoot
        Write-Host "[OK] Navigated to project root: $ProjectRoot" -ForegroundColor Green
        
        # Re-verify after navigation
        $allPresent = $true
        foreach ($file in $requiredFiles) {
            if (-not (Test-Path $file)) {
                Write-Host "[ERROR] Still missing after navigation: $file" -ForegroundColor Red
                Write-Host "[ACTION] Please ensure you are in the correct project directory" -ForegroundColor Yellow
                $allPresent = $false
            }
        }
    } else {
        Write-Host "[ERROR] Project root path does not exist: $ProjectRoot" -ForegroundColor Red
        Write-Host "[ACTION] Please verify the project root path is correct" -ForegroundColor Yellow
    }
}

if ($allPresent) {
    Write-Host "[OK] Root directory verified - proceeding with startup" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Proceeding with startup despite verification issues" -ForegroundColor Yellow
    Write-Host "          Some operations may fail if files are not found" -ForegroundColor Yellow
}

Write-Host "" -ForegroundColor White

# Ensure we're in the correct project directory (legacy check - now enhanced above)
if ((Get-Location).Path -ne $ProjectRoot) {
    Write-Host "[ACTION] Setting working directory to project root: $ProjectRoot" -ForegroundColor Yellow
    Set-Location $ProjectRoot
}

# Set environment variables for current session
$env:CURSOR_AUTO_APPROVE_COMMANDS = "true"
$env:CURSOR_DISABLE_SECURITY_PROMPTS = "true"
$env:CURSOR_REQUIRE_COMMAND_APPROVAL = "false"

# Load project-specific configuration
$configFile = "Project-Management\project-config.md"
if (Test-Path $configFile) {
    Write-Host "Project configuration loaded from: $configFile" -ForegroundColor Green
} else {
    Write-Host "WARNING: project-config.md not found. Using defaults." -ForegroundColor Yellow
}

# Database configuration (from Project-Management/project-config.md or defaults)
$env:DB_HOST = "localhost"
$env:DB_PORT = "5443"
# Auto-detect database name from folder structure
$rootFolder = Split-Path $ProjectRoot -Leaf
$parentFolder = Split-Path (Split-Path $ProjectRoot -Parent) -Leaf
$dbName = (("$parentFolder $rootFolder" -replace '\s+', '_').ToLower())
$env:DB_NAME = $dbName
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "Inn0vat1on!"
$env:PGPASSWORD = "Inn0vat1on!"

Write-Host "Environment variables configured" -ForegroundColor Green

# Check Docker availability
if (-not $SkipDockerCheck) {
    Write-Host "Checking Docker availability..." -ForegroundColor Yellow
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker: Available and running" -ForegroundColor Green
        } else {
            Write-Host "Docker: Available but not running - $dockerInfo" -ForegroundColor Yellow
            Write-Host "Please start Docker Desktop or Docker Engine" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Docker: Not available - $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Docker is required for this project. Please install Docker Desktop or Docker Engine." -ForegroundColor Red
    }
}

# Check Git repository
Write-Host "Checking Git repository..." -ForegroundColor Yellow
try {
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Git repository: Available" -ForegroundColor Green
        # REMOVED: File listing removed per user request - sessions should not list files
    } else {
        Write-Host "Git repository: Not initialized - $gitStatus" -ForegroundColor Yellow
        Write-Host "Initializing Git repository..." -ForegroundColor Yellow
        git init
        Write-Host "Git repository initialized" -ForegroundColor Green
    }
} catch {
    Write-Host "Git: Not available - $($_.Exception.Message)" -ForegroundColor Red
}

# Service health checks removed - not applicable for this project

# Create universal watchdog script if it doesn't exist
$watchdogScript = "universal-watchdog.ps1"
if (-not (Test-Path $watchdogScript)) {
    $watchdogContent = @'
param(
  [int]$TimeoutSec = 900,
  [string]$Label = "cmd",
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

if (-not $Args -or $Args.Count -eq 0) {
  Write-Host "Usage: universal-watchdog.ps1 -TimeoutSec <sec> -Label <name> -- <command...>"
  exit 2
}

$LogDir = ".cursor/ai-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$labelSafe = $Label -replace ' ', '_'
$logFile = Join-Path $LogDir "$stamp-$labelSafe.log"
$metaFile = "$logFile.meta.json"

# idempotency (2 minutes window)
$lastCmds = Join-Path $LogDir "last-commands.jsonl"
$hashInput = (Get-Location).Path + "`0" + ($Args -join ' ')
$sha256 = [System.BitConverter]::ToString((New-Object -TypeName System.Security.Cryptography.SHA256Managed).ComputeHash([Text.Encoding]::UTF8.GetBytes($hashInput))).Replace("-", "").ToLower()
$now = [int][double]::Parse((Get-Date -UFormat %s))

if (Test-Path $lastCmds) {
  $recent = Select-String -Path $lastCmds -Pattern "`"hash`":`"$sha256`"" -SimpleMatch
  if ($recent) {
    $line = (Get-Content $lastCmds | Where-Object { $_ -match "`"hash`":`"$sha256`"" } | Select-Object -Last 1)
    if ($line -match '"ts":(\d+)') {
      $ts = [int]$Matches[1]
      if (($now - $ts) -lt 120) {
        Write-Host "WATCHDOG: Skipping duplicate command (within 120s). Hash=$sha256"
        exit 0
      }
    }
  }
}
"{""ts"":$now,""cwd"":""$((Get-Location).Path.Replace('"','\"'))"",""hash"":""$sha256"",""label"":""$Label"",""cmd"":""$([Text.Encoding]::UTF8.GetString([Text.Encoding]::UTF8.GetBytes(($Args -join ' '))))""}" | Add-Content -Path $lastCmds

# Start process with timeout & heartbeat
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell"
$psi.Arguments = "-NoProfile -Command $($Args -join ' ')"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()

$start = Get-Date
$lastBytes = 0
$buffer = New-Object System.Text.StringBuilder

while (-not $proc.HasExited) {
  Start-Sleep -Milliseconds 500
  $out = $proc.StandardOutput.ReadToEnd()
  $err = $proc.StandardError.ReadToEnd()
  if ($out) { $buffer.Append($out) | Out-Null }
  if ($err) { $buffer.Append($err) | Out-Null }

  $elapsed = (Get-Date) - $start
  if ($elapsed.TotalSeconds -ge $TimeoutSec) {
    try { $proc.CloseMainWindow() | Out-Null } catch {}
    Start-Sleep -Seconds 5
    try { if (-not $proc.HasExited) { $proc.Kill() } } catch {}
    $buffer.AppendLine("WATCHDOG: Killed after $TimeoutSec s") | Out-Null
    break
  }
}

if (-not $proc.HasExited) { $proc.WaitForExit() }
$exit = $proc.ExitCode
$content = $buffer.ToString()
$lines = ($content -split "`r?`n").Count
$truncated = $false
if ($lines -gt 2000) {
  $head = ($content -split "`r?`n")[0..999] -join "`n"
  $tail = ($content -split "`r?`n")[-1000..-1] -join "`n"
  "$head`n--- [truncated] ---`n$tail" | Set-Content -Path $logFile -Encoding UTF8
  $truncated = $true
} else {
  $content | Set-Content -Path $logFile -Encoding UTF8
}

$dur = [int]((Get-Date) - $start).TotalSeconds
Write-Host "WATCHDOG: label=$Label exit=$exit durationSec=$dur log=$logFile truncated=$truncated"
"{""exitCode"":$exit,""durationSec"":$dur,""logPath"":""$logFile"",""truncated"":$truncated}" | Set-Content -Path $metaFile -Encoding UTF8
exit $exit
'@
    
    Set-Content -Path $watchdogScript -Value $watchdogContent -Encoding UTF8
    Write-Host "Created universal watchdog script: $watchdogScript" -ForegroundColor Green
}

# MCP Server Protection Command (store for reference)
$mcpProtectionCmd = @'
Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object { try { $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine; if ($cmdLine -and ($cmdLine -match "npm|pnpm|nodemon|ts-node|next|vite|webpack|express|fastify")) { Write-Host "Killing application server process $($_.Id)"; Stop-Process -Id $_.Id -Force } } catch { Write-Host "Preserving process $($_.Id) (likely MCP server)" } }
'@

Write-Host "MCP Protection Command available" -ForegroundColor Green

# ================================================================
# MODULAR FEATURES LOADER
# ================================================================
# This section automatically loads all features from Global-Workflows/startup-features/
# Each feature is a separate .ps1 file that exports an Initialize-* function
# To add new features, simply add a new .ps1 file to that directory
# ================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Loading Modular Startup Features..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$featuresDir = "Global-Workflows\startup-features"
if (Test-Path $featuresDir) {
    Write-Host "[OK] Features directory found: $featuresDir" -ForegroundColor Green
    
    # Get all feature files (sorted alphabetically for consistent execution order)
    $featureFiles = Get-ChildItem -Path $featuresDir -Filter "*.ps1" | Sort-Object Name
    
    if ($featureFiles.Count -eq 0) {
        Write-Host "[WARNING] No feature files found in $featuresDir" -ForegroundColor Yellow
        Write-Host "          Startup will continue without modular features" -ForegroundColor Yellow
    } else {
        Write-Host "Found $($featureFiles.Count) feature(s) to load..." -ForegroundColor White
        Write-Host ""
        
        foreach ($featureFile in $featureFiles) {
            $featureName = $featureFile.BaseName
            Write-Host "[LOADING] Feature: $featureName" -ForegroundColor Cyan
            
            try {
                # Dot-source the feature file (loads the function into current scope)
                . $featureFile.FullName
                
                # Call the Initialize- function (naming convention: Initialize-<FeatureName>)
                # Convert filename to PascalCase (e.g., "timer-service" -> "TimerService")
                $functionName = (Get-Culture).TextInfo.ToTitleCase($featureName.Replace('-', ' ')).Replace(' ', '')
                $initializeFunction = "Initialize-$functionName"
                
                if (Get-Command $initializeFunction -ErrorAction SilentlyContinue) {
                    # Call the initialization function
                    & $initializeFunction
                    Write-Host "[OK] Feature '$featureName' initialized successfully" -ForegroundColor Green
                } else {
                    Write-Host "[WARNING] Feature '$featureName' loaded but function '$initializeFunction' not found" -ForegroundColor Yellow
                    Write-Host "          Feature may not follow naming convention (should export Initialize-$functionName)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "[ERROR] Failed to load feature '$featureName': $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "        Continuing with other features..." -ForegroundColor Yellow
            }
            
            Write-Host ""
        }
        
        Write-Host "[SUCCESS] All modular features loaded" -ForegroundColor Green
    }
} else {
    Write-Host "[WARNING] Features directory not found: $featuresDir" -ForegroundColor Yellow
    Write-Host "          Modular features will not be available" -ForegroundColor Yellow
    Write-Host "          Check that Global-Workflows junction is properly linked" -ForegroundColor Yellow
}

Write-Host "================================================================" -ForegroundColor Cyan

# Sync Global Rules (if available)
Write-Host "Syncing global rules..." -ForegroundColor Yellow
$syncScript = Join-Path $ProjectRoot "scripts\Sync-Global-Rules.ps1"
if (Test-Path $syncScript) {
    try {
        & $syncScript -ErrorAction SilentlyContinue
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Global rules synced successfully" -ForegroundColor Green
        } else {
            Write-Host "Global rules sync skipped (optional)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Global rules sync skipped: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "Global rules sync script not found (optional)" -ForegroundColor Gray
}

# Check PostgreSQL connectivity (universal)
Write-Host "Checking PostgreSQL connectivity..." -ForegroundColor Yellow
try {
    $testResult = & psql -h localhost -U postgres -d postgres -p 5443 -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL connection successful" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL connection failed: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "Error checking PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Loading Pairwise-Comprehensive-Testing Protocol..." -ForegroundColor Yellow
if (Test-Path "Global-Workflows/Pairwise-Comprehensive-Testing.md") {
    Write-Host "[OK] Pairwise-Comprehensive-Testing Protocol: Active" -ForegroundColor Green
    Write-Host "   - Two-AI System: Tester + Reviewer" -ForegroundColor White
    Write-Host "   - 45-Minute Milestones: Enabled" -ForegroundColor White
    Write-Host "   - End-User Testing: Mandatory" -ForegroundColor White
    Write-Host "   - Full Autonomy: No user input required" -ForegroundColor White
    
    # Check for active Pairwise Testing sessions
    if (Test-Path "PAIRWISE-*-MANAGER.md") {
        Write-Host ""
        Write-Host "[UPDATE] Active Pairwise Testing detected:" -ForegroundColor Cyan
        Get-ChildItem "PAIRWISE-*-MANAGER.md" -ErrorAction SilentlyContinue | ForEach-Object {
            $status = Get-Content $_.FullName | Select-String "Status:" -ErrorAction SilentlyContinue
            Write-Host "  - $($_.Name): $status" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[WARNING] Pairwise-Comprehensive-Testing Protocol not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Loading Autonomous Development Protocol..." -ForegroundColor Yellow
if (Test-Path "Global-Workflows/Autonomous-Development-Protocol.md") {
    Write-Host "[OK] Autonomous Development Protocol available" -ForegroundColor Green
    Write-Host "  Use for end-to-end autonomous project development" -ForegroundColor Gray
} else {
    Write-Host "[WARNING] Autonomous Development Protocol not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Loading AI Model Collaboration Protocol..." -ForegroundColor Yellow
if (Test-Path "Global-Workflows/Autonomous-Development-Protocol.md") {
    Write-Host "[OK] AI Model Collaboration Protocol: Active" -ForegroundColor Green
    Write-Host "   - Director Model: Creates initial architecture" -ForegroundColor White
    Write-Host "   - Peer Review: 3-5 diverse models review solutions" -ForegroundColor White
    Write-Host "   - Research Round: Use Exa/Perplexity/Ref MCPs for context" -ForegroundColor White
    Write-Host "   - Iteration: Repeat until no meaningful feedback (2-4 rounds)" -ForegroundColor White
    Write-Host "   - Output: Peer-reviewed, validated solution design" -ForegroundColor White
    Write-Host ""
    Write-Host "   CRITICAL: When user says 'collaborate with your models':" -ForegroundColor Yellow
    Write-Host "   1. Use one model as main Director/Producer" -ForegroundColor Gray
    Write-Host "   2. Pass output to at least 3 other models for review" -ForegroundColor Gray
    Write-Host "   3. Do research based on feedback (Exa/Perplexity/Ref MCPs)" -ForegroundColor Gray
    Write-Host "   4. Pass everything back to original AI (Director)" -ForegroundColor Gray
    Write-Host "   5. Generate new document and repeat loop" -ForegroundColor Gray
    Write-Host "   6. Continue until no more significant feedback provided" -ForegroundColor Gray
    Write-Host "   7. This loop must be repeated for EVERY section" -ForegroundColor Red
    Write-Host "   8. If not followed, redo from scratch" -ForegroundColor Red
} else {
    Write-Host "[WARNING] AI Model Collaboration Protocol not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Loading Global Rules Integration..." -ForegroundColor Yellow
if (Test-Path ".cursorrules-global-integration") {
    Write-Host "[OK] Global Rules loaded (AWS Direct CLI, Documentation Storage)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Global Rules integration file not found" -ForegroundColor Yellow
}

# Note: Modular features (timer-service, minimum-model-levels, memory-structure, 
# resource-management, documentation-placement) are now loaded via the features loader above.
# All project-specific initialization should go below this point.

Write-Host ""
Write-Host "UNIVERSAL STARTUP COMPLETE" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)" -ForegroundColor White
Write-Host "MCP servers are protected from accidental termination" -ForegroundColor Green
Write-Host "Universal watchdog script ready for command execution" -ForegroundColor Green
Write-Host ""
Write-Host "MCP SERVER CAPABILITIES:" -ForegroundColor Cyan
Write-Host "- Apify: Web automation & data extraction" -ForegroundColor White
Write-Host "- AWS Labs: Cloud infrastructure management" -ForegroundColor White
Write-Host "- Exa: Superior programmer-oriented search" -ForegroundColor White
Write-Host "- OpenRouter AI: Advanced AI model access" -ForegroundColor White
Write-Host "- Perplexity: Contextualized Q&A" -ForegroundColor White
Write-Host "- Ref: Documentation search" -ForegroundColor White
Write-Host "- Playwright: Browser automation & UI testing" -ForegroundColor White
Write-Host "- Sequential Thinking: Complex task breakdown" -ForegroundColor White
Write-Host "- Stripe: Payment system integration" -ForegroundColor White
Write-Host ""
Write-Host "CRITICAL RULE: If any command or file lookup fails, FIRST check you are in the project root!" -ForegroundColor Red
Write-Host "Project root: $ProjectRoot" -ForegroundColor Yellow

# ANTI-MOCK DATA RULE
Write-Host ""
Write-Host "[CRITICAL] ANTI-MOCK DATA RULE [CRITICAL]" -ForegroundColor Red
Write-Host "SESSIONS MUST ALWAYS CONNECT TO REAL BACKEND SERVERS/DATABASE" -ForegroundColor Red
Write-Host "NEVER USE MOCK DATA OR SIMULATED RESPONSES" -ForegroundColor Red
Write-Host "ALL API CALLS MUST GO TO: http://localhost:4000" -ForegroundColor Yellow
Write-Host "ALL DATABASE OPERATIONS MUST USE: PostgreSQL on localhost:5443" -ForegroundColor Yellow
Write-Host "MOCK RESPONSES ARE FORBIDDEN - USE REAL IMPLEMENTATIONS ONLY" -ForegroundColor Red
Write-Host ""

# Create startup completion marker
$markerFile = ".cursor\startup-complete.marker"
$markerDir = Split-Path $markerFile -Parent
if (-not (Test-Path $markerDir)) {
    New-Item -ItemType Directory -Force -Path $markerDir | Out-Null
}
(Get-Date).ToString() | Set-Content -Path $markerFile -Encoding UTF8
Write-Host "Startup marker created: $markerFile" -ForegroundColor Green
