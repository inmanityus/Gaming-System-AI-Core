# Automated UE5 Build Pipeline
# REAL IMPLEMENTATION - Full automation for UE5 project building

param(
    [switch]$SkipGeneration = $false,
    [switch]$SkipBuild = $false,
    [string]$Configuration = "Development"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  UE5 AUTOMATED BUILD PIPELINE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$ProjectPath = "unreal\BodyBroker.uproject"

# Step 1: Generate Visual Studio files
if (-not $SkipGeneration)
{
    Write-Host "[STEP 1] Generating Visual Studio solution files..." -ForegroundColor Yellow
    & "$PSScriptRoot\generate-vs-files.ps1" -ProjectPath $ProjectPath
    if ($LASTEXITCODE -ne 0)
    {
        Write-Host "[ERROR] Failed to generate solution files" -ForegroundColor Red
        exit 1
    }
    Write-Host "[STEP 1] ✅ Complete" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Build the project
if (-not $SkipBuild)
{
    Write-Host "[STEP 2] Compiling UE5 project..." -ForegroundColor Yellow
    & "$PSScriptRoot\build-ue5-project.ps1" -ProjectPath $ProjectPath -Configuration $Configuration
    if ($LASTEXITCODE -ne 0)
    {
        Write-Host "[ERROR] Compilation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[STEP 2] ✅ Complete" -ForegroundColor Green
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  BUILD PIPELINE COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green



