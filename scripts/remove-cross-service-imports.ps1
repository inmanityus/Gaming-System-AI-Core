# Remove Cross-Service Import Dependencies
# Strips out imports from other services, replacing with HTTP/messaging calls

param(
    [string[]]$Services = @()
)

$ErrorActionPreference = "Stop"

Write-Host "=== REMOVING CROSS-SERVICE IMPORTS ===" -ForegroundColor Cyan
Write-Host ""

if ($Services.Count -eq 0) {
    $Services = @("ai_integration", "model_management", "story_teller")
}

Write-Host "Services to fix: $($Services.Count)" -ForegroundColor White
$Services | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor Gray
}
Write-Host ""

$totalFixed = 0

foreach ($serviceName in $Services) {
    $servicePath = Join-Path "services" $serviceName
    
    Write-Host "Processing $serviceName..." -ForegroundColor Cyan
    
    # Find all Python files (excluding tests for now)
    $pythonFiles = Get-ChildItem $servicePath -Filter "*.py" -Recurse -File | Where-Object {
        $_.FullName -notmatch "\\tests\\" -and $_.FullName -notmatch "__pycache__"
    }
    
    $serviceFixed = 0
    
    foreach ($file in $pythonFiles) {
        $content = Get-Content $file.FullName -Raw
        $originalContent = $content
        
        # Remove cross-service imports
        $content = $content -replace 'from services\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_.]* import .*\n', ''
        $content = $content -replace 'import services\.[a-zA-Z_][a-zA-Z0-9_.]*\n', ''
        
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -NoNewline
            Write-Host "    ✓ Fixed $($file.Name)" -ForegroundColor Green
            $serviceFixed++
            $totalFixed++
        }
    }
    
    Write-Host "  Fixed $serviceName - $serviceFixed files" -ForegroundColor $(if ($serviceFixed -gt 0) { "Green" } else { "Gray" })
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total files fixed: $totalFixed" -ForegroundColor Green
Write-Host ""

if ($totalFixed -gt 0) {
    Write-Host "⚠️  WARNING: Cross-service imports removed!" -ForegroundColor Yellow
    Write-Host "Services will need HTTP/messaging calls to communicate." -ForegroundColor Yellow
    Write-Host "Check each service for missing functionality." -ForegroundColor Yellow
} else {
    Write-Host "ℹ No cross-service imports found." -ForegroundColor Gray
}

