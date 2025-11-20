# Test script to verify API keys are loaded properly
Write-Host "`nTesting API Key Configuration..." -ForegroundColor Cyan

# First, load the secrets
$secretsScript = "./docs/security/.private/load-secrets.ps1"
if (Test-Path $secretsScript) {
    . $secretsScript
} else {
    Write-Host "❌ Secrets loading script not found!" -ForegroundColor Red
    exit 1
}

Write-Host "`nChecking loaded API keys..." -ForegroundColor Yellow

# Check each key
$keys = @(
    @{Name="OPENAI_API_KEY"; Prefix="sk-proj-"; Service="OpenAI"},
    @{Name="OPENROUTER_API_KEY"; Prefix="sk-or-v1-"; Service="OpenRouter"},
    @{Name="ANTHROPIC_API_KEY"; Prefix="sk-ant-api03-"; Service="Anthropic/Claude"}
)

$allGood = $true
foreach ($key in $keys) {
    $value = [System.Environment]::GetEnvironmentVariable($key.Name)
    if ($value) {
        if ($value.StartsWith($key.Prefix)) {
            $maskedKey = $value.Substring(0, 15) + "..." + $value.Substring($value.Length - 4)
            Write-Host "✅ $($key.Service): $maskedKey" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($key.Service): Key format unexpected" -ForegroundColor Yellow
            $allGood = $false
        }
    } else {
        Write-Host "❌ $($key.Service): Not found" -ForegroundColor Red
        $allGood = $false
    }
}

if ($allGood) {
    Write-Host "`n🎉 All API keys loaded successfully!" -ForegroundColor Green
    Write-Host "Your services can now use these keys safely." -ForegroundColor Cyan
} else {
    Write-Host "`n⚠️  Some keys are missing or incorrect." -ForegroundColor Yellow
    Write-Host "Make sure you saved them in: docs\security\.private\api-keys.env" -ForegroundColor White
}
