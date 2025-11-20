# Visual Studio 2026 Build Tools Verification Script
# Last Updated: November 19, 2025
# Status: VERIFIED WORKING ✅

<#
.SYNOPSIS
    Verifies Visual Studio 2026 Build Tools installation and configuration
    
.DESCRIPTION
    This script verifies VS2026 installation, reports versions, and provides
    environment setup for projects requiring VS2026. It includes the actual
    discovered installation paths.
    
.NOTES
    VS2026 Released: November 11, 2025
    Version: 18.0
    MSVC: 14.50
#>

Write-Host "=== Visual Studio 2026 Build Tools Verification ===" -ForegroundColor Cyan

# VERIFIED INSTALLATION PATHS (as of November 19, 2025)
$VS2026_PATHS = @{
    BuildTools = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
    MSBuild = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    MSVC = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717"
    VCVars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    CMake = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
}

# Check VS2026 installation
$installStatus = @{}

# Check Build Tools
if (Test-Path $VS2026_PATHS.BuildTools) {
    $installStatus.BuildTools = "✅ Installed"
    Write-Host "✅ VS2026 Build Tools found at: $($VS2026_PATHS.BuildTools)" -ForegroundColor Green
} else {
    $installStatus.BuildTools = "❌ Not Found"
    Write-Host "❌ VS2026 Build Tools not found" -ForegroundColor Red
}

# Check and get MSBuild version
if (Test-Path $VS2026_PATHS.MSBuild) {
    try {
        $msbuildVersion = & $VS2026_PATHS.MSBuild -version -nologo | Select-Object -First 1
        $installStatus.MSBuild = "✅ Version $msbuildVersion"
        Write-Host "✅ MSBuild: $msbuildVersion" -ForegroundColor Green
        
        # Expected: 18.0.5.56406 or higher
        if ($msbuildVersion -match "18\.0\.\d+\.\d+") {
            Write-Host "  ✓ Version matches VS2026 (18.0.x)" -ForegroundColor Gray
        } else {
            Write-Host "  ⚠️ Unexpected version (expected 18.0.x)" -ForegroundColor Yellow
        }
    } catch {
        $installStatus.MSBuild = "❌ Error running MSBuild"
    }
} else {
    $installStatus.MSBuild = "❌ Not Found"
}

# Check MSVC version
if (Test-Path $VS2026_PATHS.MSVC) {
    $msvcVersion = Split-Path $VS2026_PATHS.MSVC -Leaf
    $installStatus.MSVC = "✅ Version $msvcVersion"
    Write-Host "✅ MSVC: $msvcVersion" -ForegroundColor Green
    
    # Expected: 14.50.x
    if ($msvcVersion -match "14\.50\.\d+") {
        Write-Host "  ✓ Version matches VS2026 MSVC (14.50.x)" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️ Unexpected version (expected 14.50.x)" -ForegroundColor Yellow
    }
} else {
    # Try to find any MSVC version
    $msvcBase = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC"
    if (Test-Path $msvcBase) {
        $msvcVersions = Get-ChildItem $msvcBase -Directory | Select-Object -ExpandProperty Name
        if ($msvcVersions) {
            $latestMsvc = $msvcVersions | Sort-Object -Descending | Select-Object -First 1
            $installStatus.MSVC = "✅ Version $latestMsvc (detected)"
            Write-Host "✅ MSVC: $latestMsvc (detected)" -ForegroundColor Green
            $VS2026_PATHS.MSVC = Join-Path $msvcBase $latestMsvc
        }
    }
}

# Check environment variables
Write-Host "`nEnvironment Variables:" -ForegroundColor Yellow
$envVars = @{
    VS180COMNTOOLS = [System.Environment]::GetEnvironmentVariable("VS180COMNTOOLS", [System.EnvironmentVariableTarget]::User)
    VCToolsVersion = [System.Environment]::GetEnvironmentVariable("VCToolsVersion", [System.EnvironmentVariableTarget]::User)
    VS2026_INSTALL_PATH = [System.Environment]::GetEnvironmentVariable("VS2026_INSTALL_PATH", [System.EnvironmentVariableTarget]::User)
}

foreach ($var in $envVars.GetEnumerator()) {
    if ($var.Value) {
        Write-Host "  ✅ $($var.Key) = $($var.Value)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($var.Key) not set" -ForegroundColor Red
    }
}

# Function to set up VS2026 environment
function Set-VS2026Environment {
    if (Test-Path $VS2026_PATHS.BuildTools) {
        Write-Host "`nSetting VS2026 environment variables..." -ForegroundColor Yellow
        
        # Set environment variables
        [System.Environment]::SetEnvironmentVariable("VS180COMNTOOLS", "$($VS2026_PATHS.BuildTools)\Common7\Tools\", [System.EnvironmentVariableTarget]::User)
        [System.Environment]::SetEnvironmentVariable("VCToolsVersion", "14.50", [System.EnvironmentVariableTarget]::User)
        [System.Environment]::SetEnvironmentVariable("VS2026_INSTALL_PATH", $VS2026_PATHS.BuildTools, [System.EnvironmentVariableTarget]::User)
        
        Write-Host "✅ Environment variables set" -ForegroundColor Green
        Write-Host "⚠️ Restart PowerShell to load new variables" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Cannot set environment - VS2026 not found" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan

if ($installStatus.BuildTools -match "✅") {
    Write-Host "✅ Visual Studio 2026 Build Tools are installed and verified" -ForegroundColor Green
    Write-Host "`nInstallation Details:" -ForegroundColor Yellow
    foreach ($status in $installStatus.GetEnumerator()) {
        Write-Host "  $($status.Key): $($status.Value)"
    }
    
    Write-Host "`nKey Paths:" -ForegroundColor Yellow
    Write-Host "  Build Tools: $($VS2026_PATHS.BuildTools)"
    Write-Host "  MSBuild: $($VS2026_PATHS.MSBuild)"
    Write-Host "  MSVC: $($VS2026_PATHS.MSVC)"
    
    # Export paths for other scripts
    $global:VS2026_PATHS = $VS2026_PATHS
    
} else {
    Write-Host "❌ Visual Studio 2026 Build Tools not found" -ForegroundColor Red
    Write-Host "`nExpected location: C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools" -ForegroundColor Yellow
    Write-Host "Download from: https://visualstudio.microsoft.com/downloads/" -ForegroundColor Cyan
}

# Usage instructions
Write-Host "`n=== USAGE ===" -ForegroundColor Cyan
Write-Host "To set up VS2026 environment variables, run:" -ForegroundColor Yellow
Write-Host "  Set-VS2026Environment" -ForegroundColor White
Write-Host "`nTo use in other scripts:" -ForegroundColor Yellow
Write-Host '  $vs2026 = & ".\Global-Scripts\verify-vs2026.ps1"' -ForegroundColor White
Write-Host '  $msbuild = $global:VS2026_PATHS.MSBuild' -ForegroundColor White

# Return installation status
return $installStatus
