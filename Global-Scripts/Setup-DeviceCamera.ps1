# Setup Device Camera for Android AVDs
# Configures Android emulators to use host webcam

param(
    [Parameter(Mandatory=$true)]
    [string]$DeviceName,  # AVD name to configure
    
    [ValidateSet("0", "1", "2", "auto")]
    [string]$CameraId = "auto",  # Host webcam ID or "auto" for default
    
    [string]$AndroidSdkPath = "$env:LOCALAPPDATA\Android\Sdk"
)

$ErrorActionPreference = "Stop"

Write-Host "`n📷 Android AVD Camera Configuration" -ForegroundColor Cyan
Write-Host "=" * 60

# Set Android Home
$env:ANDROID_HOME = $AndroidSdkPath

# Define paths
$emulator = "$AndroidSdkPath\emulator\emulator.exe"
$avdPath = "$env:USERPROFILE\.android\avd\$DeviceName.avd"

# Verify emulator exists
if (-not (Test-Path $emulator)) {
    Write-Host "❌ Emulator not found at: $emulator" -ForegroundColor Red
    exit 1
}

# Verify AVD exists
if (-not (Test-Path $avdPath)) {
    Write-Host "❌ AVD not found: $DeviceName" -ForegroundColor Red
    Write-Host "   Path: $avdPath" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ AVD found: $DeviceName" -ForegroundColor Green

# Get available webcams
Write-Host "`n📹 Detecting available webcams..." -ForegroundColor Cyan

$webcamOutput = & $emulator -webcam-list 2>&1
Write-Host $webcamOutput

# Determine camera to use
$cameraName = if ($CameraId -eq "auto") {
    Write-Host "`n🔍 Using auto-detect for camera" -ForegroundColor Cyan
    "webcam0"
} else {
    Write-Host "`n🔍 Using camera ID: $CameraId" -ForegroundColor Cyan
    "webcam$CameraId"
}

# Update AVD configuration
$configPath = "$avdPath\config.ini"

if (-not (Test-Path $configPath)) {
    Write-Host "❌ AVD config not found: $configPath" -ForegroundColor Red
    exit 1
}

Write-Host "`n📝 Updating AVD configuration..." -ForegroundColor Cyan

# Read current config
$config = Get-Content $configPath

# Update camera settings
$updated = $false
$newConfig = $config | ForEach-Object {
    if ($_ -match "^hw.camera.back=") {
        $updated = $true
        "hw.camera.back=$cameraName"
    } elseif ($_ -match "^hw.camera.front=") {
        $updated = $true
        "hw.camera.front=$cameraName"
    } else {
        $_
    }
}

# Add camera settings if not present
if (-not ($config -match "hw.camera.back=")) {
    $newConfig += "hw.camera.back=$cameraName"
    $updated = $true
}
if (-not ($config -match "hw.camera.front=")) {
    $newConfig += "hw.camera.front=$cameraName"
    $updated = $true
}

if ($updated) {
    # Backup original config
    $backupPath = "$configPath.backup"
    Copy-Item -Path $configPath -Destination $backupPath -Force
    Write-Host "   ✅ Backup created: $backupPath" -ForegroundColor Green
    
    # Write updated config
    Set-Content -Path $configPath -Value $newConfig
    Write-Host "   ✅ Configuration updated" -ForegroundColor Green
    
    # Show changes
    Write-Host "`n📋 Camera Configuration:" -ForegroundColor Cyan
    Write-Host "   Front Camera: $cameraName" -ForegroundColor White
    Write-Host "   Back Camera: $cameraName" -ForegroundColor White
} else {
    Write-Host "   ℹ️  Camera already configured" -ForegroundColor Gray
}

# Test camera configuration
Write-Host "`n🧪 Testing camera configuration..." -ForegroundColor Cyan
Write-Host "   Launching emulator with camera enabled..." -ForegroundColor Cyan
Write-Host "   (Emulator will start - close it manually when done testing)" -ForegroundColor Yellow

try {
    & $emulator -avd $DeviceName -camera-back $cameraName -camera-front $cameraName -gpu host
} catch {
    Write-Host "`n⚠️  Emulator launch cancelled or failed" -ForegroundColor Yellow
}

Write-Host "`n✅ Camera configuration complete!" -ForegroundColor Green
Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open Camera app in emulator to test camera" -ForegroundColor White
Write-Host "   2. Front and back cameras should use your webcam" -ForegroundColor White
Write-Host "   3. Use -camera-back and -camera-front flags when launching emulator" -ForegroundColor White

Write-Host "`n💡 Launch Command:" -ForegroundColor Cyan
Write-Host "   & `"$emulator`" -avd $DeviceName -camera-back $cameraName -camera-front $cameraName -gpu host" -ForegroundColor Gray

