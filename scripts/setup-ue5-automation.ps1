# Setup UE5 Automation - Detects and configures build tools
# REAL IMPLEMENTATION - Finds all necessary tools for automation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  UE5 AUTOMATION SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$setup = @{
    "UnrealBuildTool" = $null
    "VisualStudio" = $null
    "MSBuild" = $null
    "UE5Engine" = $null
}

# Find UE5 Engine
Write-Host "[SEARCH] Looking for UE5 Engine..." -ForegroundColor Yellow
$ueVersions = Get-ChildItem "C:\Program Files\Epic Games\" -Directory -Filter "UE_*" -ErrorAction SilentlyContinue | 
    Sort-Object Name -Descending

if ($ueVersions)
{
    $latestUE = $ueVersions[0]
    $setup.UE5Engine = $latestUE.FullName
    Write-Host "[FOUND] UE5 Engine: $($latestUE.Name) at $($latestUE.FullName)" -ForegroundColor Green
    
    # Find UnrealBuildTool
    $buildTool = Join-Path $latestUE.FullName "Engine\Build\BatchFiles\Build.bat"
    if (Test-Path $buildTool)
    {
        $setup.UnrealBuildTool = $buildTool
        Write-Host "[FOUND] UnrealBuildTool: $buildTool" -ForegroundColor Green
    }
}
else
{
    Write-Host "[NOT FOUND] UE5 Engine not detected" -ForegroundColor Yellow
    Write-Host "[ACTION REQUIRED] Please install UE5 or provide path manually" -ForegroundColor Red
}

Write-Host ""

# Find Visual Studio / MSBuild
Write-Host "[SEARCH] Looking for Visual Studio / MSBuild..." -ForegroundColor Yellow
$vsPaths = @(
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
)

foreach ($path in $vsPaths)
{
    if (Test-Path $path)
    {
        $setup.MSBuild = $path
        $setup.VisualStudio = Split-Path (Split-Path (Split-Path $path)) -Parent
        Write-Host "[FOUND] MSBuild: $path" -ForegroundColor Green
        break
    }
}

if (-not $setup.MSBuild)
{
    Write-Host "[NOT FOUND] Visual Studio / MSBuild not detected" -ForegroundColor Yellow
    Write-Host "[ACTION REQUIRED] Please install Visual Studio 2019 or 2022" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

foreach ($key in $setup.Keys)
{
    if ($setup[$key])
    {
        Write-Host "[$key] ✅ $($setup[$key])" -ForegroundColor Green
    }
    else
    {
        Write-Host "[$key] ❌ Not found" -ForegroundColor Red
    }
}

Write-Host ""

# Save configuration
$configPath = ".ue5-build-config.json"
$setup | ConvertTo-Json | Out-File $configPath
Write-Host "[CONFIG] Saved to: $configPath" -ForegroundColor Cyan

if ($setup.UnrealBuildTool -and $setup.MSBuild)
{
    Write-Host ""
    Write-Host "[STATUS] ✅ Automation ready!" -ForegroundColor Green
    Write-Host "[NEXT] Run: .\scripts\automated-ue5-build.ps1" -ForegroundColor Cyan
}
else
{
    Write-Host ""
    Write-Host "[STATUS] ⚠️ Some tools missing - automation may not work fully" -ForegroundColor Yellow
}






