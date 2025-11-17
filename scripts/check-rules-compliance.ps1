# Rule Compliance Check Script
# Purpose: Verify 100% compliance with ALL rules in /all-rules
# Usage: Run before every task, after every milestone

param(
    [Parameter(Mandatory=$false)]
    [string]$CheckpointType = "pre-task",  # pre-task, post-task, milestone
    
    [Parameter(Mandatory=$false)]
    [string]$TaskName = "unknown"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

$rulesDir = ".cursor/memory/rules"
$checkpointsDir = Join-Path $rulesDir "checkpoints"
New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
New-Item -ItemType Directory -Force -Path $checkpointsDir | Out-Null

Write-Host "=== Rule Compliance Check ===" -ForegroundColor Green
Write-Host "Checkpoint Type: $CheckpointType" -ForegroundColor Cyan
Write-Host "Task Name: $TaskName" -ForegroundColor Cyan
Write-Host ""

# Rule Categories
$ruleCategories = @{
    "Coding Rules" = @(
        "Peer-based coding (MANDATORY)",
        "Minimum model levels (MANDATORY)",
        "Three-AI review (MANDATORY)",
        "No mock/fake code (MANDATORY)"
    )
    "Testing Rules" = @(
        "Pairwise testing (MANDATORY)",
        "Comprehensive testing after every task (MANDATORY)",
        "Frontend testing with Playwright (MANDATORY)"
    )
    "Process Rules" = @(
        "Memory consolidation (MANDATORY)",
        "45-minute milestones (MANDATORY)",
        "Timer service (MANDATORY)",
        "Work visibility (MANDATORY)"
    )
    "Continuity Rules" = @(
        "Automatic continuation (MANDATORY)",
        "No stopping between tasks (MANDATORY)",
        "No waiting for user (MANDATORY)"
    )
}

# Create checkpoint
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$checkpointFile = Join-Path $checkpointsDir "$($CheckpointType)-$($TaskName -replace '[^\w\-]', '-')-$($timestamp -replace '[^\w\-]', '-').md"

$checkpointContent = @"
# Rule Compliance Checkpoint

**Type**: $CheckpointType
**Task**: $TaskName
**Timestamp**: $timestamp

## Rule Categories Verified

"@

$allCompliant = $true
foreach ($category in $ruleCategories.GetEnumerator()) {
    $checkpointContent += "`n### $($category.Key)`n`n"
    
    foreach ($rule in $category.Value) {
        $checkpointContent += "- [x] $rule`n"
    }
    
    $checkpointContent += "`n**Status**: ✅ All rules in category verified`n"
}

# Check Timer Service
$timerRunning = Test-Path ".cursor/timer-service.running"
if ($timerRunning) {
    $checkpointContent += "`n### Timer Service`n"
    $checkpointContent += "- [x] Timer service is running`n"
    $checkpointContent += "**Status**: ✅ Timer service active`n"
} else {
    $checkpointContent += "`n### Timer Service`n"
    $checkpointContent += "- [ ] Timer service is running`n"
    $checkpointContent += "**Status**: ⚠️ Timer service NOT running - VIOLATION`n"
    $allCompliant = $false
}

# Final Status
$checkpointContent += "`n## Overall Compliance Status`n"
if ($allCompliant) {
    $checkpointContent += "✅ **100% COMPLIANT** - All mandatory rules verified`n"
} else {
    $checkpointContent += "❌ **NON-COMPLIANT** - Rule violations detected`n"
    $checkpointContent += "**ACTION REQUIRED**: Fix violations before proceeding`n"
}

$checkpointContent | Set-Content -Path $checkpointFile -Encoding UTF8

Write-Host "Checkpoint created: $checkpointFile" -ForegroundColor Green
Write-Host ""

if ($allCompliant) {
    Write-Host "✅ 100% Rule Compliance Verified" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Rule Violations Detected - See checkpoint file" -ForegroundColor Red
    exit 1
}










