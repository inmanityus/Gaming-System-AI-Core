# Multi-Tier Deployment Validation Script
# Validates all three tiers (Gold, Silver, Bronze)

param(
    [string]$GoldEndpoint = "http://localhost:8001",
    [string]$SilverEndpoint = "http://localhost:8002",
    [string]$BronzeEndpointName = "",
    [switch]$SkipBronze = $false
)

Write-Host "=== Multi-Tier Deployment Validation ===" -ForegroundColor Cyan
Write-Host ""

$overallSuccess = $true

# Validate Gold Tier
Write-Host "Validating Gold Tier..." -ForegroundColor Yellow
$goldScript = Join-Path $PSScriptRoot "validate-gold-tier.ps1"
if (Test-Path $goldScript) {
    & $goldScript -Endpoint $GoldEndpoint
    if ($LASTEXITCODE -ne 0) {
        $overallSuccess = $false
    }
} else {
    Write-Host "  ✗ Gold tier validation script not found" -ForegroundColor Red
    $overallSuccess = $false
}

Write-Host ""

# Validate Silver Tier
Write-Host "Validating Silver Tier..." -ForegroundColor Yellow
$silverScript = Join-Path $PSScriptRoot "validate-silver-tier.ps1"
if (Test-Path $silverScript) {
    & $silverScript -Endpoint $SilverEndpoint
    if ($LASTEXITCODE -ne 0) {
        $overallSuccess = $false
    }
} else {
    Write-Host "  ✗ Silver tier validation script not found" -ForegroundColor Red
    $overallSuccess = $false
}

Write-Host ""

# Validate Bronze Tier
if (-not $SkipBronze) {
    Write-Host "Validating Bronze Tier..." -ForegroundColor Yellow
    $bronzeScript = Join-Path $PSScriptRoot "validate-bronze-tier.ps1"
    if (Test-Path $bronzeScript) {
        if (-not [string]::IsNullOrEmpty($BronzeEndpointName)) {
            & $bronzeScript -EndpointName $BronzeEndpointName
        } else {
            & $bronzeScript
        }
        if ($LASTEXITCODE -ne 0) {
            $overallSuccess = $false
        }
    } else {
        Write-Host "  ✗ Bronze tier validation script not found" -ForegroundColor Red
        $overallSuccess = $false
    }
} else {
    Write-Host "Skipping Bronze tier validation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Overall Validation Result ===" -ForegroundColor Cyan
if ($overallSuccess) {
    Write-Host "✓ All tiers validated successfully" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Validation failed for one or more tiers" -ForegroundColor Red
    exit 1
}




