# Test All Public Pages
Write-Host "`n🌐 PHASE 1: TESTING ALL PUBLIC PAGES`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:3000"
$publicPages = @(
    @{ Url = "/"; Name = "Home" },
    @{ Url = "/services"; Name = "Services" },
    @{ Url = "/trainers"; Name = "Trainers" },
    @{ Url = "/testimonials"; Name = "Testimonials" },
    @{ Url = "/about"; Name = "About" },
    @{ Url = "/contact"; Name = "Contact" },
    @{ Url = "/ai-analyzer"; Name = "AI Analyzer" },
    @{ Url = "/login"; Name = "Login" },
    @{ Url = "/signup"; Name = "Signup" },
    @{ Url = "/extranet/for-trainers"; Name = "For Trainers" }
)

$passCount = 0
$failCount = 0

foreach ($page in $publicPages) {
    $url = "$baseUrl$($page.Url)"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ $($page.Name) page - Status 200" -ForegroundColor Green
            $passCount++
        } else {
            Write-Host "  ✗ $($page.Name) page - Status $($response.StatusCode)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ✗ $($page.Name) page - ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n📊 Results: $passCount passed, $failCount failed" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

if ($failCount -eq 0) {
    Write-Host "`n✅ PHASE 1 COMPLETE - All public pages accessible`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  PHASE 1 INCOMPLETE - Some pages failed`n" -ForegroundColor Yellow
    exit 1
}


