# Be Free Fitness Development Startup Script (PowerShell)
# This script sets up the development environment

Write-Host "🚀 Starting Be Free Fitness Development Environment..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "docker/data/postgres" | Out-Null
New-Item -ItemType Directory -Force -Path "docker/data/redis" | Out-Null
New-Item -ItemType Directory -Force -Path "docker/data/minio" | Out-Null
New-Item -ItemType Directory -Force -Path "apps/api/uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "apps/api/logs" | Out-Null

# Copy environment file if it doesn't exist
if (-not (Test-Path "Docker-Template/env/dev/.env")) {
    Write-Host "📝 Creating environment file..." -ForegroundColor Yellow
    Copy-Item "Project-Management/environment-config.env" "Docker-Template/env/dev/.env"
    Write-Host "⚠️  Please update Docker-Template/env/dev/.env with your actual values" -ForegroundColor Yellow
}

# Create password files if they don't exist
if (-not (Test-Path "Docker-Template/env/dev/postgres_password.txt")) {
    Write-Host "🔐 Creating PostgreSQL password file..." -ForegroundColor Yellow
    "postgres" | Out-File -FilePath "Docker-Template/env/dev/postgres_password.txt" -Encoding UTF8
}

if (-not (Test-Path "Docker-Template/env/dev/minio_access_key.txt")) {
    Write-Host "🔐 Creating MinIO access key file..." -ForegroundColor Yellow
    "minioadmin" | Out-File -FilePath "Docker-Template/env/dev/minio_access_key.txt" -Encoding UTF8
}

if (-not (Test-Path "Docker-Template/env/dev/minio_secret_key.txt")) {
    Write-Host "🔐 Creating MinIO secret key file..." -ForegroundColor Yellow
    "minioadmin" | Out-File -FilePath "Docker-Template/env/dev/minio_secret_key.txt" -Encoding UTF8
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    pnpm install
} else {
    npm install
}

# Start Docker services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
Set-Location "Docker-Template"
docker-compose up -d postgres redis minio mailhog

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if services are healthy
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow
docker-compose ps

Set-Location ".."

Write-Host "✅ Development environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Update Docker-Template/env/dev/.env with your actual values"
Write-Host "2. Run 'npm run dev:api' to start the API server"
Write-Host "3. Run 'npm run dev:web' to start the web server"
Write-Host "4. Visit http://localhost:3000 to see the website"
Write-Host "5. Visit http://localhost:4000/healthz to check API health"
Write-Host "6. Visit http://localhost:8025 to see emails (MailHog)"
Write-Host ""
Write-Host "🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "- View logs: docker-compose logs -f [service-name]"
Write-Host "- Stop services: docker-compose down"
Write-Host "- Restart services: docker-compose restart [service-name]"