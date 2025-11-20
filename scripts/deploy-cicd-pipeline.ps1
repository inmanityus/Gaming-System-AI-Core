# Deploy CI/CD Pipeline to GitHub
# This script helps deploy the CI/CD pipeline to your repository

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubOrg,
    
    [Parameter(Mandatory=$true)]
    [string]$GitHubRepo,
    
    [string]$AWSAccountId = "695353648052",
    [string]$AWSRegion = "us-east-1"
)

Write-Host "=== CI/CD Pipeline Deployment Script ===" -ForegroundColor Cyan
Write-Host "Repository: $GitHubOrg/$GitHubRepo" -ForegroundColor Yellow
Write-Host "AWS Account: $AWSAccountId" -ForegroundColor Yellow
Write-Host "Region: $AWSRegion" -ForegroundColor Yellow

# Check prerequisites
Write-Host "`nChecking prerequisites..." -ForegroundColor Green

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found. Please install: https://cli.github.com/" -ForegroundColor Red
    exit 1
}
Write-Host "✅ GitHub CLI found" -ForegroundColor Green

# Check if AWS CLI is installed
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}
Write-Host "✅ AWS CLI found" -ForegroundColor Green

# Check GitHub authentication
Write-Host "`nChecking GitHub authentication..." -ForegroundColor Green
$ghAuth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub. Run: gh auth login" -ForegroundColor Red
    exit 1
}
Write-Host "✅ GitHub authenticated" -ForegroundColor Green

# Step 1: Setup IAM roles
Write-Host "`n=== Step 1: Setting up IAM roles ===" -ForegroundColor Cyan
Write-Host "Running IAM setup script..." -ForegroundColor Yellow

$iamScript = Join-Path $PSScriptRoot "setup-github-actions-iam.ps1"
if (Test-Path $iamScript) {
    & $iamScript -GitHubOrg $GitHubOrg -GitHubRepo $GitHubRepo -AWSAccountId $AWSAccountId -AWSRegion $AWSRegion
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ IAM setup failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  IAM setup script not found. Manual setup required." -ForegroundColor Yellow
}

# Step 2: Configure GitHub repository
Write-Host "`n=== Step 2: Configuring GitHub repository ===" -ForegroundColor Cyan

# Set repository secrets
Write-Host "Setting repository secrets..." -ForegroundColor Yellow

# AWS Account ID
gh secret set AWS_ACCOUNT_ID --body $AWSAccountId --repo "$GitHubOrg/$GitHubRepo"
Write-Host "✅ AWS_ACCOUNT_ID secret set" -ForegroundColor Green

# AWS Region
gh secret set AWS_REGION --body $AWSRegion --repo "$GitHubOrg/$GitHubRepo"
Write-Host "✅ AWS_REGION secret set" -ForegroundColor Green

# Create environments
Write-Host "`nCreating GitHub environments..." -ForegroundColor Yellow

# Create staging environment
Write-Host "Creating staging environment..." -ForegroundColor Gray
$stagingEnv = @{
    environment_name = "staging"
    wait_timer = 0
    reviewers = @()
    deployment_branch_policy = @{
        protected_branches = $false
        custom_branch_policies = $true
    }
}

# Note: gh CLI doesn't support creating environments directly
# This needs to be done via GitHub UI or API
Write-Host "⚠️  Please create 'staging' environment manually in GitHub Settings → Environments" -ForegroundColor Yellow
Write-Host "   No protection rules required for staging" -ForegroundColor Gray

Write-Host "`nCreating production environment..." -ForegroundColor Gray
Write-Host "⚠️  Please create 'production' environment manually in GitHub Settings → Environments" -ForegroundColor Yellow
Write-Host "   Recommended protection rules:" -ForegroundColor Gray
Write-Host "   - Required reviewers: 1-2" -ForegroundColor Gray
Write-Host "   - Restrict to 'main' branch only" -ForegroundColor Gray
Write-Host "   - Optional: Add wait timer (5-10 minutes)" -ForegroundColor Gray

# Step 3: Verify files
Write-Host "`n=== Step 3: Verifying CI/CD files ===" -ForegroundColor Cyan

$requiredFiles = @(
    ".github/workflows/comprehensive-ci-v2.yml"
    ".github/workflows/deploy-with-promotion.yml"
    ".github/workflows/security-scan.yml"
    ".github/services.json"
    "scripts/validate-python-imports.py"
    "scripts/smoke-test-service-v2.sh"
    "scripts/monitor-production-deployment.sh"
)

$allFilesPresent = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
        $allFilesPresent = $false
    }
}

if (-not $allFilesPresent) {
    Write-Host "`n❌ Some required files are missing" -ForegroundColor Red
    exit 1
}

# Step 4: Push to repository
Write-Host "`n=== Step 4: Pushing to repository ===" -ForegroundColor Cyan

$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Yellow

if ($currentBranch -ne "main") {
    Write-Host "⚠️  Not on main branch. Switch to main? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'y') {
        git checkout main
    }
}

# Check if there are commits to push
$unpushedCommits = git log origin/main..HEAD --oneline
if ($unpushedCommits) {
    Write-Host "`nUnpushed commits:" -ForegroundColor Yellow
    Write-Host $unpushedCommits -ForegroundColor Gray
    
    Write-Host "`nPush to origin/main? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'y') {
        git push origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully pushed to origin/main" -ForegroundColor Green
        } else {
            Write-Host "❌ Push failed" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "✅ No unpushed commits" -ForegroundColor Green
}

# Step 5: Verify workflows
Write-Host "`n=== Step 5: Verifying workflows ===" -ForegroundColor Cyan

Write-Host "Checking workflow status..." -ForegroundColor Yellow
$workflows = gh workflow list --repo "$GitHubOrg/$GitHubRepo" --limit 10

if ($workflows -match "comprehensive-ci-v2") {
    Write-Host "✅ Comprehensive CI workflow found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Comprehensive CI workflow not found yet" -ForegroundColor Yellow
}

if ($workflows -match "deploy-with-promotion") {
    Write-Host "✅ Deploy with Promotion workflow found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Deploy workflow not found yet" -ForegroundColor Yellow
}

if ($workflows -match "security-scan") {
    Write-Host "✅ Security Scan workflow found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Security workflow not found yet" -ForegroundColor Yellow
}

# Final instructions
Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Go to https://github.com/$GitHubOrg/$GitHubRepo/settings/environments" -ForegroundColor White
Write-Host "   - Create 'staging' environment (no protection)" -ForegroundColor Gray
Write-Host "   - Create 'production' environment (with protection rules)" -ForegroundColor Gray

Write-Host "`n2. Test the pipeline:" -ForegroundColor White
Write-Host "   - Create a PR with a small change to one service" -ForegroundColor Gray
Write-Host "   - Verify only that service is built/tested" -ForegroundColor Gray
Write-Host "   - Merge PR and verify deployment workflow" -ForegroundColor Gray

Write-Host "`n3. Monitor initial runs:" -ForegroundColor White
Write-Host "   - Check Actions tab: https://github.com/$GitHubOrg/$GitHubRepo/actions" -ForegroundColor Gray
Write-Host "   - Review any failures and adjust" -ForegroundColor Gray

Write-Host "`n4. Deploy a service to staging:" -ForegroundColor White
Write-Host "   - Go to Actions → Deploy with Promotion → Run workflow" -ForegroundColor Gray
Write-Host "   - Select a service and environment" -ForegroundColor Gray

Write-Host "`n✅ CI/CD Pipeline deployment script complete!" -ForegroundColor Green
