# Install All Admin Site Dependencies
# Comprehensive dependency installer

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Admin Site Dependencies Installer" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
$NodeVersion = node --version 2>$null
if ($NodeVersion) {
    Write-Host "  ✅ Node.js $NodeVersion" -ForegroundColor Green
} else {
    Write-Host "  ❌ Node.js not found - please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check npm
$NpmVersion = npm --version 2>$null
if ($NpmVersion) {
    Write-Host "  ✅ npm $NpmVersion" -ForegroundColor Green
} else {
    Write-Host "  ❌ npm not found" -ForegroundColor Red
    exit 1
}

# Install main dependencies
Write-Host ""
Write-Host "Installing npm packages..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ npm install failed" -ForegroundColor Red
    exit 1
}

Write-Host "  ✅ npm packages installed" -ForegroundColor Green

# Install admin-specific dependencies
Write-Host ""
Write-Host "Installing admin-specific packages..." -ForegroundColor Yellow

$AdminPackages = @(
    "bcryptjs",
    "jsonwebtoken",
    "nodemailer",
    "openai",
    "stripe",
    "twilio",
    "redis",
    "@aws-sdk/client-s3",
    "@aws-sdk/client-ses",
    "@aws-sdk/s3-request-presigner",
    "firebase-admin"
)

$DevPackages = @(
    "@types/bcryptjs",
    "@types/jsonwebtoken",
    "@types/nodemailer"
)

foreach ($Package in $AdminPackages) {
    Write-Host "  Installing $Package..." -ForegroundColor Gray
    npm install $Package --silent
}

Write-Host "  ✅ Admin packages installed" -ForegroundColor Green

# Install dev dependencies
Write-Host ""
Write-Host "Installing dev dependencies..." -ForegroundColor Yellow

foreach ($Package in $DevPackages) {
    Write-Host "  Installing $Package..." -ForegroundColor Gray
    npm install -D $Package --silent
}

Write-Host "  ✅ Dev packages installed" -ForegroundColor Green

# Check PostgreSQL
Write-Host ""
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
$PsqlVersion = psql --version 2>$null
if ($PsqlVersion) {
    Write-Host "  ✅ $PsqlVersion" -ForegroundColor Green
    
    # Test connection
    $PgTest = psql -h localhost -U postgres -d postgres -c "SELECT 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ PostgreSQL connection successful" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  PostgreSQL not running or connection failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  PostgreSQL not found (optional for development)" -ForegroundColor Yellow
}

# Check Redis
Write-Host ""
Write-Host "Checking Redis..." -ForegroundColor Yellow
$RedisTest = redis-cli ping 2>$null
if ($RedisTest -eq "PONG") {
    Write-Host "  ✅ Redis is running" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Redis not running (optional)" -ForegroundColor Yellow
}

# Check MailHog
Write-Host ""
Write-Host "Checking MailHog..." -ForegroundColor Yellow
try {
    $MailHogTest = Invoke-RestMethod -Uri "http://localhost:8025/api/v2/messages" -TimeoutSec 2
    Write-Host "  ✅ MailHog is running" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  MailHog not running (required for email)" -ForegroundColor Yellow
    Write-Host "     Download: https://github.com/mailhog/MailHog/releases" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Installation Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Core dependencies installed" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Copy .env.admin-example to .env" -ForegroundColor Cyan
Write-Host "  2. Update environment variables" -ForegroundColor Cyan
Write-Host "  3. Start PostgreSQL and MailHog" -ForegroundColor Cyan
Write-Host "  4. Run database migrations" -ForegroundColor Cyan
Write-Host "  5. Create first admin user" -ForegroundColor Cyan
Write-Host "  6. Start development servers" -ForegroundColor Cyan
Write-Host ""
Write-Host "See docs/Admin-Site-Quick-Start.md for details" -ForegroundColor Gray






