# Project Cleanup Script
# Organizes documentation and files according to cleanup-project rules

param(
    [switch]$Execute = $false
)

$ErrorActionPreference = "Continue"

Write-Host "=== PROJECT CLEANUP SCRIPT ===" -ForegroundColor Cyan
Write-Host ""

# Phase 1: Create required docs subfolders
Write-Host "[PHASE 1] Creating required documentation subfolders..." -ForegroundColor Yellow

$requiredSubfolders = @(
    "docs/Requirements",
    "docs/Solutions",
    "docs/Tasks",
    "docs/Architecture",
    "docs/API",
    "docs/Development",
    "docs/Deployment",
    "docs/User-Guides",
    "docs/Troubleshooting",
    "docs/Changelog",
    "docs/updates",
    "docs/success-output",
    "docs/temp",
    "docs/logs"
)

foreach ($folder in $requiredSubfolders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "  [OK] Created $folder" -ForegroundColor Green
    }
}

# Phase 2: Move milestone and session files from root to docs/updates/
Write-Host ""
Write-Host "[PHASE 2] Moving milestone and session files from root..." -ForegroundColor Yellow

$milestoneFiles = Get-ChildItem -Path . -Filter "MILESTONE-*.md" -File -ErrorAction SilentlyContinue
$sessionFiles = Get-ChildItem -Path . -Filter "SESSION-*.md" -File -ErrorAction SilentlyContinue
$progressFiles = Get-ChildItem -Path . -Filter "PROGRESS-*.md" -File -ErrorAction SilentlyContinue
$handoffFiles = Get-ChildItem -Path . -Filter "HANDOFF-*.md" -File -ErrorAction SilentlyContinue
$completeFiles = Get-ChildItem -Path . -Filter "*-COMPLETE.md" -File -ErrorAction SilentlyContinue
$statusFiles = Get-ChildItem -Path . -Filter "*-STATUS*.md" -File -ErrorAction SilentlyContinue

$filesToMove = @()
$filesToMove += $milestoneFiles
$filesToMove += $sessionFiles
$filesToMove += $progressFiles
$filesToMove += $handoffFiles
$filesToMove += $completeFiles
$filesToMove += $statusFiles

# Also move other non-essential root files
$otherRootFiles = Get-ChildItem -Path . -Filter "*.md" -File -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -ne "README.md" -and
    $_.FullName -notlike "*\docs\*" -and
    $_.FullName -notlike "*\Global-*"
}

$filesToMove += $otherRootFiles

$movedCount = 0
foreach ($file in $filesToMove) {
    if ($file -and $file.Exists -and $file.FullName -notlike "*\docs\*") {
        $dest = Join-Path "docs/updates" $file.Name
        if ($Execute) {
            Move-Item -Path $file.FullName -Destination $dest -Force -ErrorAction SilentlyContinue
            Write-Host "  [MOVED] $($file.Name) -> docs/updates/" -ForegroundColor Yellow
            $movedCount++
        } else {
            Write-Host "  [WOULD MOVE] $($file.Name) -> docs/updates/" -ForegroundColor Gray
        }
    }
}

Write-Host "  [INFO] Found $($filesToMove.Count) files to move from root (moved: $movedCount)" -ForegroundColor White

# Phase 3: Organize docs/ root files into subfolders
Write-Host ""
Write-Host "[PHASE 3] Organizing docs/ root files into subfolders..." -ForegroundColor Yellow

$docsRootFiles = Get-ChildItem -Path "docs" -Filter "*.md" -File -ErrorAction SilentlyContinue | Where-Object {
    $_.FullName -notlike "*\requirements\*" -and
    $_.FullName -notlike "*\solutions\*" -and
    $_.FullName -notlike "*\tasks\*" -and
    $_.FullName -notlike "*\architecture\*" -and
    $_.FullName -notlike "*\deployment\*" -and
    $_.FullName -notlike "*\development\*" -and
    $_.FullName -notlike "*\narrative\*" -and
    $_.FullName -notlike "*\integration\*" -and
    $_.FullName -notlike "*\infrastructure\*" -and
    $_.FullName -notlike "*\updates\*" -and
    $_.FullName -notlike "*\success-output\*" -and
    $_.FullName -notlike "*\temp\*" -and
    $_.FullName -notlike "*\logs\*"
}

$docsMovedCount = 0
foreach ($file in $docsRootFiles) {
    $category = "Architecture"  # Default category
    
    # Categorize based on filename/content
    $name = $file.Name
    if ($name -match "REQUIREMENT|Requirements|Requirement") {
        $category = "Requirements"
    } elseif ($name -match "SOLUTION|Solution|SOLUTIONS") {
        $category = "Solutions"
    } elseif ($name -match "TASK|Task|TASKS") {
        $category = "Tasks"
    } elseif ($name -match "ARCHITECTURE|Architecture|Arch") {
        $category = "Architecture"
    } elseif ($name -match "DEPLOYMENT|Deployment|DEPLOY") {
        $category = "Deployment"
    } elseif ($name -match "API|Blueprint|API") {
        $category = "API"
    } elseif ($name -match "STATUS|Status|COMPLETE|Complete|SUMMARY|Summary|VERIFICATION|Verification") {
        $category = "updates"  # Status/complete files go to updates
    } else {
        $category = "Architecture"  # Default to Architecture
    }
    
    $dest = Join-Path "docs/$category" $file.Name
    if ($Execute) {
        Move-Item -Path $file.FullName -Destination $dest -Force -ErrorAction SilentlyContinue
        Write-Host "  [MOVED] $($file.Name) -> docs/$category/" -ForegroundColor Yellow
        $docsMovedCount++
    } else {
        Write-Host "  [WOULD MOVE] $($file.Name) -> docs/$category/" -ForegroundColor Gray
    }
}

Write-Host "  [INFO] Found $($docsRootFiles.Count) files in docs/ root to organize (moved: $docsMovedCount)" -ForegroundColor White

# Phase 4: Move requirements files to Requirements subfolder
Write-Host ""
Write-Host "[PHASE 4] Ensuring all requirements files are in docs/Requirements/..." -ForegroundColor Yellow

$requirementsFiles = Get-ChildItem -Path . -Filter "*requirements*.md" -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    $_.FullName -notlike "*\docs\Requirements\*" -and
    $_.FullName -notlike "*\node_modules\*" -and
    $_.FullName -notlike "*\Global-*\*"
}

$reqMovedCount = 0
foreach ($file in $requirementsFiles) {
    $dest = Join-Path "docs/Requirements" $file.Name
    if ($Execute) {
        Move-Item -Path $file.FullName -Destination $dest -Force -ErrorAction SilentlyContinue
        Write-Host "  [MOVED] $($file.Name) -> docs/Requirements/" -ForegroundColor Yellow
        $reqMovedCount++
    } else {
        Write-Host "  [WOULD MOVE] $($file.Name) -> docs/Requirements/" -ForegroundColor Gray
    }
}

Write-Host "  [INFO] Found $($requirementsFiles.Count) requirements files to move (moved: $reqMovedCount)" -ForegroundColor White

Write-Host ""
Write-Host "=== CLEANUP SUMMARY ===" -ForegroundColor Cyan
Write-Host "  Root files moved: $movedCount" -ForegroundColor White
Write-Host "  Docs root files organized: $docsMovedCount" -ForegroundColor White
Write-Host "  Requirements files moved: $reqMovedCount" -ForegroundColor White
Write-Host ""
if (-not $Execute) {
    Write-Host "[INFO] This was a dry run. Run with -Execute to perform actual moves." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Cleanup completed!" -ForegroundColor Green
}

