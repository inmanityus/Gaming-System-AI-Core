# Admin Site Setup Script
# One-time setup for admin site infrastructure

param(
    [switch]$SkipDependencies,
    [switch]$SkipMigrations,
    [switch]$SkipAdminUser
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Be Free Fitness - Admin Site Setup" -ForegroundColor Cyan  
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# PostgreSQL
try {
    $pgVersion = psql --version
    Write-Host "✓ PostgreSQL installed: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ PostgreSQL not found. Please install PostgreSQL." -ForegroundColor Red
    exit 1
}

# Redis
try {
    redis-cli --version
    Write-Host "✓ Redis installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Redis not found. Install Redis for rate limiting." -ForegroundColor Yellow
}

# Node.js
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install dependencies
if (-not $SkipDependencies) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    
    # Parse admin dependencies
    if (Test-Path "package.json.admin-dependencies") {
        Write-Host "Installing admin-specific packages..." -ForegroundColor Yellow
        
        $deps = Get-Content "package.json.admin-dependencies" | ConvertFrom-Json
        $packages = $deps.dependencies.PSObject.Properties | ForEach-Object { "$($_.Name)@$($_.Value)" }
        
        npm install @($packages)
        
        Write-Host "✓ Dependencies installed" -ForegroundColor Green
    }
}

Write-Host ""

# Run migrations
if (-not $SkipMigrations) {
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    
    $migrations = @(
        "database-migrations/admin-001-security-hardening.sql",
        "database-migrations/admin-002-core-admin-tables.sql",
        "database-migrations/admin-003-all-admin-features.sql"
    )
    
    foreach ($migration in $migrations) {
        Write-Host "  Applying: $migration" -ForegroundColor Gray
        psql -h localhost -U postgres -d befreefitness -f $migration -q
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Applied: $migration" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Failed: $migration" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "✓ All migrations applied" -ForegroundColor Green
}

Write-Host ""

# Create initial admin user
if (-not $SkipAdminUser) {
    Write-Host "Setting up initial admin user..." -ForegroundColor Yellow
    
    $adminEmail = Read-Host "Admin email (default: admin@befreefitness.ai)"
    if ([string]::IsNullOrWhiteSpace($adminEmail)) {
        $adminEmail = "admin@befreefitness.ai"
    }
    
    $adminPassword = Read-Host "Admin password (min 12 chars)" -AsSecureString
    $adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword)
    )
    
    if ($adminPasswordPlain.Length -lt 12) {
        Write-Host "✗ Password must be at least 12 characters" -ForegroundColor Red
        exit 1
    }
    
    # Hash password using Node.js
    $hashScript = @"
const argon2 = require('argon2');
(async () => {
  const hash = await argon2.hash('$adminPasswordPlain', {
    type: argon2.argon2id,
    memoryCost: 19456,
    timeCost: 3,
    parallelism: 1,
  });
  console.log(hash);
})();
"@
    
    $passwordHash = node -e $hashScript
    
    # Update admin user in database
    $updateQuery = @"
UPDATE admin_users 
SET password_hash = '$passwordHash',
    status = 'active',
    password_changed_at = NOW()
WHERE email = '$adminEmail';
"@
    
    psql -h localhost -U postgres -d befreefitness -c $updateQuery -q
    
    Write-Host "✓ Admin user configured: $adminEmail" -ForegroundColor Green
}

Write-Host ""

# Environment file check
if (-not (Test-Path ".env.admin")) {
    Write-Host "⚠ .env.admin not found. Copy .env.admin.example and configure." -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "   Admin Site Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure .env.admin with your settings" -ForegroundColor White
Write-Host "2. Generate JWT keys and store in AWS Secrets Manager" -ForegroundColor White
Write-Host "3. Start admin API: npm run dev:admin-api" -ForegroundColor White
Write-Host "4. Start admin web: npm run dev:admin-web" -ForegroundColor White
Write-Host "5. Login at: http://localhost:3001/admin/login" -ForegroundColor White
Write-Host ""






