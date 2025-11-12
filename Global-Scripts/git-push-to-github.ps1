# Git Push to GitHub with Auto-Repo Creation
# This script ensures commits are pushed to GitHub, creating a private repo if needed

param(
    [string]$CommitMessage = "",
    [switch]$SkipCheck = $false
)

Write-Host "=== Git Push to GitHub ===" -ForegroundColor Cyan

# Check if we're in a git repo
if (-not (git rev-parse --git-dir 2>$null)) {
    Write-Host "[ERROR] Not a Git repository" -ForegroundColor Red
    Write-Host "Initialize Git first: git init" -ForegroundColor Yellow
    exit 1
}

# Check for existing remote
$remoteUrl = git remote get-url origin 2>$null
$hasRemote = $LASTEXITCODE -eq 0

if (-not $hasRemote -or -not $remoteUrl) {
    Write-Host "[INFO] No GitHub remote found. Creating private repository..." -ForegroundColor Yellow
    
    # Check if GitHub CLI is available
    $ghAvailable = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $ghAvailable) {
        Write-Host "[ERROR] GitHub CLI (gh) not found" -ForegroundColor Red
        Write-Host "Install: winget install GitHub.cli" -ForegroundColor Yellow
        Write-Host "Or manually create repo at: https://github.com/new" -ForegroundColor Yellow
        exit 1
    }
    
    # Check GitHub CLI authentication
    $authStatus = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] GitHub CLI not authenticated" -ForegroundColor Yellow
        Write-Host "Attempting to authenticate..." -ForegroundColor Cyan
        
        # Try to use token from environment
        if ($env:GH_TOKEN) {
            Write-Host "Using GH_TOKEN from environment" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] GitHub CLI authentication required" -ForegroundColor Red
            Write-Host "Run: gh auth login" -ForegroundColor Yellow
            Write-Host "Or set: `$env:GH_TOKEN = 'your-token'" -ForegroundColor Yellow
            exit 1
        }
    }
    
    # Get project name from directory or git config
    $projectName = Split-Path -Leaf (Get-Location)
    
    # Check if repo name contains spaces (invalid for GitHub)
    $repoName = $projectName -replace '\s+', '-' -replace '[^a-zA-Z0-9_-]', ''
    
    # Generate description
    $description = if (Test-Path "README.md") {
        # Try to extract description from README
        $readmeContent = Get-Content "README.md" -Raw
        if ($readmeContent -match '^\*\*Project\*\*:\s*(.+?)(?:\n|$)') {
            $matches[1].Trim()
        } elseif ($readmeContent -match '#\s+(.+?)(?:\n|$)') {
            $matches[1].Trim()
        } else {
            "$repoName - Project repository"
        }
    } else {
        "$repoName - Project repository"
    }
    
    Write-Host "Creating private repository: $repoName" -ForegroundColor Cyan
    
    try {
        # Create private repository
        $result = gh repo create $repoName `
            --private `
            --source=. `
            --remote=origin `
            --description $description 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Private repository created!" -ForegroundColor Green
            Write-Host "  Repo: $result" -ForegroundColor Gray
            $hasRemote = $true
        } else {
            Write-Host "❌ Failed to create repository" -ForegroundColor Red
            Write-Host $result -ForegroundColor Yellow
            Write-Host "`nManual steps:" -ForegroundColor Cyan
            Write-Host "1. Create repo at: https://github.com/new (make it PRIVATE)" -ForegroundColor Gray
            Write-Host "2. Run: git remote add origin https://github.com/yourusername/$repoName.git" -ForegroundColor Gray
            exit 1
        }
    } catch {
        Write-Host "❌ Error creating repository: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Verify we have commits to push
$branchName = git rev-parse --abbrev-ref HEAD 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not determine current branch" -ForegroundColor Red
    exit 1
}

# Check if we have unpushed commits
$remoteRef = "origin/$branchName"
$localCommits = git rev-list "$remoteRef"..HEAD 2>$null | Measure-Object -Line
$hasUnpushed = $LASTEXITCODE -eq 0 -and $localCommits.Lines -gt 0

# Also check if remote exists and branch exists there
$remoteBranch = git ls-remote --heads origin $branchName 2>$null
$remoteExists = $LASTEXITCODE -eq 0 -and $remoteBranch

if (-not $remoteExists) {
    Write-Host "[INFO] Remote branch '$branchName' doesn't exist yet. Will create on push." -ForegroundColor Yellow
    $hasUnpushed = $true
}

if ($hasUnpushed -or -not $remoteExists) {
    Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
    Write-Host "  Branch: $branchName" -ForegroundColor Gray
    Write-Host "  Remote: $remoteUrl" -ForegroundColor Gray
    
    git push -u origin $branchName 2>&1 | ForEach-Object {
        if ($_ -match "error|fatal") {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -match "warning") {
            Write-Host $_ -ForegroundColor Yellow
        } else {
            Write-Host $_ -ForegroundColor Gray
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    } else {
        Write-Host "❌ Push failed. Check errors above." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Repository is up to date with GitHub" -ForegroundColor Green
}

Write-Host "`n✅ Complete!" -ForegroundColor Green

