# Generate Visual Studio Solution Files for UE5 Project
# REAL IMPLEMENTATION - Uses Unreal Engine's solution generator

param(
    [string]$ProjectPath = "unreal\BodyBroker.uproject",
    [string]$UEEnginePath = ""
)

Write-Host "[GEN] Generating Visual Studio solution files..." -ForegroundColor Cyan

# Find UE5 Engine
if ([string]::IsNullOrEmpty($UEEnginePath))
{
    $ueInstallPath = Get-ChildItem "C:\Program Files\Epic Games\" -Directory -Filter "UE_*" -ErrorAction SilentlyContinue | 
        Select-Object -First 1
    
    if ($ueInstallPath)
    {
        $UEEnginePath = $ueInstallPath.FullName
        Write-Host "[GEN] Auto-detected UE5: $UEEnginePath" -ForegroundColor Green
    }
    else
    {
        Write-Host "[ERROR] UE5 Engine not found. Please specify -UEEnginePath" -ForegroundColor Red
        exit 1
    }
}

# Find Unreal Version Selector or RightClickBuild
$GenToolPath = Join-Path $UEEnginePath "Engine\Binaries\DotNET\UnrealVersionSelector\UnrealVersionSelector.exe"
if (-not (Test-Path $GenToolPath))
{
    # Alternative: Use UnrealBuildTool directly with -projectfiles
    $BuildToolPath = Join-Path $UEEnginePath "Engine\Build\BatchFiles\Build.bat"
    if (Test-Path $BuildToolPath)
    {
        Write-Host "[GEN] Using UnrealBuildTool for project files..." -ForegroundColor Yellow
        $GenToolPath = $BuildToolPath
    }
    else
    {
        Write-Host "[ERROR] Solution generator not found" -ForegroundColor Red
        exit 1
    }
}

# Resolve project path
$FullProjectPath = Resolve-Path $ProjectPath -ErrorAction Stop
$ProjectName = [System.IO.Path]::GetFileNameWithoutExtension($FullProjectPath)

Write-Host "[GEN] Project: $ProjectName" -ForegroundColor Cyan
Write-Host "[GEN] Full path: $FullProjectPath" -ForegroundColor Gray

# Generate project files
$GenArgs = @(
    "-projectfiles",
    "-project=`"$FullProjectPath`"",
    "-game",
    "-rocket",
    "-progress"
)

Write-Host "[GEN] Executing: $GenToolPath $($GenArgs -join ' ')" -ForegroundColor Cyan

$process = Start-Process -FilePath $GenToolPath -ArgumentList $GenArgs -NoNewWindow -Wait -PassThru

if ($process.ExitCode -eq 0)
{
    Write-Host "[GEN] ✅ Visual Studio files generated successfully!" -ForegroundColor Green
    Write-Host "[GEN] Solution file: unreal\BodyBroker.sln" -ForegroundColor Cyan
    exit 0
}
else
{
    Write-Host "[GEN] ❌ Generation failed with exit code: $($process.ExitCode)" -ForegroundColor Red
    exit $process.ExitCode
}



