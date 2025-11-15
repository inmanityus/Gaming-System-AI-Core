# Test Android Virtual Devices
# Launches AVDs, navigates to URL, captures screenshots

param(
    [string]$Url = "https://befreefitness.ai/ai-analyzer",
    [string]$OutputDir = ".logs/mobile-testing/android",
    [string[]]$Devices,  # Specific devices to test (empty = all)
    [int]$WaitSeconds = 10,  # Wait time after loading page
    [string]$AndroidSdkPath = "$env:LOCALAPPDATA\Android\Sdk"
)

$ErrorActionPreference = "Stop"

Write-Host "`n📱 Android Device Testing" -ForegroundColor Cyan
Write-Host "=" * 60

# Set Android Home
$env:ANDROID_HOME = $AndroidSdkPath

# Define paths
$emulator = "$AndroidSdkPath\emulator\emulator.exe"
$adb = "$AndroidSdkPath\platform-tools\adb.exe"

# Verify tools exist
if (-not (Test-Path $emulator)) {
    Write-Host "❌ Emulator not found at: $emulator" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $adb)) {
    Write-Host "❌ ADB not found at: $adb" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Android SDK tools found" -ForegroundColor Green

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "✅ Output directory: $OutputDir" -ForegroundColor Green

# Get list of available AVDs
$availableAVDs = & $emulator -list-avds 2>&1
if (-not $availableAVDs) {
    Write-Host "❌ No AVDs found. Run Create-AndroidAVDs.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "`n📋 Available AVDs:" -ForegroundColor Cyan
$availableAVDs | ForEach-Object { Write-Host "   - $_" -ForegroundColor White }

# Determine which devices to test
if ($Devices -and $Devices.Count -gt 0) {
    $testDevices = $Devices
} else {
    $testDevices = $availableAVDs
}

Write-Host "`n🚀 Testing URL: $Url" -ForegroundColor Cyan

# Function to wait for device to be ready
function Wait-ForDevice {
    param([int]$MaxWaitSeconds = 120)
    
    Write-Host "   ⏳ Waiting for device to boot..." -ForegroundColor Cyan
    $startTime = Get-Date
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $MaxWaitSeconds) {
        $deviceState = & $adb shell getprop sys.boot_completed 2>&1
        if ($deviceState -match "1") {
            Write-Host "   ✅ Device ready" -ForegroundColor Green
            Start-Sleep -Seconds 5  # Extra wait for stability
            return $true
        }
        Start-Sleep -Seconds 2
    }
    
    Write-Host "   ⚠️  Device boot timeout" -ForegroundColor Yellow
    return $false
}

# Function to test a device
function Test-Device {
    param(
        [string]$DeviceName,
        [string]$TestUrl,
        [string]$OutputPath
    )
    
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "📱 Testing: $DeviceName" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # Launch emulator in background
    Write-Host "   🚀 Launching emulator..." -ForegroundColor Cyan
    $process = Start-Process -FilePath $emulator `
        -ArgumentList "-avd", $DeviceName, "-gpu", "host", "-no-snapshot-load", "-wipe-data" `
        -PassThru `
        -WindowStyle Hidden
    
    Write-Host "   ✅ Emulator process started (PID: $($process.Id))" -ForegroundColor Green
    
    # Wait for device to be ready
    if (-not (Wait-ForDevice -MaxWaitSeconds 180)) {
        Write-Host "   ❌ Device failed to boot" -ForegroundColor Red
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        return $false
    }
    
    try {
        # Get device info
        Write-Host "`n   📊 Device Information:" -ForegroundColor Cyan
        $model = & $adb shell getprop ro.product.model 2>&1
        $androidVersion = & $adb shell getprop ro.build.version.release 2>&1
        $screenSize = & $adb shell wm size 2>&1
        
        Write-Host "      Model: $model" -ForegroundColor White
        Write-Host "      Android: $androidVersion" -ForegroundColor White
        Write-Host "      Screen: $screenSize" -ForegroundColor White
        
        # Open Chrome and navigate to URL
        Write-Host "`n   🌐 Opening Chrome and dismissing all setup screens..." -ForegroundColor Cyan
        
        # Step 1: Open Chrome
        & $adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        
        # Step 2: Dismiss Chrome welcome screens
        & $adb shell input keyevent 66 2>&1 | Out-Null  # Enter (Accept terms)
        Start-Sleep -Seconds 2
        & $adb shell input keyevent 66 2>&1 | Out-Null  # Enter (Next)
        Start-Sleep -Seconds 2
        
        # Step 3: Dismiss "Add Google Account" screen - Click "Continue without account"
        # This is typically at the bottom of the screen - tap coordinates for "No thanks" or similar
        Write-Host "   📱 Dismissing Google account prompt..." -ForegroundColor Cyan
        & $adb shell input keyevent 61 2>&1 | Out-Null  # Tab to navigate
        Start-Sleep -Seconds 1
        & $adb shell input keyevent 61 2>&1 | Out-Null  # Tab again to "Continue without account"
        Start-Sleep -Seconds 1
        & $adb shell input keyevent 66 2>&1 | Out-Null  # Enter to select
        Start-Sleep -Seconds 2
        
        # Step 4: Press Back to clear any remaining Chrome screens
        & $adb shell input keyevent 4 2>&1 | Out-Null   # Back button
        Start-Sleep -Seconds 1
        
        # Step 3: Now navigate to actual URL
        Write-Host "   🌐 Navigating to URL..." -ForegroundColor Cyan
        & $adb shell am start -a android.intent.action.VIEW -d $TestUrl com.android.chrome 2>&1 | Out-Null
        
        # Step 4: Wait longer for page to fully load (25 seconds minimum)
        $actualWaitTime = [Math]::Max($WaitSeconds, 25)
        Write-Host "   ⏳ Waiting ${actualWaitTime}s for page to fully load..." -ForegroundColor Cyan
        Start-Sleep -Seconds $actualWaitTime
        
        # Take screenshots
        Write-Host "`n   📸 Capturing screenshots..." -ForegroundColor Cyan
        
        # Portrait screenshot
        $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $portraitFile = "$OutputPath\${DeviceName}_portrait_${timestamp}.png"
        & $adb exec-out screencap -p > $portraitFile
        
        if (Test-Path $portraitFile) {
            $fileSize = (Get-Item $portraitFile).Length
            if ($fileSize -gt 1000) {
                Write-Host "   ✅ Portrait screenshot: $portraitFile" -ForegroundColor Green
                Write-Host "      Size: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor Gray
            } else {
                Write-Host "   ⚠️  Portrait screenshot may be corrupted (too small)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ Portrait screenshot failed" -ForegroundColor Red
        }
        
        # Rotate to landscape
        Write-Host "`n   🔄 Rotating to landscape..." -ForegroundColor Cyan
        & $adb shell settings put system accelerometer_rotation 0 2>&1 | Out-Null
        & $adb shell settings put system user_rotation 1 2>&1 | Out-Null
        Start-Sleep -Seconds 3
        
        # Landscape screenshot
        $landscapeFile = "$OutputPath\${DeviceName}_landscape_${timestamp}.png"
        & $adb exec-out screencap -p > $landscapeFile
        
        if (Test-Path $landscapeFile) {
            $fileSize = (Get-Item $landscapeFile).Length
            if ($fileSize -gt 1000) {
                Write-Host "   ✅ Landscape screenshot: $landscapeFile" -ForegroundColor Green
                Write-Host "      Size: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor Gray
            } else {
                Write-Host "   ⚠️  Landscape screenshot may be corrupted (too small)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ Landscape screenshot failed" -ForegroundColor Red
        }
        
        # Get Chrome DevTools info (if available)
        Write-Host "`n   🔍 Attempting to capture page info..." -ForegroundColor Cyan
        try {
            & $adb forward tcp:9222 localabstract:chrome_devtools_remote 2>&1 | Out-Null
            Write-Host "   ✅ Chrome DevTools forwarded to localhost:9222" -ForegroundColor Green
            Write-Host "      You can connect Playwright to this for advanced testing" -ForegroundColor Gray
        } catch {
            Write-Host "   ⚠️  Could not forward Chrome DevTools" -ForegroundColor Yellow
        }
        
        Write-Host "`n   ✅ Device test complete" -ForegroundColor Green
        return $true
        
    } finally {
        # Cleanup - shutdown emulator
        Write-Host "`n   🛑 Shutting down emulator..." -ForegroundColor Cyan
        & $adb emu kill 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        
        # Force kill if still running
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        
        Write-Host "   ✅ Emulator shut down" -ForegroundColor Green
    }
}

# Test all devices
$results = @()

foreach ($device in $testDevices) {
    if ($availableAVDs -contains $device) {
        $success = Test-Device -DeviceName $device -TestUrl $Url -OutputPath $OutputDir
        $results += @{
            Device = $device
            Success = $success
        }
    } else {
        Write-Host "`n⚠️  Device not found: $device" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`n" + ("=" * 60)
Write-Host "📊 Testing Summary:" -ForegroundColor Cyan
Write-Host "=" * 60

$successCount = ($results | Where-Object { $_.Success }).Count
$failCount = ($results | Where-Object { -not $_.Success }).Count

foreach ($result in $results) {
    $status = if ($result.Success) { "✅ SUCCESS" } else { "❌ FAILED" }
    $color = if ($result.Success) { "Green" } else { "Red" }
    Write-Host "   $status - $($result.Device)" -ForegroundColor $color
}

Write-Host "`n   Total: $($results.Count) | Success: $successCount | Failed: $failCount" -ForegroundColor White
Write-Host "`n📁 Screenshots saved to: $OutputDir" -ForegroundColor Cyan

if ($failCount -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Check logs above for details." -ForegroundColor Yellow
}

