# Create Android Virtual Devices for Mobile Testing
# Creates Samsung Galaxy S23, Google Pixel 9 Pro, and other required test devices

param(
    [string]$AndroidSdkPath = "$env:LOCALAPPDATA\Android\Sdk",
    [switch]$Force  # Delete existing AVDs with same names
)

$ErrorActionPreference = "Stop"

Write-Host "`n📱 Android Virtual Device Creation" -ForegroundColor Cyan
Write-Host "=" * 60

# Set Android Home
$env:ANDROID_HOME = $AndroidSdkPath

# Define paths
$sdkmanager = "$AndroidSdkPath\cmdline-tools\latest\bin\sdkmanager.bat"
$avdmanager = "$AndroidSdkPath\cmdline-tools\latest\bin\avdmanager.bat"

# Verify tools exist
if (-not (Test-Path $sdkmanager)) {
    Write-Host "❌ sdkmanager not found" -ForegroundColor Red
    Write-Host "   Run Install-AndroidSDKTools.ps1 first" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $avdmanager)) {
    Write-Host "❌ avdmanager not found" -ForegroundColor Red
    Write-Host "   Run Install-AndroidSDKTools.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Android SDK tools found" -ForegroundColor Green

# Define test devices
$devices = @(
    @{
        Name = "Samsung_Galaxy_S23_Test"
        DisplayName = "Samsung Galaxy S23 (Test)"
        Package = "system-images;android-34;google_apis_playstore;x86_64"
        Device = "pixel_6"  # Using Pixel 6 as base (similar specs to S23)
        ScreenSize = "1080x2340"
        RAM = "8192"  # 8GB
        Heap = "512"
        Cores = "4"
    },
    @{
        Name = "Google_Pixel_9_Pro_Test"
        DisplayName = "Google Pixel 9 Pro (Test)"
        Package = "system-images;android-36;google_apis_playstore;x86_64"
        Device = "pixel_9_pro"
        ScreenSize = "1344x2992"
        RAM = "16384"  # 16GB
        Heap = "1024"
        Cores = "6"
    },
    @{
        Name = "Generic_Android_Phone_Test"
        DisplayName = "Generic Android Phone (Test)"
        Package = "system-images;android-34;google_apis_playstore;x86_64"
        Device = "pixel_5"
        ScreenSize = "1080x2340"
        RAM = "6144"  # 6GB
        Heap = "512"
        Cores = "4"
    },
    @{
        Name = "Generic_Android_Tablet_Test"
        DisplayName = "Generic Android Tablet (Test)"
        Package = "system-images;android-34;google_apis_playstore;x86_64"
        Device = "pixel_tablet"
        ScreenSize = "2560x1600"
        RAM = "8192"
        Heap = "512"
        Cores = "4"
    }
)

# Function to check if system image is installed
function Test-SystemImage {
    param([string]$Package)
    
    $installedImages = & $sdkmanager --list_installed 2>&1 | Out-String
    return $installedImages -match [regex]::Escape($Package)
}

# Function to install system image
function Install-SystemImage {
    param([string]$Package)
    
    Write-Host "   📥 Installing system image: $Package" -ForegroundColor Cyan
    try {
        $yesString = "y`n"
        $yesString | & $sdkmanager $Package 2>&1 | ForEach-Object {
            if ($_ -match "percent|Installing|Unzipping") {
                Write-Host "      $_" -ForegroundColor Gray
            }
        }
        Write-Host "   ✅ System image installed" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "   ❌ Installation failed: $_" -ForegroundColor Red
        return $false
    }
}

# Function to delete AVD if it exists
function Remove-ExistingAVD {
    param([string]$Name)
    
    $existingAVDs = & $avdmanager list avd 2>&1 | Out-String
    if ($existingAVDs -match $Name) {
        Write-Host "   🗑️  Deleting existing AVD: $Name" -ForegroundColor Yellow
        try {
            & $avdmanager delete avd -n $Name 2>&1 | Out-Null
            Write-Host "   ✅ Existing AVD deleted" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Could not delete existing AVD" -ForegroundColor Yellow
        }
    }
}

# Function to create AVD
function New-AndroidAVD {
    param(
        [string]$Name,
        [string]$DisplayName,
        [string]$Package,
        [string]$Device,
        [string]$ScreenSize,
        [string]$RAM,
        [string]$Heap,
        [string]$Cores
    )
    
    Write-Host "`n📱 Creating: $DisplayName" -ForegroundColor Cyan
    
    # Check if system image is installed
    if (-not (Test-SystemImage -Package $Package)) {
        Write-Host "   ⚠️  System image not installed" -ForegroundColor Yellow
        if (-not (Install-SystemImage -Package $Package)) {
            Write-Host "   ❌ Skipping AVD creation" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "   ✅ System image already installed" -ForegroundColor Green
    }
    
    # Delete existing AVD if Force flag is set
    if ($Force) {
        Remove-ExistingAVD -Name $Name
    }
    
    # Check if AVD already exists
    $existingAVDs = & $avdmanager list avd 2>&1 | Out-String
    if ($existingAVDs -match $Name) {
        Write-Host "   ⚠️  AVD already exists. Use -Force to recreate." -ForegroundColor Yellow
        return $true
    }
    
    # Create AVD
    Write-Host "   🔨 Creating virtual device..." -ForegroundColor Cyan
    try {
        $noString = "no`n"
        $noString | & $avdmanager create avd `
            -n $Name `
            -k $Package `
            -d $Device `
            2>&1 | Out-Null
        
        # Configure AVD settings
        $configPath = "$env:USERPROFILE\.android\avd\$Name.avd\config.ini"
        if (Test-Path $configPath) {
            # Read current config
            $config = Get-Content $configPath
            
            # Update settings
            $config = $config | ForEach-Object {
                if ($_ -match "^hw.ramSize=") {
                    "hw.ramSize=$RAM"
                } elseif ($_ -match "^vm.heapSize=") {
                    "vm.heapSize=$Heap"
                } elseif ($_ -match "^hw.cpu.ncore=") {
                    "hw.cpu.ncore=$Cores"
                } elseif ($_ -match "^hw.gpu.mode=") {
                    "hw.gpu.mode=host"
                } elseif ($_ -match "^hw.gpu.enabled=") {
                    "hw.gpu.enabled=yes"
                } else {
                    $_
                }
            }
            
            # Add GPU settings if not present
            if ($config -notmatch "hw.gpu.mode=") {
                $config += "hw.gpu.mode=host"
            }
            if ($config -notmatch "hw.gpu.enabled=") {
                $config += "hw.gpu.enabled=yes"
            }
            
            # Write updated config
            Set-Content -Path $configPath -Value $config
            
            Write-Host "   ✅ AVD created successfully" -ForegroundColor Green
            Write-Host "      RAM: ${RAM}MB, Cores: $Cores, GPU: Host" -ForegroundColor Gray
            return $true
        } else {
            Write-Host "   ❌ AVD creation failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "   ❌ AVD creation failed: $_" -ForegroundColor Red
        return $false
    }
}

# Create all devices
Write-Host "`n🚀 Creating test devices..." -ForegroundColor Cyan
$successCount = 0
$failCount = 0

foreach ($device in $devices) {
    $result = New-AndroidAVD `
        -Name $device.Name `
        -DisplayName $device.DisplayName `
        -Package $device.Package `
        -Device $device.Device `
        -ScreenSize $device.ScreenSize `
        -RAM $device.RAM `
        -Heap $device.Heap `
        -Cores $device.Cores
    
    if ($result) {
        $successCount++
    } else {
        $failCount++
    }
}

# Summary
Write-Host "`n" + ("=" * 60)
Write-Host "📊 AVD Creation Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Success: $successCount" -ForegroundColor Green
Write-Host "   ❌ Failed: $failCount" -ForegroundColor Red

# List all AVDs
Write-Host "`n📋 Available AVDs:" -ForegroundColor Cyan
& $avdmanager list avd 2>&1 | ForEach-Object {
    if ($_ -match "Name:") {
        Write-Host "   $_" -ForegroundColor White
    }
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Run Test-AndroidDevices.ps1 to launch and test devices" -ForegroundColor White
Write-Host "   2. Use Mobile-Testing-Suite.ps1 for comprehensive testing" -ForegroundColor White

