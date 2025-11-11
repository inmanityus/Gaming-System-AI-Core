# Continuous Build Automation for UE5 Project
# REAL IMPLEMENTATION - Watches for changes and automatically rebuilds

param(
    [int]$CheckInterval = 30,  # Check every 30 seconds
    [switch]$BuildOnStart = $true
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  UE5 CONTINUOUS BUILD AUTOMATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[MODE] Watching for source file changes..." -ForegroundColor Yellow
Write-Host "[INTERVAL] Checking every $CheckInterval seconds" -ForegroundColor Gray
Write-Host ""

$ProjectPath = "unreal\BodyBroker.uproject"
$SourceDir = "unreal\Source"
$LastBuildTime = Get-Date

# Build on start if requested
if ($BuildOnStart)
{
    Write-Host "[INITIAL BUILD] Building project..." -ForegroundColor Yellow
    & "$PSScriptRoot\automated-ue5-build.ps1"
    $LastBuildTime = Get-Date
    Write-Host "[INITIAL BUILD] ✅ Complete" -ForegroundColor Green
    Write-Host ""
}

Write-Host "[WATCHING] Monitoring for changes..." -ForegroundColor Cyan
Write-Host "[STOP] Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

try
{
    while ($true)
    {
        # Check for source file changes
        $sourceFiles = Get-ChildItem -Path $SourceDir -Recurse -Include *.h,*.cpp -ErrorAction SilentlyContinue
        
        $needsBuild = $false
        foreach ($file in $sourceFiles)
        {
            if ($file.LastWriteTime -gt $LastBuildTime)
            {
                Write-Host "[CHANGE DETECTED] $($file.Name) was modified" -ForegroundColor Yellow
                $needsBuild = $true
            }
        }
        
        if ($needsBuild)
        {
            Write-Host "[REBUILD] Starting automatic rebuild..." -ForegroundColor Cyan
            $buildStart = Get-Date
            
            & "$PSScriptRoot\automated-ue5-build.ps1"
            
            $buildDuration = (Get-Date) - $buildStart
            if ($LASTEXITCODE -eq 0)
            {
                Write-Host "[REBUILD] ✅ Complete (Duration: $($buildDuration.TotalSeconds)s)" -ForegroundColor Green
                $LastBuildTime = Get-Date
            }
            else
            {
                Write-Host "[REBUILD] ❌ Failed" -ForegroundColor Red
            }
            Write-Host ""
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}
catch
{
    Write-Host "[STOPPED] Continuous build automation stopped" -ForegroundColor Yellow
}







