# Stub Cross-Service Dependencies
# Comments out cross-service imports so services can start independently
# Adds TODO markers for proper HTTP/messaging implementation

param(
    [string[]]$Services = @("ai_integration", "model_management", "story_teller")
)

Write-Host "=== STUBBING CROSS-SERVICE DEPENDENCIES ===" -ForegroundColor Cyan
Write-Host ""

$totalStubbed = 0

foreach ($serviceName in $Services) {
    $servicePath = Join-Path "services" $serviceName
    
    Write-Host "Processing $serviceName..." -ForegroundColor Cyan
    
    $pythonFiles = Get-ChildItem $servicePath -Filter "*.py" -Recurse -File | Where-Object {
        $_.FullName -notmatch "\\tests\\" -and $_.FullName -notmatch "__pycache__"
    }
    
    foreach ($file in $pythonFiles) {
        $lines = Get-Content $file.FullName
        $modified = $false
        $newLines = @()
        
        foreach ($line in $lines) {
            if ($line -match '^from services\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_.]* import') {
                # Comment out cross-service import
                $newLines += "# TODO: Replace with HTTP/messaging call"
                $newLines += "# $line"
                $modified = $true
                $totalStubbed++
            } elseif ($line -match '^import services\.[a-zA-Z_][a-zA-Z0-9_]*') {
                # Comment out cross-service import
                $newLines += "# TODO: Replace with HTTP/messaging call"
                $newLines += "# $line"
                $modified = $true
                $totalStubbed++
            } else {
                $newLines += $line
            }
        }
        
        if ($modified) {
            $newLines | Set-Content $file.FullName
            Write-Host "    ✓ Stubbed $($file.Name)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total imports stubbed: $totalStubbed" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  Services will start but some features may not work!" -ForegroundColor Yellow
Write-Host "Next step: Implement HTTP/messaging for stubbed imports" -ForegroundColor Cyan

