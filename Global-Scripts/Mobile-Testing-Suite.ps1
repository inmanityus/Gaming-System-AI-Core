# Comprehensive Mobile Testing Suite
# Orchestrates complete mobile testing across local Android AVDs and remote iOS devices

param(
    [string]$Url = "https://befreefitness.ai/ai-analyzer",
    [string]$OutputDir = ".logs/mobile-testing",
    [switch]$SkipAndroid,  # Skip local Android testing
    [switch]$SkipRemote,    # Skip remote iOS/Android testing
    [string]$RemoteService = "BrowserStack",  # BrowserStack, SauceLabs, or LambdaTest
    [string]$RemoteUsername,  # Remote service username
    [string]$RemoteAccessKey,  # Remote service access key
    [switch]$SetupOnly  # Only setup, don't run tests
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📱 COMPREHENSIVE MOBILE TESTING SUITE" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Create base output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$androidOutputDir = "$OutputDir\android"
$remoteOutputDir = "$OutputDir\remote"
$reportOutputDir = "$OutputDir\reports"

foreach ($dir in @($androidOutputDir, $remoteOutputDir, $reportOutputDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "`n✅ Output directories created:" -ForegroundColor Green
Write-Host "   Android: $androidOutputDir" -ForegroundColor White
Write-Host "   Remote: $remoteOutputDir" -ForegroundColor White
Write-Host "   Reports: $reportOutputDir" -ForegroundColor White

# Get script directory (Global-Scripts location)
$scriptDir = $PSScriptRoot

# ============================================================================
# SETUP PHASE
# ============================================================================

Write-Host "`n" + ("=" * 60)
Write-Host "🔧 SETUP PHASE" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Check if Android SDK command-line tools are installed
$androidSdkPath = "$env:LOCALAPPDATA\Android\Sdk"
$sdkmanager = "$androidSdkPath\cmdline-tools\latest\bin\sdkmanager.bat"

if (-not (Test-Path $sdkmanager)) {
    Write-Host "`n⚠️  Android SDK command-line tools not found" -ForegroundColor Yellow
    Write-Host "   Installing command-line tools..." -ForegroundColor Cyan
    
    try {
        & "$scriptDir\Install-AndroidSDKTools.ps1"
        if ($LASTEXITCODE -ne 0) {
            throw "Installation failed with exit code $LASTEXITCODE"
        }
        Write-Host "   ✅ Command-line tools installed" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Installation failed: $_" -ForegroundColor Red
        Write-Host "   Continuing without Android SDK tools..." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n✅ Android SDK command-line tools found" -ForegroundColor Green
}

# Check if test AVDs exist
$emulator = "$androidSdkPath\emulator\emulator.exe"
if (Test-Path $emulator) {
    $availableAVDs = & $emulator -list-avds 2>&1
    $testAVDs = @("Samsung_Galaxy_S23_Test", "Google_Pixel_9_Pro_Test")
    $missingAVDs = $testAVDs | Where-Object { $availableAVDs -notcontains $_ }
    
    if ($missingAVDs.Count -gt 0) {
        Write-Host "`n⚠️  Required test AVDs not found: $($missingAVDs -join ', ')" -ForegroundColor Yellow
        Write-Host "   Creating test AVDs..." -ForegroundColor Cyan
        
        try {
            & "$scriptDir\Create-AndroidAVDs.ps1" -Force
            if ($LASTEXITCODE -ne 0) {
                throw "AVD creation failed with exit code $LASTEXITCODE"
            }
            Write-Host "   ✅ Test AVDs created" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ AVD creation failed: $_" -ForegroundColor Red
            Write-Host "   Android testing may be limited" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n✅ Required test AVDs found" -ForegroundColor Green
    }
}

# Validate remote service credentials
if (-not $SkipRemote) {
    Write-Host "`n📋 Remote Service Configuration:" -ForegroundColor Cyan
    Write-Host "   Service: $RemoteService" -ForegroundColor White
    
    if (-not $RemoteUsername -or -not $RemoteAccessKey) {
        Write-Host "   ⚠️  Remote service credentials not provided" -ForegroundColor Yellow
        Write-Host "   Checking environment variables..." -ForegroundColor Cyan
        
        # Check environment variables based on service
        switch ($RemoteService) {
            "BrowserStack" {
                $RemoteUsername = $env:BROWSERSTACK_USERNAME
                $RemoteAccessKey = $env:BROWSERSTACK_ACCESS_KEY
            }
            "SauceLabs" {
                $RemoteUsername = $env:SAUCE_USERNAME
                $RemoteAccessKey = $env:SAUCE_ACCESS_KEY
            }
            "LambdaTest" {
                $RemoteUsername = $env:LT_USERNAME
                $RemoteAccessKey = $env:LT_ACCESS_KEY
            }
        }
        
        if (-not $RemoteUsername -or -not $RemoteAccessKey) {
            Write-Host "   ❌ Remote service credentials not found" -ForegroundColor Red
            Write-Host "   Set environment variables or pass -RemoteUsername and -RemoteAccessKey" -ForegroundColor Yellow
            Write-Host "   Skipping remote testing..." -ForegroundColor Yellow
            $SkipRemote = $true
        } else {
            Write-Host "   ✅ Credentials loaded from environment" -ForegroundColor Green
        }
    } else {
        Write-Host "   ✅ Credentials provided via parameters" -ForegroundColor Green
    }
}

if ($SetupOnly) {
    Write-Host "`n✅ Setup complete! Use -SetupOnly:$false to run tests." -ForegroundColor Green
    exit 0
}

# ============================================================================
# TESTING PHASE
# ============================================================================

Write-Host "`n" + ("=" * 60)
Write-Host "🧪 TESTING PHASE" -ForegroundColor Cyan
Write-Host ("=" * 60)

$testResults = @{
    Android = @()
    Remote = @()
    StartTime = Get-Date
}

# ============================================================================
# 1. LOCAL ANDROID TESTING
# ============================================================================

if (-not $SkipAndroid) {
    Write-Host "`n📱 LOCAL ANDROID DEVICE TESTING" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    try {
        & "$scriptDir\Test-AndroidDevices.ps1" `
            -Url $Url `
            -OutputDir $androidOutputDir `
            -WaitSeconds 10
        
        $testResults.Android = @{
            Success = ($LASTEXITCODE -eq 0)
            ExitCode = $LASTEXITCODE
        }
    } catch {
        Write-Host "`n❌ Android testing failed: $_" -ForegroundColor Red
        $testResults.Android = @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
} else {
    Write-Host "`n⏭️  Skipping local Android testing" -ForegroundColor Yellow
    $testResults.Android = @{ Skipped = $true }
}

# ============================================================================
# 2. REMOTE iOS & ANDROID TESTING
# ============================================================================

if (-not $SkipRemote) {
    Write-Host "`n🌐 REMOTE DEVICE TESTING ($RemoteService)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    try {
        & "$scriptDir\Test-RemoteDevices.ps1" `
            -Service $RemoteService `
            -Username $RemoteUsername `
            -AccessKey $RemoteAccessKey `
            -Url $Url `
            -OutputDir $remoteOutputDir `
            -WaitSeconds 10
        
        $testResults.Remote = @{
            Success = ($LASTEXITCODE -eq 0)
            ExitCode = $LASTEXITCODE
            Service = $RemoteService
        }
    } catch {
        Write-Host "`n❌ Remote testing failed: $_" -ForegroundColor Red
        $testResults.Remote = @{
            Success = $false
            Error = $_.Exception.Message
            Service = $RemoteService
        }
    }
} else {
    Write-Host "`n⏭️  Skipping remote device testing" -ForegroundColor Yellow
    $testResults.Remote = @{ Skipped = $true }
}

# ============================================================================
# REPORT GENERATION
# ============================================================================

Write-Host "`n" + ("=" * 60)
Write-Host "📊 GENERATING TEST REPORT" -ForegroundColor Cyan
Write-Host ("=" * 60)

$testResults.EndTime = Get-Date
$testResults.Duration = ($testResults.EndTime - $testResults.StartTime).TotalSeconds

# Count screenshots
$androidScreenshots = if (Test-Path $androidOutputDir) {
    (Get-ChildItem -Path $androidOutputDir -Filter "*.png" -ErrorAction SilentlyContinue).Count
} else { 0 }

$remoteScreenshots = if (Test-Path $remoteOutputDir) {
    (Get-ChildItem -Path $remoteOutputDir -Filter "*.png" -ErrorAction SilentlyContinue).Count
} else { 0 }

$totalScreenshots = $androidScreenshots + $remoteScreenshots

# Generate HTML report
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportFile = "$reportOutputDir\mobile-test-report-$timestamp.html"

$htmlReport = @"
<!DOCTYPE html>
<html>
<head>
    <title>Mobile Testing Report - $timestamp</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .success { color: #27ae60; font-weight: bold; }
        .failure { color: #e74c3c; font-weight: bold; }
        .skipped { color: #95a5a6; font-style: italic; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; padding: 10px 15px; background: white; border-radius: 5px; }
        .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #34495e; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ecf0f1; }
        .screenshot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .screenshot { border: 2px solid #ecf0f1; border-radius: 5px; overflow: hidden; }
        .screenshot img { width: 100%; height: auto; display: block; }
        .screenshot-label { background: #34495e; color: white; padding: 8px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Mobile Testing Report</h1>
        <p><strong>Generated:</strong> $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
        <p><strong>Test URL:</strong> $Url</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">
                <div class="metric-label">Total Screenshots</div>
                <div class="metric-value">$totalScreenshots</div>
            </div>
            <div class="metric">
                <div class="metric-label">Android Screenshots</div>
                <div class="metric-value">$androidScreenshots</div>
            </div>
            <div class="metric">
                <div class="metric-label">Remote Screenshots</div>
                <div class="metric-value">$remoteScreenshots</div>
            </div>
            <div class="metric">
                <div class="metric-label">Duration</div>
                <div class="metric-value">$([math]::Round($testResults.Duration, 1))s</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test Suite</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
            <tr>
                <td>Local Android Devices</td>
                <td>$( if ($testResults.Android.Skipped) { '<span class="skipped">SKIPPED</span>' } elseif ($testResults.Android.Success) { '<span class="success">✅ PASSED</span>' } else { '<span class="failure">❌ FAILED</span>' } )</td>
                <td>$( if ($testResults.Android.Error) { $testResults.Android.Error } else { "$androidScreenshots screenshots captured" } )</td>
            </tr>
            <tr>
                <td>Remote Devices ($RemoteService)</td>
                <td>$( if ($testResults.Remote.Skipped) { '<span class="skipped">SKIPPED</span>' } elseif ($testResults.Remote.Success) { '<span class="success">✅ PASSED</span>' } else { '<span class="failure">❌ FAILED</span>' } )</td>
                <td>$( if ($testResults.Remote.Error) { $testResults.Remote.Error } else { "$remoteScreenshots screenshots captured" } )</td>
            </tr>
        </table>
        
        <h2>Screenshots</h2>
        <div class="screenshot-grid">
"@

# Helper function to convert image to base64 data URI
function Get-ImageDataUri {
    param([string]$ImagePath)
    if (Test-Path $ImagePath) {
        $bytes = [System.IO.File]::ReadAllBytes($ImagePath)
        $base64 = [Convert]::ToBase64String($bytes)
        return "data:image/png;base64,$base64"
    }
    return ""
}

# Add Android screenshots to report (embedded as base64)
if ($androidScreenshots -gt 0) {
    Get-ChildItem -Path $androidOutputDir -Filter "*.png" -ErrorAction SilentlyContinue | ForEach-Object {
        $dataUri = Get-ImageDataUri $_.FullName
        $htmlReport += @"
            <div class="screenshot">
                <img src="$dataUri" alt="$($_.Name)">
                <div class="screenshot-label">$($_.Name)</div>
            </div>
"@
    }
}

# Add remote screenshots to report (embedded as base64)
if ($remoteScreenshots -gt 0) {
    Get-ChildItem -Path $remoteOutputDir -Filter "*.png" -ErrorAction SilentlyContinue | ForEach-Object {
        $dataUri = Get-ImageDataUri $_.FullName
        $htmlReport += @"
            <div class="screenshot">
                <img src="$dataUri" alt="$($_.Name)">
                <div class="screenshot-label">$($_.Name)</div>
            </div>
"@
    }
}

$htmlReport += @"
        </div>
    </div>
</body>
</html>
"@

# Save HTML report
Set-Content -Path $reportFile -Value $htmlReport
Write-Host "`n✅ HTML report generated: $reportFile" -ForegroundColor Green

# Generate JSON report
$jsonReport = $testResults | ConvertTo-Json -Depth 10
$jsonReportFile = "$reportOutputDir\mobile-test-report-$timestamp.json"
Set-Content -Path $jsonReportFile -Value $jsonReport
Write-Host "✅ JSON report generated: $jsonReportFile" -ForegroundColor Green

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host "`n" + ("=" * 60)
Write-Host "🎯 FINAL SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 60)

Write-Host "`n📊 Test Results:" -ForegroundColor Cyan
if ($testResults.Android.Skipped) {
    Write-Host "   Android: SKIPPED" -ForegroundColor Yellow
} elseif ($testResults.Android.Success) {
    Write-Host "   Android: ✅ PASSED ($androidScreenshots screenshots)" -ForegroundColor Green
} else {
    Write-Host "   Android: ❌ FAILED" -ForegroundColor Red
}

if ($testResults.Remote.Skipped) {
    Write-Host "   Remote: SKIPPED" -ForegroundColor Yellow
} elseif ($testResults.Remote.Success) {
    Write-Host "   Remote: ✅ PASSED ($remoteScreenshots screenshots)" -ForegroundColor Green
} else {
    Write-Host "   Remote: ❌ FAILED" -ForegroundColor Red
}

Write-Host "`n📸 Total Screenshots: $totalScreenshots" -ForegroundColor Cyan
Write-Host "⏱️  Total Duration: $([math]::Round($testResults.Duration, 1)) seconds" -ForegroundColor Cyan
Write-Host "`n📁 Output Locations:" -ForegroundColor Cyan
Write-Host "   Android: $androidOutputDir" -ForegroundColor White
Write-Host "   Remote: $remoteOutputDir" -ForegroundColor White
Write-Host "   Reports: $reportOutputDir" -ForegroundColor White
Write-Host "`n📄 View Report: $reportFile" -ForegroundColor Cyan

# Open report in browser
try {
    Start-Process $reportFile
    Write-Host "`n✅ Report opened in browser" -ForegroundColor Green
} catch {
    Write-Host "`n⚠️  Could not auto-open report" -ForegroundColor Yellow
}

# Determine overall success
$overallSuccess = ((-not $testResults.Android.Skipped -and $testResults.Android.Success) -or $testResults.Android.Skipped) -and 
                  ((-not $testResults.Remote.Skipped -and $testResults.Remote.Success) -or $testResults.Remote.Skipped)

if ($overallSuccess) {
    Write-Host "`n✅ ALL TESTS PASSED!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  SOME TESTS FAILED - Review report for details" -ForegroundColor Yellow
    exit 1
}

