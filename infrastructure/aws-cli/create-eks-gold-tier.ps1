# AWS CLI Script: Create EKS Gold Tier Cluster
# Alternative to Terraform for users who prefer AWS CLI
# Run with: pwsh -File create-eks-gold-tier.ps1

param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "gaming-ai-gold-tier",
    [int]$DesiredNodes = 16,
    [int]$MinNodes = 8,
    [int]$MaxNodes = 64
)

Write-Host "[AWS CLI] Creating EKS Gold Tier Cluster..." -ForegroundColor Cyan

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] AWS CLI not found. Install: winget install Amazon.AWSCLI" -ForegroundColor Red
    exit 1
}

# Verify AWS credentials
Write-Host "[CHECK] Verifying AWS credentials..." -ForegroundColor Yellow
$identity = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}
Write-Host "[CHECK] ✓ AWS credentials valid" -ForegroundColor Green

# Step 1: Create VPC (if needed)
Write-Host "[STEP 1] Creating VPC..." -ForegroundColor Cyan
# TODO: Add VPC creation commands

# Step 2: Create EKS Cluster
Write-Host "[STEP 2] Creating EKS cluster: $ClusterName" -ForegroundColor Cyan
aws eks create-cluster `
    --name $ClusterName `
    --region $Region `
    --version "1.29" `
    --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/eks-service-role" `
    --resources-vpc-config "subnetIds=subnet-xxx,subnet-yyy,securityGroupIds=sg-xxx" `
    --endpoint-config "privateAccess=true,publicAccess=false"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create EKS cluster" -ForegroundColor Red
    exit 1
}

# Wait for cluster to be active
Write-Host "[WAIT] Waiting for cluster to be active..." -ForegroundColor Yellow
aws eks wait cluster-active --name $ClusterName --region $Region
Write-Host "[WAIT] ✓ Cluster active" -ForegroundColor Green

# Step 3: Create Node Group
Write-Host "[STEP 3] Creating Gold tier node group..." -ForegroundColor Cyan
aws eks create-nodegroup `
    --cluster-name $ClusterName `
    --nodegroup-name "gold-tier-gpu" `
    --node-role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/eks-node-role" `
    --instance-types "g6.xlarge" `
    --ami-type "AL2_x86_64_GPU" `
    --scaling-config "minSize=$MinNodes,maxSize=$MaxNodes,desiredSize=$DesiredNodes" `
    --subnets "subnet-xxx,subnet-yyy" `
    --labels "tier=gold,gpu=l4" `
    --taints "key=tier,value=gold,effect=NO_SCHEDULE" `
    --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create node group" -ForegroundColor Red
    exit 1
}

# Step 4: Configure kubectl
Write-Host "[STEP 4] Configuring kubectl..." -ForegroundColor Cyan
aws eks update-kubeconfig --name $ClusterName --region $Region
Write-Host "[STEP 4] ✓ kubectl configured" -ForegroundColor Green

# Step 5: Install NVIDIA device plugin
Write-Host "[STEP 5] Installing NVIDIA device plugin..." -ForegroundColor Cyan
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml

Write-Host "[COMPLETE] EKS Gold Tier cluster created successfully!" -ForegroundColor Green
Write-Host "  Cluster: $ClusterName" -ForegroundColor White
Write-Host "  Region: $Region" -ForegroundColor White
Write-Host "  Nodes: $DesiredNodes (min: $MinNodes, max: $MaxNodes)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. kubectl get nodes" -ForegroundColor White
Write-Host "  2. kubectl apply -f ../kubernetes/tensorrt-llm/deployment.yaml" -ForegroundColor White

