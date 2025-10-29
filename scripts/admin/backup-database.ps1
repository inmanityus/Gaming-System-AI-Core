# Database Backup Script
# Creates timestamped backup of admin database

param(
    [string]$BackupDir = ".\backups",
    [switch]$Compress
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Database Backup Utility" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Create backup directory
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
    Write-Host "✅ Created backup directory: $BackupDir" -ForegroundColor Green
}

# Generate filename
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupFile = Join-Path $BackupDir "befreefitness-admin-$Timestamp.sql"

Write-Host "Creating backup..." -ForegroundColor Yellow
Write-Host "  Database: befreefitness" -ForegroundColor Cyan
Write-Host "  Output: $BackupFile" -ForegroundColor Cyan
Write-Host ""

# Create backup
try {
    pg_dump -h localhost -U postgres -d befreefitness -f $BackupFile
    
    $FileSize = (Get-Item $BackupFile).Length / 1MB
    Write-Host "✅ Backup created successfully" -ForegroundColor Green
    Write-Host "  Size: $([Math]::Round($FileSize, 2)) MB" -ForegroundColor Cyan
    
    # Compress if requested
    if ($Compress) {
        Write-Host ""
        Write-Host "Compressing backup..." -ForegroundColor Yellow
        
        $CompressedFile = "$BackupFile.gz"
        & gzip -9 $BackupFile
        
        if (Test-Path $CompressedFile) {
            $CompressedSize = (Get-Item $CompressedFile).Length / 1MB
            $CompressionRatio = [Math]::Round((1 - ($CompressedSize / $FileSize)) * 100, 1)
            
            Write-Host "✅ Backup compressed" -ForegroundColor Green
            Write-Host "  Original: $([Math]::Round($FileSize, 2)) MB" -ForegroundColor Cyan
            Write-Host "  Compressed: $([Math]::Round($CompressedSize, 2)) MB" -ForegroundColor Cyan
            Write-Host "  Savings: ${CompressionRatio}%" -ForegroundColor Cyan
            
            $BackupFile = $CompressedFile
        }
    }
    
    Write-Host ""
    Write-Host "Backup complete: $BackupFile" -ForegroundColor Green
    
    # Cleanup old backups (keep last 7 days)
    Write-Host ""
    Write-Host "Cleaning up old backups..." -ForegroundColor Yellow
    
    $OldBackups = Get-ChildItem -Path $BackupDir -Filter "befreefitness-admin-*.sql*" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
    
    if ($OldBackups) {
        foreach ($OldBackup in $OldBackups) {
            Remove-Item $OldBackup.FullName -Force
            Write-Host "  Removed: $($OldBackup.Name)" -ForegroundColor Gray
        }
        Write-Host "✅ Cleaned up $($OldBackups.Count) old backup(s)" -ForegroundColor Green
    }
    else {
        Write-Host "  No old backups to remove" -ForegroundColor Gray
    }
}
catch {
    Write-Host "❌ Backup failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan






