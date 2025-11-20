# Configure Visual Studio 2026 Build Tools

Write-Host "=== Configuring Visual Studio 2026 Build Tools ===" -ForegroundColor Cyan

# Check for VS2026 in both Program Files locations
$vs2026Paths = @(
    @{ Base = "${env:ProgramFiles}\Microsoft Visual Studio\18"; Arch = "x64" },
    @{ Base = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18"; Arch = "x86" }
)

$vsPath = $null
$vsEdition = $null

foreach ($pathInfo in $vs2026Paths) {
    $basePath = $pathInfo.Base
    
    $editions = @(
        @{ Path = "$basePath\BuildTools"; Edition = "BuildTools" },
        @{ Path = "$basePath\Enterprise"; Edition = "Enterprise" },
        @{ Path = "$basePath\Professional"; Edition = "Professional" },
        @{ Path = "$basePath\Community"; Edition = "Community" }
    )
    
    foreach ($edition in $editions) {
        if (Test-Path $edition.Path) {
            $vsPath = $edition.Path
            $vsEdition = $edition.Edition
            Write-Host "Found VS2026 in $($pathInfo.Arch) directory" -ForegroundColor Gray
            break
        }
    }
    
    if ($vsPath) { break }
}

if (-not $vsPath) {
    Write-Host "[ERROR] Visual Studio 2026 not found!" -ForegroundColor Red
    Write-Host "Expected locations:" -ForegroundColor Yellow
    Write-Host "  - ${env:ProgramFiles}\Microsoft Visual Studio\18\" -ForegroundColor Yellow
    Write-Host "  - ${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\" -ForegroundColor Yellow
    
    # Check what VS versions are installed
    Write-Host "`nInstalled Visual Studio versions:" -ForegroundColor Yellow
    
    if (Test-Path "${env:ProgramFiles}\Microsoft Visual Studio") {
        Write-Host "In Program Files (x64):" -ForegroundColor Gray
        Get-ChildItem "${env:ProgramFiles}\Microsoft Visual Studio" -Directory | ForEach-Object {
            $ver = $_.Name
            Write-Host "  - Version $ver" -ForegroundColor White
        }
    }
    
    if (Test-Path "${env:ProgramFiles(x86)}\Microsoft Visual Studio") {
        Write-Host "In Program Files (x86):" -ForegroundColor Gray
        Get-ChildItem "${env:ProgramFiles(x86)}\Microsoft Visual Studio" -Directory | ForEach-Object {
            $ver = $_.Name
            Write-Host "  - Version $ver" -ForegroundColor White
        }
    }
    
    Write-Host "`nPlease install Visual Studio 2026 Build Tools or higher" -ForegroundColor Yellow
    Write-Host "Download from: https://visualstudio.microsoft.com/downloads/" -ForegroundColor Cyan
    exit 1
}

Write-Host "✓ Found Visual Studio 2026 $vsEdition at: $vsPath" -ForegroundColor Green

# Check MSBuild
$msbuildPath = Join-Path $vsPath "MSBuild\Current\Bin\MSBuild.exe"
if (Test-Path $msbuildPath) {
    $msbuildVersion = & $msbuildPath -version -nologo | Select-Object -First 1
    Write-Host "✓ MSBuild version: $msbuildVersion" -ForegroundColor Green
} else {
    Write-Host "[ERROR] MSBuild not found at: $msbuildPath" -ForegroundColor Red
    exit 1
}

# Check MSVC version
$msvcPath = Join-Path $vsPath "VC\Tools\MSVC"
if (Test-Path $msvcPath) {
    $msvcVersions = Get-ChildItem $msvcPath -Directory | Select-Object -ExpandProperty Name
    $latestMsvc = $msvcVersions | Sort-Object -Descending | Select-Object -First 1
    Write-Host "✓ MSVC version: $latestMsvc" -ForegroundColor Green
    
    if ($latestMsvc -notlike "14.5*") {
        Write-Host "[WARNING] Expected MSVC 14.50.x for VS2026, found: $latestMsvc" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] MSVC not found at: $msvcPath" -ForegroundColor Red
}

# Set environment variables
Write-Host "`nSetting environment variables..." -ForegroundColor Yellow

# VS2026 specific vars
[System.Environment]::SetEnvironmentVariable("VS180COMNTOOLS", "$vsPath\Common7\Tools\", [System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable("VCToolsVersion", "14.50", [System.EnvironmentVariableTarget]::User)
[System.Environment]::SetEnvironmentVariable("VS2026_INSTALL_PATH", $vsPath, [System.EnvironmentVariableTarget]::User)

# Update PATH for VS2026 tools
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
$vsToolsPath = "$vsPath\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
$msbuildDir = Split-Path $msbuildPath -Parent

if ($currentPath -notlike "*$msbuildDir*") {
    $newPath = "$msbuildDir;$currentPath"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, [System.EnvironmentVariableTarget]::User)
    Write-Host "✓ Added MSBuild to PATH" -ForegroundColor Green
}

if ((Test-Path $vsToolsPath) -and ($currentPath -notlike "*$vsToolsPath*")) {
    $newPath = "$vsToolsPath;$currentPath"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, [System.EnvironmentVariableTarget]::User)
    Write-Host "✓ Added CMake to PATH" -ForegroundColor Green
}

# Create VS2026 detection script
$detectionScript = @'
# VS2026 Detection Helper
function Get-VS2026Path {
    $paths = @(
        "${env:ProgramFiles}\Microsoft Visual Studio\18\BuildTools",
        "${env:ProgramFiles}\Microsoft Visual Studio\18\Enterprise",
        "${env:ProgramFiles}\Microsoft Visual Studio\18\Professional",
        "${env:ProgramFiles}\Microsoft Visual Studio\18\Community",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\Enterprise",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\Professional",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\Community"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return $null
}

function Test-VS2026 {
    $vsPath = Get-VS2026Path
    if ($vsPath) {
        Write-Host "VS2026 found at: $vsPath" -ForegroundColor Green
        return $true
    }
    Write-Host "VS2026 not found" -ForegroundColor Red
    return $false
}

function Get-VS2026MSBuild {
    $vsPath = Get-VS2026Path
    if ($vsPath) {
        return Join-Path $vsPath "MSBuild\Current\Bin\MSBuild.exe"
    }
    return $null
}

# Export functions
Export-ModuleMember -Function Get-VS2026Path, Test-VS2026, Get-VS2026MSBuild
'@

$detectionScript | Out-File -FilePath "scripts/VS2026-Detection.psm1" -Encoding UTF8
Write-Host "✓ Created VS2026 detection module" -ForegroundColor Green

# Update UE5 build configuration
Write-Host "`nUpdating UE5 build configuration..." -ForegroundColor Yellow

# Check for BuildConfiguration.xml
$engineDir = "C:\Program Files\Epic Games\UE_5.7\Engine"
$buildConfigPath = "$env:APPDATA\Unreal Engine\UnrealBuildTool\BuildConfiguration.xml"

if (-not (Test-Path (Split-Path $buildConfigPath -Parent))) {
    New-Item -ItemType Directory -Path (Split-Path $buildConfigPath -Parent) -Force | Out-Null
}

$buildConfig = @"
<?xml version="1.0" encoding="utf-8"?>
<Configuration xmlns="https://www.unrealengine.com/BuildConfiguration">
  <WindowsPlatform>
    <CompilerVersion>VisualStudio2026</CompilerVersion>
    <ToolchainVersion>14.50</ToolchainVersion>
  </WindowsPlatform>
  <ParallelExecutor>
    <MaxProcessorCount>16</MaxProcessorCount>
    <ProcessorCountMultiplier>1</ProcessorCountMultiplier>
  </ParallelExecutor>
  <BuildConfiguration>
    <bUseUnityBuild>true</bUseUnityBuild>
    <bUsePCHFiles>true</bUsePCHFiles>
    <bUseIncrementalLinking>true</bUseIncrementalLinking>
  </BuildConfiguration>
</Configuration>
"@

$buildConfig | Out-File -FilePath $buildConfigPath -Encoding UTF8
Write-Host "✓ Updated UnrealBuildTool configuration" -ForegroundColor Green

# Create batch file for VS2026 developer command prompt
$devCmdBatch = @"
@echo off
echo Setting up VS2026 Developer Command Prompt...
call "$vsPath\Common7\Tools\VsDevCmd.bat" -arch=x64
echo.
echo Visual Studio 2026 environment ready!
echo MSVC Version: %VCToolsVersion%
echo VS Install Path: %VSINSTALLDIR%
echo.
"@

$devCmdBatch | Out-File -FilePath "scripts/VS2026-DevCmd.bat" -Encoding ASCII
Write-Host "✓ Created VS2026 developer command prompt script" -ForegroundColor Green

# Test C++20 support
Write-Host "`nTesting C++20 compiler support..." -ForegroundColor Yellow

$testCode = @'
#include <iostream>
#include <concepts>
#include <ranges>
#include <format>

template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

template<Numeric T>
T add(T a, T b) {
    return a + b;
}

int main() {
    auto result = add(5, 3);
    std::cout << std::format("VS2026 C++20 Test: {} + {} = {}\n", 5, 3, result);
    
    // C++20 ranges
    auto vec = std::views::iota(1, 10) | std::views::filter([](int i) { return i % 2 == 0; });
    
    std::cout << "Even numbers: ";
    for (int n : vec) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
    
    return 0;
}
'@

$testCode | Out-File -FilePath "test-cpp20.cpp" -Encoding UTF8

# Try to compile the test
$vcvarsPath = "$vsPath\VC\Auxiliary\Build\vcvars64.bat"
if (Test-Path $vcvarsPath) {
    $compileScript = @"
@echo off
call "$vcvarsPath"
cl.exe /std:c++20 /EHsc test-cpp20.cpp /Fe:test-cpp20.exe
"@
    
    $compileScript | Out-File -FilePath "compile-test.bat" -Encoding ASCII
    $result = & cmd.exe /c compile-test.bat 2>&1
    
    if (Test-Path "test-cpp20.exe") {
        Write-Host "✓ C++20 compilation successful!" -ForegroundColor Green
        $output = & .\test-cpp20.exe
        Write-Host "  Output: $output" -ForegroundColor Gray
        
        # Cleanup
        Remove-Item "test-cpp20.exe", "test-cpp20.obj" -ErrorAction SilentlyContinue
    } else {
        Write-Host "[WARNING] C++20 compilation test failed" -ForegroundColor Yellow
    }
    
    Remove-Item "compile-test.bat", "test-cpp20.cpp" -ErrorAction SilentlyContinue
}

Write-Host "`n=== VS2026 Configuration Complete ===" -ForegroundColor Green
Write-Host "✓ VS2026 $vsEdition installed and configured" -ForegroundColor White
Write-Host "✓ Environment variables set" -ForegroundColor White
Write-Host "✓ UE5 build configuration updated" -ForegroundColor White
Write-Host "✓ Helper scripts created" -ForegroundColor White

Write-Host "`n=== Important Information ===" -ForegroundColor Cyan
Write-Host "VS2026 Path: $vsPath" -ForegroundColor Yellow
Write-Host "MSBuild: $msbuildPath" -ForegroundColor Yellow
Write-Host "MSVC Version: $latestMsvc" -ForegroundColor Yellow

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Restart PowerShell to load new environment variables"
Write-Host "2. Run update-to-ue5.7.ps1 to update Unreal Engine"
Write-Host "3. Build the project with VS2026"
Write-Host "4. Enable C++20 features in project settings"

Write-Host "`nNote: VS2026 uses folder '18' as it's version 18.0" -ForegroundColor Yellow
Write-Host "Released: November 11, 2025" -ForegroundColor Gray
