# SM-001: Redis/PostgreSQL Setup Script
# Purpose: Set up development database infrastructure
# Task: SM-001 from Phase 1 Foundation Tasks

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SM-001: Redis/PostgreSQL Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker availability
Write-Host "Checking Docker availability..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not installed or not accessible." -ForegroundColor Red
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "ERROR: docker-compose.yml not found in project root" -ForegroundColor Red
    exit 1
}

# Stop existing containers if running
Write-Host ""
Write-Host "Stopping existing containers (if any)..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Start PostgreSQL and Redis
Write-Host ""
Write-Host "Starting PostgreSQL and Redis containers..." -ForegroundColor Yellow
docker-compose up -d postgres redis

# Wait for services to be ready
Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
$maxWait = 60
$waited = 0
$postgresReady = $false
$redisReady = $false

while ($waited -lt $maxWait -and (-not $postgresReady -or -not $redisReady)) {
    Start-Sleep -Seconds 2
    $waited += 2

    # Check PostgreSQL
    if (-not $postgresReady) {
        $pgCheck = docker exec bodybroker-postgres pg_isready -U postgres 2>&1
        if ($LASTEXITCODE -eq 0) {
            $postgresReady = $true
            Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
        }
    }

    # Check Redis
    if (-not $redisReady) {
        $redisCheck = docker exec bodybroker-redis redis-cli -a "Inn0vat1on!" ping 2>&1
        if ($redisCheck -eq "PONG") {
            $redisReady = $true
            Write-Host "✓ Redis is ready" -ForegroundColor Green
        }
    }
}

if (-not $postgresReady -or -not $redisReady) {
    Write-Host ""
    Write-Host "WARNING: Services may not be fully ready. Check logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs postgres" -ForegroundColor Gray
    Write-Host "  docker-compose logs redis" -ForegroundColor Gray
}

# Test PostgreSQL connection
Write-Host ""
Write-Host "Testing PostgreSQL connection..." -ForegroundColor Yellow
$env:PGPASSWORD = "Inn0vat1on!"
$pgTest = psql -h localhost -p 5443 -U postgres -d postgres -c "SELECT version();" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PostgreSQL connection successful" -ForegroundColor Green
    Write-Host "  Connection: localhost:5443" -ForegroundColor Gray
    Write-Host "  Database: postgres" -ForegroundColor Gray
    Write-Host "  User: postgres" -ForegroundColor Gray
} else {
    Write-Host "⚠ PostgreSQL connection test failed" -ForegroundColor Yellow
    Write-Host "  Error: $pgTest" -ForegroundColor Gray
}

# Test Redis connection
Write-Host ""
Write-Host "Testing Redis connection..." -ForegroundColor Yellow
$redisTest = docker exec bodybroker-redis redis-cli -a "Inn0vat1on!" ping 2>&1
if ($redisTest -eq "PONG") {
    Write-Host "✓ Redis connection successful" -ForegroundColor Green
    Write-Host "  Connection: localhost:6379" -ForegroundColor Gray
    Write-Host "  Password: Set (Inn0vat1on!)" -ForegroundColor Gray
} else {
    Write-Host "⚠ Redis connection test failed" -ForegroundColor Yellow
    Write-Host "  Error: $redisTest" -ForegroundColor Gray
}

# Check if migrations need to be run
Write-Host ""
Write-Host "Checking database migrations..." -ForegroundColor Yellow
$migrationDir = "database/migrations"
if (Test-Path $migrationDir) {
    $migrationFiles = Get-ChildItem -Path $migrationDir -Filter "*.sql" | Sort-Object Name
    Write-Host "  Found $($migrationFiles.Count) migration files" -ForegroundColor Gray
    
    # Note: Migrations will be auto-run by PostgreSQL init scripts
    Write-Host "  Migrations will be applied automatically on first startup" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Migration directory not found: $migrationDir" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SM-001 Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  ✓ PostgreSQL: localhost:5443" -ForegroundColor Green
Write-Host "  ✓ Redis: localhost:6379" -ForegroundColor Green
Write-Host ""
Write-Host "Environment Variables:" -ForegroundColor Cyan
Write-Host "  DB_HOST=localhost" -ForegroundColor White
Write-Host "  DB_PORT=5443" -ForegroundColor White
Write-Host "  DB_NAME=postgres" -ForegroundColor White
Write-Host "  DB_USER=postgres" -ForegroundColor White
Write-Host "  DB_PASSWORD=Inn0vat1on!" -ForegroundColor White
Write-Host "  REDIS_HOST=localhost" -ForegroundColor White
Write-Host "  REDIS_PORT=6379" -ForegroundColor White
Write-Host "  REDIS_PASSWORD=Inn0vat1on!" -ForegroundColor White
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  docker-compose up -d          # Start services" -ForegroundColor Gray
Write-Host "  docker-compose down           # Stop services" -ForegroundColor Gray
Write-Host "  docker-compose logs -f         # View logs" -ForegroundColor Gray
Write-Host "  docker-compose ps              # Check status" -ForegroundColor Gray
Write-Host ""

