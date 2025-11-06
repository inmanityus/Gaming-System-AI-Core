# GE-001: Unreal Engine 5 Project Setup Verification
# Purpose: Verify UE5 project setup and Steam SDK integration
# Task: GE-001 from Phase 1 Foundation Tasks

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GE-001: UE5 Project Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "unreal"
$uprojectFile = Join-Path $projectPath "BodyBroker.uproject"

# Check if project directory exists
Write-Host "Checking project structure..." -ForegroundColor Yellow
if (-not (Test-Path $projectPath)) {
    Write-Host "  ✗ Project directory not found: $projectPath" -ForegroundColor Red
    Write-Host "    GE-001 setup incomplete" -ForegroundColor Yellow
    exit 1
}
Write-Host "  ✓ Project directory exists" -ForegroundColor Green

# Check .uproject file
if (-not (Test-Path $uprojectFile)) {
    Write-Host "  ✗ .uproject file not found: $uprojectFile" -ForegroundColor Red
    Write-Host "    GE-001 setup incomplete" -ForegroundColor Yellow
    exit 1
}
Write-Host "  ✓ .uproject file exists" -ForegroundColor Green

# Parse .uproject file
Write-Host ""
Write-Host "Checking project configuration..." -ForegroundColor Yellow
try {
    $uprojectContent = Get-Content $uprojectFile -Raw | ConvertFrom-Json
    
    # Check engine version
    $engineVersion = $uprojectContent.EngineAssociation
    if ($engineVersion -match "5\.(6|7|8|9)") {
        Write-Host "  ✓ Engine version: $engineVersion (UE5.6+)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Engine version: $engineVersion (should be 5.6+)" -ForegroundColor Yellow
    }
    
    # Check modules
    if ($uprojectContent.Modules -and $uprojectContent.Modules.Count -gt 0) {
        Write-Host "  ✓ Modules configured: $($uprojectContent.Modules.Count)" -ForegroundColor Green
        foreach ($module in $uprojectContent.Modules) {
            Write-Host "    - $($module.Name) ($($module.Type))" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠ No modules configured" -ForegroundColor Yellow
    }
    
    # Check plugins
    if ($uprojectContent.Plugins -and $uprojectContent.Plugins.Count -gt 0) {
        Write-Host "  ✓ Plugins configured: $($uprojectContent.Plugins.Count)" -ForegroundColor Green
        
        $steamPluginFound = $false
        foreach ($plugin in $uprojectContent.Plugins) {
            $pluginName = $plugin.Name
            $pluginEnabled = $plugin.Enabled
            $status = if ($pluginEnabled) { "enabled" } else { "disabled" }
            $color = if ($pluginEnabled) { "Green" } else { "Yellow" }
            Write-Host "    - $pluginName ($status)" -ForegroundColor $color
            
            if ($pluginName -match "Steam" -and $pluginEnabled) {
                $steamPluginFound = $true
            }
        }
        
        if ($steamPluginFound) {
            Write-Host "  ✓ Steam SDK plugin enabled" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Steam SDK plugin not found or disabled" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠ No plugins configured" -ForegroundColor Yellow
    }
    
    # Check target platforms
    if ($uprojectContent.TargetPlatforms -and $uprojectContent.TargetPlatforms.Count -gt 0) {
        Write-Host "  ✓ Target platforms: $($uprojectContent.TargetPlatforms -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ No target platforms specified" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ✗ Failed to parse .uproject file" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
    exit 1
}

# Check Source directory
Write-Host ""
Write-Host "Checking source code structure..." -ForegroundColor Yellow
$sourcePath = Join-Path $projectPath "Source"
if (Test-Path $sourcePath) {
    Write-Host "  ✓ Source directory exists" -ForegroundColor Green
    
    $sourceFiles = Get-ChildItem -Path $sourcePath -Recurse -Include "*.cpp","*.h" | Measure-Object
    if ($sourceFiles.Count -gt 0) {
        Write-Host "  ✓ Source files found: $($sourceFiles.Count)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ No source files found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ Source directory not found" -ForegroundColor Yellow
}

# Check Visual Studio solution
Write-Host ""
Write-Host "Checking build files..." -ForegroundColor Yellow
$slnFile = Join-Path $projectPath "BodyBroker.sln"
if (Test-Path $slnFile) {
    Write-Host "  ✓ Visual Studio solution exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Visual Studio solution not found" -ForegroundColor Yellow
    Write-Host "    Generate with: Right-click .uproject → Generate Visual Studio project files" -ForegroundColor Gray
}

# Check README
Write-Host ""
Write-Host "Checking documentation..." -ForegroundColor Yellow
$readmeFile = Join-Path $projectPath "README.md"
if (Test-Path $readmeFile) {
    Write-Host "  ✓ README.md exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ README.md not found" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "GE-001 Verification Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Project Status:" -ForegroundColor Cyan
Write-Host "  ✓ UE5 project structure exists" -ForegroundColor Green
Write-Host "  ✓ .uproject file configured" -ForegroundColor Green
if ($steamPluginFound) {
    Write-Host "  ✓ Steam SDK integrated" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Steam SDK integration needs verification" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open BodyBroker.uproject in UE5 Editor" -ForegroundColor White
Write-Host "  2. Verify project opens without errors" -ForegroundColor White
Write-Host "  3. Generate Visual Studio files if needed" -ForegroundColor White
Write-Host "  4. Compile C++ code" -ForegroundColor White
Write-Host "  5. Test build configuration" -ForegroundColor White
Write-Host ""
Write-Host "Acceptance Criteria:" -ForegroundColor Cyan
Write-Host "  [ ] Project opens without errors" -ForegroundColor White
Write-Host "  [ ] Steam SDK integrated" -ForegroundColor White
Write-Host "  [ ] Git repository initialized" -ForegroundColor White
Write-Host "  [ ] Build configuration working" -ForegroundColor White
Write-Host ""

