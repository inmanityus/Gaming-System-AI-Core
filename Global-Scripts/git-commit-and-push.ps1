# Git Commit and Push - Universal Wrapper
# Use this for all Git commits - automatically pushes to GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$Message,
    
    [switch]$SkipPush = $false
)

Write-Host "=== Git Commit and Push ===" -ForegroundColor Cyan

# Check if git repo
if (-not (git rev-parse --git-dir 2>$null)) {
    Write-Host "[ERROR] Not a Git repository" -ForegroundColor Red
    exit 1
}

# Stage all changes
Write-Host "Staging changes..." -ForegroundColor Yellow
git add -A

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to stage changes" -ForegroundColor Red
    exit 1
}

# Check if there are changes to commit
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "[INFO] No changes to commit" -ForegroundColor Yellow
    exit 0
}

# Commit
Write-Host "Committing..." -ForegroundColor Yellow
git commit -m $Message

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Commit failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Committed: $Message" -ForegroundColor Green

# Push to GitHub (unless skipped)
if (-not $SkipPush) {
    Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
    
    $pushScript = "Global-Scripts\git-push-to-github.ps1"
    if (Test-Path $pushScript) {
        pwsh -ExecutionPolicy Bypass -File $pushScript
    } else {
        Write-Host "[WARNING] git-push-to-github.ps1 not found" -ForegroundColor Yellow
        Write-Host "Attempting direct push..." -ForegroundColor Yellow
        
        # Try direct push
        $remoteExists = git remote get-url origin 2>$null
        if ($LASTEXITCODE -eq 0) {
            $branch = git rev-parse --abbrev-ref HEAD
            git push -u origin $branch
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Push failed. Run manually: git push -u origin $branch" -ForegroundColor Red
                exit 1
            }
            Write-Host "✅ Pushed to GitHub" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] No remote configured. Create repo first." -ForegroundColor Red
            Write-Host "See: .\scripts\create-github-repo.ps1" -ForegroundColor Yellow
            exit 1
        }
    }
}

Write-Host "`n✅ Complete!" -ForegroundColor Green

