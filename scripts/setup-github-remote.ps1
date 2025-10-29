# Setup GitHub Remote
# Use this script to connect your local repo to GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUrl
)

Write-Host "=== Setting Up GitHub Remote ===" -ForegroundColor Cyan
Write-Host ""

# Check if remote already exists
$existingRemote = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[WARNING] Remote 'origin' already exists:" -ForegroundColor Yellow
    Write-Host "  $existingRemote" -ForegroundColor Gray
    $overwrite = Read-Host "Overwrite? (y/N)"
    if ($overwrite -ne "y") {
        Write-Host "Cancelled" -ForegroundColor Red
        exit
    }
    git remote remove origin
}

# Add remote
Write-Host "Adding GitHub remote..." -ForegroundColor Yellow
git remote add origin $GitHubUrl

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Remote added successfully!" -ForegroundColor Green
    Write-Host "  URL: $GitHubUrl" -ForegroundColor Gray
    
    # Verify
    Write-Host "`nVerifying remote..." -ForegroundColor Yellow
    git remote -v
    
    Write-Host "`n✅ Setup complete!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Push to GitHub: git push -u origin master" -ForegroundColor Gray
    Write-Host "  2. Or if using 'main' branch: git push -u origin main" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to add remote" -ForegroundColor Red
    Write-Host "Verify the URL format:" -ForegroundColor Yellow
    Write-Host "  SSH: git@github.com:username/repo.git" -ForegroundColor Gray
    Write-Host "  HTTPS: https://github.com/username/repo.git" -ForegroundColor Gray
}

