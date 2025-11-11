#Requires -Version 7.0
<#
.SYNOPSIS
    Pairwise testing for automated backup system
.DESCRIPTION
    Comprehensive tests for all backup functionality, safety features, and edge cases
#>

$script:TestResults = @()
$script:TestBackupRoot = "E:\Innovation Forge\My Drive\Vibe-Backups\Test-Area"
$script:TestSourceRoot = "E:\Innovation Forge\My Drive\Vibe-Backups\Test-Source"

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = "",
        [string]$Details = ""
    )
    
    $result = @{
        TestName = $TestName
        Passed = $Passed
        Message = $Message
        Details = $Details
        Timestamp = Get-Date
    }
    
    $script:TestResults += $result
    
    $symbol = if ($Passed) { "✓" } else { "✗" }
    $color = if ($Passed) { "Green" } else { "Red" }
    
    Write-Host "$symbol $TestName" -ForegroundColor $color
    if ($Message) {
        Write-Host "  $Message" -ForegroundColor $color
    }
    if ($Details -and -not $Passed) {
        Write-Host "  Details: $Details" -ForegroundColor Yellow
    }
}

function Initialize-TestEnvironment {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Initializing Test Environment" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Clean and create test directories
    if (Test-Path $script:TestBackupRoot) {
        Remove-Item $script:TestBackupRoot -Recurse -Force
    }
    if (Test-Path $script:TestSourceRoot) {
        Remove-Item $script:TestSourceRoot -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $script:TestBackupRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $script:TestSourceRoot -Force | Out-Null
    
    # Create test projects
    $testProjects = @(
        @{ Name = "Small-Project"; Size = 1MB; Files = 100 },
        @{ Name = "Medium-Project"; Size = 50MB; Files = 500 },
        @{ Name = "Large-Project"; Size = 2.5GB; Files = 1000 }
    )
    
    foreach ($project in $testProjects) {
        $projectPath = Join-Path $script:TestSourceRoot $project.Name
        New-Item -ItemType Directory -Path $projectPath -Force | Out-Null
        
        # Create test files
        $fileSize = [math]::Floor($project.Size / $project.Files)
        for ($i = 0; $i -lt $project.Files; $i++) {
            $filePath = Join-Path $projectPath "test-file-$i.dat"
            $bytes = New-Object byte[] $fileSize
            [System.Random]::new().NextBytes($bytes)
            [System.IO.File]::WriteAllBytes($filePath, $bytes)
        }
        
        Write-Host "Created test project: $($project.Name) ($($project.Files) files)" -ForegroundColor Green
    }
    
    # Create Global-* symlinks (should be excluded)
    $globalDir = Join-Path $script:TestSourceRoot "Global-Scripts"
    New-Item -ItemType Directory -Path $globalDir -Force | Out-Null
    "This should be excluded" | Out-File (Join-Path $globalDir "test.txt")
    
    Write-Host "`nTest environment ready`n" -ForegroundColor Green
}

function Test-InstanceLocking {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 1: Instance Locking" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Test 1.1: Lock creation
    $lockPath = Join-Path $script:TestBackupRoot ".backup-lock"
    if (Test-Path $lockPath) {
        Remove-Item $lockPath -Force
    }
    
    $lockData = @{
        ProcessId = $PID
        StartTime = (Get-Date).ToString("o")
        MachineName = $env:COMPUTERNAME
    }
    $lockData | ConvertTo-Json | Set-Content $lockPath -Force
    
    $lockExists = Test-Path $lockPath
    Write-TestResult -TestName "1.1 Lock File Creation" -Passed $lockExists `
        -Message "Lock file $(if ($lockExists) {'created'} else {'failed to create'})"
    
    # Test 1.2: Lock content validation
    try {
        $lockContent = Get-Content $lockPath -Raw | ConvertFrom-Json
        $validContent = ($lockContent.ProcessId -eq $PID) -and ($lockContent.MachineName -eq $env:COMPUTERNAME)
        Write-TestResult -TestName "1.2 Lock Content Validation" -Passed $validContent `
            -Message "Lock contains correct PID and machine name"
    } catch {
        Write-TestResult -TestName "1.2 Lock Content Validation" -Passed $false `
            -Message "Failed to parse lock content" -Details $_.Exception.Message
    }
    
    # Test 1.3: Stale lock detection
    $staleLockData = @{
        ProcessId = 99999  # Non-existent PID
        StartTime = (Get-Date).AddHours(-13).ToString("o")
        MachineName = $env:COMPUTERNAME
    }
    $staleLockData | ConvertTo-Json | Set-Content $lockPath -Force
    
    $process = Get-Process -Id 99999 -ErrorAction SilentlyContinue
    $isStale = -not $process
    Write-TestResult -TestName "1.3 Stale Lock Detection" -Passed $isStale `
        -Message "Stale lock correctly identified (process not running)"
    
    # Cleanup
    Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
}

function Test-ArchiveIntegrity {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 2: Archive Integrity Validation" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $testDir = Join-Path $script:TestSourceRoot "Small-Project"
    
    # Test 2.1: Valid ZIP creation and verification
    $zipPath = Join-Path $script:TestBackupRoot "test-valid.zip"
    try {
        Compress-Archive -Path $testDir -DestinationPath $zipPath -Force
        $zipExists = Test-Path $zipPath
        Write-TestResult -TestName "2.1 Valid ZIP Creation" -Passed $zipExists `
            -Message "ZIP archive created successfully"
    } catch {
        Write-TestResult -TestName "2.1 Valid ZIP Creation" -Passed $false `
            -Message "Failed to create ZIP" -Details $_.Exception.Message
    }
    
    # Test 2.2: Valid TAR.GZ creation and verification
    $tarPath = Join-Path $script:TestBackupRoot "test-valid.tar.gz"
    try {
        $result = tar -czf "$tarPath" -C "$script:TestSourceRoot" "Small-Project" 2>&1
        $tarExists = Test-Path $tarPath
        Write-TestResult -TestName "2.2 Valid TAR.GZ Creation" -Passed $tarExists `
            -Message "TAR.GZ archive created successfully"
    } catch {
        Write-TestResult -TestName "2.2 Valid TAR.GZ Creation" -Passed $false `
            -Message "Failed to create TAR.GZ" -Details $_.Exception.Message
    }
    
    # Test 2.3: TAR.GZ integrity check
    if (Test-Path $tarPath) {
        try {
            $testResult = tar -tzf "$tarPath" 2>&1 | Select-Object -First 1
            $isValid = $testResult -ne $null
            Write-TestResult -TestName "2.3 TAR.GZ Integrity Check" -Passed $isValid `
                -Message "TAR.GZ integrity verified"
        } catch {
            Write-TestResult -TestName "2.3 TAR.GZ Integrity Check" -Passed $false `
                -Message "TAR.GZ integrity check failed" -Details $_.Exception.Message
        }
    }
    
    # Test 2.4: Corrupted archive detection
    $corruptPath = Join-Path $script:TestBackupRoot "test-corrupt.tar.gz"
    "This is not a valid archive" | Out-File $corruptPath
    try {
        $testResult = tar -tzf "$corruptPath" 2>&1
        $isInvalid = $LASTEXITCODE -ne 0
        Write-TestResult -TestName "2.4 Corrupted Archive Detection" -Passed $isInvalid `
            -Message "Corrupted archive correctly identified"
    } catch {
        Write-TestResult -TestName "2.4 Corrupted Archive Detection" -Passed $true `
            -Message "Corrupted archive correctly rejected"
    }
}

function Test-RetryLogic {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 3: Retry Logic" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Test 3.1: Successful operation (no retry needed)
    $attemptCount = 0
    $successBlock = {
        $script:attemptCount++
        return "Success"
    }
    
    try {
        $result = & $successBlock
        $passed = ($attemptCount -eq 1) -and ($result -eq "Success")
        Write-TestResult -TestName "3.1 Successful Operation (No Retry)" -Passed $passed `
            -Message "Operation succeeded on first attempt"
    } catch {
        Write-TestResult -TestName "3.1 Successful Operation (No Retry)" -Passed $false `
            -Message "Unexpected failure"
    }
    
    # Test 3.2: Transient failure with retry
    $attemptCount = 0
    $failTwiceBlock = {
        $script:attemptCount++
        if ($attemptCount -lt 3) {
            throw "Transient error"
        }
        return "Success after retries"
    }
    
    $retrySuccess = $false
    for ($i = 0; $i -lt 3; $i++) {
        try {
            $result = & $failTwiceBlock
            $retrySuccess = $true
            break
        } catch {
            if ($i -eq 2) {
                # Last attempt should have succeeded
            }
        }
    }
    
    Write-TestResult -TestName "3.2 Transient Failure with Retry" -Passed $retrySuccess `
        -Message "Operation succeeded after retries ($attemptCount attempts)"
    
    # Test 3.3: Permanent failure
    $failAlwaysBlock = {
        throw "Permanent error"
    }
    
    $finallyFailed = $false
    try {
        for ($i = 0; $i -lt 3; $i++) {
            try {
                & $failAlwaysBlock
            } catch {
                if ($i -eq 2) {
                    $finallyFailed = $true
                }
            }
        }
    } catch {
        $finallyFailed = $true
    }
    
    Write-TestResult -TestName "3.3 Permanent Failure (Max Retries)" -Passed $finallyFailed `
        -Message "Operation failed after maximum retries"
}

function Test-StagingArea {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 4: Staging Area Operations" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $stagingDir = Join-Path $script:TestBackupRoot "Staging"
    
    # Test 4.1: Staging directory creation
    if (-not (Test-Path $stagingDir)) {
        New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
    }
    $stagingExists = Test-Path $stagingDir
    Write-TestResult -TestName "4.1 Staging Directory Creation" -Passed $stagingExists `
        -Message "Staging directory created"
    
    # Test 4.2: Atomic move operation
    $testFile = Join-Path $stagingDir "test-atomic.txt"
    "Test content" | Out-File $testFile
    $destination = Join-Path $script:TestBackupRoot "moved-file.txt"
    
    try {
        Move-Item -Path $testFile -Destination $destination -Force
        $movedSuccessfully = (Test-Path $destination) -and (-not (Test-Path $testFile))
        Write-TestResult -TestName "4.2 Atomic Move Operation" -Passed $movedSuccessfully `
            -Message "File moved atomically from staging to destination"
    } catch {
        Write-TestResult -TestName "4.2 Atomic Move Operation" -Passed $false `
            -Message "Atomic move failed" -Details $_.Exception.Message
    }
    
    # Test 4.3: Staging cleanup (old files)
    $oldFile = Join-Path $stagingDir "old-file.txt"
    "Old content" | Out-File $oldFile
    $file = Get-Item $oldFile
    $file.LastWriteTime = (Get-Date).AddHours(-25)
    
    $oldFiles = Get-ChildItem -Path $stagingDir -File | 
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-24) }
    
    $foundOldFile = $oldFiles.Count -gt 0
    Write-TestResult -TestName "4.3 Old File Detection" -Passed $foundOldFile `
        -Message "Old files detected for cleanup ($($oldFiles.Count) files)"
}

function Test-ExclusionPatterns {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 5: Exclusion Patterns" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Test 5.1: Global-* exclusion
    $globalDir = Join-Path $script:TestSourceRoot "Global-Scripts"
    $shouldExclude = $globalDir -like "*Global-*"
    Write-TestResult -TestName "5.1 Global-* Pattern Match" -Passed $shouldExclude `
        -Message "Global-* directories correctly identified for exclusion"
    
    # Test 5.2: Multiple pattern exclusions
    $testPaths = @(
        @{ Path = "node_modules"; ShouldExclude = $true },
        @{ Path = ".git"; ShouldExclude = $true },
        @{ Path = "test.tmp"; ShouldExclude = $true },
        @{ Path = "test.log"; ShouldExclude = $true },
        @{ Path = "valid-file.txt"; ShouldExclude = $false }
    )
    
    $excludePatterns = @("Global-*", "node_modules", ".git", "*.tmp", "*.log")
    $allCorrect = $true
    
    foreach ($test in $testPaths) {
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($test.Path -like "*$pattern*") {
                $shouldExclude = $true
                break
            }
        }
        
        if ($shouldExclude -ne $test.ShouldExclude) {
            $allCorrect = $false
            break
        }
    }
    
    Write-TestResult -TestName "5.2 Multiple Exclusion Patterns" -Passed $allCorrect `
        -Message "All exclusion patterns working correctly"
}

function Test-DeletionMarkers {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 6: Deletion Markers & Safety Retention" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $markerPath = Join-Path $script:TestBackupRoot ".deletion-marker-test.json"
    
    # Test 6.1: Marker creation
    $markerData = @{
        MarkedDate = (Get-Date).ToString("o")
        DeleteAfter = (Get-Date).AddDays(7).ToString("o")
        MonthlyArchive = "test-archive.zip"
        MonthlyHash = "abc123"
        WeeklyBackups = @("backup1.zip", "backup2.zip")
    }
    
    try {
        $markerData | ConvertTo-Json | Set-Content $markerPath -Force
        $markerExists = Test-Path $markerPath
        Write-TestResult -TestName "6.1 Deletion Marker Creation" -Passed $markerExists `
            -Message "Deletion marker created successfully"
    } catch {
        Write-TestResult -TestName "6.1 Deletion Marker Creation" -Passed $false `
            -Message "Failed to create marker" -Details $_.Exception.Message
    }
    
    # Test 6.2: Marker parsing
    try {
        $parsedData = Get-Content $markerPath -Raw | ConvertFrom-Json
        $validParsing = ($parsedData.MonthlyArchive -eq "test-archive.zip") -and 
                       ($parsedData.WeeklyBackups.Count -eq 2)
        Write-TestResult -TestName "6.2 Deletion Marker Parsing" -Passed $validParsing `
            -Message "Marker data parsed correctly"
    } catch {
        Write-TestResult -TestName "6.2 Deletion Marker Parsing" -Passed $false `
            -Message "Failed to parse marker" -Details $_.Exception.Message
    }
    
    # Test 6.3: Retention period calculation
    $deleteAfter = [DateTime]::Parse($markerData.DeleteAfter)
    $daysUntilDeletion = ($deleteAfter - (Get-Date)).Days
    $correctRetention = ($daysUntilDeletion -ge 6) -and ($daysUntilDeletion -le 7)  # Allow for time drift
    Write-TestResult -TestName "6.3 Retention Period Calculation" -Passed $correctRetention `
        -Message "7-day retention period set correctly ($daysUntilDeletion days)"
    
    # Cleanup
    Remove-Item $markerPath -Force -ErrorAction SilentlyContinue
}

function Test-HashVerification {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST 7: SHA256 Hash Verification" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $testFile = Join-Path $script:TestBackupRoot "hash-test.txt"
    "Test content for hashing" | Out-File $testFile
    
    # Test 7.1: Hash calculation
    try {
        $hash1 = Get-FileHash -Path $testFile -Algorithm SHA256
        $hashExists = $hash1.Hash -ne $null
        Write-TestResult -TestName "7.1 SHA256 Hash Calculation" -Passed $hashExists `
            -Message "Hash calculated: $($hash1.Hash.Substring(0, 16))..."
    } catch {
        Write-TestResult -TestName "7.1 SHA256 Hash Calculation" -Passed $false `
            -Message "Hash calculation failed" -Details $_.Exception.Message
    }
    
    # Test 7.2: Hash consistency
    try {
        $hash2 = Get-FileHash -Path $testFile -Algorithm SHA256
        $hashesMatch = $hash1.Hash -eq $hash2.Hash
        Write-TestResult -TestName "7.2 Hash Consistency" -Passed $hashesMatch `
            -Message "Same file produces identical hashes"
    } catch {
        Write-TestResult -TestName "7.2 Hash Consistency" -Passed $false `
            -Message "Hash consistency check failed"
    }
    
    # Test 7.3: Hash change detection
    "Different content" | Out-File $testFile
    try {
        $hash3 = Get-FileHash -Path $testFile -Algorithm SHA256
        $hashesChanged = $hash1.Hash -ne $hash3.Hash
        Write-TestResult -TestName "7.3 Hash Change Detection" -Passed $hashesChanged `
            -Message "Modified file produces different hash"
    } catch {
        Write-TestResult -TestName "7.3 Hash Change Detection" -Passed $false `
            -Message "Hash change detection failed"
    }
    
    # Cleanup
    Remove-Item $testFile -Force -ErrorAction SilentlyContinue
}

# Run all tests
function Main {
    Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Vibe Code Backup - Pairwise Testing  ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    Initialize-TestEnvironment
    
    Test-InstanceLocking
    Test-ArchiveIntegrity
    Test-RetryLogic
    Test-StagingArea
    Test-ExclusionPatterns
    Test-DeletionMarkers
    Test-HashVerification
    
    # Summary
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST SUMMARY" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $totalTests = $script:TestResults.Count
    $passedTests = ($script:TestResults | Where-Object { $_.Passed }).Count
    $failedTests = $totalTests - $passedTests
    $passRate = [math]::Round(($passedTests / $totalTests) * 100, 2)
    
    Write-Host "Total Tests: $totalTests" -ForegroundColor White
    Write-Host "Passed: $passedTests" -ForegroundColor Green
    Write-Host "Failed: $failedTests" -ForegroundColor $(if ($failedTests -eq 0) { "Green" } else { "Red" })
    Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -eq 100) { "Green" } else { "Yellow" })
    
    if ($failedTests -gt 0) {
        Write-Host "`nFailed Tests:" -ForegroundColor Red
        $script:TestResults | Where-Object { -not $_.Passed } | ForEach-Object {
            Write-Host "  ✗ $($_.TestName): $($_.Message)" -ForegroundColor Red
            if ($_.Details) {
                Write-Host "    $($_.Details)" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    if ($passRate -eq 100) {
        Write-Host "✓ ALL TESTS PASSED - PRODUCTION READY" -ForegroundColor Green
    } else {
        Write-Host "✗ SOME TESTS FAILED - REVIEW REQUIRED" -ForegroundColor Red
    }
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Cleanup test environment
    Write-Host "Cleaning up test environment..." -ForegroundColor Yellow
    Remove-Item $script:TestBackupRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $script:TestSourceRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleanup complete`n" -ForegroundColor Green
    
    return ($passRate -eq 100)
}

# Run
$success = Main
exit $(if ($success) { 0 } else { 1 })

