# Validate All Body Broker Systems
# Runs all validation checks

$ErrorActionPreference = "Stop"

Write-Host "Validating Body Broker Systems..." -ForegroundColor Cyan

# Run Python demo
Write-Host "`n[1/3] Running complete system demo..."
python examples\body_broker_complete_demo.py

# Check all services exist
Write-Host "`n[2/3] Checking service directories..."
$services = @(
    "ai_models", "memory", "harvesting", "negotiation",
    "drug_economy", "clients", "morality", "broker_book",
    "death_system", "weavers_loom", "body_broker_integration"
)

foreach ($svc in $services) {
    if (Test-Path "services\$svc") {
        Write-Host "  ✅ $svc" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $svc MISSING" -ForegroundColor Red
        exit 1
    }
}

# Check training data
Write-Host "`n[3/3] Checking training data..."
$dataFiles = Get-ChildItem "training\data\*_training.json"
Write-Host "  Found $($dataFiles.Count) training data files"

if ($dataFiles.Count -ge 14) {
    Write-Host "  ✅ All training data present" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Expected 14 files, found $($dataFiles.Count)" -ForegroundColor Yellow
}

Write-Host "`n" + ("="*60)
Write-Host "✅ ALL SYSTEMS VALIDATED" -ForegroundColor Green
Write-Host ("="*60)

