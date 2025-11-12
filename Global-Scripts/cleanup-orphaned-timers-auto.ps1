# Cleanup Orphaned Timer Service Script (Auto-Clean Mode)
# Automatically identifies and removes orphaned timer services

param(
    [switch]$AutoClean = $false
)

Write-Host "🧹 TIMER SERVICE CLEANUP (Auto Mode)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$issuesFound = @()
$cleanupsPerformed = @()

# Step 1: Check for orphaned background jobs
Write-Host "[1/5] Checking for orphaned PowerShell background jobs..." -ForegroundColor Yellow
$allJobs = Get-Job -ErrorAction SilentlyContinue
$timerJobs = $allJobs | Where-Object { $_.Name -like "*Timer*" -or $_.Name -like "*Cursor*" }

if ($timerJobs) {
    $issuesFound += "Found $($timerJobs.Count) orphaned timer job(s)"
    Write-Host "  ⚠️  Found $($timerJobs.Count) orphaned timer job(s):" -ForegroundColor Yellow
    $timerJobs | ForEach-Object {
        Write-Host "     - Job ID: $($_.Id), Name: $($_.Name), State: $($_.State), Started: $($_.PSBeginTime)" -ForegroundColor Gray
    }
    
    if ($AutoClean) {
        $timerJobs | ForEach-Object {
            Remove-Job $_ -Force -ErrorAction SilentlyContinue
            $cleanupsPerformed += "Removed job $($_.Id)"
            Write-Host "     ✓ Removed job $($_.Id)" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  ✅ No orphaned background jobs found" -ForegroundColor Green
}

Write-Host ""

# Step 2: Check for orphaned PowerShell processes (old sessions)
Write-Host "[2/5] Checking for orphaned PowerShell processes..." -ForegroundColor Yellow
$allPwsh = Get-Process -Name "pwsh","powershell" -ErrorAction SilentlyContinue
$orphaned = $allPwsh | Where-Object { 
    $_.StartTime -lt (Get-Date).AddHours(-2) -and 
    ($_.CPU -lt 10 -or $_.WorkingSet -lt 200MB)
}

if ($orphaned) {
    $issuesFound += "Found $($orphaned.Count) orphaned PowerShell process(es)"
    Write-Host "  ⚠️  Found $($orphaned.Count) potentially orphaned process(es):" -ForegroundColor Yellow
    $orphaned | ForEach-Object {
        $age = (Get-Date) - $_.StartTime
        Write-Host "     - PID: $($_.Id), CPU: $([math]::Round($_.CPU, 2))s, Memory: $([math]::Round($_.WorkingSet/1MB, 2))MB, Age: $([math]::Round($age.TotalHours, 1))h" -ForegroundColor Gray
    }
    
    if ($AutoClean) {
        Write-Host "     🔄 Auto-cleaning orphaned processes..." -ForegroundColor Yellow
        $orphaned | ForEach-Object {
            try {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                $cleanupsPerformed += "Killed orphaned process $($_.Id)"
                Write-Host "     ✓ Killed process $($_.Id)" -ForegroundColor Green
            } catch {
                Write-Host "     ✗ Failed to kill process $($_.Id): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "  ✅ No orphaned processes detected" -ForegroundColor Green
}

Write-Host ""

# Step 3: Check for orphaned timer marker files
Write-Host "[3/5] Checking for timer service marker files..." -ForegroundColor Yellow
$timerMarker = ".cursor/timer-service.running"
$sessionIdFile = ".cursor/timer-session-id.txt"

if (Test-Path $timerMarker) {
    $markerTime = (Get-Item $timerMarker).LastWriteTime
    $age = (Get-Date) - $markerTime
    
    Write-Host "  ⚠️  Found timer marker file (last updated: $markerTime, age: $([math]::Round($age.TotalMinutes, 1)) minutes)" -ForegroundColor Yellow
    
    # If marker is older than 2 hours, it's likely orphaned
    if ($age.TotalHours -gt 2) {
        $issuesFound += "Orphaned timer marker file (age: $([math]::Round($age.TotalHours, 1))h)"
        Write-Host "     ⚠️  Marker is older than 2 hours - likely orphaned" -ForegroundColor Yellow
        
        if ($AutoClean) {
            Remove-Item $timerMarker -Force -ErrorAction SilentlyContinue
            $cleanupsPerformed += "Removed orphaned timer marker file"
            Write-Host "     ✓ Removed orphaned marker file" -ForegroundColor Green
        }
    } else {
        Write-Host "     ℹ️  Marker appears active (age: $([math]::Round($age.TotalMinutes, 1)) minutes)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✅ No timer marker file found" -ForegroundColor Green
}

if (Test-Path $sessionIdFile) {
    $sessionContent = Get-Content $sessionIdFile -ErrorAction SilentlyContinue -First 1
    Write-Host "  ℹ️  Found session ID file: $sessionContent" -ForegroundColor Gray
    
    # Check if session ID file is old
    $fileAge = (Get-Item $sessionIdFile).LastWriteTime
    $age = (Get-Date) - $fileAge
    if ($age.TotalHours -gt 2) {
        $issuesFound += "Old session ID file (age: $([math]::Round($age.TotalHours, 1))h)"
        if ($AutoClean) {
            Remove-Item $sessionIdFile -Force -ErrorAction SilentlyContinue
            $cleanupsPerformed += "Removed old session ID file"
            Write-Host "     ✓ Removed old session ID file" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  ✅ No session ID file found" -ForegroundColor Green
}

Write-Host ""

# Step 4: Check for nested directory structure problem
Write-Host "[4/5] Checking for nested directory structure issues..." -ForegroundColor Yellow
$deploymentPath = "$env:USERPROFILE\.cursor\Deployment\Global"
$nestedDirs = 0

if (Test-Path $deploymentPath) {
    try {
        $allDirs = Get-ChildItem -Path $deploymentPath -Recurse -Directory -ErrorAction SilentlyContinue -Depth 10
        $nestedDirs = ($allDirs | Where-Object { 
            $_.FullName -match 'Deployment\\Global\\Deployment\\Global' 
        }).Count
        
        if ($nestedDirs -gt 10) {
            $issuesFound += "Found $nestedDirs deeply nested directories"
            Write-Host "  ⚠️  Found deeply nested directory structure ($nestedDirs+ nested directories)" -ForegroundColor Yellow
            Write-Host "     This is likely causing file duplication issues" -ForegroundColor Yellow
            Write-Host "     ⚠️  WARNING: Cleanup of this structure may take significant time" -ForegroundColor Red
            Write-Host "     Recommendation: Manual cleanup recommended to avoid data loss" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ Directory structure appears normal" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ⚠️  Error checking directory structure: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ No deployment directory found" -ForegroundColor Green
}

Write-Host ""

# Step 5: Summary
Write-Host "[5/5] Summary" -ForegroundColor Yellow
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($issuesFound.Count -eq 0) {
    Write-Host "✅ NO ISSUES FOUND - Timer Service is clean!" -ForegroundColor Green
} else {
    Write-Host "⚠️  ISSUES FOUND:" -ForegroundColor Yellow
    $issuesFound | ForEach-Object {
        Write-Host "   • $_" -ForegroundColor Red
    }
    
    if ($AutoClean -and $cleanupsPerformed.Count -gt 0) {
        Write-Host ""
        Write-Host "✅ CLEANUPS PERFORMED:" -ForegroundColor Green
        $cleanupsPerformed | ForEach-Object {
            Write-Host "   ✓ $_" -ForegroundColor Green
        }
    } elseif (-not $AutoClean) {
        Write-Host ""
        Write-Host "💡 To auto-clean these issues, run:" -ForegroundColor Cyan
        Write-Host "   pwsh -ExecutionPolicy Bypass -File 'scripts/cleanup-orphaned-timers-auto.ps1' -AutoClean" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run /start-right to properly initialize timer service" -ForegroundColor White
Write-Host "  2. Verify timer service status:" -ForegroundColor White
Write-Host "     Test-Path '.cursor/timer-service.running'" -ForegroundColor Gray
Write-Host "  3. Check for timer jobs:" -ForegroundColor White
Write-Host "     Get-Job | Where-Object { `$_.Name -like '*Timer*' }" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Return exit code based on issues found
if ($issuesFound.Count -gt 0) {
    exit 1
} else {
    exit 0
}





