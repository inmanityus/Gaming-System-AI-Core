# Test Services in AWS
# Runs integration tests against deployed AWS services

param(
    [string]$AWSProfile = "default",
    [string]$AWSRegion = "us-east-1"
)

$ErrorActionPreference = "Stop"

Write-Host "[AWS TEST] Testing Services in AWS..." -ForegroundColor Cyan
Write-Host "[REGION] $AWSRegion" -ForegroundColor White
Write-Host "[PROFILE] $AWSProfile" -ForegroundColor White

# Get service endpoints from AWS
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Getting service endpoints..." -ForegroundColor White

# This would get endpoints from ECS/EKS/API Gateway
# For now, we'll test against known endpoints if configured
$serviceEndpoints = @{
    "story_teller" = $env:AWS_STORY_TELLER_URL
    "ai_integration" = $env:AWS_AI_INTEGRATION_URL
    "event_bus" = $env:AWS_EVENT_BUS_URL
    "time_manager" = $env:AWS_TIME_MANAGER_URL
    "weather_manager" = $env:AWS_WEATHER_MANAGER_URL
}

$testResults = @()
$failed = 0

foreach ($service in $serviceEndpoints.Keys) {
    $endpoint = $serviceEndpoints[$service]
    
    if (-not $endpoint) {
        Write-Host "[SKIP] $service - no endpoint configured" -ForegroundColor Yellow
        continue
    }

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Testing $service at $endpoint..." -ForegroundColor White
    
    try {
        # Test health endpoint
        $response = Invoke-WebRequest -Uri "$endpoint/health" -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ $service - Health check passed" -ForegroundColor Green
            $testResults += @{ Service = $service; Status = "PASSED" }
        }
        else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ $service - Health check failed (Status: $($response.StatusCode))" -ForegroundColor Red
            $testResults += @{ Service = $service; Status = "FAILED"; Error = "Status $($response.StatusCode)" }
            $failed++
        }
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ $service - Test failed: $_" -ForegroundColor Red
        $testResults += @{ Service = $service; Status = "FAILED"; Error = $_.Exception.Message }
        $failed++
    }
}

# Run integration tests if they exist
if (Test-Path "tests\aws_integration") {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Running AWS integration tests..." -ForegroundColor White
    
    # Set environment variables for tests
    $env:AWS_REGION = $AWSRegion
    $env:AWS_PROFILE = $AWSProfile
    
    python -m pytest tests/aws_integration/ -v --tb=short 2>&1 | Tee-Object -Variable testOutput
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] AWS integration tests failed" -ForegroundColor Red
        $failed++
    }
    else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ AWS integration tests passed" -ForegroundColor Green
    }
}

# Summary
Write-Host ""
Write-Host "[AWS TEST SUMMARY]" -ForegroundColor Cyan
foreach ($result in $testResults) {
    $color = if ($result.Status -eq "PASSED") { "Green" } else { "Red" }
    Write-Host "  $($result.Service): $($result.Status)" -ForegroundColor $color
    if ($result.Error) {
        Write-Host "    Error: $($result.Error)" -ForegroundColor Yellow
    }
}

if ($failed -eq 0) {
    Write-Host "[RESULT] ✅ All AWS services tested successfully" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "[RESULT] ❌ $failed service(s) failed testing" -ForegroundColor Red
    exit 1
}



