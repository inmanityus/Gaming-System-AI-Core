#Requires -Version 7.0
<#
.SYNOPSIS
    Automated hierarchical backup system for Vibe Code projects
.DESCRIPTION
    Weekly backups at 3 AM, monthly consolidation on 1st, yearly consolidation on Jan 1st
    Maintains: Weekly (current month) -> Monthly (up to 12 months) -> Yearly (indefinite)
#>

param(
    [switch]$TestMode = $false
)

# Configuration
$script:Config = @{
    SourceRoot = "E:\Vibe Code"
    CursorProfile = "C:\Users\kento\.cursor"
    BackupRoot = "E:\Innovation Forge\My Drive\Vibe-Backups"
    WeeklyFolder = "Weekly"
    MonthlyFolder = "Monthly"
    YearlyFolder = "Yearly"
    LogFolder = "Logs"
    StagingFolder = "Staging"
    LockFile = ".backup-lock"
    ExcludePatterns = @("Global-*", "node_modules", ".git", "*.tmp", "*.log")
    MaxRetries = 3
    RetryDelay = 5
    SafetyRetentionDays = 7  # Keep old backups for 7 days after consolidation
}

# Instance locking to prevent concurrent runs
function Test-BackupLock {
    $lockPath = Join-Path $script:Config.BackupRoot $script:Config.LockFile
    
    if (Test-Path $lockPath) {
        $lockContent = Get-Content $lockPath -Raw | ConvertFrom-Json
        $lockTime = [DateTime]::Parse($lockContent.StartTime)
        $lockPid = $lockContent.ProcessId
        
        # Check if process is still running
        $process = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
        if ($process) {
            $elapsed = (Get-Date) - $lockTime
            if ($elapsed.TotalHours -lt 12) {
                Write-Host "Another backup instance is running (PID: $lockPid, Started: $lockTime)" -ForegroundColor Yellow
                return $false
            } else {
                Write-Host "Stale lock detected (> 12 hours old). Removing..." -ForegroundColor Yellow
                Remove-Item $lockPath -Force
            }
        } else {
            Write-Host "Stale lock detected (process not running). Removing..." -ForegroundColor Yellow
            Remove-Item $lockPath -Force
        }
    }
    
    # Create lock
    $lockData = @{
        ProcessId = $PID
        StartTime = (Get-Date).ToString("o")
        MachineName = $env:COMPUTERNAME
    }
    $lockData | ConvertTo-Json | Set-Content $lockPath -Force
    return $true
}

function Remove-BackupLock {
    $lockPath = Join-Path $script:Config.BackupRoot $script:Config.LockFile
    if (Test-Path $lockPath) {
        Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
    }
}

# Initialize logging
function Initialize-Logging {
    $logDir = Join-Path $script:Config.BackupRoot $script:Config.LogFolder
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
    $script:LogFile = Join-Path $logDir "backup-$timestamp.log"
    
    Write-Log "========================================" -NoTimestamp
    Write-Log "Vibe Code Automated Backup System" -NoTimestamp
    Write-Log "========================================" -NoTimestamp
    Write-Log "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Log "Test Mode: $TestMode"
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Level = "INFO",
        [switch]$NoTimestamp
    )
    
    $timestamp = if ($NoTimestamp) { "" } else { "[$(Get-Date -Format 'HH:mm:ss')] " }
    $logMessage = "$timestamp[$Level] $Message"
    
    Add-Content -Path $script:LogFile -Value $logMessage
    
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        default { Write-Host $logMessage }
    }
}

# Retry wrapper for operations
function Invoke-WithRetry {
    param(
        [ScriptBlock]$ScriptBlock,
        [string]$OperationName,
        [int]$MaxRetries = $script:Config.MaxRetries,
        [int]$RetryDelay = $script:Config.RetryDelay
    )
    
    $attempt = 0
    $lastError = $null
    
    while ($attempt -lt $MaxRetries) {
        $attempt++
        try {
            return & $ScriptBlock
        } catch {
            $lastError = $_
            if ($attempt -lt $MaxRetries) {
                Write-Log "  Attempt $attempt failed: $($_.Exception.Message). Retrying in $RetryDelay seconds..." -Level WARNING
                Start-Sleep -Seconds $RetryDelay
            }
        }
    }
    
    throw "Operation '$OperationName' failed after $MaxRetries attempts. Last error: $lastError"
}

# Verify archive integrity
function Test-ArchiveIntegrity {
    param(
        [string]$ArchivePath
    )
    
    try {
        if ($ArchivePath -like "*.tar.gz") {
            # Test TAR archive
            $testResult = tar -tzf "$ArchivePath" 2>&1 | Select-Object -First 1
            return ($testResult -ne $null) -and ($LASTEXITCODE -eq 0)
        } else {
            # Test ZIP archive by reading the archive
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
            $entryCount = $zip.Entries.Count
            $zip.Dispose()
            return $entryCount -gt 0
        }
    } catch {
        Write-Log "  Archive integrity check failed: $_" -Level ERROR
        return $false
    }
}

# Calculate file hash for verification
function Get-FileHashSafe {
    param(
        [string]$Path
    )
    
    try {
        $hash = Get-FileHash -Path $Path -Algorithm SHA256
        return $hash.Hash
    } catch {
        Write-Log "  Failed to calculate hash: $_" -Level ERROR
        return $null
    }
}

# Get all projects to backup
function Get-ProjectsToBackup {
    Write-Log "Scanning for projects..."
    
    $projects = @()
    
    # Get all directories in Vibe Code, excluding Global-* symlinks
    $vibeProjects = Get-ChildItem -Path $script:Config.SourceRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike "Global-*" } |
        ForEach-Object { 
            @{
                Name = $_.Name
                Path = $_.FullName
                Type = "Project"
            }
        }
    
    $projects += $vibeProjects
    
    # Add Cursor profile
    if (Test-Path $script:Config.CursorProfile) {
        $projects += @{
            Name = "Cursor-Profile"
            Path = $script:Config.CursorProfile
            Type = "CursorProfile"
        }
    }
    
    Write-Log "Found $($projects.Count) items to backup" -Level SUCCESS
    return $projects
}

# Create safe backup without interfering with running processes
function Backup-ProjectSafely {
    param(
        [hashtable]$Project,
        [string]$DestinationPath
    )
    
    $projectName = $Project.Name
    Write-Log "Backing up: $projectName"
    
    $stagingDir = Join-Path $script:Config.BackupRoot $script:Config.StagingFolder
    $tempList = $null
    $archivePath = $null
    
    try {
        # Ensure staging directory exists
        if (-not (Test-Path $stagingDir)) {
            New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
        }
        
        # Calculate size first
        $size = Invoke-WithRetry -OperationName "Calculate $projectName size" -ScriptBlock {
            (Get-ChildItem -Path $Project.Path -Recurse -File -ErrorAction SilentlyContinue | 
                Measure-Object -Property Length -Sum).Sum / 1GB
        }
        
        Write-Log "  Size: $([math]::Round($size, 2)) GB"
        
        # Use TAR for large projects (> 2 GB), ZIP for smaller
        if ($size -gt 2) {
            Write-Log "  Using TAR format (large project)"
            
            # Create in staging first for atomicity
            $stagingArchive = Join-Path $stagingDir "$projectName-$(Get-Date -Format 'yyyyMMdd-HHmmss').tar.gz"
            
            Invoke-WithRetry -OperationName "Create TAR archive for $projectName" -ScriptBlock {
                # TAR with exclusions
                $excludeArgs = $script:Config.ExcludePatterns | ForEach-Object { "--exclude=`"$_`"" }
                $tarCmd = "tar -czf `"$stagingArchive`" -C `"$(Split-Path $Project.Path)`" $($excludeArgs -join ' ') `"$(Split-Path $Project.Path -Leaf)`" 2>&1"
                
                $result = Invoke-Expression $tarCmd
                if ($LASTEXITCODE -ne 0) {
                    throw "TAR command failed with exit code $LASTEXITCODE"
                }
            }
            
            $archivePath = "$DestinationPath.tar.gz"
            
        } else {
            Write-Log "  Using ZIP format"
            
            # Create in staging first for atomicity
            $stagingArchive = Join-Path $stagingDir "$projectName-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
            
            Invoke-WithRetry -OperationName "Create ZIP archive for $projectName" -ScriptBlock {
                # Get all files excluding patterns
                $files = Get-ChildItem -Path $Project.Path -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { 
                        $shouldExclude = $false
                        foreach ($pattern in $script:Config.ExcludePatterns) {
                            if ($_.FullName -like "*$pattern*") {
                                $shouldExclude = $true
                                break
                            }
                        }
                        -not $shouldExclude
                    }
                
                if ($files.Count -eq 0) {
                    throw "No files found to backup for $projectName"
                }
                
                # Compress using Compress-Archive with chunking for large file sets
                $chunkSize = 1000
                $chunks = [Math]::Ceiling($files.Count / $chunkSize)
                
                for ($i = 0; $i -lt $chunks; $i++) {
                    $start = $i * $chunkSize
                    $chunkFiles = $files | Select-Object -Skip $start -First $chunkSize
                    
                    if ($i -eq 0) {
                        Compress-Archive -Path $chunkFiles.FullName -DestinationPath $stagingArchive -CompressionLevel Optimal -Force
                    } else {
                        Compress-Archive -Path $chunkFiles.FullName -DestinationPath $stagingArchive -CompressionLevel Optimal -Update
                    }
                }
            }
            
            $archivePath = "$DestinationPath.zip"
        }
        
        # Verify archive integrity
        Write-Log "  Verifying archive integrity..."
        $isValid = Test-ArchiveIntegrity -ArchivePath $stagingArchive
        if (-not $isValid) {
            throw "Archive integrity check failed"
        }
        Write-Log "  Archive integrity verified" -Level SUCCESS
        
        # Calculate hash for verification
        $hash = Get-FileHashSafe -Path $stagingArchive
        if ($hash) {
            Write-Log "  SHA256: $($hash.Substring(0, 16))..."
        }
        
        # Move from staging to final destination atomically
        Invoke-WithRetry -OperationName "Move archive to destination" -ScriptBlock {
            Move-Item -Path $stagingArchive -Destination $archivePath -Force
        }
        
        if (Test-Path $archivePath) {
            $archiveSize = (Get-Item $archivePath).Length / 1GB
            Write-Log "  ✓ Success: $([math]::Round($archiveSize, 2)) GB" -Level SUCCESS
            return @{ 
                Success = $true
                Path = $archivePath
                Size = $archiveSize
                Hash = $hash
            }
        } else {
            throw "Archive was not moved to destination"
        }
        
    } catch {
        Write-Log "  ✗ Error: $_" -Level ERROR
        
        # Cleanup staging archive on failure
        if ($stagingArchive -and (Test-Path $stagingArchive)) {
            Remove-Item $stagingArchive -Force -ErrorAction SilentlyContinue
        }
        
        return @{ Success = $false; Error = $_.Exception.Message }
        
    } finally {
        # Always cleanup temp files
        if ($tempList -and (Test-Path $tempList)) {
            Remove-Item $tempList -Force -ErrorAction SilentlyContinue
        }
    }
}

# Perform weekly backup
function Invoke-WeeklyBackup {
    Write-Log "`n========================================" -NoTimestamp
    Write-Log "WEEKLY BACKUP" -NoTimestamp
    Write-Log "========================================" -NoTimestamp
    
    $weekNumber = Get-Date -UFormat %V
    $year = Get-Date -Format "yyyy"
    $weekLabel = "$year-W$weekNumber"
    
    Write-Log "Week: $weekLabel"
    
    $projects = Get-ProjectsToBackup
    $results = @()
    
    foreach ($project in $projects) {
        $projectWeeklyDir = Join-Path $script:Config.BackupRoot $script:Config.WeeklyFolder
        if (-not (Test-Path $projectWeeklyDir)) {
            New-Item -ItemType Directory -Path $projectWeeklyDir -Force | Out-Null
        }
        
        $backupName = "$($project.Name)-$weekLabel"
        $backupPath = Join-Path $projectWeeklyDir $backupName
        
        $result = Backup-ProjectSafely -Project $project -DestinationPath $backupPath
        $results += $result
    }
    
    $successful = ($results | Where-Object { $_.Success }).Count
    Write-Log "`nWeekly backup complete: $successful/$($results.Count) successful" -Level SUCCESS
    
    return $results
}

# Consolidate weekly backups into monthly
function Invoke-MonthlyConsolidation {
    Write-Log "`n========================================" -NoTimestamp
    Write-Log "MONTHLY CONSOLIDATION" -NoTimestamp
    Write-Log "========================================" -NoTimestamp
    
    $year = Get-Date -Format "yyyy"
    $month = Get-Date -Format "MM"
    $monthLabel = "$year-$month"
    
    Write-Log "Consolidating month: $monthLabel"
    
    $weeklyDir = Join-Path $script:Config.BackupRoot $script:Config.WeeklyFolder
    $monthlyDir = Join-Path $script:Config.BackupRoot $script:Config.MonthlyFolder
    
    if (-not (Test-Path $monthlyDir)) {
        New-Item -ItemType Directory -Path $monthlyDir -Force | Out-Null
    }
    
    # Get all weekly backups for this month
    $weeklyBackups = Get-ChildItem -Path $weeklyDir -File |
        Where-Object { $_.Name -match "$year-W\d+" }
    
    if ($weeklyBackups.Count -eq 0) {
        Write-Log "No weekly backups found to consolidate" -Level WARNING
        return
    }
    
    # Group by project name (extract from filename, not full path)
    $projectGroups = $weeklyBackups | Group-Object { 
        if ($_.Name -match "^(.+?)-\d{4}-W\d+") { 
            $matches[1] 
        }
    }
    
    Write-Log "Found $($projectGroups.Count) projects with weekly backups"
    
    foreach ($group in $projectGroups) {
        $projectName = $group.Name
        Write-Log "Consolidating: $projectName"
        
        $monthlyArchive = Join-Path $monthlyDir "$projectName-$monthLabel-Monthly.zip"
        
        try {
            # Create monthly archive containing all weekly backups with retry
            Invoke-WithRetry -OperationName "Create monthly archive for $projectName" -ScriptBlock {
                $weeklyFiles = $group.Group | ForEach-Object { $_.FullName }
                Compress-Archive -Path $weeklyFiles -DestinationPath $monthlyArchive -CompressionLevel Optimal -Force
            }
            
            if (Test-Path $monthlyArchive) {
                # Verify archive integrity
                Write-Log "  Verifying monthly archive integrity..."
                $isValid = Test-ArchiveIntegrity -ArchivePath $monthlyArchive
                if (-not $isValid) {
                    throw "Monthly archive integrity check failed for $projectName"
                }
                
                $size = (Get-Item $monthlyArchive).Length / 1GB
                $hash = Get-FileHashSafe -Path $monthlyArchive
                Write-Log "  ✓ Created monthly archive: $([math]::Round($size, 2)) GB" -Level SUCCESS
                
                # Mark weekly backups for deletion (safety retention)
                $deletionMarker = Join-Path (Split-Path $monthlyArchive) ".deletion-marker-$projectName-$monthLabel.json"
                $deletionData = @{
                    MarkedDate = (Get-Date).ToString("o")
                    DeleteAfter = (Get-Date).AddDays($script:Config.SafetyRetentionDays).ToString("o")
                    MonthlyArchive = $monthlyArchive
                    MonthlyHash = $hash
                    WeeklyBackups = @($group.Group | ForEach-Object { $_.FullName })
                }
                $deletionData | ConvertTo-Json | Set-Content $deletionMarker -Force
                
                Write-Log "  Weekly backups marked for deletion after $($script:Config.SafetyRetentionDays) days"
            }
        } catch {
            Write-Log "  ✗ Error creating monthly archive: $_" -Level ERROR
        }
    }
    
    Write-Log "`nMonthly consolidation complete" -Level SUCCESS
}

# Consolidate monthly backups into yearly
function Invoke-YearlyConsolidation {
    Write-Log "`n========================================" -NoTimestamp
    Write-Log "YEARLY CONSOLIDATION" -NoTimestamp
    Write-Log "========================================" -NoTimestamp
    
    $lastYear = (Get-Date).AddYears(-1).Year
    Write-Log "Consolidating year: $lastYear"
    
    $monthlyDir = Join-Path $script:Config.BackupRoot $script:Config.MonthlyFolder
    $yearlyDir = Join-Path $script:Config.BackupRoot $script:Config.YearlyFolder
    
    if (-not (Test-Path $yearlyDir)) {
        New-Item -ItemType Directory -Path $yearlyDir -Force | Out-Null
    }
    
    # Get all monthly backups for last year
    $monthlyBackups = Get-ChildItem -Path $monthlyDir -File |
        Where-Object { $_.Name -match "$lastYear-\d{2}-Monthly" }
    
    if ($monthlyBackups.Count -eq 0) {
        Write-Log "No monthly backups found for $lastYear" -Level WARNING
        return
    }
    
    # Group by project name (extract from filename, not full path)
    $projectGroups = $monthlyBackups | Group-Object { 
        if ($_.Name -match "^(.+?)-\d{4}-\d{2}-Monthly") { 
            $matches[1] 
        }
    }
    
    Write-Log "Found $($projectGroups.Count) projects with monthly backups"
    
    foreach ($group in $projectGroups) {
        $projectName = $group.Name
        Write-Log "Consolidating: $projectName"
        
        $yearlyArchive = Join-Path $yearlyDir "$projectName-$lastYear-Annual.zip"
        
        try {
            # Create yearly archive containing all monthly backups with retry
            Invoke-WithRetry -OperationName "Create yearly archive for $projectName" -ScriptBlock {
                $monthlyFiles = $group.Group | ForEach-Object { $_.FullName }
                Compress-Archive -Path $monthlyFiles -DestinationPath $yearlyArchive -CompressionLevel Optimal -Force
            }
            
            if (Test-Path $yearlyArchive) {
                # Verify archive integrity
                Write-Log "  Verifying yearly archive integrity..."
                $isValid = Test-ArchiveIntegrity -ArchivePath $yearlyArchive
                if (-not $isValid) {
                    throw "Yearly archive integrity check failed for $projectName"
                }
                
                $size = (Get-Item $yearlyArchive).Length / 1GB
                $hash = Get-FileHashSafe -Path $yearlyArchive
                Write-Log "  ✓ Created yearly archive: $([math]::Round($size, 2)) GB" -Level SUCCESS
                
                # Mark monthly backups for deletion (safety retention)
                $deletionMarker = Join-Path (Split-Path $yearlyArchive) ".deletion-marker-$projectName-$lastYear-annual.json"
                $deletionData = @{
                    MarkedDate = (Get-Date).ToString("o")
                    DeleteAfter = (Get-Date).AddDays($script:Config.SafetyRetentionDays).ToString("o")
                    YearlyArchive = $yearlyArchive
                    YearlyHash = $hash
                    MonthlyBackups = @($group.Group | ForEach-Object { $_.FullName })
                }
                $deletionData | ConvertTo-Json | Set-Content $deletionMarker -Force
                
                Write-Log "  Monthly backups marked for deletion after $($script:Config.SafetyRetentionDays) days"
            }
        } catch {
            Write-Log "  ✗ Error creating yearly archive: $_" -Level ERROR
        }
    }
    
    Write-Log "`nYearly consolidation complete" -Level SUCCESS
}

# Process deletion markers and cleanup old backups
function Invoke-DeletionCleanup {
    Write-Log "`n========================================" -NoTimestamp
    Write-Log "DELETION CLEANUP" -NoTimestamp
    Write-Log "========================================" -NoTimestamp
    
    $allMarkers = Get-ChildItem -Path $script:Config.BackupRoot -Recurse -Filter ".deletion-marker-*.json" -File
    
    if ($allMarkers.Count -eq 0) {
        Write-Log "No deletion markers found"
        return
    }
    
    Write-Log "Found $($allMarkers.Count) deletion markers"
    
    foreach ($marker in $allMarkers) {
        try {
            $deletionData = Get-Content $marker.FullName -Raw | ConvertFrom-Json
            $deleteAfter = [DateTime]::Parse($deletionData.DeleteAfter)
            
            if ((Get-Date) -ge $deleteAfter) {
                Write-Log "Processing marker: $($marker.Name)"
                
                # Verify parent archive still exists and is valid
                $parentArchive = if ($deletionData.MonthlyArchive) { 
                    $deletionData.MonthlyArchive 
                } else { 
                    $deletionData.YearlyArchive 
                }
                
                if (Test-Path $parentArchive) {
                    $isValid = Test-ArchiveIntegrity -ArchivePath $parentArchive
                    
                    if ($isValid) {
                        # Safe to delete old backups
                        $backupsToDelete = if ($deletionData.WeeklyBackups) {
                            $deletionData.WeeklyBackups
                        } else {
                            $deletionData.MonthlyBackups
                        }
                        
                        $deletedCount = 0
                        foreach ($backup in $backupsToDelete) {
                            if (Test-Path $backup) {
                                Remove-Item $backup -Force
                                $deletedCount++
                                Write-Log "  Deleted: $(Split-Path $backup -Leaf)"
                            }
                        }
                        
                        # Remove marker
                        Remove-Item $marker.FullName -Force
                        Write-Log "  ✓ Cleaned up $deletedCount old backups" -Level SUCCESS
                    } else {
                        Write-Log "  ✗ Parent archive failed integrity check. Keeping old backups." -Level ERROR
                    }
                } else {
                    Write-Log "  ✗ Parent archive not found. Keeping old backups." -Level ERROR
                }
            } else {
                $daysRemaining = ($deleteAfter - (Get-Date)).Days
                Write-Log "Marker $($marker.Name): $daysRemaining days until deletion"
            }
        } catch {
            Write-Log "  ✗ Error processing marker: $_" -Level ERROR
        }
    }
    
    Write-Log "`nDeletion cleanup complete" -Level SUCCESS
}

# Cleanup old staging files
function Clear-StagingArea {
    $stagingDir = Join-Path $script:Config.BackupRoot $script:Config.StagingFolder
    
    if (Test-Path $stagingDir) {
        # Remove files older than 24 hours
        $oldFiles = Get-ChildItem -Path $stagingDir -File | 
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-24) }
        
        if ($oldFiles.Count -gt 0) {
            Write-Log "Cleaning $($oldFiles.Count) old staging files..."
            foreach ($file in $oldFiles) {
                Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
            }
            Write-Log "Staging area cleaned" -Level SUCCESS
        }
    }
}

# Setup initial backup structure with current backups
function Initialize-BackupStructure {
    Write-Log "`n========================================" -NoTimestamp
    Write-Log "INITIALIZING BACKUP STRUCTURE" -NoTimestamp
    Write-Log "========================================" -NoTimestamp
    
    $weeklyDir = Join-Path $script:Config.BackupRoot $script:Config.WeeklyFolder
    if (-not (Test-Path $weeklyDir)) {
        New-Item -ItemType Directory -Path $weeklyDir -Force | Out-Null
        Write-Log "Created Weekly folder" -Level SUCCESS
    }
    
    # Move current backups to Weekly folder
    $currentBackups = Get-ChildItem -Path $script:Config.BackupRoot -File |
        Where-Object { $_.Name -match "backup-2025-11-10" }
    
    if ($currentBackups.Count -gt 0) {
        Write-Log "Moving $($currentBackups.Count) current backups to Weekly folder"
        
        foreach ($backup in $currentBackups) {
            $newName = $backup.Name -replace "backup-2025-11-10-\d+", "2025-W45"
            $newPath = Join-Path $weeklyDir $newName
            
            Move-Item -Path $backup.FullName -Destination $newPath -Force
            Write-Log "  Moved: $($backup.Name) -> $newName"
        }
        
        Write-Log "Initial structure setup complete" -Level SUCCESS
    }
}

# Main execution
function Main {
    try {
        # Check for concurrent execution
        if (-not (Test-BackupLock)) {
            Write-Host "ERROR: Another backup instance is already running. Exiting." -ForegroundColor Red
            exit 2
        }
        
        try {
            Initialize-Logging
            
            # Clean staging area
            Clear-StagingArea
            
            # Check if this is first run (setup)
            $weeklyDir = Join-Path $script:Config.BackupRoot $script:Config.WeeklyFolder
            if (-not (Test-Path $weeklyDir)) {
                Initialize-BackupStructure
            }
            
            # Determine what to run based on date
            $today = Get-Date
            $isFirstOfMonth = $today.Day -eq 1
            $isJanuaryFirst = $today.Month -eq 1 -and $today.Day -eq 1
            
            if ($TestMode) {
                Write-Log "Test mode: Running all operations" -Level WARNING
                Invoke-WeeklyBackup
                Invoke-MonthlyConsolidation
                Invoke-YearlyConsolidation
                Invoke-DeletionCleanup
            } else {
                # Always run weekly backup
                Invoke-WeeklyBackup
                
                # Run monthly consolidation on 1st of month
                if ($isFirstOfMonth) {
                    Invoke-MonthlyConsolidation
                }
                
                # Run yearly consolidation on January 1st
                if ($isJanuaryFirst) {
                    Invoke-YearlyConsolidation
                }
                
                # Always run deletion cleanup (processes markers)
                Invoke-DeletionCleanup
            }
            
            Write-Log "`n========================================" -NoTimestamp
            Write-Log "BACKUP COMPLETED SUCCESSFULLY" -NoTimestamp
            Write-Log "========================================" -NoTimestamp
            Write-Log "Ended: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            
            exit 0
            
        } finally {
            # Always release lock
            Remove-BackupLock
        }
        
    } catch {
        Write-Log "`nFATAL ERROR: $_" -Level ERROR
        Write-Log $_.ScriptStackTrace -Level ERROR
        Remove-BackupLock
        exit 1
    }
}

# Run
Main

