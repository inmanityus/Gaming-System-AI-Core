# Setup Global Repository Junctions
# Creates Windows junction links to the shared global Cursor repository

param([switch]$Force)

$ErrorActionPreference = "Stop"

# Global repository path
$GlobalRepoPath = "C:\Users\kento\.cursor\global-cursor-repo"

# Junction mappings
$Junctions = @{
    "Global-Reasoning" = "reasoning"
    "Global-History" = "history"
    "Global-Scripts" = "scripts"
    "Global-Workflows" = "rules"
    "Global-Docs" = "docs"
    "Global-Utils" = "utils"
}

Write-Host "[LINK] Setting up Global Repository Junctions..." -ForegroundColor Green
Write-Host "Global Repository: $GlobalRepoPath" -ForegroundColor Cyan

# Check if global repository exists
if (-not (Test-Path $GlobalRepoPath)) {
    Write-Host "[ERROR] Global repository not found at: $GlobalRepoPath" -ForegroundColor Red
    Write-Host "Please ensure the global-cursor-repo exists before running this script." -ForegroundColor Yellow
    exit 1
}

# Create junctions
foreach ($junctionName in $Junctions.Keys) {
    $targetPath = Join-Path $GlobalRepoPath $Junctions[$junctionName]
    
    # Check if target exists
    if (-not (Test-Path $targetPath)) {
        Write-Host "[WARNING] Target path not found: $targetPath" -ForegroundColor Yellow
        continue
    }
    
    # Remove existing junction if it exists
    if (Test-Path $junctionName) {
        if ($Force) {
            Write-Host "[REMOVE] Removing existing junction: $junctionName" -ForegroundColor Yellow
            Remove-Item $junctionName -Force
        } else {
            Write-Host "[WARNING] Junction already exists: $junctionName (use -Force to replace)" -ForegroundColor Yellow
            continue
        }
    }
    
    # Create junction
    try {
        New-Item -ItemType Junction -Path $junctionName -Target $targetPath | Out-Null
        Write-Host "[OK] Created: $junctionName -> $targetPath" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Failed to create junction $junctionName`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "[SUCCESS] Global Junctions Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "[SUMMARY] Created Junctions:" -ForegroundColor Cyan
foreach ($junctionName in $Junctions.Keys) {
    if (Test-Path $junctionName) {
        Write-Host "  [OK] $junctionName" -ForegroundColor Green
    } else {
        Write-Host "  [FAILED] $junctionName (failed)" -ForegroundColor Red
    }
}
