# Simplified Cursor Visibility Script
# Ensures Global-* folders and .cursor directory are visible

param(
    [switch]$Force
)

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path $scriptDir -Parent

Write-Host "=== ENSURING CURSOR VISIBILITY ===" -ForegroundColor Green

function Clear-HiddenAttribute {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    try {
        $item = Get-Item $Path -Force
        if ($item.Attributes -band [IO.FileAttributes]::Hidden) {
            $item.Attributes = $item.Attributes -bxor [IO.FileAttributes]::Hidden
            Write-Host "Made visible: $Path" -ForegroundColor Green
        }
    } catch {
        Write-Host "Could not modify attributes for: $Path" -ForegroundColor Yellow
    }
}

# Ensure .cursor directory is visible
$cursorDir = Join-Path $projectRoot ".cursor"
if (Test-Path $cursorDir) {
    Clear-HiddenAttribute -Path $cursorDir
}

# Ensure Global-* folders are visible
$globalFolders = @("Global-Rules", "Global-Scripts", "Global-Workflows", "Global-Utils")
foreach ($folder in $globalFolders) {
    $fullPath = Join-Path $projectRoot $folder
    if (Test-Path $fullPath) {
        Clear-HiddenAttribute -Path $fullPath
        Write-Host "Global folder accessible: $folder" -ForegroundColor Green
    } else {
        Write-Host "Global folder missing: $folder" -ForegroundColor Yellow
    }
}

# Ensure scripts directory is visible
$scriptsDir = Join-Path $projectRoot "scripts"
if (Test-Path $scriptsDir) {
    Clear-HiddenAttribute -Path $scriptsDir
}

Write-Host "Visibility check complete" -ForegroundColor Green
Write-Host "Working directory: $projectRoot" -ForegroundColor White

