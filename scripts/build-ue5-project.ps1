# Build UE5 Project - Automated Compilation Script
# REAL IMPLEMENTATION - Uses actual UnrealBuildTool to compile project

param(
    [string]$ProjectPath = "unreal\BodyBroker.uproject",
    [string]$Configuration = "Development",
    [string]$Platform = "Win64",
    [string]$UEEnginePath = ""
)

Write-Host "[BUILD] Starting UE5 project compilation..." -ForegroundColor Cyan
Write-Host "[BUILD] Project: $ProjectPath" -ForegroundColor Yellow
Write-Host "[BUILD] Configuration: $Configuration" -ForegroundColor Yellow
Write-Host "[BUILD] Platform: $Platform" -ForegroundColor Yellow

# Find UE5 Engine
if ([string]::IsNullOrEmpty($UEEnginePath))
{
    $ueInstallPath = Get-ChildItem "C:\Program Files\Epic Games\" -Directory -Filter "UE_*" -ErrorAction SilentlyContinue | 
        Select-Object -First 1
    
    if ($ueInstallPath)
    {
        $UEEnginePath = $ueInstallPath.FullName
        Write-Host "[BUILD] Auto-detected UE5: $UEEnginePath" -ForegroundColor Green
    }
    else
    {
        Write-Host "[ERROR] UE5 Engine not found. Please specify -UEEnginePath" -ForegroundColor Red
        exit 1
    }
}

# Find UnrealBuildTool
$BuildToolPath = Join-Path $UEEnginePath "Engine\Build\BatchFiles\Build.bat"
if (-not (Test-Path $BuildToolPath))
{
    Write-Host "[ERROR] UnrealBuildTool not found at: $BuildToolPath" -ForegroundColor Red
    exit 1
}

Write-Host "[BUILD] Using UnrealBuildTool: $BuildToolPath" -ForegroundColor Green

# Resolve project path
$FullProjectPath = Resolve-Path $ProjectPath -ErrorAction Stop
$ProjectName = [System.IO.Path]::GetFileNameWithoutExtension($FullProjectPath)

Write-Host "[BUILD] Building project: $ProjectName" -ForegroundColor Cyan
Write-Host "[BUILD] Full path: $FullProjectPath" -ForegroundColor Gray

# Build command
$BuildArgs = @(
    $ProjectName + "Editor",
    $Platform,
    $Configuration,
    "-project=`"$FullProjectPath`"",
    "-rocket",
    "-NoHotReloadFromIDE"
)

Write-Host "[BUILD] Executing: $BuildToolPath $($BuildArgs -join ' ')" -ForegroundColor Cyan

# Execute build
$process = Start-Process -FilePath $BuildToolPath -ArgumentList $BuildArgs -NoNewWindow -Wait -PassThru

if ($process.ExitCode -eq 0)
{
    Write-Host "[BUILD] ✅ Compilation successful!" -ForegroundColor Green
    exit 0
}
else
{
    Write-Host "[BUILD] ❌ Compilation failed with exit code: $($process.ExitCode)" -ForegroundColor Red
    exit $process.ExitCode
}



