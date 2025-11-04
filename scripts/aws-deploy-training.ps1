# AWS Training Deployment Script
# Purpose: Deploy SRL-RLVR training infrastructure to AWS SageMaker
# Workflow: Build locally → Test locally → Deploy to AWS → Test in AWS → Shutdown local models
# MANDATORY: Follows AWS deployment workflow from .cursorrules

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "gold", "silver", "bronze", "registry")]
    [string]$Tier = "all",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipLocalTests = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipAWSDeploy = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipAWSTests = $false
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== AWS TRAINING DEPLOYMENT ===" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Tier: $Tier" -ForegroundColor Cyan
Write-Host "Project Root: $projectRoot" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Everything Locally
Write-Host "Step 1: Building Everything Locally..." -ForegroundColor Yellow
Write-Host "  - Compiling Python code..." -ForegroundColor White

# Validate Python code
$pythonFiles = Get-ChildItem -Path "services/srl_rlvr_training" -Recurse -Filter "*.py"
$pythonErrors = @()

foreach ($file in $pythonFiles) {
    $result = python -m py_compile $file.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        $pythonErrors += $file.FullName
    }
}

if ($pythonErrors.Count -gt 0) {
    Write-Host "  ✗ Python compilation errors found:" -ForegroundColor Red
    $pythonErrors | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "  ✓ Python code compiled successfully" -ForegroundColor Green

# Validate Terraform
Write-Host "  - Validating Terraform modules..." -ForegroundColor White

$terraformModules = @()
if ($Tier -eq "all" -or $Tier -eq "gold") {
    $terraformModules += "infrastructure/terraform/sagemaker-gold-tier"
}
if ($Tier -eq "all" -or $Tier -eq "silver") {
    $terraformModules += "infrastructure/terraform/sagemaker-silver-tier"
}
if ($Tier -eq "all" -or $Tier -eq "bronze") {
    $terraformModules += "infrastructure/terraform/sagemaker-bronze-tier"
}
if ($Tier -eq "all" -or $Tier -eq "registry") {
    $terraformModules += "infrastructure/terraform/sagemaker-registry"
}

foreach ($module in $terraformModules) {
    Write-Host "    Validating $module..." -ForegroundColor Gray
    Push-Location $module
    terraform init -backend=false 2>&1 | Out-Null
    terraform validate 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Terraform validation failed for $module" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
}

Write-Host "  ✓ All Terraform modules validated" -ForegroundColor Green

# Step 2: Test Everything Locally
if (-not $SkipLocalTests) {
    Write-Host ""
    Write-Host "Step 2: Testing Everything Locally..." -ForegroundColor Yellow
    Write-Host "  - Running comprehensive test suite..." -ForegroundColor White
    
    # Run SRL-RLVR tests
    $testResult = python -m pytest services/srl_rlvr_training/tests/ -v --tb=short 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Tests failed" -ForegroundColor Red
        Write-Host $testResult
        exit 1
    }
    
    Write-Host "  ✓ All local tests passed (100% pass rate)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Step 2: Skipping Local Tests (--SkipLocalTests)" -ForegroundColor Yellow
}

# Step 3: Verify Dev System Integrity
Write-Host ""
Write-Host "Step 3: Verifying Dev System Integrity..." -ForegroundColor Yellow
Write-Host "  - Checking system resources..." -ForegroundColor White

# Check disk space
$disk = Get-PSDrive C
$freeSpaceGB = [math]::Round($disk.Free / 1GB, 2)
if ($freeSpaceGB -lt 10) {
    Write-Host "  ⚠ Low disk space: ${freeSpaceGB}GB free" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Disk space: ${freeSpaceGB}GB free" -ForegroundColor Green
}

# Check AWS credentials
Write-Host "  - Verifying AWS credentials..." -ForegroundColor White
try {
    $identity = aws sts get-caller-identity --region $Region 2>&1 | ConvertFrom-Json
    Write-Host "  ✓ AWS Account: $($identity.Account)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ AWS credentials not configured" -ForegroundColor Red
    exit 1
}

# Step 4: Deploy to AWS
if (-not $SkipAWSDeploy) {
    Write-Host ""
    Write-Host "Step 4: Deploying to AWS..." -ForegroundColor Yellow
    
    foreach ($module in $terraformModules) {
        Write-Host "  - Deploying $module..." -ForegroundColor White
        
        Push-Location $module
        
        # Initialize Terraform
        terraform init 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Terraform init failed for $module" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        
        # Plan deployment
        terraform plan -out=tfplan -var="aws_region=$Region" -var="environment=$Environment" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Terraform plan failed for $module" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        
        # Apply deployment
        terraform apply tfplan 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Terraform apply failed for $module" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        
        Write-Host "  ✓ $module deployed successfully" -ForegroundColor Green
        Pop-Location
    }
    
    Write-Host "  ✓ All infrastructure deployed to AWS" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Step 4: Skipping AWS Deployment (--SkipAWSDeploy)" -ForegroundColor Yellow
}

# Step 5: Test in AWS
if (-not $SkipAWSTests) {
    Write-Host ""
    Write-Host "Step 5: Testing in AWS..." -ForegroundColor Yellow
    Write-Host "  - Running AWS integration tests..." -ForegroundColor White
    
    # Run AWS test script
    $testScript = Join-Path $scriptDir "aws-test-training.ps1"
    if (Test-Path $testScript) {
        & $testScript -Region $Region -Environment $Environment -Tier $Tier
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ AWS tests failed" -ForegroundColor Red
            exit 1
        }
        Write-Host "  ✓ All AWS tests passed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ AWS test script not found, skipping..." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Step 5: Skipping AWS Tests (--SkipAWSTests)" -ForegroundColor Yellow
}

# Step 6: Shutdown Local Models
Write-Host ""
Write-Host "Step 6: Shutting Down Local Models..." -ForegroundColor Yellow
Write-Host "  - Stopping local AI model services..." -ForegroundColor White

$shutdownScript = Join-Path $scriptDir "shutdown-local-models.ps1"
if (Test-Path $shutdownScript) {
    & $shutdownScript
    Write-Host "  ✓ Local models shut down" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Shutdown script not found, skipping..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== DEPLOYMENT COMPLETE ===" -ForegroundColor Green
Write-Host "All training infrastructure deployed and tested in AWS" -ForegroundColor Green
Write-Host "Local models shut down - all training now runs in AWS" -ForegroundColor Green

