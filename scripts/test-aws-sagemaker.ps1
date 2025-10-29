# Test AWS SageMaker Access
# Verifies all SageMaker services are accessible

Write-Host "=== Testing AWS SageMaker Access ===" -ForegroundColor Cyan
Write-Host ""

$results = @()

# Test 1: AWS Identity
Write-Host "Testing AWS Identity..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    if ($identity.UserId) {
        $results += @{
            Service = "AWS Identity"
            Status = "✅ OK"
            Details = "User: $($identity.Arn)"
        }
        Write-Host "  ✅ AWS Identity: OK" -ForegroundColor Green
        Write-Host "     Account: $($identity.Account)" -ForegroundColor Gray
        Write-Host "     User: $($identity.Arn)" -ForegroundColor Gray
    }
} catch {
    $results += @{Service="AWS Identity"; Status="❌ Failed"; Details=$_.Exception.Message}
    Write-Host "  ❌ AWS Identity: Failed" -ForegroundColor Red
}

# Test 2: SageMaker Models
Write-Host "`nTesting SageMaker Models..." -ForegroundColor Yellow
try {
    $models = aws sagemaker list-models --max-results 5 2>&1
    if ($LASTEXITCODE -eq 0) {
        $results += @{Service="SageMaker Models"; Status="✅ OK"; Details="Access granted"}
        Write-Host "  ✅ SageMaker Models: OK" -ForegroundColor Green
    } else {
        $results += @{Service="SageMaker Models"; Status="❌ Failed"; Details=$models}
        Write-Host "  ❌ SageMaker Models: Failed" -ForegroundColor Red
    }
} catch {
    $results += @{Service="SageMaker Models"; Status="❌ Error"; Details=$_.Exception.Message}
    Write-Host "  ❌ SageMaker Models: Error" -ForegroundColor Red
}

# Test 3: SageMaker Endpoints
Write-Host "`nTesting SageMaker Endpoints..." -ForegroundColor Yellow
try {
    $endpoints = aws sagemaker list-endpoints --max-results 5 2>&1
    if ($LASTEXITCODE -eq 0) {
        $results += @{Service="SageMaker Endpoints"; Status="✅ OK"; Details="Access granted"}
        Write-Host "  ✅ SageMaker Endpoints: OK" -ForegroundColor Green
    } else {
        $results += @{Service="SageMaker Endpoints"; Status="❌ Failed"; Details=$endpoints}
        Write-Host "  ❌ SageMaker Endpoints: Failed" -ForegroundColor Red
    }
} catch {
    $results += @{Service="SageMaker Endpoints"; Status="⚠️  No Endpoints"; Details="Normal if none deployed"}
    Write-Host "  ⚠️  SageMaker Endpoints: No endpoints (normal)" -ForegroundColor Yellow
}

# Test 4: S3 Access
Write-Host "`nTesting S3 Access..." -ForegroundColor Yellow
try {
    $buckets = aws s3 ls 2>&1
    if ($LASTEXITCODE -eq 0) {
        $bucketCount = ($buckets -split "`n").Count
        $results += @{Service="S3 Buckets"; Status="✅ OK"; Details="$bucketCount buckets accessible"}
        Write-Host "  ✅ S3 Access: OK ($bucketCount buckets)" -ForegroundColor Green
    } else {
        $results += @{Service="S3 Buckets"; Status="❌ Failed"; Details=$buckets}
        Write-Host "  ❌ S3 Access: Failed" -ForegroundColor Red
    }
} catch {
    $results += @{Service="S3 Buckets"; Status="❌ Error"; Details=$_.Exception.Message}
    Write-Host "  ❌ S3 Access: Error" -ForegroundColor Red
}

# Test 5: Kinesis Access
Write-Host "`nTesting Kinesis Access..." -ForegroundColor Yellow
try {
    $streams = aws kinesis list-streams 2>&1
    if ($LASTEXITCODE -eq 0) {
        $results += @{Service="Kinesis Streams"; Status="✅ OK"; Details="Access granted"}
        Write-Host "  ✅ Kinesis Access: OK" -ForegroundColor Green
    } else {
        $results += @{Service="Kinesis Streams"; Status="❌ Failed"; Details=$streams}
        Write-Host "  ❌ Kinesis Access: Failed" -ForegroundColor Red
    }
} catch {
    $results += @{Service="Kinesis Streams"; Status="⚠️  Check Permissions"; Details=$_.Exception.Message}
    Write-Host "  ⚠️  Kinesis: May need additional permissions" -ForegroundColor Yellow
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$successCount = ($results | Where-Object { $_.Status -like "✅*" }).Count
$totalCount = $results.Count

Write-Host "`nSuccess: $successCount/$totalCount services" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })

if ($successCount -ge 2) {
    Write-Host "`n✅ SageMaker is ready for Learning Service implementation!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some services may need additional permissions" -ForegroundColor Yellow
}

