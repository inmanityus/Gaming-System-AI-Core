# Run Knowledge Base Document Ingestion
# Ingests 23 narrative documents into PostgreSQL with pgvector

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Knowledge Base Document Ingestion" -ForegroundColor Green
Write-Host ""

# Check if kb-postgres is running
$containerStatus = docker ps --filter "name=kb-postgres" --format "{{.Status}}"
if (-not $containerStatus) {
    Write-Host "❌ kb-postgres container not running" -ForegroundColor Red
    Write-Host "Starting kb-postgres..." -ForegroundColor Yellow
    docker-compose -f docker-compose-kb.yml up -d
    Start-Sleep -Seconds 10
}

Write-Host "✅ PostgreSQL with pgvector ready" -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5443"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "Inn0vat1on!"
$env:POSTGRES_DB = "gaming_system_ai_core"

Write-Host "📚 Document Ingestion Pipeline:" -ForegroundColor Cyan
Write-Host "  - 7 main narrative docs (00-06)" -ForegroundColor Gray
Write-Host "  - 6 guides (emotional, magic, creatures, etc.)" -ForegroundColor Gray
Write-Host "  - 10 experiences (dungeons, portals, battles, etc.)" -ForegroundColor Gray
Write-Host "  = 23 total documents" -ForegroundColor Gray
Write-Host ""

# Run ingestion (with proper Python path)
Write-Host "🔄 Running ingestion..." -ForegroundColor Cyan
cd "services\knowledge_base"

# Check if dependencies installed
if (-not (Test-Path ".venv")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -q -r requirements.txt
} else {
    .\.venv\Scripts\Activate.ps1
}

# Run ingestion
python ingest_documents.py

Write-Host ""
Write-Host "="*70 -ForegroundColor Green
Write-Host "✅ KNOWLEDGE BASE INGESTION COMPLETE" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green
Write-Host ""
Write-Host "Verify:" -ForegroundColor Cyan
Write-Host '  docker exec kb-postgres psql -U postgres -d gaming_system_ai_core -c "SELECT COUNT(*) FROM narrative_documents;"' -ForegroundColor Gray
Write-Host ""

