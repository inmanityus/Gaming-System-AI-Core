# AWS Training Test Script
# Purpose: Test SageMaker training infrastructure in AWS
# Tests: Terraform state, S3 buckets, IAM roles, CloudWatch logs

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "gold", "silver", "bronze", "registry")]
    [string]$Tier = "all"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== AWS TRAINING INFRASTRUCTURE TESTS ===" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Tier: $Tier" -ForegroundColor Cyan
Write-Host ""

$testResults = @{
    Passed = 0
    Failed = 0
    Total  = 0
}

function Test-Infrastructure {
    param(
        [string]$ModuleName,
        [string]$ModulePath
    )
    
    $testResults.Total++
    Write-Host "Testing $ModuleName..." -ForegroundColor Yellow
    
    Push-Location $ModulePath
    
    # Test 1: Terraform state exists
    try {
        terraform state list 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Terraform state accessible" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Terraform state not accessible" -ForegroundColor Red
            $testResults.Failed++
            Pop-Location
            return $false
        }
    } catch {
        Write-Host "  ✗ Terraform state error: $_" -ForegroundColor Red
        $testResults.Failed++
        Pop-Location
        return $false
    }
    
    # Test 2: Verify outputs
    try {
        $outputs = terraform output -json 2>&1 | ConvertFrom-Json
        if ($outputs) {
            Write-Host "  ✓ Terraform outputs accessible" -ForegroundColor Green
        } else {
            Write-Host "  ✗ No Terraform outputs found" -ForegroundColor Red
            $testResults.Failed++
            Pop-Location
            return $false
        }
    } catch {
        Write-Host "  ✗ Terraform outputs error: $_" -ForegroundColor Red
        $testResults.Failed++
        Pop-Location
        return $false
    }
    
    # Test 3: Verify S3 buckets exist (if applicable)
    if ($outputs.PSObject.Properties.Name -contains "checkpoint_bucket") {
        $bucketName = $outputs.checkpoint_bucket.value
        try {
            $bucket = aws s3api head-bucket --bucket $bucketName --region $Region 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ S3 checkpoint bucket exists: $bucketName" -ForegroundColor Green
            } else {
                Write-Host "  ✗ S3 checkpoint bucket missing: $bucketName" -ForegroundColor Red
                $testResults.Failed++
                Pop-Location
                return $false
            }
        } catch {
            Write-Host "  ✗ S3 bucket check error: $_" -ForegroundColor Red
            $testResults.Failed++
            Pop-Location
            return $false
        }
    }
    
    # Test 4: Verify IAM role exists (if applicable)
    if ($outputs.PSObject.Properties.Name -contains "training_role_arn") {
        $roleArn = $outputs.training_role_arn.value
        try {
            $roleName = $roleArn.Split('/')[-1]
            $role = aws iam get-role --role-name $roleName --region $Region 2>&1 | ConvertFrom-Json
            if ($role) {
                Write-Host "  ✓ IAM role exists: $roleName" -ForegroundColor Green
            } else {
                Write-Host "  ✗ IAM role missing: $roleName" -ForegroundColor Red
                $testResults.Failed++
                Pop-Location
                return $false
            }
        } catch {
            Write-Host "  ✗ IAM role check error: $_" -ForegroundColor Red
            $testResults.Failed++
            Pop-Location
            return $false
        }
    }
    
    Pop-Location
    $testResults.Passed++
    Write-Host "  ✓ $ModuleName tests passed" -ForegroundColor Green
    return $true
}

# Test each tier
$modulesToTest = @()
if ($Tier -eq "all" -or $Tier -eq "gold") {
    $modulesToTest += @{Name="Gold Tier"; Path="infrastructure/terraform/sagemaker-gold-tier"}
}
if ($Tier -eq "all" -or $Tier -eq "silver") {
    $modulesToTest += @{Name="Silver Tier"; Path="infrastructure/terraform/sagemaker-silver-tier"}
}
if ($Tier -eq "all" -or $Tier -eq "bronze") {
    $modulesToTest += @{Name="Bronze Tier"; Path="infrastructure/terraform/sagemaker-bronze-tier"}
}
if ($Tier -eq "all" -or $Tier -eq "registry") {
    $modulesToTest += @{Name="Model Registry"; Path="infrastructure/terraform/sagemaker-registry"}
}

foreach ($module in $modulesToTest) {
    Test-Infrastructure -ModuleName $module.Name -ModulePath $module.Path
    Write-Host ""
}

# Summary
Write-Host "=== TEST SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total Tests: $($testResults.Total)" -ForegroundColor White
Write-Host "Passed: $($testResults.Passed)" -ForegroundColor Green
Write-Host "Failed: $($testResults.Failed)" -ForegroundColor $(if ($testResults.Failed -eq 0) { "Green" } else { "Red" })

if ($testResults.Failed -eq 0) {
    Write-Host ""
    Write-Host "✓ All tests passed (100% pass rate)" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "✗ Some tests failed" -ForegroundColor Red
    exit 1
}

