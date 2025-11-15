# Bronze Tier Deployment Validation Script
# Validates Bronze tier SageMaker async inference deployment

param(
    [string]$EndpointName = "",
    [string]$Region = "us-east-1"
)

Write-Host "=== Bronze Tier Deployment Validation ===" -ForegroundColor Cyan

$errors = @()
$warnings = @()

# Check AWS CLI availability
Write-Host "`n[1/4] Checking AWS CLI availability..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ AWS CLI available" -ForegroundColor Green
    } else {
        $errors += "AWS CLI not available"
        exit 1
    }
} catch {
    $errors += "AWS CLI not found: $($_.Exception.Message)"
    exit 1
}

# Test 1: Endpoint Status
Write-Host "`n[2/4] Checking SageMaker endpoint status..." -ForegroundColor Yellow
if ([string]::IsNullOrEmpty($EndpointName)) {
    Write-Host "  ⚠ Endpoint name not provided, listing available endpoints..." -ForegroundColor Yellow
    try {
        $endpoints = aws sagemaker list-endpoints --region $Region --output json | ConvertFrom-Json
        $endpointNames = $endpoints.Endpoints | Where-Object { $_.EndpointName -like "*bronze*" -or $_.EndpointName -like "*async*" } | Select-Object -ExpandProperty EndpointName
        
        if ($endpointNames.Count -eq 0) {
            $warnings += "No Bronze tier endpoints found"
        } else {
            Write-Host "  Found endpoints:" -ForegroundColor White
            $endpointNames | ForEach-Object { Write-Host "    - $_" -ForegroundColor White }
            $EndpointName = $endpointNames[0]
        }
    } catch {
        $warnings += "Could not list endpoints: $($_.Exception.Message)"
    }
} else {
    try {
        $endpointInfo = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region --output json | ConvertFrom-Json
        $status = $endpointInfo.EndpointStatus
        
        if ($status -eq "InService") {
            Write-Host "  ✓ Endpoint '$EndpointName' is InService" -ForegroundColor Green
        } else {
            $warnings += "Endpoint '$EndpointName' status: $status"
        }
    } catch {
        $errors += "Could not describe endpoint '$EndpointName': $($_.Exception.Message)"
    }
}

# Test 2: Endpoint Configuration
Write-Host "`n[3/4] Checking endpoint configuration..." -ForegroundColor Yellow
if (-not [string]::IsNullOrEmpty($EndpointName)) {
    try {
        $endpointInfo = aws sagemaker describe-endpoint --endpoint-name $EndpointName --region $Region --output json | ConvertFrom-Json
        $configName = $endpointInfo.EndpointConfigName
        
        $configInfo = aws sagemaker describe-endpoint-config --endpoint-config-name $configName --region $Region --output json | ConvertFrom-Json
        
        if ($configInfo.AsyncInferenceConfig) {
            Write-Host "  ✓ Async inference configuration present" -ForegroundColor Green
        } else {
            $errors += "Async inference configuration not found"
        }
        
        if ($configInfo.OutputConfig) {
            Write-Host "  ✓ Output configuration present" -ForegroundColor Green
        } else {
            $warnings += "Output configuration not found"
        }
    } catch {
        $errors += "Could not check endpoint configuration: $($_.Exception.Message)"
    }
} else {
    $warnings += "Skipping configuration check (no endpoint name)"
}

# Test 3: S3 Access
Write-Host "`n[4/4] Checking S3 access for output retrieval..." -ForegroundColor Yellow
try {
    $buckets = aws s3 ls --region $Region 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ S3 access available" -ForegroundColor Green
    } else {
        $warnings += "S3 access check failed: $buckets"
    }
} catch {
    $warnings += "S3 access check failed: $($_.Exception.Message)"
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








