#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates desktop shortcut for Red Alert - AI Validation Dashboard

.DESCRIPTION
    Creates a desktop shortcut that launches the validation report system
    with appropriate icon and settings.
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Creating Desktop Shortcut: Red Alert - AI Validation Dashboard" -ForegroundColor Cyan
Write-Host ""

# Get paths
$scriptPath = Join-Path $PSScriptRoot "launch-red-alert.ps1"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Red Alert - AI Validation Dashboard.lnk"

# Check if launch script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Launch script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

# Create WScript.Shell COM object
$WScriptShell = New-Object -ComObject WScript.Shell

# Create shortcut
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)

# Set shortcut properties
$shortcut.TargetPath = "pwsh.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$scriptPath`""
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = "Red Alert - AI Validation Dashboard for Body Broker Testing"
$shortcut.WindowStyle = 1  # Normal window

# Use PowerShell icon (red-ish)
$shortcut.IconLocation = "powershell.exe,0"

# Save shortcut
$shortcut.Save()

Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $shortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now double-click the shortcut to launch:" -ForegroundColor Yellow
Write-Host "  🚨 Red Alert - AI Validation Dashboard" -ForegroundColor Red
Write-Host ""
Write-Host "The system will:" -ForegroundColor DarkGray
Write-Host "  1. Start Docker backend (port 8010)" -ForegroundColor DarkGray
Write-Host "  2. Start Next.js dashboard (port 3000)" -ForegroundColor DarkGray
Write-Host "  3. Open browser to /reports" -ForegroundColor DarkGray
Write-Host "  4. Run independently (no Cursor needed!)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press any key to close..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

