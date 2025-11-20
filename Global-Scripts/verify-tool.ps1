# ================================================================
# QUICK TOOL VERIFICATION HELPER
# ================================================================
# Simplified tool verification for AI sessions
# Usage: .\Global-Scripts\verify-tool.ps1 -Tool Python
#        .\Global-Scripts\verify-tool.ps1 -Tool Python -ShowPath
#        .\Global-Scripts\verify-tool.ps1 -Tool Python -RequireOrExit
# ================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(
        "Python", "Pip", "Node", "NPM", "Docker", "Git", "AWS", 
        "Terraform", "Kubectl", "PowerShell7", "UnrealEngine",
        "UnrealBuildTool", "UnrealUAT", "UnrealVersionSelector", "Psql",
        "VS2026", "MSBuild", "MSVC", "VS2026DevCmd"
    )]
    [string]$Tool,
    
    [switch]$ShowPath = $false,
    [switch]$RequireOrExit = $false,
    [switch]$Quiet = $false
)

# Load tool paths if not already loaded
if (-not $global:ToolPaths) {
    $toolPathsScript = Join-Path $PSScriptRoot "tool-paths.ps1"
    if (Test-Path $toolPathsScript) {
        $global:ToolPaths = & $toolPathsScript
    } else {
        Write-Error "Tool verification system not found: $toolPathsScript"
        exit 1
    }
}

# Get tool path
$toolPath = $global:ToolPaths[$Tool]

# Handle result
if ($toolPath) {
    if (-not $Quiet) {
        Write-Host "✅ $Tool verified" -ForegroundColor Green
    }
    
    if ($ShowPath) {
        Write-Host "   Path: $toolPath" -ForegroundColor White
    }
    
    # Return the path
    return $toolPath
} else {
    # Tool not found
    if (-not $Quiet) {
        Write-Host "❌ $Tool not found" -ForegroundColor Red
    }
    
    # Show expected locations for common tools
    switch ($Tool) {
        "Python" {
            Write-Host "   Expected: C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe" -ForegroundColor Yellow
        }
        "Node" {
            Write-Host "   Expected: C:\Program Files\nodejs\node.exe" -ForegroundColor Yellow
        }
        "Docker" {
            Write-Host "   Expected: C:\Program Files\Docker\Docker\resources\bin\docker.exe" -ForegroundColor Yellow
        }
        "UnrealEngine" {
            Write-Host "   Expected: C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe" -ForegroundColor Yellow
        }
    }
    
    if ($RequireOrExit) {
        Write-Error "$Tool is required but not found. Cannot continue."
        exit 1
    }
    
    return $null
}

