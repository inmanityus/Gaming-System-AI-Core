# Security Setup Verification Script
# CRITICAL: This script MUST be run at the start of EVERY session

Write-Host "`n🔒 SECURITY VERIFICATION CHECK 🔒" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$securityIssues = @()

# 1. Check if docs/security exists
if (-not (Test-Path "docs/security")) {
    $securityIssues += "❌ Missing docs/security folder"
} else {
    Write-Host "✅ docs/security folder exists" -ForegroundColor Green
}

# 2. Check if .private directory exists and is git-ignored
if (-not (Test-Path "docs/security/.private")) {
    $securityIssues += "❌ Missing docs/security/.private folder"
} else {
    Write-Host "✅ docs/security/.private folder exists" -ForegroundColor Green
}

# 3. Check .gitignore for security patterns
if (Test-Path ".gitignore") {
    $gitignore = Get-Content ".gitignore" -Raw
    $requiredPatterns = @(
        "docs/security/.private/",
        "*.pem",
        "*.key",
        ".env",
        "api-keys.env"
    )
    
    foreach ($pattern in $requiredPatterns) {
        if ($gitignore -notmatch [regex]::Escape($pattern)) {
            $securityIssues += "❌ .gitignore missing pattern: $pattern"
        }
    }
    
    if ($gitignore -match "docs/security/.private/" -and 
        $gitignore -match "\.env" -and 
        $gitignore -match "\*.key") {
        Write-Host "✅ .gitignore has security patterns" -ForegroundColor Green
    }
} else {
    $securityIssues += "❌ Missing .gitignore file"
}

# 4. Check for exposed secrets in common locations
Write-Host "`nScanning for exposed secrets..." -ForegroundColor Yellow
$exposedFiles = @()

# Check root directory for .env files
Get-ChildItem -Path . -Filter ".env*" -File -Depth 0 | ForEach-Object {
    if ($_.Name -ne ".env.example") {
        $exposedFiles += $_.FullName
    }
}

# Check for common secret file names
$secretFilePatterns = @("*.pem", "*.key", "*secret*", "*credential*", "api-keys.*")
foreach ($pattern in $secretFilePatterns) {
    Get-ChildItem -Path . -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { 
        $_.FullName -notlike "*node_modules*" -and 
        $_.FullName -notlike "*.git*" -and
        $_.FullName -notlike "*docs\security\.private*"
    } | ForEach-Object {
        $exposedFiles += $_.FullName
    }
}

if ($exposedFiles.Count -gt 0) {
    $securityIssues += "❌ Found potentially exposed secret files:"
    $exposedFiles | Select-Object -Unique | ForEach-Object {
        $securityIssues += "   - $_"
    }
} else {
    Write-Host "✅ No obvious exposed secret files" -ForegroundColor Green
}

# 5. Check if security documentation exists
$requiredDocs = @(
    "docs/security/README.md",
    "docs/security/api-keys-required.md"
)

foreach ($doc in $requiredDocs) {
    if (-not (Test-Path $doc)) {
        $securityIssues += "❌ Missing required documentation: $doc"
    }
}

if ((Test-Path "docs/security/README.md") -and (Test-Path "docs/security/api-keys-required.md")) {
    Write-Host "✅ Security documentation exists" -ForegroundColor Green
}

# Report results
Write-Host "`n=================================" -ForegroundColor Cyan
if ($securityIssues.Count -eq 0) {
    Write-Host "✅ ALL SECURITY CHECKS PASSED! ✅" -ForegroundColor Green
    Write-Host "`nSecurity folder ready at: docs/security/" -ForegroundColor Cyan
    Write-Host "Store secrets in: docs/security/.private/ (git-ignored)" -ForegroundColor Cyan
} else {
    Write-Host "❌ SECURITY ISSUES DETECTED! ❌" -ForegroundColor Red
    Write-Host "`nIssues found:" -ForegroundColor Red
    $securityIssues | ForEach-Object {
        Write-Host $_
    }
    
    Write-Host "`n🚨 CRITICAL: Fix these security issues immediately!" -ForegroundColor Yellow
    Write-Host "Run: /clean-project to set up proper security structure" -ForegroundColor Yellow
}

Write-Host "`n🔐 REMEMBER: NEVER share API keys in chat!" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
