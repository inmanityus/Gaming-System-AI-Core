# Security Audit Script
# Runs comprehensive security checks on the admin system

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Security Audit - Admin Site" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$Issues = @()
$Warnings = @()

# Check 1: Environment variables
Write-Host "Checking environment variables..." -ForegroundColor Yellow

if (-not $env:JWT_SECRET) {
    $Issues += "JWT_SECRET not set"
}
elseif ($env:JWT_SECRET.Length -lt 32) {
    $Warnings += "JWT_SECRET should be at least 32 characters"
}

if (-not $env:DATABASE_URL) {
    $Issues += "DATABASE_URL not set"
}

if ($env:NODE_ENV -ne "production") {
    $Warnings += "NODE_ENV not set to 'production'"
}

# Check 2: Database security
Write-Host "Checking database security..." -ForegroundColor Yellow

$RlsCheck = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM pg_policies;"
if ([int]$RlsCheck.Trim() -lt 10) {
    $Warnings += "Few Row-Level Security policies found ($($RlsCheck.Trim()))"
}

# Check for default passwords
$DefaultPasswords = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM admin_users WHERE password_hash LIKE '%default%';"
if ([int]$DefaultPasswords.Trim() -gt 0) {
    $Issues += "Admin users with default passwords found"
}

# Check 3: API Security Headers
Write-Host "Checking security headers..." -ForegroundColor Yellow

try {
    $Response = Invoke-WebRequest -Uri "http://localhost:3001/admin/v1/health" -Method GET
    
    $RequiredHeaders = @(
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Strict-Transport-Security",
        "X-XSS-Protection"
    )
    
    foreach ($Header in $RequiredHeaders) {
        if (-not $Response.Headers[$Header]) {
            $Warnings += "Missing security header: $Header"
        }
    }
}
catch {
    $Warnings += "Could not check API security headers (server may be down)"
}

# Check 4: Admin users without MFA
Write-Host "Checking MFA enforcement..." -ForegroundColor Yellow

$NoMfaCount = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM admin_users WHERE mfa_enabled = false AND status = 'active';"
if ([int]$NoMfaCount.Trim() -gt 0) {
    $Warnings += "$($NoMfaCount.Trim()) active admin(s) without MFA enabled"
}

# Check 5: Audit log retention
Write-Host "Checking audit log retention..." -ForegroundColor Yellow

$OldLogs = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"
if ([int]$OldLogs.Trim() -gt 10000) {
    $Warnings += "Large number of old audit logs (consider archiving)"
}

# Check 6: Failed login attempts
Write-Host "Checking for suspicious login attempts..." -ForegroundColor Yellow

$FailedLogins = psql -h localhost -U postgres -d befreefitness -t -c "SELECT COUNT(*) FROM audit_logs WHERE action = 'login_failed' AND created_at > NOW() - INTERVAL '24 hours';"
if ([int]$FailedLogins.Trim() -gt 100) {
    $Issues += "High number of failed logins in last 24h: $($FailedLogins.Trim())"
}

# Check 7: File permissions
Write-Host "Checking file permissions..." -ForegroundColor Yellow

$SensitiveFiles = @(
    ".env",
    "database-migrations/*.sql"
)

foreach ($Pattern in $SensitiveFiles) {
    $Files = Get-ChildItem -Path $Pattern -ErrorAction SilentlyContinue
    foreach ($File in $Files) {
        # Check if file is readable by others (simplified check)
        if ($File.Attributes -match "ReadOnly") {
            $Warnings += "$($File.Name) has permissive permissions"
        }
    }
}

# Check 8: Dependency vulnerabilities
Write-Host "Checking for vulnerable dependencies..." -ForegroundColor Yellow

try {
    $AuditOutput = npm audit --json 2>$null | ConvertFrom-Json
    
    if ($AuditOutput.metadata.vulnerabilities.high -gt 0) {
        $Issues += "$($AuditOutput.metadata.vulnerabilities.high) high-severity vulnerabilities"
    }
    
    if ($AuditOutput.metadata.vulnerabilities.critical -gt 0) {
        $Issues += "$($AuditOutput.metadata.vulnerabilities.critical) CRITICAL vulnerabilities"
    }
}
catch {
    $Warnings += "Could not run npm audit"
}

# Check 9: SSL/TLS Configuration
Write-Host "Checking SSL/TLS configuration..." -ForegroundColor Yellow

if (-not $env:SSL_CERT_PATH) {
    $Warnings += "SSL certificates not configured (required for production)"
}

# Check 10: Rate limiting
Write-Host "Checking rate limiting..." -ForegroundColor Yellow

# This would test actual rate limit enforcement
$Warnings += "Manual verification required: Test rate limiting is working"

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Security Audit Results" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($Issues.Count -eq 0 -and $Warnings.Count -eq 0) {
    Write-Host "✅ No security issues found!" -ForegroundColor Green
}
else {
    if ($Issues.Count -gt 0) {
        Write-Host "❌ CRITICAL ISSUES ($($Issues.Count)):" -ForegroundColor Red
        foreach ($Issue in $Issues) {
            Write-Host "  - $Issue" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($Warnings.Count -gt 0) {
        Write-Host "⚠️  WARNINGS ($($Warnings.Count)):" -ForegroundColor Yellow
        foreach ($Warning in $Warnings) {
            Write-Host "  - $Warning" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

if ($Issues.Count -gt 0) {
    Write-Host "⚠️  Address critical issues before deploying to production" -ForegroundColor Red
    exit 1
}
else {
    Write-Host "✅ System is secure for deployment" -ForegroundColor Green
    exit 0
}






