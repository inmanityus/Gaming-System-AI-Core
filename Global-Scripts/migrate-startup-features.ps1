# Migrate Startup Features Script
# This script updates existing startup.ps1 files to use the modular features system
# without destroying project-specific additions

param(
    [string]$ProjectPath = $PWD.Path,
    [switch]$Backup = $true,
    [switch]$DryRun = $false
)

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Startup Features Migration Script" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Validate project path
if (-not (Test-Path $ProjectPath)) {
    Write-Host "[ERROR] Project path does not exist: $ProjectPath" -ForegroundColor Red
    exit 1
}

$startupFile = Join-Path $ProjectPath "startup.ps1"
if (-not (Test-Path $startupFile)) {
    Write-Host "[ERROR] startup.ps1 not found in: $ProjectPath" -ForegroundColor Red
    Write-Host "        This script must be run from a project directory with startup.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Found startup.ps1: $startupFile" -ForegroundColor Green

# Read current startup.ps1
$currentContent = Get-Content $startupFile -Raw
$originalContent = $currentContent

# Check if already migrated
if ($currentContent -match "# MODULAR FEATURES LOADER") {
    Write-Host "[INFO] startup.ps1 already appears to use modular features system" -ForegroundColor Yellow
    Write-Host "       Skipping migration" -ForegroundColor Yellow
    exit 0
}

Write-Host "[INFO] Analyzing current startup.ps1..." -ForegroundColor Cyan

# Find markers for project-specific sections
# Look for common patterns that indicate project-specific code
$projectSpecificMarkers = @(
    "# Project-specific",
    "# PROJECT SPECIFIC",
    "# Custom",
    "# CUSTOM",
    "# Local",
    "# LOCAL",
    "# Project root:",
    "Project root:",
    "UNIVERSAL STARTUP COMPLETE"
)

# Find where project-specific code starts
$projectSpecificStart = $null
foreach ($marker in $projectSpecificMarkers) {
    $index = $currentContent.IndexOf($marker)
    if ($index -ge 0) {
        # Find the line number
        $lineNumber = ($currentContent.Substring(0, $index) -split "`r?`n").Count
        if (-not $projectSpecificStart -or $lineNumber -lt $projectSpecificStart) {
            $projectSpecificStart = $lineNumber
        }
    }
}

# If we can't find a marker, look for "UNIVERSAL STARTUP COMPLETE" as a safe insertion point
if (-not $projectSpecificStart) {
    $match = Select-String -Path $startupFile -Pattern "UNIVERSAL STARTUP COMPLETE" -AllMatches
    if ($match) {
        $lines = Get-Content $startupFile
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match "UNIVERSAL STARTUP COMPLETE") {
                $projectSpecificStart = $i
                break
            }
        }
    }
}

# Read the shared startup.ps1 template to get the modular loader section
$sharedStartupPath = "$env:USERPROFILE\.cursor\Deployment\For Every Project\startup.ps1"
if (-not (Test-Path $sharedStartupPath)) {
    Write-Host "[ERROR] Shared startup template not found: $sharedStartupPath" -ForegroundColor Red
    Write-Host "        Cannot extract modular loader section" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Found shared startup template: $sharedStartupPath" -ForegroundColor Green

$sharedContent = Get-Content $sharedStartupPath -Raw

# Extract the modular features loader section from shared template
$loaderStartPattern = "# ================================================================`r?`n# MODULAR FEATURES LOADER"
$loaderEndPattern = "# Note: Modular features"
$loaderSection = ""

if ($sharedContent -match "(?s)$loaderStartPattern.*?(?=# Note: Modular features|UNIVERSAL STARTUP COMPLETE)") {
    $loaderSection = $matches[0]
    # Clean up the match
    $loaderSection = $loaderSection -replace "(`r?`n)+$", "`r`n"
}

if ([string]::IsNullOrEmpty($loaderSection)) {
    Write-Host "[WARNING] Could not extract loader section from shared template" -ForegroundColor Yellow
    Write-Host "         Will use hardcoded loader section" -ForegroundColor Yellow
    
    # Use hardcoded loader as fallback
    $loaderSection = @'
# ================================================================
# MODULAR FEATURES LOADER
# ================================================================
# This section automatically loads all features from Global-Workflows/startup-features/
# Each feature is a separate .ps1 file that exports an Initialize-* function
# To add new features, simply add a new .ps1 file to that directory
# ================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Loading Modular Startup Features..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$featuresDir = "Global-Workflows\startup-features"
if (Test-Path $featuresDir) {
    Write-Host "[OK] Features directory found: $featuresDir" -ForegroundColor Green
    
    # Get all feature files (sorted alphabetically for consistent execution order)
    $featureFiles = Get-ChildItem -Path $featuresDir -Filter "*.ps1" | Sort-Object Name
    
    if ($featureFiles.Count -eq 0) {
        Write-Host "[WARNING] No feature files found in $featuresDir" -ForegroundColor Yellow
        Write-Host "          Startup will continue without modular features" -ForegroundColor Yellow
    } else {
        Write-Host "Found $($featureFiles.Count) feature(s) to load..." -ForegroundColor White
        Write-Host ""
        
        foreach ($featureFile in $featureFiles) {
            $featureName = $featureFile.BaseName
            Write-Host "[LOADING] Feature: $featureName" -ForegroundColor Cyan
            
            try {
                # Dot-source the feature file (loads the function into current scope)
                . $featureFile.FullName
                
                # Call the Initialize- function (naming convention: Initialize-<FeatureName>)
                # Convert filename to PascalCase (e.g., "timer-service" -> "TimerService")
                $functionName = (Get-Culture).TextInfo.ToTitleCase($featureName.Replace('-', ' ')).Replace(' ', '')
                $initializeFunction = "Initialize-$functionName"
                
                if (Get-Command $initializeFunction -ErrorAction SilentlyContinue) {
                    # Call the initialization function
                    & $initializeFunction
                    Write-Host "[OK] Feature '$featureName' initialized successfully" -ForegroundColor Green
                } else {
                    Write-Host "[WARNING] Feature '$featureName' loaded but function '$initializeFunction' not found" -ForegroundColor Yellow
                    Write-Host "          Feature may not follow naming convention (should export Initialize-$functionName)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "[ERROR] Failed to load feature '$featureName': $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "        Continuing with other features..." -ForegroundColor Yellow
            }
            
            Write-Host ""
        }
        
        Write-Host "[SUCCESS] All modular features loaded" -ForegroundColor Green
    }
} else {
    Write-Host "[WARNING] Features directory not found: $featuresDir" -ForegroundColor Yellow
    Write-Host "          Modular features will not be available" -ForegroundColor Yellow
    Write-Host "          Check that Global-Workflows junction is properly linked" -ForegroundColor Yellow
}

Write-Host "================================================================" -ForegroundColor Cyan

'@
}

# Now we need to identify where to insert the loader
# Strategy: Insert AFTER "MCP Protection Command available" and BEFORE any project-specific code

$insertionPoint = $null
$lines = Get-Content $startupFile

# Find "MCP Protection Command available"
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "MCP Protection Command available") {
        # Find the next non-empty line after this
        for ($j = $i + 1; $j -lt $lines.Count; $j++) {
            if ($lines[$j].Trim() -ne "") {
                $insertionPoint = $j
                break
            }
        }
        break
    }
}

# If we can't find MCP protection line, try to find "Sync Global Rules"
if (-not $insertionPoint) {
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "Sync.*Global.*Rules|Syncing global rules") {
            $insertionPoint = $i
            break
        }
    }
}

# Fallback: Insert before "UNIVERSAL STARTUP COMPLETE"
if (-not $insertionPoint) {
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "UNIVERSAL STARTUP COMPLETE") {
            $insertionPoint = $i
            break
        }
    }
}

if (-not $insertionPoint) {
    Write-Host "[ERROR] Cannot determine insertion point for modular loader" -ForegroundColor Red
    Write-Host "        Please manually update startup.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Will insert modular loader at line $insertionPoint" -ForegroundColor Green

# Check for features that need to be removed (duplicated in feature modules)
$featuresToRemove = @(
    "# CRITICAL: Minimum Model Level Enforcement",
    "Loading Minimum Model Level Rules",
    "Checking Memory Structure for Optimal AI Sessions",
    "# Resource Management System",
    "Checking documentation placement"
)

$linesToRemove = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
    foreach ($featurePattern in $featuresToRemove) {
        if ($lines[$i] -match $featurePattern) {
            # Find the entire block to remove
            $blockStart = $i
            $blockEnd = $i
            
            # Look for the end of the block (next section header or empty line followed by comment)
            for ($j = $i + 1; $j -lt $lines.Count; $j++) {
                if ($lines[$j] -match "^# ===|^Write-Host.*===|UNIVERSAL STARTUP|Loading Global Rules") {
                    $blockEnd = $j - 1
                    break
                }
            }
            
            # If we found a block, mark it for removal
            if ($blockEnd -gt $blockStart) {
                for ($k = $blockStart; $k -le $blockEnd; $k++) {
                    if ($k -notin $linesToRemove) {
                        $linesToRemove += $k
                    }
                }
            }
        }
    }
}

if ($linesToRemove.Count -gt 0) {
    Write-Host "[INFO] Found $($linesToRemove.Count) line(s) to remove (duplicate feature code)" -ForegroundColor Yellow
}

# Create backup if requested
if ($Backup -and -not $DryRun) {
    $backupFile = "$startupFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $startupFile $backupFile
    Write-Host "[OK] Created backup: $backupFile" -ForegroundColor Green
}

if ($DryRun) {
    Write-Host "[DRY RUN] Would insert modular loader at line $insertionPoint" -ForegroundColor Cyan
    Write-Host "[DRY RUN] Would remove $($linesToRemove.Count) duplicate line(s)" -ForegroundColor Cyan
    Write-Host "[DRY RUN] No changes made" -ForegroundColor Cyan
    exit 0
}

# Build the new file content
$newLines = @()

# Add all lines up to insertion point
for ($i = 0; $i -lt $insertionPoint; $i++) {
    if ($i -notin $linesToRemove) {
        $newLines += $lines[$i]
    }
}

# Add the modular loader
$newLines += ""
$newLines += $loaderSection -split "`r?`n"

# Add comment about project-specific code
$newLines += ""
$newLines += "# Note: Modular features (timer-service, minimum-model-levels, memory-structure,"
$newLines += "# resource-management, documentation-placement) are now loaded via the features loader above."
$newLines += "# All project-specific initialization should go below this point."

# Add remaining lines (skip removed ones)
for ($i = $insertionPoint; $i -lt $lines.Count; $i++) {
    if ($i -notin $linesToRemove) {
        $newLines += $lines[$i]
    }
}

# Write the new file
$newContent = $newLines -join "`r`n"
Set-Content -Path $startupFile -Value $newContent -Encoding UTF8

Write-Host ""
Write-Host "[SUCCESS] startup.ps1 migrated successfully!" -ForegroundColor Green
Write-Host "   - Added modular features loader" -ForegroundColor White
Write-Host "   - Removed $($linesToRemove.Count) duplicate line(s)" -ForegroundColor White
Write-Host "   - Preserved project-specific code" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Test startup.ps1 to ensure it works correctly" -ForegroundColor White
Write-Host "   2. Verify all features load properly" -ForegroundColor White
Write-Host "   3. If issues occur, restore from backup: $backupFile" -ForegroundColor White

