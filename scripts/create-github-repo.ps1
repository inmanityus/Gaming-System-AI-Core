# Create Private GitHub Repository
# This script creates a new private repo and connects it to the local repository

param(
    [string]$RepoName = "Gaming-System-AI-Core",
    [string]$GitHubToken
)

Write-Host "=== Creating Private GitHub Repository ===" -ForegroundColor Cyan
Write-Host ""

# Check GitHub CLI authentication
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub CLI not authenticated" -ForegroundColor Yellow
    Write-Host "`nOption 1: Authenticate GitHub CLI (Interactive)" -ForegroundColor Cyan
    Write-Host "  Run: gh auth login" -ForegroundColor Gray
    Write-Host "  Then run this script again" -ForegroundColor Gray
    
    Write-Host "`nOption 2: Use GitHub Token" -ForegroundColor Cyan
    if ($GitHubToken) {
        $env:GH_TOKEN = $GitHubToken
        Write-Host "  Using provided token" -ForegroundColor Green
    } else {
        Write-Host "  Set GH_TOKEN environment variable:" -ForegroundColor Gray
        Write-Host "    `$env:GH_TOKEN = 'your-github-token'" -ForegroundColor White
        Write-Host "  Or pass as parameter:" -ForegroundColor Gray
        Write-Host "    .\scripts\create-github-repo.ps1 -GitHubToken 'your-token'" -ForegroundColor White
        Write-Host "`n  Then run this script again" -ForegroundColor Gray
        exit 1
    }
}

# Check if repo already exists locally
if (git remote get-url origin 2>$null) {
    Write-Host "[WARNING] Remote 'origin' already exists" -ForegroundColor Yellow
    $existingUrl = git remote get-url origin
    Write-Host "  Current: $existingUrl" -ForegroundColor Gray
    $overwrite = Read-Host "Remove and recreate? (y/N)"
    if ($overwrite -eq "y") {
        git remote remove origin
    } else {
        Write-Host "Cancelled" -ForegroundColor Red
        exit
    }
}

# Create repository
Write-Host "`nCreating private repository: $RepoName" -ForegroundColor Yellow
$description = "AI-Driven Gaming Core - The Body Broker: Horror game with hierarchical LLM architecture, dynamic NPCs, and procedural content generation"

try {
    $result = gh repo create $RepoName `
        --private `
        --source=. `
        --remote=origin `
        --description $description 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Repository created successfully!" -ForegroundColor Green
        Write-Host "  Repo: $($result -join ' ')" -ForegroundColor Gray
        
        # Push to GitHub
        Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
        git push -u origin master 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Code pushed to GitHub!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Push may have failed. Try manually:" -ForegroundColor Yellow
            Write-Host "  git push -u origin master" -ForegroundColor Gray
        }
        
        Write-Host "`n✅ Complete! Repository is private and code is synced." -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create repository" -ForegroundColor Red
        Write-Host $result -ForegroundColor Yellow
        
        Write-Host "`nManual Steps:" -ForegroundColor Cyan
        Write-Host "1. Create repo on GitHub.com (make it private)" -ForegroundColor Gray
        Write-Host "2. Run: git remote add origin https://github.com/yourusername/$RepoName.git" -ForegroundColor Gray
        Write-Host "3. Run: git push -u origin master" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

