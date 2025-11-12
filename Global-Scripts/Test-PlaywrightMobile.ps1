# Playwright Mobile Device Emulation Testing
# Uses Playwright's device emulation for additional mobile testing coverage

param(
    [string]$Url = "https://befreefitness.ai/ai-analyzer",
    [string]$OutputDir = ".logs/mobile-testing/playwright",
    [string[]]$Devices,  # Specific devices to test (empty = all)
    [int]$WaitSeconds = 5
)

$ErrorActionPreference = "Stop"

Write-Host "`n🎭 Playwright Mobile Device Emulation Testing" -ForegroundColor Cyan
Write-Host "=" * 60

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "✅ Output directory: $OutputDir" -ForegroundColor Green

# Define Playwright device configurations
$defaultDevices = @(
    "iPhone 13",
    "iPhone 14 Pro",
    "iPhone 15 Pro",
    "iPad Pro",
    "Pixel 5",
    "Pixel 7",
    "Galaxy S9+",
    "Galaxy Tab S4"
)

# Determine which devices to test
$testDevices = if ($Devices -and $Devices.Count -gt 0) {
    $Devices
} else {
    $defaultDevices
}

Write-Host "`n📋 Testing $($testDevices.Count) devices with Playwright:" -ForegroundColor Cyan
$testDevices | ForEach-Object { Write-Host "   - $_" -ForegroundColor White }

# Create Playwright test script
$playwrightScript = @"
const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const testDevices = JSON.parse(process.argv[2]);
const testUrl = process.argv[3];
const outputDir = process.argv[4];
const waitSeconds = parseInt(process.argv[5]) * 1000;

async function testDevice(deviceName) {
    console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`📱 Testing: `+ deviceName);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    
    let browser, context, page;
    
    try {
        // Get device configuration
        const device = devices[deviceName];
        if (!device) {
            throw new Error(`Device not found: `+ deviceName);
        }
        
        console.log(`   📋 Device Configuration:`);
        console.log(`      Viewport: `+ device.viewport.width + `x` + device.viewport.height);
        console.log(`      User Agent: `+ device.userAgent.substring(0, 60) + `...`);
        console.log(`      Has Touch: `+ device.hasTouch);
        
        // Launch browser
        console.log(`\n   🚀 Launching browser...`);
        browser = await chromium.launch({
            headless: true
        });
        
        // Create context with device emulation
        context = await browser.newContext({
            ...device,
            locale: 'en-US',
            timezoneId: 'America/New_York'
        });
        
        page = await context.newPage();
        console.log(`   ✅ Browser launched with device emulation`);
        
        // Navigate to URL
        console.log(`\n   🌐 Navigating to: `+ testUrl);
        await page.goto(testUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        console.log(`   ✅ Navigation successful`);
        
        // Wait for page load
        console.log(`   ⏳ Waiting `+ (waitSeconds/1000) + `s for page load...`);
        await page.waitForTimeout(waitSeconds);
        
        // Take screenshot - Portrait
        console.log(`\n   📸 Capturing screenshots...`);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
        const deviceNameSafe = deviceName.replace(/[^a-zA-Z0-9]/g, '_');
        
        const portraitFile = path.join(outputDir, ``+ deviceNameSafe + `_portrait_` + timestamp + `.png`);
        await page.screenshot({
            path: portraitFile,
            fullPage: true
        });
        
        const stats = fs.statSync(portraitFile);
        console.log(`   ✅ Portrait screenshot: `+ path.basename(portraitFile));
        console.log(`      Size: `+ (stats.size / 1024).toFixed(2) + ` KB`);
        
        // Rotate to landscape (if mobile device)
        if (device.isMobile) {
            console.log(`\n   🔄 Rotating to landscape...`);
            const landscape = {
                width: device.viewport.height,
                height: device.viewport.width
            };
            await page.setViewportSize(landscape);
            await page.waitForTimeout(2000);
            
            const landscapeFile = path.join(outputDir, ``+ deviceNameSafe + `_landscape_` + timestamp + `.png`);
            await page.screenshot({
                path: landscapeFile,
                fullPage: true
            });
            
            const landscapeStats = fs.statSync(landscapeFile);
            console.log(`   ✅ Landscape screenshot: `+ path.basename(landscapeFile));
            console.log(`      Size: `+ (landscapeStats.size / 1024).toFixed(2) + ` KB`);
        }
        
        // Capture page metrics
        const metrics = await page.evaluate(() => {
            return {
                title: document.title,
                url: window.location.href,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                bodyHeight: document.body.scrollHeight
            };
        });
        
        console.log(`\n   📊 Page Metrics:`);
        console.log(`      Title: `+ metrics.title);
        console.log(`      Viewport: `+ metrics.viewportWidth + `x` + metrics.viewportHeight);
        console.log(`      Body Height: `+ metrics.bodyHeight + `px`);
        
        console.log(`\n   ✅ Device test complete`);
        return { success: true, device: deviceName };
        
    } catch (error) {
        console.error(`\n   ❌ Test failed: `+ error.message);
        return { success: false, device: deviceName, error: error.message };
        
    } finally {
        if (page) await page.close().catch(() => {});
        if (context) await context.close().catch(() => {});
        if (browser) await browser.close().catch(() => {});
    }
}

async function runTests() {
    console.log(`\n🧪 Starting Playwright Mobile Tests`);
    console.log(`URL: `+ testUrl);
    console.log(`Devices: `+ testDevices.length);
    
    const results = [];
    
    for (const device of testDevices) {
        const result = await testDevice(device);
        results.push(result);
        
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Summary
    console.log(`\n` + `=`.repeat(60));
    console.log(`📊 Testing Summary:`);
    console.log(`=`.repeat(60));
    
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;
    
    results.forEach(result => {
        const status = result.success ? `✅ SUCCESS` : `❌ FAILED`;
        console.log(`   `+ status + ` - ` + result.device);
    });
    
    console.log(`\n   Total: `+ results.length + ` | Success: `+ successCount + ` | Failed: `+ failCount);
    
    return failCount === 0 ? 0 : 1;
}

runTests()
    .then(exitCode => process.exit(exitCode))
    .catch(error => {
        console.error(`Fatal error: `+ error.message);
        process.exit(1);
    });
"@

# Save Playwright script
$tempScriptPath = "$env:TEMP\playwright-mobile-test-$(Get-Random).js"
Set-Content -Path $tempScriptPath -Value $playwrightScript

try {
    Write-Host "`n🔍 Checking Playwright installation..." -ForegroundColor Cyan
    
    # Check if Playwright is installed
    $playwrightCheck = npx playwright --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Playwright not found. Installing..." -ForegroundColor Yellow
        npm install -g playwright 2>&1 | Out-Null
        npx playwright install 2>&1 | Out-Null
        Write-Host "✅ Playwright installed" -ForegroundColor Green
    } else {
        Write-Host "✅ Playwright found: $playwrightCheck" -ForegroundColor Green
    }
    
    # Run Playwright tests
    Write-Host "`n🚀 Running Playwright tests..." -ForegroundColor Cyan
    
    $devicesJson = $testDevices | ConvertTo-Json -Compress
    node $tempScriptPath $devicesJson $Url $OutputDir $WaitSeconds
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "`n✅ All Playwright tests passed!" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  Some Playwright tests failed." -ForegroundColor Yellow
    }
    
    # List generated screenshots
    $screenshots = Get-ChildItem -Path $OutputDir -Filter "*.png" -ErrorAction SilentlyContinue
    if ($screenshots) {
        Write-Host "`n📸 Generated Screenshots ($($screenshots.Count)):" -ForegroundColor Cyan
        $screenshots | ForEach-Object {
            Write-Host "   - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor White
        }
    }
    
    Write-Host "`n📁 Screenshots saved to: $OutputDir" -ForegroundColor Cyan
    
    exit $exitCode
    
} finally {
    # Cleanup temporary script
    if (Test-Path $tempScriptPath) {
        Remove-Item -Path $tempScriptPath -Force -ErrorAction SilentlyContinue
    }
}

