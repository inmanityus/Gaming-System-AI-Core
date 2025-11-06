# AI-002: vLLM Server Setup Script for AWS
# Purpose: Deploy vLLM server on AWS EKS/EC2 with GPU support
# Task: AI-002 from Phase 2 Core Integration

param(
    [string]$Region = "us-east-1",
    [string]$InstanceType = "g5.xlarge",  # NVIDIA A10G 24GB
    [string]$AmiId = "",
    [switch]$UseEKS = $false,
    [string]$EKSClusterName = "gaming-ai-gold-tier"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI-002: vLLM Server Setup (AWS)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
Write-Host "Checking AWS CLI..." -ForegroundColor Yellow
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found. Install: winget install Amazon.AWSCLI" -ForegroundColor Red
    exit 1
}
Write-Host "✓ AWS CLI found" -ForegroundColor Green

# Verify AWS credentials
Write-Host ""
Write-Host "Verifying AWS credentials..." -ForegroundColor Yellow
$identity = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}
Write-Host "✓ AWS credentials valid" -ForegroundColor Green
$accountId = (aws sts get-caller-identity --query Account --output text)
Write-Host "  Account: $accountId" -ForegroundColor Gray
Write-Host "  Region: $Region" -ForegroundColor Gray

if ($UseEKS) {
    Write-Host ""
    Write-Host "=== EKS Deployment Mode ===" -ForegroundColor Cyan
    Write-Host "Deploying vLLM to EKS cluster: $EKSClusterName" -ForegroundColor Yellow
    
    # Check if cluster exists
    $clusterExists = aws eks describe-cluster --name $EKSClusterName --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: EKS cluster '$EKSClusterName' not found" -ForegroundColor Red
        Write-Host "  Create cluster first: pwsh -File infrastructure/aws-cli/create-eks-gold-tier.ps1" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ EKS cluster found" -ForegroundColor Green
    
    # Configure kubectl
    Write-Host ""
    Write-Host "Configuring kubectl..." -ForegroundColor Yellow
    aws eks update-kubeconfig --name $EKSClusterName --region $Region
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ kubectl configured" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to configure kubectl" -ForegroundColor Red
        exit 1
    }
    
    # Create vLLM deployment YAML
    Write-Host ""
    Write-Host "Creating vLLM Kubernetes deployment..." -ForegroundColor Yellow
    $deploymentYaml = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-server
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-server
  template:
    metadata:
      labels:
        app: vllm-server
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-3.1-8B-Instruct"
        - name: ENABLE_LORA
          value: "true"
        - name: MAX_LORA_RANK
          value: "64"
        - name: MAX_LORAS
          value: "20"
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
spec:
  selector:
    app: vllm-server
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
"@
    
    $deploymentFile = "infrastructure/kubernetes/vllm/deployment.yaml"
    $deploymentDir = Split-Path $deploymentFile -Parent
    if (-not (Test-Path $deploymentDir)) {
        New-Item -ItemType Directory -Force -Path $deploymentDir | Out-Null
    }
    $deploymentYaml | Out-File -FilePath $deploymentFile -Encoding UTF8
    Write-Host "✓ Deployment YAML created: $deploymentFile" -ForegroundColor Green
    
    # Apply deployment
    Write-Host ""
    Write-Host "Deploying vLLM to EKS..." -ForegroundColor Yellow
    kubectl apply -f $deploymentFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ vLLM deployment created" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to deploy vLLM" -ForegroundColor Red
        exit 1
    }
    
    # Wait for deployment
    Write-Host ""
    Write-Host "Waiting for vLLM pods to be ready..." -ForegroundColor Yellow
    kubectl wait --for=condition=available --timeout=300s deployment/vllm-server
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ vLLM pods ready" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Deployment may still be starting" -ForegroundColor Yellow
    }
    
    # Get service endpoint
    Write-Host ""
    Write-Host "Getting service endpoint..." -ForegroundColor Yellow
    $serviceEndpoint = kubectl get service vllm-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>&1
    if ($serviceEndpoint -and $serviceEndpoint -ne "") {
        Write-Host "✓ vLLM service endpoint: $serviceEndpoint" -ForegroundColor Green
    } else {
        Write-Host "  Service endpoint pending (check with: kubectl get service vllm-service)" -ForegroundColor Yellow
    }
    
} else {
    Write-Host ""
    Write-Host "=== EC2 Deployment Mode ===" -ForegroundColor Cyan
    Write-Host "Deploying vLLM on EC2 instance: $InstanceType" -ForegroundColor Yellow
    
    # Create EC2 instance with GPU
    Write-Host ""
    Write-Host "Creating EC2 GPU instance..." -ForegroundColor Yellow
    
    # Get default VPC
    $vpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region
    if (-not $vpcId -or $vpcId -eq "None") {
        Write-Host "ERROR: No default VPC found" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Using VPC: $vpcId" -ForegroundColor Gray
    
    # Get subnet
    $subnetId = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[0].SubnetId" --output text --region $Region
    Write-Host "  Using Subnet: $subnetId" -ForegroundColor Gray
    
    # Get or create security group
    $sgName = "vllm-server-sg"
    $sgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=$sgName" --query "SecurityGroups[0].GroupId" --output text --region $Region
    if (-not $sgId -or $sgId -eq "None") {
        Write-Host "  Creating security group..." -ForegroundColor Gray
        $sgId = aws ec2 create-security-group --group-name $sgName --description "vLLM Server Security Group" --vpc-id $vpcId --region $Region --query "GroupId" --output text
        aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $Region | Out-Null
        Write-Host "  ✓ Security group created: $sgId" -ForegroundColor Green
    } else {
        Write-Host "  Using existing security group: $sgId" -ForegroundColor Gray
    }
    
    # Get GPU AMI (Deep Learning AMI or custom)
    if ([string]::IsNullOrEmpty($AmiId)) {
        Write-Host "  Finding GPU-enabled AMI..." -ForegroundColor Gray
        $AmiId = aws ec2 describe-images --owners amazon --filters "Name=name,Values=Deep Learning Base GPU AMI*" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text --region $Region
        if (-not $AmiId -or $AmiId -eq "None") {
            Write-Host "ERROR: No GPU AMI found. Specify --AmiId parameter" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "  Using AMI: $AmiId" -ForegroundColor Gray
    
    # Create instance
    Write-Host ""
    Write-Host "Launching EC2 instance..." -ForegroundColor Yellow
    $instanceId = aws ec2 run-instances `
        --image-id $AmiId `
        --instance-type $InstanceType `
        --subnet-id $subnetId `
        --security-group-ids $sgId `
        --associate-public-ip-address `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=vllm-server},{Key=Purpose,Value=AI-Inference}]" `
        --region $Region `
        --query "Instances[0].InstanceId" `
        --output text
    
    if ($LASTEXITCODE -eq 0 -and $instanceId) {
        Write-Host "✓ EC2 instance created: $instanceId" -ForegroundColor Green
        Write-Host "  Waiting for instance to be running..." -ForegroundColor Yellow
        aws ec2 wait instance-running --instance-ids $instanceId --region $Region
        Write-Host "  ✓ Instance running" -ForegroundColor Green
        
        # Get public IP
        $publicIp = aws ec2 describe-instances --instance-ids $instanceId --region $Region --query "Reservations[0].Instances[0].PublicIpAddress" --output text
        Write-Host "  Public IP: $publicIp" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. SSH to instance: ssh ec2-user@$publicIp" -ForegroundColor White
        Write-Host "  2. Install vLLM: pip install vllm" -ForegroundColor White
        Write-Host "  3. Start vLLM server: python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.1-8B-Instruct --port 8000" -ForegroundColor White
        Write-Host "  4. Test: curl http://$publicIp`:8000/health" -ForegroundColor White
    } else {
        Write-Host "ERROR: Failed to create EC2 instance" -ForegroundColor Red
        exit 1
    }
}

# Test vLLM server
Write-Host ""
Write-Host "Testing vLLM server..." -ForegroundColor Yellow
if ($UseEKS) {
    $testUrl = if ($serviceEndpoint) { "http://$serviceEndpoint:8000" } else { "http://localhost:8000" }
} else {
    $testUrl = "http://$publicIp:8000"
}

Start-Sleep -Seconds 10  # Wait for server to start

try {
    $healthCheck = Invoke-RestMethod -Uri "$testUrl/health" -Method Get -TimeoutSec 5
    Write-Host "✓ vLLM server is healthy" -ForegroundColor Green
    Write-Host "  Endpoint: $testUrl" -ForegroundColor Gray
} catch {
    Write-Host "⚠ vLLM server may not be ready yet" -ForegroundColor Yellow
    Write-Host "  Check logs and wait for server to start" -ForegroundColor Yellow
    Write-Host "  Endpoint: $testUrl" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "AI-002 Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "vLLM Server:" -ForegroundColor Cyan
if ($UseEKS) {
    Write-Host "  Deployment: EKS ($EKSClusterName)" -ForegroundColor White
    Write-Host "  Endpoint: $testUrl" -ForegroundColor White
    Write-Host "  Check status: kubectl get pods -l app=vllm-server" -ForegroundColor Gray
} else {
    Write-Host "  Instance: $instanceId ($InstanceType)" -ForegroundColor White
    Write-Host "  Public IP: $publicIp" -ForegroundColor White
    Write-Host "  Endpoint: $testUrl" -ForegroundColor White
}
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Verify server is running" -ForegroundColor White
Write-Host "  2. Test inference: curl -X POST $testUrl/v1/completions -H 'Content-Type: application/json' -d '{\"model\":\"llama3.1:8b\",\"prompt\":\"Hello\",\"max_tokens\":10}'" -ForegroundColor Gray
Write-Host "  3. Configure VLLM_BASE_URL environment variable" -ForegroundColor White
Write-Host ""

