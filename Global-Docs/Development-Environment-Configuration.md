# Global Development Environment Configuration

**Last Updated**: November 19, 2025  
**Status**: Active Configuration

## Visual Studio 2026 Build Tools ✅

### Installation Details (VERIFIED)
- **Edition**: Build Tools
- **Version**: 18.0 (VS2026)
- **Location**: `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`
- **MSBuild**: Version 18.0.5.56406
- **MSVC**: Version 14.50.35717
- **Release Date**: November 11, 2025

### Key Paths
```powershell
# Build Tools Root
$VS2026_BuildTools = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"

# MSBuild Executable
$MSBuild = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe"

# MSVC Compiler
$MSVC = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717"

# Developer Command Prompt
$VCVars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

# CMake
$CMake = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
```

### Environment Variables
```powershell
VS180COMNTOOLS = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\"
VCToolsVersion = "14.50"
VS2026_INSTALL_PATH = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools"
```

### Verification Script
```powershell
# Use the global verification script
& ".\Global-Scripts\verify-vs2026.ps1"
```

## Unreal Engine 5.7

### Installation Details
- **Version**: 5.7 (Latest)
- **Location**: `C:\Program Files\Epic Games\UE_5.7`
- **Status**: Configured for VS2026

### Key Paths
```powershell
# Engine Root
$UE57_Root = "C:\Program Files\Epic Games\UE_5.7"

# Build Tool
$UnrealBuildTool = "$UE57_Root\Engine\Build\BatchFiles\Build.bat"

# Version Selector
$UnrealVersionSelector = "$UE57_Root\Engine\Binaries\DotNET\UnrealVersionSelector\UnrealVersionSelector.exe"

# Automation Tool
$UAT = "$UE57_Root\Engine\Build\BatchFiles\RunUAT.bat"
```

### UE5.7 + VS2026 Configuration
```xml
<!-- UnrealBuildTool BuildConfiguration.xml -->
<Configuration xmlns="https://www.unrealengine.com/BuildConfiguration">
  <WindowsPlatform>
    <CompilerVersion>VisualStudio2026</CompilerVersion>
    <ToolchainVersion>14.50</ToolchainVersion>
  </WindowsPlatform>
</Configuration>
```

## Python Configuration

### Installation
- **Version**: 3.13.x (NOT 3.14 - compatibility issues)
- **Location**: `C:\Users\kento\AppData\Local\Programs\Python\Python313`
- **Note**: Use explicit path, NOT Windows App Alias

### Key Paths
```powershell
$Python = "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe"
$Pip = "C:\Users\kento\AppData\Local\Programs\Python\Python313\Scripts\pip.exe"
```

## Node.js Configuration

### Installation
- **Version**: 20.x LTS
- **NPM**: Latest
- **Location**: Default system installation

## Docker Configuration

### Windows Docker Desktop
- **Status**: Required for containerized services
- **WSL2**: Backend enabled
- **Resource Limits**: Configure based on system

## PowerShell Configuration

### Version
- **PowerShell Core**: 7.x (pwsh.exe)
- **Location**: `C:\Program Files\PowerShell\7\pwsh.exe`
- **Execution Policy**: RemoteSigned (minimum)

## AWS CLI

### Installation
- **Version**: 2.x
- **Configuration**: Profile-based (`~/.aws/config`)
- **Default Region**: us-east-1

## Development Tools Verification

### Quick Check Script
```powershell
# Create a comprehensive check
$tools = @{
    "VS2026" = { Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools" }
    "UE5.7" = { Test-Path "C:\Program Files\Epic Games\UE_5.7" }
    "Python" = { Test-Path "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe" }
    "Node" = { Get-Command node -ErrorAction SilentlyContinue }
    "Docker" = { Get-Command docker -ErrorAction SilentlyContinue }
    "AWS" = { Get-Command aws -ErrorAction SilentlyContinue }
    "PowerShell7" = { $PSVersionTable.PSVersion.Major -ge 7 }
}

Write-Host "=== Development Environment Check ===" -ForegroundColor Cyan
foreach ($tool in $tools.GetEnumerator()) {
    $result = & $tool.Value
    $status = if ($result) { "✅" } else { "❌" }
    Write-Host "$status $($tool.Key)" -ForegroundColor $(if ($result) { "Green" } else { "Red" })
}
```

## Project-Specific Tools

### The Body Broker Game
- **Engine**: Unreal Engine 5.7
- **Compiler**: VS2026 (MSVC 14.50)
- **Build System**: UnrealBuildTool with VS2026
- **Target Platforms**: Win64 (PC), Console

### AI Core Backend
- **Language**: Python 3.13
- **Framework**: FastAPI
- **Database**: PostgreSQL 15 (Aurora)
- **Cache**: Redis 7.0
- **Message Queue**: NATS 2.10
- **Search**: OpenSearch 2.11
- **Container**: Docker/ECS

## Helper Scripts in Global-Scripts

1. **verify-vs2026.ps1** - Verify VS2026 installation
2. **verify-tool.ps1** - Generic tool verification
3. **monitor-resources.ps1** - Resource monitoring
4. **cleanup-orphaned-timers-auto.ps1** - Timer cleanup
5. **memory-optimization.ps1** - Memory management

## Known Issues & Solutions

### VS2026 Not Found
- Check both Program Files locations
- Run `.\Global-Scripts\verify-vs2026.ps1`
- Set environment variables manually if needed

### Python 3.14 Compatibility
- Many packages don't support 3.14 yet
- Use Python 3.13 for production
- Check requirements before upgrading

### UE5.7 + VS2026
- Must update .uproject EngineAssociation to "5.7"
- Regenerate project files after VS2026 install
- Use BuildConfiguration.xml for compiler settings

---

**Note**: This configuration is verified as of November 19, 2025. Always run verification scripts before starting development to ensure all tools are properly configured.
