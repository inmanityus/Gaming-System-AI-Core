# Database Restore Script
# Restores database from backup file

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Database Restore Utility" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Verify backup file exists
if (-not (Test-Path $BackupFile)) {
    Write-Host "❌ Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "⚠️  WARNING: This will OVERWRITE the current database!" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Backup file: $BackupFile" -ForegroundColor Cyan
Write-Host "  Target database: befreefitness" -ForegroundColor Cyan
Write-Host ""

$Confirm = Read-Host "Type 'RESTORE' to continue"

if ($Confirm -ne "RESTORE") {
    Write-Host "❌ Restore cancelled" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Restoring database..." -ForegroundColor Yellow

try {
    # Decompress if needed
    $RestoreFile = $BackupFile
    if ($BackupFile -match "\.gz$") {
        Write-Host "Decompressing backup..." -ForegroundColor Yellow
        $RestoreFile = $BackupFile -replace "\.gz$", ""
        & gunzip -k $BackupFile
    }
    
    # Drop existing database and recreate
    Write-Host "Dropping existing database..." -ForegroundColor Yellow
    psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS befreefitness;"
    psql -h localhost -U postgres -c "CREATE DATABASE befreefitness;"
    
    # Restore
    Write-Host "Restoring from backup..." -ForegroundColor Yellow
    psql -h localhost -U postgres -d befreefitness -f $RestoreFile
    
    # Cleanup temp file if decompressed
    if ($RestoreFile -ne $BackupFile -and (Test-Path $RestoreFile)) {
        Remove-Item $RestoreFile -Force
    }
    
    Write-Host ""
    Write-Host "✅ Database restored successfully" -ForegroundColor Green
    
    # Verify restore
    Write-Host ""
    Write-Host "Verifying restore..." -ForegroundColor Yellow
    
    $TableCount = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
    Write-Host "  Tables restored: $($TableCount.Trim())" -ForegroundColor Cyan
    
    $UserCount = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM users;"
    Write-Host "  Users: $($UserCount.Trim())" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ Restore failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan






