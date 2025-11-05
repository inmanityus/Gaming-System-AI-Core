# Start Language System gRPC Server
# Usage: pwsh -ExecutionPolicy Bypass -File scripts/start-grpc-server.ps1 [port]

param(
    [int]$Port = 50051
)

Write-Host "=== Starting Language System gRPC Server ===" -ForegroundColor Cyan
Write-Host "Port: $Port" -ForegroundColor Yellow

$ErrorActionPreference = "Stop"

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found - install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Start gRPC server
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Starting gRPC server on port $Port..." -ForegroundColor Green
python -m services.language_system.grpc.server_main $Port

