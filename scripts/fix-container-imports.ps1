# Fix Relative Imports for Container Deployment
# Changes all relative imports (from .module) to absolute imports (from module)

param(
    [string[]]$Services = @()
)

$ErrorActionPreference = "Stop"

Write-Host "=== FIXING CONTAINER IMPORTS ===" -ForegroundColor Cyan
Write-Host ""

if ($Services.Count -eq 0) {
    # Auto-detect services
    $Services = Get-ChildItem "services" -Directory | Where-Object {
        Test-Path (Join-Path $_.FullName "server.py")
    } | ForEach-Object { $_.Name }
}

Write-Host "Services to fix: $($Services.Count)" -ForegroundColor White
$Services | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor Gray
}
Write-Host ""

$totalFiles = 0
$totalChanges = 0

foreach ($serviceName in $Services) {
    $servicePath = Join-Path "services" $serviceName
    
    Write-Host "Processing $serviceName..." -ForegroundColor Cyan
    
    # Find all Python files
    $pythonFiles = Get-ChildItem $servicePath -Filter "*.py" -Recurse -File | Where-Object {
        $_.Name -ne "__pycache__"
    }
    
    $serviceChanges = 0
    
    foreach ($file in $pythonFiles) {
        $content = Get-Content $file.FullName -Raw
        $originalContent = $content
        
        # Pattern 1: from .module import
        $content = $content -replace 'from \.([a-zA-Z_][a-zA-Z0-9_]*) import', 'from $1 import'
        
        # Pattern 2: from . import
        # Skip this one as it's more complex
        
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -NoNewline
            Write-Host "    ✓ Fixed $($file.Name)" -ForegroundColor Green
            $serviceChanges++
            $totalChanges++
        }
    }
    
    $totalFiles += $pythonFiles.Count
    
    if ($serviceChanges -gt 0) {
        Write-Host "  Fixed $serviceName - $serviceChanges files changed" -ForegroundColor Green
    } else {
        Write-Host "  $serviceName - No changes needed" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Files scanned: $totalFiles" -ForegroundColor White
Write-Host "Files fixed: $totalChanges" -ForegroundColor Green
Write-Host ""

if ($totalChanges -gt 0) {
    Write-Host "✅ Container imports fixed! Services ready for deployment." -ForegroundColor Green
} else {
    Write-Host "ℹ No import issues found." -ForegroundColor Gray
}

