# GitHub Repository Setup Script
# Creates a private GitHub repository named "AI-Core" and syncs local code

param(
    [string]$RepoName = "AI-Core",
    [string]$Username = "inmanityus",
    [switch]$SkipAuth = $false
)

Write-Host "=== GitHub Repository Setup ===" -ForegroundColor Cyan
Write-Host "Repository: $Username/$RepoName" -ForegroundColor White
Write-Host "Visibility: Private" -ForegroundColor White
Write-Host ""

# Check GitHub CLI authentication
if (-not $SkipAuth) {
    Write-Host "Checking GitHub CLI authentication..." -ForegroundColor Yellow
    $authCheck = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] GitHub CLI not authenticated" -ForegroundColor Red
        Write-Host "Please run: gh auth login" -ForegroundColor Yellow
        Write-Host "Then re-run this script" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[OK] GitHub CLI authenticated" -ForegroundColor Green
}

# Check if repository already exists
Write-Host "Checking if repository exists..." -ForegroundColor Yellow
$repoExists = gh repo view "$Username/$RepoName" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[INFO] Repository already exists" -ForegroundColor Yellow
    
    # Check if it's private
    $repoInfo = gh repo view "$Username/$RepoName" --json visibility
    $visibility = ($repoInfo | ConvertFrom-Json).visibility
    Write-Host "Current visibility: $visibility" -ForegroundColor Cyan
    
    if ($visibility -ne "PRIVATE") {
        Write-Host "Making repository private..." -ForegroundColor Yellow
        gh repo edit "$Username/$RepoName" --visibility private
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Repository set to private" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Could not change visibility (may need manual update)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[OK] Repository is already private" -ForegroundColor Green
    }
} else {
    Write-Host "Creating new private repository..." -ForegroundColor Yellow
    gh repo create $RepoName --private --source=. --remote=origin --description "AI-powered gaming system core for 'The Body Broker' - Deep learning system with hierarchical LLM architecture"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create repository" -ForegroundColor Red
        Write-Host "You may need to:" -ForegroundColor Yellow
        Write-Host "  1. Authenticate: gh auth login" -ForegroundColor White
        Write-Host "  2. Or create manually at: https://github.com/new" -ForegroundColor White
        exit 1
    }
    Write-Host "[OK] Repository created" -ForegroundColor Green
}

# Update remote URL
Write-Host "Configuring git remote..." -ForegroundColor Yellow
git remote set-url origin "https://github.com/$Username/$RepoName.git"
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Remote URL updated" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Could not update remote URL" -ForegroundColor Yellow
}

# Check current branch
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "This may take a while with many commits..." -ForegroundColor Gray
git push -u origin $currentBranch

if ($LASTEXITCODE -eq 0) {
    Write-Host "" -ForegroundColor White
    Write-Host "[SUCCESS] Repository setup complete!" -ForegroundColor Green
    Write-Host "Repository URL: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Failed to push to GitHub" -ForegroundColor Red
    Write-Host "You may need to push manually: git push -u origin $currentBranch" -ForegroundColor Yellow
    exit 1
}

Write-Host "" -ForegroundColor White
Write-Host "=== Setup Complete ===" -ForegroundColor Green

