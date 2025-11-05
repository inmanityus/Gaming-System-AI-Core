# Gold Tier Deployment Validation Script
# Validates Gold tier infrastructure deployment and health

param(
    [string]$Endpoint = "http://localhost:8001",
    [int]$TimeoutSec = 30
)

Write-Host "=== Gold Tier Deployment Validation ===" -ForegroundColor Cyan

$errors = @()
$warnings = @()

# Test 1: Health Check
Write-Host "`n[1/5] Testing health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$Endpoint/health" -TimeoutSec $TimeoutSec -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.status -eq "healthy") {
            Write-Host "  ✓ Health check passed" -ForegroundColor Green
        } else {
            $errors += "Health check returned status: $($data.status)"
        }
    } else {
        $errors += "Health check returned status code: $($response.StatusCode)"
    }
} catch {
    $errors += "Health check failed: $($_.Exception.Message)"
}

# Test 2: Readiness Check
Write-Host "`n[2/5] Testing readiness endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$Endpoint/ready" -TimeoutSec $TimeoutSec -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.ready -eq $true) {
            Write-Host "  ✓ Readiness check passed" -ForegroundColor Green
        } else {
            $warnings += "Readiness check returned: $($data.ready)"
        }
    } else {
        $errors += "Readiness check returned status code: $($response.StatusCode)"
    }
} catch {
    $errors += "Readiness check failed: $($_.Exception.Message)"
}

# Test 3: Latency Test
Write-Host "`n[3/5] Testing latency requirements (<16ms)..." -ForegroundColor Yellow
$latencies = @()
$successCount = 0

for ($i = 1; $i -le 10; $i++) {
    try {
        $payload = @{
            prompt = "Test NPC action"
            max_tokens = 8
            temperature = 0.1
        } | ConvertTo-Json
        
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri "$Endpoint/v1/completions" -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 1 -ErrorAction Stop
        $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
        
        if ($response.StatusCode -eq 200) {
            $latencies += $elapsed
            $successCount++
        }
    } catch {
        # Timeout or failure
    }
}

if ($latencies.Count -gt 0) {
    $latencies = $latencies | Sort-Object
    $p95 = $latencies[[Math]::Floor($latencies.Count * 0.95)]
    $avg = ($latencies | Measure-Object -Average).Average
    
    if ($p95 -lt 16) {
        Write-Host "  ✓ Latency test passed (p95: $([Math]::Round($p95, 2))ms, avg: $([Math]::Round($avg, 2))ms)" -ForegroundColor Green
    } else {
        $errors += "Latency p95 $([Math]::Round($p95, 2))ms exceeds 16ms requirement"
    }
} else {
    $errors += "Latency test failed: no successful requests"
}

# Test 4: Metrics Endpoint
Write-Host "`n[4/5] Testing metrics endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$Endpoint/metrics" -TimeoutSec $TimeoutSec -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Metrics endpoint accessible" -ForegroundColor Green
    } else {
        $warnings += "Metrics endpoint returned status code: $($response.StatusCode)"
    }
} catch {
    $warnings += "Metrics endpoint not accessible: $($_.Exception.Message)"
}

# Test 5: Inference Test
Write-Host "`n[5/5] Testing inference capability..." -ForegroundColor Yellow
try {
    $payload = @{
        prompt = "Action:"
        max_tokens = 4
        temperature = 0.0
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$Endpoint/v1/completions" -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 1 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.choices -and $data.choices.Count -gt 0) {
            Write-Host "  ✓ Inference test passed" -ForegroundColor Green
        } else {
            $errors += "Inference returned no choices"
        }
    } else {
        $errors += "Inference returned status code: $($response.StatusCode)"
    }
} catch {
    $errors += "Inference test failed: $($_.Exception.Message)"
}

# Summary
Write-Host "`n=== Validation Summary ===" -ForegroundColor Cyan
if ($errors.Count -eq 0) {
    Write-Host "✓ All critical tests passed" -ForegroundColor Green
    if ($warnings.Count -gt 0) {
        Write-Host "`nWarnings:" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    }
    exit 0
} else {
    Write-Host "✗ Validation failed with $($errors.Count) error(s):" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

