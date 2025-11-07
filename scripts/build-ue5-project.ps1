# UE5 Project Build Script
# Convenient wrapper for building UE5 projects from command line

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "unreal\BodyBroker.uproject",
    
    [Parameter(Mandatory=$false)]
    [string]$Configuration = "Development",
    
    [Parameter(Mandatory=$false)]
    [string]$Platform = "Win64",
    
    [Parameter(Mandatory=$false)]
    [string]$TargetType = "Editor",
    
    [Parameter(Mandatory=$false)]
    [string]$UEPath = ""
)

Write-Host "=== UE5 Project Build Script ===" -ForegroundColor Cyan
Write-Host ""

# Resolve project path
$fullProjectPath = Resolve-Path $ProjectPath -ErrorAction Stop
Write-Host "Project: $fullProjectPath" -ForegroundColor White

# Auto-detect UE5.6.1 if path not provided
if ([string]::IsNullOrEmpty($UEPath)) {
    # CRITICAL: UE 5.6.1 is installed at UE_5.6 folder (version 5.6.1, folder name is UE_5.6)
    $UEPath = "C:\Program Files\Epic Games\UE_5.6"
    
    if (-not (Test-Path $UEPath)) {
        Write-Host "❌ UE 5.6.1 not found at: $UEPath" -ForegroundColor Red
        Write-Host "Please install UE 5.6.1 or update -UEPath parameter" -ForegroundColor Yellow
        exit 1
    }
}

# Check UE installation
if (-not (Test-Path $UEPath)) {
    Write-Host "❌ UE5 not found at: $UEPath" -ForegroundColor Red
    Write-Host "Please install UE 5.6.1 or update -UEPath parameter" -ForegroundColor Yellow
    exit 1
}

$buildBat = Join-Path $UEPath "Engine\Build\BatchFiles\Build.bat"
if (-not (Test-Path $buildBat)) {
    Write-Host "❌ Build.bat not found at: $buildBat" -ForegroundColor Red
    exit 1
}

Write-Host "UE Path: $UEPath" -ForegroundColor White
Write-Host "✓ Using UE 5.6.1 (correct version)" -ForegroundColor Green
Write-Host "Configuration: $Configuration" -ForegroundColor White
Write-Host "Platform: $Platform" -ForegroundColor White
Write-Host "Target Type: $TargetType" -ForegroundColor White
Write-Host ""

# Build command
Write-Host "Starting build..." -ForegroundColor Yellow
Write-Host ""

& cmd.exe /c "`"$buildBat`" $Configuration $Platform -Project=`"$fullProjectPath`" -TargetType=$TargetType -Progress -NoEngineChanges"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
