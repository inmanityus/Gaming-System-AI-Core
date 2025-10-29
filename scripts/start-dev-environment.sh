#!/bin/bash

# Be Free Fitness Development Startup Script
# This script sets up the development environment

echo "🚀 Starting Be Free Fitness Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p docker/data/postgres
mkdir -p docker/data/redis
mkdir -p docker/data/minio
mkdir -p apps/api/uploads
mkdir -p apps/api/logs

# Copy environment file if it doesn't exist
if [ ! -f "Docker-Template/env/dev/.env" ]; then
    echo "📝 Creating environment file..."
    cp "Project-Management/environment-config.env" "Docker-Template/env/dev/.env"
    echo "⚠️  Please update Docker-Template/env/dev/.env with your actual values"
fi

# Create password files if they don't exist
if [ ! -f "Docker-Template/env/dev/postgres_password.txt" ]; then
    echo "🔐 Creating PostgreSQL password file..."
    echo "postgres" > "Docker-Template/env/dev/postgres_password.txt"
fi

if [ ! -f "Docker-Template/env/dev/minio_access_key.txt" ]; then
    echo "🔐 Creating MinIO access key file..."
    echo "minioadmin" > "Docker-Template/env/dev/minio_access_key.txt"
fi

if [ ! -f "Docker-Template/env/dev/minio_secret_key.txt" ]; then
    echo "🔐 Creating MinIO secret key file..."
    echo "minioadmin" > "Docker-Template/env/dev/minio_secret_key.txt"
fi

# Install dependencies
echo "📦 Installing dependencies..."
if command -v pnpm &> /dev/null; then
    pnpm install
else
    npm install
fi

# Start Docker services
echo "🐳 Starting Docker services..."
cd Docker-Template
docker-compose up -d postgres redis minio mailhog

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."
docker-compose ps

echo "✅ Development environment is ready!"
echo ""
echo "📋 Next steps:"
echo "1. Update Docker-Template/env/dev/.env with your actual values"
echo "2. Run 'npm run dev:api' to start the API server"
echo "3. Run 'npm run dev:web' to start the web server"
echo "4. Visit http://localhost:3000 to see the website"
echo "5. Visit http://localhost:4000/healthz to check API health"
echo "6. Visit http://localhost:8025 to see emails (MailHog)"
echo ""
echo "🔧 Useful commands:"
echo "- View logs: docker-compose logs -f [service-name]"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart [service-name]"
