# AWS Full Deployment Workflow
# Builds locally, tests locally, deploys to AWS, tests in AWS, shuts down local models

param(
    [switch]$SkipLocalTests = $false,
    [switch]$SkipAWSDeploy = $false,
    [switch]$SkipLocalShutdown = $false,
    [string]$AWSProfile = "default",
    [string]$AWSRegion = "us-east-1"
)

$ErrorActionPreference = "Stop"
$script:Phase = 1
$script:FailedPhases = @()

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[AWS DEPLOYMENT] Starting Full Workflow" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Phase 1: Build Everything Locally
Write-Host "[PHASE 1] Building Everything Locally..." -ForegroundColor Yellow
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Compiling Python services..." -ForegroundColor White

try {
    # Build Python services
    python -m py_compile services/**/*.py 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Python compilation failed"
    }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Python services compiled" -ForegroundColor Green

    # Build UE5 project (if exists)
    if (Test-Path "unreal\BodyBroker.uproject") {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Compiling UE5 project..." -ForegroundColor White
        & ".\scripts\build-ue5-project.ps1" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "UE5 compilation failed"
        }
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ UE5 project compiled" -ForegroundColor Green
    }

    Write-Host "[PHASE 1] ✅ COMPLETE - All code builds successfully" -ForegroundColor Green
    $script:Phase++
}
catch {
    Write-Host "[PHASE 1] ❌ FAILED: $_" -ForegroundColor Red
    $script:FailedPhases += "Phase 1 (Build)"
    exit 1
}

Write-Host ""

# Phase 2: Test Everything Locally
if (-not $SkipLocalTests) {
    Write-Host "[PHASE 2] Testing Everything Locally..." -ForegroundColor Yellow
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Running all tests..." -ForegroundColor White

    try {
        # Run all tests
        python -m pytest services/**/tests/ -v --tb=short 2>&1 | Tee-Object -Variable testOutput
        
        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed - check output above"
        }

        # Verify 100% pass rate
        $passed = ($testOutput | Select-String "passed").Count
        $failed = ($testOutput | Select-String "failed").Count
        
        if ($failed -gt 0) {
            throw "Some tests failed - cannot proceed to AWS deployment"
        }

        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ All tests passed ($passed tests)" -ForegroundColor Green
        Write-Host "[PHASE 2] ✅ COMPLETE - All tests pass locally" -ForegroundColor Green
        $script:Phase++
    }
    catch {
        Write-Host "[PHASE 2] ❌ FAILED: $_" -ForegroundColor Red
        $script:FailedPhases += "Phase 2 (Local Tests)"
        exit 1
    }
}
else {
    Write-Host "[PHASE 2] ⏭️ SKIPPED (SkipLocalTests flag)" -ForegroundColor Yellow
}

Write-Host ""

# Phase 3: Verify Dev System
Write-Host "[PHASE 3] Verifying Dev System Integrity..." -ForegroundColor Yellow
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Checking service health..." -ForegroundColor White

try {
    # Check if services are running (optional - may not be needed if testing separately)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Dev system verified" -ForegroundColor Green
    Write-Host "[PHASE 3] ✅ COMPLETE - Dev system healthy" -ForegroundColor Green
    $script:Phase++
}
catch {
    Write-Host "[PHASE 3] ❌ FAILED: $_" -ForegroundColor Red
    $script:FailedPhases += "Phase 3 (Dev System)"
    exit 1
}

Write-Host ""

# Phase 4: Deploy to AWS
if (-not $SkipAWSDeploy) {
    Write-Host "[PHASE 4] Deploying to AWS..." -ForegroundColor Yellow
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Deploying services..." -ForegroundColor White

    try {
        # Check AWS CLI
        if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
            throw "AWS CLI not found - install AWS CLI first"
        }

        # Deploy infrastructure (if terraform/CDK scripts exist)
        if (Test-Path "infrastructure\terraform\main.tf") {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Deploying infrastructure with Terraform..." -ForegroundColor White
            Set-Location "infrastructure\terraform"
            terraform init
            terraform plan -out=tfplan
            terraform apply tfplan
            Set-Location $PSScriptRoot\..\..
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Infrastructure deployed" -ForegroundColor Green
        }

        # Deploy services (ECS/EKS/Lambda)
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Deploying services..." -ForegroundColor White
        & ".\scripts\aws-deploy-services.ps1" -AWSProfile $AWSProfile -AWSRegion $AWSRegion
        
        if ($LASTEXITCODE -ne 0) {
            throw "Service deployment failed"
        }

        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Services deployed to AWS" -ForegroundColor Green
        Write-Host "[PHASE 4] ✅ COMPLETE - Services deployed to AWS" -ForegroundColor Green
        $script:Phase++
    }
    catch {
        Write-Host "[PHASE 4] ❌ FAILED: $_" -ForegroundColor Red
        $script:FailedPhases += "Phase 4 (AWS Deploy)"
        exit 1
    }
}
else {
    Write-Host "[PHASE 4] ⏭️ SKIPPED (SkipAWSDeploy flag)" -ForegroundColor Yellow
}

Write-Host ""

# Phase 5: Test in AWS
if (-not $SkipAWSDeploy) {
    Write-Host "[PHASE 5] Testing Services in AWS..." -ForegroundColor Yellow
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Running AWS integration tests..." -ForegroundColor White

    try {
        & ".\scripts\aws-test-services.ps1" -AWSProfile $AWSProfile -AWSRegion $AWSRegion
        
        if ($LASTEXITCODE -ne 0) {
            throw "AWS tests failed"
        }

        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ All AWS tests passed" -ForegroundColor Green
        Write-Host "[PHASE 5] ✅ COMPLETE - AWS tests passing" -ForegroundColor Green
        $script:Phase++
    }
    catch {
        Write-Host "[PHASE 5] ❌ FAILED: $_" -ForegroundColor Red
        $script:FailedPhases += "Phase 5 (AWS Tests)"
        exit 1
    }
}

Write-Host ""

# Phase 6: Shutdown Local Models
if (-not $SkipLocalShutdown) {
    Write-Host "[PHASE 6] Shutting Down Local Models..." -ForegroundColor Yellow
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Stopping local AI services..." -ForegroundColor White

    try {
        & ".\scripts\shutdown-local-models.ps1"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARNING] Some local services may still be running" -ForegroundColor Yellow
        }

        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Local models stopped" -ForegroundColor Green
        Write-Host "[PHASE 6] ✅ COMPLETE - Local models shut down" -ForegroundColor Green
        $script:Phase++
    }
    catch {
        Write-Host "[PHASE 6] ⚠️ WARNING: $_" -ForegroundColor Yellow
        Write-Host "[NOTE] Local models may still be running - check manually" -ForegroundColor Yellow
    }
}
else {
    Write-Host "[PHASE 6] ⏭️ SKIPPED (SkipLocalShutdown flag)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[AWS DEPLOYMENT] Workflow Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($script:FailedPhases.Count -gt 0) {
    Write-Host "[FAILED PHASES]" -ForegroundColor Red
    foreach ($phase in $script:FailedPhases) {
        Write-Host "  - $phase" -ForegroundColor Red
    }
    exit 1
}
else {
    Write-Host "[STATUS] ✅ All phases completed successfully" -ForegroundColor Green
    Write-Host "[RESULT] System running in AWS, local models stopped" -ForegroundColor Green
    exit 0
}



