# ================================================================
# TOOL PATH VERIFICATION SYSTEM
# ================================================================
# This script provides centralized tool location verification
# CRITICAL: ALWAYS verify tool locations before executing them
# PREVENTS: Session crashes from missing or incorrectly pathed tools
#
# Usage:
#   $tools = & "Global-Scripts\tool-paths.ps1"
#   if ($tools.Python) {
#       & $tools.Python --version
#   } else {
#       Write-Error "Python not found!"
#   }
# ================================================================

param(
    [switch]$Verbose = $false,
    [switch]$ShowAll = $false
)

# ================================================================
# KNOWN TOOL LOCATIONS (USER-SPECIFIC)
# ================================================================
# These are the verified locations for this system
# Update these if tools are installed in different locations
# ================================================================

$KnownPaths = @{
    # Python 3.13 - CRITICAL: Use full path, not Windows App Alias
    Python = @(
        "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe",
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe"
    )
    
    # Pip (Python Package Manager)
    Pip = @(
        "C:\Users\kento\AppData\Local\Programs\Python\Python313\Scripts\pip.exe",
        "C:\Python313\Scripts\pip.exe"
    )
    
    # Node.js
    Node = @(
        "C:\Program Files\nodejs\node.exe",
        "C:\Program Files (x86)\nodejs\node.exe"
    )
    
    # NPM (Node Package Manager)
    NPM = @(
        "C:\Program Files\nodejs\npm.cmd",
        "C:\Program Files (x86)\nodejs\npm.cmd"
    )
    
    # Docker
    Docker = @(
        "C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        "C:\Program Files\Docker\Docker\resources\docker.exe"
    )
    
    # Git
    Git = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe"
    )
    
    # AWS CLI
    AWS = @(
        "C:\Program Files\Amazon\AWSCLIV2\aws.exe",
        "C:\Program Files (x86)\Amazon\AWSCLIV2\aws.exe"
    )
    
    # Terraform
    Terraform = @(
        "C:\ProgramData\chocolatey\bin\terraform.exe",
        "C:\HashiCorp\Terraform\terraform.exe",
        "C:\terraform\terraform.exe"
    )
    
    # kubectl
    Kubectl = @(
        "C:\Program Files\Docker\Docker\resources\bin\kubectl.exe",
        "C:\ProgramData\chocolatey\bin\kubectl.exe"
    )
    
    # PowerShell 7
    PowerShell7 = @(
        "C:\Program Files\PowerShell\7\pwsh.exe"
    )
    
    # Unreal Engine 5.6.1
    UnrealEngine = @(
        "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe"
    )
    
    # Unreal Build Tool
    UnrealBuildTool = @(
        "C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat"
    )
    
    # Unreal Automation Tool (UAT)
    UnrealUAT = @(
        "C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\RunUAT.bat"
    )
    
    # Unreal Version Selector
    UnrealVersionSelector = @(
        "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\DotNET\UnrealVersionSelector\UnrealVersionSelector.exe"
    )
    
    # PostgreSQL (psql)
    Psql = @(
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe",
        "C:\Program Files\PostgreSQL\14\bin\psql.exe"
    )
}

# ================================================================
# VERIFICATION FUNCTION
# ================================================================

function Find-ToolPath {
    param(
        [string]$ToolName,
        [string[]]$PossiblePaths
    )
    
    # First, check known paths
    foreach ($path in $PossiblePaths) {
        if (Test-Path $path) {
            if ($Verbose) {
                Write-Host "[OK] $ToolName found at: $path" -ForegroundColor Green
            }
            return $path
        }
    }
    
    # Fallback: Try Get-Command (but this may return wrong path for Python)
    $cmd = Get-Command $ToolName -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        # Special handling for Python - avoid Windows App Alias
        if ($ToolName -eq "python" -and $cmd.Source -like "*WindowsApps*") {
            if ($Verbose) {
                Write-Host "[WARNING] $ToolName found via Get-Command but it's Windows App Alias" -ForegroundColor Yellow
                Write-Host "          Path: $($cmd.Source)" -ForegroundColor Yellow
            }
            return $null
        }
        
        if ($Verbose) {
            Write-Host "[OK] $ToolName found via Get-Command: $($cmd.Source)" -ForegroundColor Green
        }
        return $cmd.Source
    }
    
    # Not found
    if ($Verbose -or $ShowAll) {
        Write-Host "[NOT FOUND] $ToolName" -ForegroundColor Red
    }
    return $null
}

# ================================================================
# BUILD TOOL PATHS OBJECT
# ================================================================

$ToolPaths = @{}

foreach ($tool in $KnownPaths.Keys) {
    $path = Find-ToolPath -ToolName $tool -PossiblePaths $KnownPaths[$tool]
    $ToolPaths[$tool] = $path
}

# ================================================================
# OUTPUT FORMAT
# ================================================================

if ($ShowAll) {
    Write-Host ""
    Write-Host "=== TOOL PATH VERIFICATION RESULTS ===" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($tool in $ToolPaths.Keys | Sort-Object) {
        if ($ToolPaths[$tool]) {
            Write-Host "✅ $tool" -ForegroundColor Green
            Write-Host "   Path: $($ToolPaths[$tool])" -ForegroundColor White
        } else {
            Write-Host "❌ $tool" -ForegroundColor Red
            Write-Host "   Status: NOT FOUND" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}

# Return the tool paths object
return $ToolPaths

