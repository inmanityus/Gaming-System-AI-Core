# UE5 Automation Test Runner
# Runs Body Broker tests from command line without GUI
# Part of AI-Driven Game Testing System (Tier 0)

param(
    [string]$Filter = "BodyBroker",
    [string]$OutputDir = "test-results",
    [switch]$SmokeOnly,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Project paths
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ProjectFile = Join-Path $ProjectRoot "unreal\BodyBroker.uproject"
$UE5Editor = "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe"

# Output paths
$OutputPath = Join-Path $ProjectRoot $OutputDir
$LogPath = Join-Path $OutputPath "test-run-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Create output directory
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath | Out-Null
}

# Verify UE5 installation
if (-not (Test-Path $UE5Editor)) {
    Write-Error "UE5 Editor not found at: $UE5Editor"
    Write-Error "Please verify UE 5.6.1 installation"
    exit 1
}

# Verify project file
if (-not (Test-Path $ProjectFile)) {
    Write-Error "Project file not found at: $ProjectFile"
    exit 1
}

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  UE5 Automation Test Runner - The Body Broker" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project:  $ProjectFile" -ForegroundColor Gray
Write-Host "Filter:   $Filter" -ForegroundColor Gray
Write-Host "Output:   $OutputPath" -ForegroundColor Gray
Write-Host "Log:      $LogPath" -ForegroundColor Gray
Write-Host ""

# Adjust filter for smoke tests
if ($SmokeOnly) {
    $Filter = "$Filter+Smoke"
    Write-Host "Running SMOKE TESTS ONLY (fast tests <1 second)" -ForegroundColor Yellow
    Write-Host ""
}

# Build command
$TestCommand = "Automation RunTests Now $Filter"

$Arguments = @(
    "`"$ProjectFile`""
    "-ExecCmds=`"$TestCommand`""
    "-unattended"
    "-nopause"
    "-nullrhi"
    "-ReportOutputPath=`"$OutputPath`""
    "-log=`"$LogPath`""
)

if ($Verbose) {
    $Arguments += "-verbose"
}

Write-Host "Starting test execution..." -ForegroundColor Green
Write-Host "Command: $TestCommand" -ForegroundColor Gray
Write-Host ""
Write-Host "⏱️  This may take several minutes. Please wait..." -ForegroundColor Yellow
Write-Host ""

# Execute tests
$StartTime = Get-Date

try {
    $Process = Start-Process -FilePath $UE5Editor -ArgumentList $Arguments -Wait -PassThru -NoNewWindow
    
    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    if ($Process.ExitCode -eq 0) {
        Write-Host "✓ Test execution completed successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠ Test execution completed with exit code: $($Process.ExitCode)" -ForegroundColor Yellow
    }
    
    Write-Host "Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Parse results
    Write-Host "Parsing test results..." -ForegroundColor Cyan
    
    # Look for JSON report file
    $ReportFiles = Get-ChildItem -Path $OutputPath -Filter "*.json" | Sort-Object LastWriteTime -Descending
    
    if ($ReportFiles.Count -eq 0) {
        Write-Warning "No JSON report files found. Check log file: $LogPath"
        exit 1
    }
    
    $ReportFile = $ReportFiles[0].FullName
    Write-Host "Report file: $ReportFile" -ForegroundColor Gray
    
    # Parse JSON results
    $Results = Get-Content $ReportFile -Raw | ConvertFrom-Json
    
    # Display summary
    Write-Host ""
    Write-Host "TEST RESULTS SUMMARY:" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    $TotalTests = $Results.tests.Count
    $PassedTests = ($Results.tests | Where-Object { $_.state -eq "Success" }).Count
    $FailedTests = ($Results.tests | Where-Object { $_.state -eq "Fail" }).Count
    $SkippedTests = ($Results.tests | Where-Object { $_.state -eq "Skipped" }).Count
    
    Write-Host "Total Tests:   $TotalTests" -ForegroundColor White
    Write-Host "Passed:        $PassedTests" -ForegroundColor Green
    
    if ($FailedTests -gt 0) {
        Write-Host "Failed:        $FailedTests" -ForegroundColor Red
    } else {
        Write-Host "Failed:        $FailedTests" -ForegroundColor Gray
    }
    
    if ($SkippedTests -gt 0) {
        Write-Host "Skipped:       $SkippedTests" -ForegroundColor Yellow
    }
    
    Write-Host "Duration:      $($Duration.ToString('mm\:ss'))" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    # Show failed tests if any
    if ($FailedTests -gt 0) {
        Write-Host ""
        Write-Host "FAILED TESTS:" -ForegroundColor Red
        foreach ($Test in ($Results.tests | Where-Object { $_.state -eq "Fail" })) {
            Write-Host "  ✗ $($Test.testDisplayName)" -ForegroundColor Red
            if ($Test.errors) {
                foreach ($Error in $Test.errors) {
                    Write-Host "    $Error" -ForegroundColor Gray
                }
            }
        }
        Write-Host ""
    }
    
    # Summary
    if ($FailedTests -eq 0) {
        Write-Host ""
        Write-Host "🎉 ALL TESTS PASSED! 🎉" -ForegroundColor Green
        Write-Host ""
        exit 0
    } else {
        Write-Host ""
        Write-Host "⚠️  SOME TESTS FAILED - Review failures above" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
    
} catch {
    Write-Error "Test execution failed: $_"
    Write-Host "Check log file: $LogPath" -ForegroundColor Yellow
    exit 1
}

