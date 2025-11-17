# AWS Full Deployment Script
# Purpose: Deploy Gaming System AI Core to AWS Production (Gold, Silver, Bronze tiers)
# Requirements: AWS CLI configured, kubectl installed, Terraform installed

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipInfrastructure = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipKubernetes = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$TestOnly = $false
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== AWS Full Deployment Script ===" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Project Root: $projectRoot" -ForegroundColor Cyan
Write-Host ""

# Step 1: Prerequisites Check
Write-Host "Step 1: Checking Prerequisites..." -ForegroundColor Yellow

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

$prereqs = @{
    "AWS CLI" = Test-Command "aws"
    "Terraform" = Test-Command "terraform"
    "kubectl" = Test-Command "kubectl"
}

$missing = @()
foreach ($prereq in $prereqs.GetEnumerator()) {
    if ($prereq.Value) {
        Write-Host "  ✓ $($prereq.Key)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($prereq.Key)" -ForegroundColor Red
        $missing += $prereq.Key
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
    
    if ($missing -contains "Terraform") {
        Write-Host "Installing Terraform..." -ForegroundColor Yellow
        winget install Hashicorp.Terraform
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install Terraform. Please install manually." -ForegroundColor Red
            exit 1
        }
        Write-Host "Terraform installed. Please restart this script." -ForegroundColor Yellow
        exit 0
    }
    
    if ($missing -contains "kubectl") {
        Write-Host "Installing kubectl..." -ForegroundColor Yellow
        winget install Kubernetes.kubectl
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install kubectl. Please install manually." -ForegroundColor Red
            exit 1
        }
        Write-Host "kubectl installed. Please restart this script." -ForegroundColor Yellow
        exit 0
    }
    
    exit 1
}

# Step 2: AWS Credentials Check
Write-Host ""
Write-Host "Step 2: Verifying AWS Credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --region $Region 2>&1 | ConvertFrom-Json
    Write-Host "  ✓ AWS Account: $($identity.Account)" -ForegroundColor Green
    Write-Host "  ✓ User ARN: $($identity.Arn)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ AWS credentials not configured or invalid" -ForegroundColor Red
    Write-Host "Please run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Step 3: Create S3 Bucket for Terraform State
Write-Host ""
Write-Host "Step 3: Creating S3 Bucket for Terraform State..." -ForegroundColor Yellow

$stateBucket = "gaming-ai-terraform-state"
$bucketExists = aws s3 ls "s3://$stateBucket" --region $Region 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Creating bucket: $stateBucket" -ForegroundColor Cyan
    aws s3 mb "s3://$stateBucket" --region $Region
    aws s3api put-bucket-versioning --bucket $stateBucket --versioning-configuration Status=Enabled --region $Region
    aws s3api put-bucket-encryption --bucket $stateBucket --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }' --region $Region
    Write-Host "  ✓ S3 bucket created and configured" -ForegroundColor Green
} else {
    Write-Host "  ✓ S3 bucket already exists" -ForegroundColor Green
}

# Step 4: Deploy Infrastructure
if (-not $SkipInfrastructure -and -not $TestOnly) {
    Write-Host ""
    Write-Host "Step 4: Deploying Infrastructure..." -ForegroundColor Yellow
    
    # Deploy Gold Tier (EKS)
    Write-Host ""
    Write-Host "  Deploying Gold Tier (EKS)..." -ForegroundColor Cyan
    $goldDir = Join-Path $projectRoot "infrastructure\terraform\eks-gold-tier"
    Set-Location $goldDir
    
    terraform init -backend-config="bucket=$stateBucket" -backend-config="region=$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Gold tier Terraform init failed" -ForegroundColor Red
        exit 1
    }
    
    terraform plan -out=tfplan -var="environment=$Environment" -var="aws_region=$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Gold tier Terraform plan failed" -ForegroundColor Red
        exit 1
    }
    
    terraform apply tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Gold tier Terraform apply failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ Gold tier infrastructure deployed" -ForegroundColor Green
    
    # Get Gold tier cluster name and configure kubectl
    $goldClusterName = terraform output -raw cluster_name 2>&1
    if ($goldClusterName) {
        Write-Host "  Configuring kubectl for Gold tier cluster: $goldClusterName" -ForegroundColor Cyan
        aws eks update-kubeconfig --region $Region --name $goldClusterName
    }
    
    # Deploy Silver Tier (EKS)
    Write-Host ""
    Write-Host "  Deploying Silver Tier (EKS)..." -ForegroundColor Cyan
    $silverDir = Join-Path $projectRoot "infrastructure\terraform\eks-silver-tier"
    Set-Location $silverDir
    
    terraform init -backend-config="bucket=$stateBucket" -backend-config="region=$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Silver tier Terraform init failed" -ForegroundColor Red
        exit 1
    }
    
    terraform plan -out=tfplan -var="environment=$Environment" -var="aws_region=$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Silver tier Terraform plan failed" -ForegroundColor Red
        exit 1
    }
    
    terraform apply tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Silver tier Terraform apply failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ Silver tier infrastructure deployed" -ForegroundColor Green
    
    # Get Silver tier cluster name and configure kubectl
    $silverClusterName = terraform output -raw cluster_name 2>&1
    if ($silverClusterName) {
        Write-Host "  Configuring kubectl for Silver tier cluster: $silverClusterName" -ForegroundColor Cyan
        aws eks update-kubeconfig --region $Region --name $silverClusterName --alias silver
    }
    
    # Deploy Bronze Tier (SageMaker)
    Write-Host ""
    Write-Host "  Deploying Bronze Tier (SageMaker)..." -ForegroundColor Cyan
    $bronzeDir = Join-Path $projectRoot "infrastructure\terraform\sagemaker-bronze-tier"
    Set-Location $bronzeDir
    
    terraform init -backend-config="bucket=$stateBucket" -backend-config="region=$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Bronze tier Terraform init failed" -ForegroundColor Red
        exit 1
    }
    
    terraform plan -out=tfplan -var="environment=$Environment" -var="aws_region=$Region"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Bronze tier Terraform plan failed" -ForegroundColor Red
        exit 1
    }
    
    terraform apply tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Bronze tier Terraform apply failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ Bronze tier infrastructure deployed" -ForegroundColor Green
}

# Step 5: Deploy Kubernetes Applications
if (-not $SkipKubernetes -and -not $TestOnly) {
    Write-Host ""
    Write-Host "Step 5: Deploying Kubernetes Applications..." -ForegroundColor Yellow
    
    # Deploy Gold Tier (TensorRT-LLM)
    Write-Host ""
    Write-Host "  Deploying Gold Tier (TensorRT-LLM)..." -ForegroundColor Cyan
    $goldK8sDir = Join-Path $projectRoot "infrastructure\kubernetes\tensorrt-llm"
    Set-Location $goldK8sDir
    
    # Switch to Gold cluster context
    if ($goldClusterName) {
        aws eks update-kubeconfig --region $Region --name $goldClusterName
    }
    
    kubectl apply -f deployment.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Gold tier Kubernetes deployment failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ Gold tier Kubernetes deployment complete" -ForegroundColor Green
    
    # Deploy Silver Tier (vLLM)
    Write-Host ""
    Write-Host "  Deploying Silver Tier (vLLM)..." -ForegroundColor Cyan
    $silverK8sDir = Join-Path $projectRoot "infrastructure\kubernetes\vllm"
    Set-Location $silverK8sDir
    
    # Switch to Silver cluster context
    if ($silverClusterName) {
        aws eks update-kubeconfig --region $Region --name $silverClusterName --alias silver
        kubectl config use-context silver
    }
    
    kubectl apply -f deployment.yaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Silver tier Kubernetes deployment failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  ✓ Silver tier Kubernetes deployment complete" -ForegroundColor Green
}

# Step 6: Testing
Write-Host ""
Write-Host "Step 6: Running Tests..." -ForegroundColor Yellow

# Test Gold Tier
if ($goldClusterName) {
    Write-Host ""
    Write-Host "  Testing Gold Tier..." -ForegroundColor Cyan
    aws eks update-kubeconfig --region $Region --name $goldClusterName
    kubectl get pods -n default
    kubectl get services -n default
}

# Test Silver Tier
if ($silverClusterName) {
    Write-Host ""
    Write-Host "  Testing Silver Tier..." -ForegroundColor Cyan
    aws eks update-kubeconfig --region $Region --name $silverClusterName --alias silver
    kubectl config use-context silver
    kubectl get pods -n default
    kubectl get services -n default
}

# Test Bronze Tier (SageMaker)
Write-Host ""
Write-Host "  Testing Bronze Tier (SageMaker)..." -ForegroundColor Cyan
$bronzeDir = Join-Path $projectRoot "infrastructure\terraform\sagemaker-bronze-tier"
Set-Location $bronzeDir
$endpointName = terraform output -raw endpoint_name 2>&1
if ($endpointName) {
    Write-Host "  ✓ Bronze tier endpoint: $endpointName" -ForegroundColor Green
    aws sagemaker describe-endpoint --endpoint-name $endpointName --region $Region
}

# Step 7: Summary
Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Deployed Infrastructure:" -ForegroundColor Cyan
Write-Host "  - Gold Tier (EKS): $goldClusterName" -ForegroundColor Green
Write-Host "  - Silver Tier (EKS): $silverClusterName" -ForegroundColor Green
Write-Host "  - Bronze Tier (SageMaker): $endpointName" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify all services are running: kubectl get pods --all-namespaces" -ForegroundColor White
Write-Host "  2. Test endpoints: Run integration tests" -ForegroundColor White
Write-Host "  3. Update router configuration with endpoint URLs" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot












