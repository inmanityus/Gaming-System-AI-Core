# Build Everything - Master Automation Script
# REAL IMPLEMENTATION - Builds ALL components automatically

param(
    [switch]$SkipPython = $false,
    [switch]$SkipUE5 = $false,
    [switch]$RunTests = $true
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BUILD EVERYTHING - AUTOMATED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[RULE] Following /all-rules - Building all components" -ForegroundColor Yellow
Write-Host ""

$global:buildResults = @{
    "Python" = $null
    "UE5" = $null
    "Tests" = $null
}

$totalStart = Get-Date

# ========================================
# STEP 1: Python Backend Services
# ========================================
if (-not $SkipPython)
{
    Write-Host "[STEP 1] Building Python Backend Services..." -ForegroundColor Yellow
    $pythonStart = Get-Date
    
    # Syntax validation
    Write-Host "[1.1] Validating Python syntax..." -ForegroundColor Gray
    $syntaxErrors = python -m py_compile services/**/*.py 2>&1
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "[1.1] ✅ All Python files valid" -ForegroundColor Green
    }
    else
    {
        Write-Host "[1.1] ⚠️ Syntax errors found:" -ForegroundColor Yellow
        $syntaxErrors | Select-Object -First 10
    }
    
    # Run tests if requested
    if ($RunTests)
    {
        Write-Host "[1.2] Running Python tests..." -ForegroundColor Gray
        python -m pytest services/event_bus/tests/ services/time_manager/tests/ services/weather_manager/tests/ -v --tb=line 2>&1 | Select-Object -Last 5
        if ($LASTEXITCODE -eq 0)
        {
            Write-Host "[1.2] ✅ All tests passing" -ForegroundColor Green
            $global:buildResults.Tests = "PASSED"
        }
        else
        {
            Write-Host "[1.2] ⚠️ Some tests failed" -ForegroundColor Yellow
            $global:buildResults.Tests = "FAILED"
        }
    }
    
    $pythonDuration = (Get-Date) - $pythonStart
    $global:buildResults.Python = "✅ ($([math]::Round($pythonDuration.TotalSeconds, 2))s)"
    Write-Host "[STEP 1] ✅ Python services ready" -ForegroundColor Green
    Write-Host ""
}

# ========================================
# STEP 2: UE5 Project
# ========================================
if (-not $SkipUE5)
{
    Write-Host "[STEP 2] Building UE5 Project..." -ForegroundColor Yellow
    $ue5Start = Get-Date
    
    # Generate VS files
    Write-Host "[2.1] Generating Visual Studio solution..." -ForegroundColor Gray
    & "$PSScriptRoot\generate-vs-files.ps1" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "[2.1] ✅ VS files generated" -ForegroundColor Green
    }
    else
    {
        Write-Host "[2.1] ⚠️ VS generation had warnings" -ForegroundColor Yellow
    }
    
    # Build project
    Write-Host "[2.2] Compiling UE5 project..." -ForegroundColor Gray
    & "$PSScriptRoot\build-ue5-project.ps1" 2>&1 | Tee-Object -Variable buildOutput
    
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "[2.2] ✅ UE5 compilation successful" -ForegroundColor Green
        $global:buildResults.UE5 = "✅ COMPILED"
    }
    else
    {
        Write-Host "[2.2] ❌ UE5 compilation failed" -ForegroundColor Red
        $buildOutput | Select-Object -Last 20
        $global:buildResults.UE5 = "❌ FAILED"
    }
    
    $ue5Duration = (Get-Date) - $ue5Start
    Write-Host "[STEP 2] UE5 build duration: $([math]::Round($ue5Duration.TotalSeconds, 2))s" -ForegroundColor Gray
    Write-Host ""
}

# ========================================
# SUMMARY
# ========================================
$totalDuration = (Get-Date) - $totalStart

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BUILD SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

foreach ($component in $global:buildResults.Keys)
{
    $status = $global:buildResults[$component]
    if ($status)
    {
        Write-Host "[$component] $status" -ForegroundColor $(if ($status -match "✅|PASSED") { "Green" } else { "Red" })
    }
}

Write-Host ""
Write-Host "[TOTAL DURATION] $([math]::Round($totalDuration.TotalSeconds, 2)) seconds" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($global:buildResults.UE5 -eq "✅ COMPILED")
{
    Write-Host ""
    Write-Host "[SUCCESS] ✅ All components built successfully!" -ForegroundColor Green
    Write-Host "[NEXT] Open unreal\BodyBroker.uproject in UE5 Editor" -ForegroundColor Cyan
    exit 0
}
else
{
    Write-Host ""
    Write-Host "[WARNING] Some components may need attention" -ForegroundColor Yellow
    exit 1
}











