# Install Android SDK Command-Line Tools
# Required for AVD automation via avdmanager and sdkmanager

param(
    [string]$AndroidSdkPath = "$env:LOCALAPPDATA\Android\Sdk"
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔧 Android SDK Command-Line Tools Installation" -ForegroundColor Cyan
Write-Host "=" * 60

# Check if Android SDK exists
if (-not (Test-Path $AndroidSdkPath)) {
    Write-Host "❌ Android SDK not found at: $AndroidSdkPath" -ForegroundColor Red
    Write-Host "   Please install Android Studio first" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Android SDK found: $AndroidSdkPath" -ForegroundColor Green

# Define command-line tools download URL (latest as of Nov 2024)
$cmdlineToolsUrl = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
$downloadPath = Join-Path $env:TEMP "commandlinetools-win.zip"
$extractPath = Join-Path $AndroidSdkPath "cmdline-tools"

# Check if cmdline-tools already exists
$sdkmanagerCheck = Join-Path (Join-Path $extractPath "latest") "bin\sdkmanager.bat"
if (Test-Path $sdkmanagerCheck) {
    Write-Host "✅ Command-line tools already installed" -ForegroundColor Green
    exit 0
}

# Download command-line tools
Write-Host "`n📥 Downloading Android SDK command-line tools..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $cmdlineToolsUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "✅ Downloaded to: $downloadPath" -ForegroundColor Green
} catch [System.Net.WebException] {
    Write-Host "❌ Download failed (Network): $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} catch {
    Write-Host "❌ Download failed: $_" -ForegroundColor Red
    exit 1
}

# Extract command-line tools
Write-Host "`n📦 Extracting command-line tools..." -ForegroundColor Cyan
try {
    # Create cmdline-tools directory if it doesn't exist
    if (-not (Test-Path $extractPath)) {
        New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    }
    
    # Extract to temporary location
    $tempExtract = Join-Path $env:TEMP "cmdline-tools-temp"
    if (Test-Path $tempExtract) {
        Remove-Item -Recurse -Force $tempExtract
    }
    Expand-Archive -Path $downloadPath -DestinationPath $tempExtract -Force
    
    # Move to proper location (SDK expects cmdline-tools/latest structure)
    $latestPath = Join-Path $extractPath "latest"
    if (Test-Path $latestPath) {
        Remove-Item -Recurse -Force $latestPath
    }
    $tempCmdlineTools = Join-Path $tempExtract "cmdline-tools"
    Move-Item -Path $tempCmdlineTools -Destination $latestPath -Force
    
    Write-Host "✅ Extracted to: $latestPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Extraction failed: $_" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Force $downloadPath -ErrorAction SilentlyContinue
$tempCleanup = Join-Path $env:TEMP "cmdline-tools-temp"
Remove-Item -Recurse -Force $tempCleanup -ErrorAction SilentlyContinue

# Verify installation
$sdkmanager = Join-Path (Join-Path $extractPath "latest") "bin\sdkmanager.bat"
$avdmanager = Join-Path (Join-Path $extractPath "latest") "bin\avdmanager.bat"

if ((Test-Path $sdkmanager) -and (Test-Path $avdmanager)) {
    Write-Host "`n✅ Installation successful!" -ForegroundColor Green
    Write-Host "   sdkmanager: $sdkmanager" -ForegroundColor White
    Write-Host "   avdmanager: $avdmanager" -ForegroundColor White
    
    # Accept licenses
    Write-Host "`n📜 Accepting Android SDK licenses..." -ForegroundColor Cyan
    try {
        $env:ANDROID_HOME = $AndroidSdkPath
        $yesString = "y`ny`ny`ny`ny`ny`ny`ny`ny`n"
        $yesString | & $sdkmanager --sdk_root=$AndroidSdkPath --licenses 2>&1 | Out-Null
        Write-Host "✅ Licenses accepted" -ForegroundColor Green
    } catch {
        Write-Host "License acceptance failed (may need manual acceptance)" -ForegroundColor Yellow
        Write-Host "Run manually with: sdkmanager --licenses" -ForegroundColor Gray
    }
    
    Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Run Create-AndroidAVDs.ps1 to create test devices" -ForegroundColor White
    Write-Host "   2. Run Test-AndroidDevices.ps1 to verify setup" -ForegroundColor White
    
} else {
    Write-Host ""
    Write-Host "Installation verification failed" -ForegroundColor Red
    exit 1
}

