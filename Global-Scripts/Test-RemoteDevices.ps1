# Test iOS and Additional Android Devices via Remote Service
# Supports BrowserStack, Sauce Labs, and LambdaTest

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("BrowserStack", "SauceLabs", "LambdaTest")]
    [string]$Service,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$AccessKey,
    
    [string]$Url = "https://befreefitness.ai/ai-analyzer",
    [string]$OutputDir = ".logs/mobile-testing/remote",
    [string[]]$Devices,  # Specific devices to test (empty = default set)
    [int]$WaitSeconds = 10
)

$ErrorActionPreference = "Stop"

Write-Host "`n🌐 Remote Device Testing - $Service" -ForegroundColor Cyan
Write-Host "=" * 60

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "✅ Output directory: $OutputDir" -ForegroundColor Green

# Define default test devices
$defaultDevices = @(
    # iOS Devices
    @{
        Name = "iPhone_13_iOS_16"
        DisplayName = "iPhone 13 (iOS 16)"
        Platform = "iOS"
        PlatformVersion = "16.0"
        Device = "iPhone 13"
        Browser = "Safari"
    },
    @{
        Name = "iPhone_16_Pro_iOS_18"
        DisplayName = "iPhone 16 Pro (iOS 18)"
        Platform = "iOS"
        PlatformVersion = "18.0"
        Device = "iPhone 16 Pro"
        Browser = "Safari"
    },
    @{
        Name = "iPhone_15_Pro_iOS_17"
        DisplayName = "iPhone 15 Pro (iOS 17)"
        Platform = "iOS"
        PlatformVersion = "17.0"
        Device = "iPhone 15 Pro"
        Browser = "Safari"
    },
    @{
        Name = "iPad_Pro_12_9_iOS_17"
        DisplayName = "iPad Pro 12.9 (iOS 17)"
        Platform = "iOS"
        PlatformVersion = "17.0"
        Device = "iPad Pro 12.9 2024"
        Browser = "Safari"
    },
    # Additional Android Devices (supplement local testing)
    @{
        Name = "Samsung_Galaxy_S24_Android_14"
        DisplayName = "Samsung Galaxy S24 (Android 14)"
        Platform = "Android"
        PlatformVersion = "14.0"
        Device = "Samsung Galaxy S24"
        Browser = "Chrome"
    },
    @{
        Name = "Google_Pixel_8_Android_14"
        DisplayName = "Google Pixel 8 (Android 14)"
        Platform = "Android"
        PlatformVersion = "14.0"
        Device = "Google Pixel 8"
        Browser = "Chrome"
    }
)

# Determine which devices to test
$testDevices = if ($Devices -and $Devices.Count -gt 0) {
    $defaultDevices | Where-Object { $Devices -contains $_.Name }
} else {
    $defaultDevices
}

if ($testDevices.Count -eq 0) {
    Write-Host "❌ No devices to test" -ForegroundColor Red
    exit 1
}

Write-Host "`n📋 Testing $($testDevices.Count) devices:" -ForegroundColor Cyan
$testDevices | ForEach-Object { Write-Host "   - $($_.DisplayName)" -ForegroundColor White }

# Service-specific configuration
$hubUrl = switch ($Service) {
    "BrowserStack" {
        "https://${Username}:${AccessKey}@hub-cloud.browserstack.com/wd/hub"
    }
    "SauceLabs" {
        "https://${Username}:${AccessKey}@ondemand.us-west-1.saucelabs.com:443/wd/hub"
    }
    "LambdaTest" {
        "https://${Username}:${AccessKey}@mobile-hub.lambdatest.com/wd/hub"
    }
}

Write-Host "`n🔗 Hub URL: $hubUrl" -ForegroundColor Gray

# Function to create capabilities for service
function Get-Capabilities {
    param(
        [hashtable]$Device,
        [string]$ServiceName
    )
    
    $caps = @{
        platformName = $Device.Platform
        platformVersion = $Device.PlatformVersion
        deviceName = $Device.Device
        browserName = $Device.Browser
        "appium:automationName" = if ($Device.Platform -eq "iOS") { "XCUITest" } else { "UiAutomator2" }
    }
    
    # Service-specific capabilities
    switch ($ServiceName) {
        "BrowserStack" {
            $caps["bstack:options"] = @{
                deviceName = $Device.Device
                osVersion = $Device.PlatformVersion
                realMobile = $true
                local = $false
                networkLogs = $true
            }
        }
        "SauceLabs" {
            $caps["sauce:options"] = @{
                appiumVersion = "latest"
                deviceName = $Device.Device
                platformVersion = $Device.PlatformVersion
            }
        }
        "LambdaTest" {
            $caps["lt:options"] = @{
                deviceName = $Device.Device
                platformVersion = $Device.PlatformVersion
                isRealMobile = $true
                network = $true
                visual = $true
                video = $true
            }
        }
    }
    
    return $caps
}

# Function to test a device
function Test-RemoteDevice {
    param(
        [hashtable]$Device,
        [string]$TestUrl,
        [string]$OutputPath,
        [string]$Hub
    )
    
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "📱 Testing: $($Device.DisplayName)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    try {
        # Get capabilities
        $capabilities = Get-Capabilities -Device $Device -ServiceName $Service
        
        Write-Host "   📋 Capabilities:" -ForegroundColor Cyan
        Write-Host "      Platform: $($Device.Platform) $($Device.PlatformVersion)" -ForegroundColor White
        Write-Host "      Device: $($Device.Device)" -ForegroundColor White
        Write-Host "      Browser: $($Device.Browser)" -ForegroundColor White
        
        # Create WebDriver session
        Write-Host "`n   🔌 Creating WebDriver session..." -ForegroundColor Cyan
        
        $sessionBody = @{
            capabilities = @{
                alwaysMatch = $capabilities
            }
        } | ConvertTo-Json -Depth 10
        
        $sessionResponse = Invoke-RestMethod -Uri "$Hub/session" `
            -Method Post `
            -ContentType "application/json" `
            -Body $sessionBody `
            -TimeoutSec 120
        
        $sessionId = $sessionResponse.value.sessionId
        Write-Host "   ✅ Session created: $sessionId" -ForegroundColor Green
        
        try {
            # Navigate to URL
            Write-Host "`n   🌐 Navigating to: $TestUrl" -ForegroundColor Cyan
            $navBody = @{ url = $TestUrl } | ConvertTo-Json
            Invoke-RestMethod -Uri "$Hub/session/$sessionId/url" `
                -Method Post `
                -ContentType "application/json" `
                -Body $navBody | Out-Null
            
            Write-Host "   ✅ Navigation successful" -ForegroundColor Green
            
            # Wait for page load
            Write-Host "   ⏳ Waiting ${WaitSeconds}s for page load..." -ForegroundColor Cyan
            Start-Sleep -Seconds $WaitSeconds
            
            # Take screenshot
            Write-Host "`n   📸 Capturing screenshot..." -ForegroundColor Cyan
            $screenshotResponse = Invoke-RestMethod -Uri "$Hub/session/$sessionId/screenshot" `
                -Method Get `
                -ContentType "application/json"
            
            # Save screenshot
            $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
            $screenshotFile = "$OutputPath\$($Device.Name)_${timestamp}.png"
            
            $screenshotBytes = [Convert]::FromBase64String($screenshotResponse.value)
            [System.IO.File]::WriteAllBytes($screenshotFile, $screenshotBytes)
            
            if (Test-Path $screenshotFile) {
                $fileSize = (Get-Item $screenshotFile).Length
                Write-Host "   ✅ Screenshot saved: $screenshotFile" -ForegroundColor Green
                Write-Host "      Size: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor Gray
            }
            
            # Rotate device if supported (mobile only)
            if ($Device.Platform -ne "Desktop") {
                Write-Host "`n   🔄 Testing landscape orientation..." -ForegroundColor Cyan
                try {
                    $rotateBody = @{ orientation = "LANDSCAPE" } | ConvertTo-Json
                    Invoke-RestMethod -Uri "$Hub/session/$sessionId/orientation" `
                        -Method Post `
                        -ContentType "application/json" `
                        -Body $rotateBody | Out-Null
                    
                    Start-Sleep -Seconds 3
                    
                    # Take landscape screenshot
                    $landscapeResponse = Invoke-RestMethod -Uri "$Hub/session/$sessionId/screenshot" `
                        -Method Get `
                        -ContentType "application/json"
                    
                    $landscapeFile = "$OutputPath\$($Device.Name)_landscape_${timestamp}.png"
                    $landscapeBytes = [Convert]::FromBase64String($landscapeResponse.value)
                    [System.IO.File]::WriteAllBytes($landscapeFile, $landscapeBytes)
                    
                    if (Test-Path $landscapeFile) {
                        $fileSize = (Get-Item $landscapeFile).Length
                        Write-Host "   ✅ Landscape screenshot saved: $landscapeFile" -ForegroundColor Green
                        Write-Host "      Size: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor Gray
                    }
                } catch {
                    Write-Host "   ⚠️  Could not capture landscape orientation" -ForegroundColor Yellow
                }
            }
            
            Write-Host "`n   ✅ Device test complete" -ForegroundColor Green
            return $true
            
        } finally {
            # Delete session
            Write-Host "`n   🛑 Ending session..." -ForegroundColor Cyan
            try {
                Invoke-RestMethod -Uri "$Hub/session/$sessionId" `
                    -Method Delete `
                    -ContentType "application/json" | Out-Null
                Write-Host "   ✅ Session ended" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠️  Could not end session cleanly" -ForegroundColor Yellow
            }
        }
        
    } catch {
        Write-Host "`n   ❌ Test failed: $_" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Gray
        return $false
    }
}

# Test all devices
$results = @()

foreach ($device in $testDevices) {
    $success = Test-RemoteDevice -Device $device -TestUrl $Url -OutputPath $OutputDir -Hub $hubUrl
    $results += @{
        Device = $device.DisplayName
        Success = $success
    }
    
    # Small delay between tests
    Start-Sleep -Seconds 2
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

