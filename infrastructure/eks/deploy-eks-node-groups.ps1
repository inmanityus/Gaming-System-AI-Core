param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-ml-cluster"
)

Write-Host "=== Deploying EKS Node Groups with GPU Support ===" -ForegroundColor Cyan

# Load cluster configuration
if (-not (Test-Path "eks-cluster-info.json")) {
    Write-Host "[ERROR] eks-cluster-info.json not found. Run deploy-eks-cluster.ps1 first." -ForegroundColor Red
    exit 1
}

$clusterInfo = Get-Content "eks-cluster-info.json" | ConvertFrom-Json
$accountId = aws sts get-caller-identity --query Account --output text
$nodeRoleArn = "arn:aws:iam::${accountId}:role/ai-core-eks-node-role"

# Verify node role exists
$nodeRole = aws iam get-role --role-name ai-core-eks-node-role --query "Role.Arn" --output text 2>$null
if (-not $nodeRole -or $nodeRole -eq "None") {
    Write-Host "[ERROR] Node role not found. Run create-eks-iam-roles.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Using node role: $nodeRoleArn" -ForegroundColor Green

# Define node group configurations
$nodeGroups = @(
    @{
        name = "system-nodes"
        instanceTypes = @("t3.large", "t3a.large")
        scalingConfig = @{
            minSize = 2
            maxSize = 10
            desiredSize = 3
        }
        labels = @{
            "node-type" = "system"
            "workload-type" = "general"
        }
        taints = @()
        amiType = "AL2_x86_64"
    },
    @{
        name = "ml-cpu-nodes"
        instanceTypes = @("c6i.4xlarge", "c6a.4xlarge", "c5.4xlarge")
        scalingConfig = @{
            minSize = 1
            maxSize = 20
            desiredSize = 2
        }
        labels = @{
            "node-type" = "ml-cpu"
            "workload-type" = "cpu-intensive"
        }
        taints = @()
        amiType = "AL2_x86_64"
    },
    @{
        name = "ml-gpu-nodes"
        instanceTypes = @("g6.2xlarge", "g6.4xlarge", "g5.2xlarge")
        scalingConfig = @{
            minSize = 0
            maxSize = 10
            desiredSize = 1
        }
        labels = @{
            "node-type" = "ml-gpu"
            "workload-type" = "gpu-intensive"
            "accelerator" = "nvidia-gpu"
        }
        taints = @(
            @{
                key = "nvidia.com/gpu"
                value = "true"
                effect = "NO_SCHEDULE"
            }
        )
        amiType = "AL2_x86_64_GPU"
    },
    @{
        name = "inference-gpu-nodes"
        instanceTypes = @("g5g.xlarge", "g5g.2xlarge")  # AWS Graviton with GPU
        scalingConfig = @{
            minSize = 0
            maxSize = 20
            desiredSize = 2
        }
        labels = @{
            "node-type" = "inference-gpu"
            "workload-type" = "inference"
            "accelerator" = "nvidia-gpu"
            "architecture" = "arm64"
        }
        taints = @(
            @{
                key = "inference-only"
                value = "true"
                effect = "NO_SCHEDULE"
            }
        )
        amiType = "AL2_ARM_64_GPU"
    }
)

# Parse subnet IDs
$privateSubnetIds = $clusterInfo.privateSubnetIds.Split(',')

# Deploy each node group
foreach ($nodeGroup in $nodeGroups) {
    Write-Host "`nDeploying node group: $($nodeGroup.name)" -ForegroundColor Yellow
    Write-Host "  Instance types: $($nodeGroup.instanceTypes -join ', ')" -ForegroundColor White
    Write-Host "  Scaling: min=$($nodeGroup.scalingConfig.minSize), max=$($nodeGroup.scalingConfig.maxSize), desired=$($nodeGroup.scalingConfig.desiredSize)" -ForegroundColor White
    
    # Build labels string
    $labelsStr = ($nodeGroup.labels.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ','
    
    # Build taints array
    if ($nodeGroup.taints.Count -gt 0) {
        $taintsJson = $nodeGroup.taints | ConvertTo-Json -Compress
    } else {
        $taintsJson = "[]"
    }
    
    # Create the node group
    $createCmd = @"
aws eks create-nodegroup \
    --cluster-name $ClusterName \
    --nodegroup-name $($nodeGroup.name) \
    --scaling-config minSize=$($nodeGroup.scalingConfig.minSize),maxSize=$($nodeGroup.scalingConfig.maxSize),desiredSize=$($nodeGroup.scalingConfig.desiredSize) \
    --subnets $($privateSubnetIds -join ' ') \
    --node-role $nodeRoleArn \
    --instance-types $($nodeGroup.instanceTypes -join ' ') \
    --ami-type $($nodeGroup.amiType) \
    --labels $labelsStr \
    --tags "Name=$($nodeGroup.name),Environment=production,Project=AI-Core" \
    --region $Region
"@
    
    if ($nodeGroup.taints.Count -gt 0) {
        $createCmd += " --taints '$taintsJson'"
    }
    
    $result = Invoke-Expression $createCmd 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Node group creation initiated: $($nodeGroup.name)" -ForegroundColor Green
    } else {
        if ($result -like "*ResourceInUseException*") {
            Write-Host "✓ Node group already exists: $($nodeGroup.name)" -ForegroundColor Yellow
        } else {
            Write-Host "[WARNING] Failed to create node group: $($nodeGroup.name)" -ForegroundColor Yellow
            Write-Host "Error: $result" -ForegroundColor Red
        }
    }
}

# Wait for node groups to be active
Write-Host "`nWaiting for node groups to be active..." -ForegroundColor Yellow
$allActive = $false
$maxWaitMinutes = 20
$startTime = Get-Date

while (-not $allActive -and ((Get-Date) - $startTime).TotalMinutes -lt $maxWaitMinutes) {
    $nodeGroupStatuses = aws eks list-nodegroups --cluster-name $ClusterName --query "nodegroups" --output json | ConvertFrom-Json
    
    $allActive = $true
    foreach ($ngName in $nodeGroupStatuses) {
        $status = aws eks describe-nodegroup `
            --cluster-name $ClusterName `
            --nodegroup-name $ngName `
            --query "nodegroup.status" `
            --output text
        
        if ($status -ne "ACTIVE" -and $status -ne "CREATE_FAILED") {
            $allActive = $false
            Write-Host -NoNewline "`r$ngName: $status " -ForegroundColor Yellow
        }
    }
    
    if (-not $allActive) {
        Start-Sleep -Seconds 30
    }
}

Write-Host "`n"

# Deploy NVIDIA device plugin for GPU nodes
Write-Host "`nDeploying NVIDIA device plugin..." -ForegroundColor Yellow
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml

# Verify nodes
Write-Host "`nVerifying node deployment..." -ForegroundColor Yellow
kubectl get nodes -L node-type,workload-type,accelerator

# Create GPU resource quota namespace
Write-Host "`nCreating ML workloads namespace with GPU quotas..." -ForegroundColor Yellow
$mlNamespace = @"
apiVersion: v1
kind: Namespace
metadata:
  name: ml-workloads
  labels:
    name: ml-workloads
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gpu-quota
  namespace: ml-workloads
spec:
  hard:
    requests.nvidia.com/gpu: "20"
    requests.cpu: "200"
    requests.memory: "1Ti"
    persistentvolumeclaims: "50"
"@

$mlNamespace | kubectl apply -f -

# Save node group configuration
$nodeGroupsInfo = @{
    clusterName = $ClusterName
    nodeGroups = $nodeGroups
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$nodeGroupsInfo | ConvertTo-Json -Depth 10 | Out-File -FilePath "eks-node-groups.json" -Encoding UTF8

Write-Host "`n=== Node Groups Deployment Complete ===" -ForegroundColor Green
Write-Host "Configuration saved to: eks-node-groups.json" -ForegroundColor Cyan

# Display node capacity
Write-Host "`nCluster Capacity:" -ForegroundColor Cyan
kubectl describe nodes | Select-String -Pattern "(Name:|Roles:|Capacity:|Allocatable:|nvidia.com/gpu:)" | Out-String

Write-Host "`nGPU Resources Available:" -ForegroundColor Yellow
kubectl get nodes -L accelerator | Where-Object { $_ -match "nvidia-gpu" }

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy sample ML workload: kubectl apply -f ml-workload-example.yaml" -ForegroundColor White
Write-Host "  2. Check GPU allocation: kubectl describe nodes | grep nvidia" -ForegroundColor White
Write-Host "  3. Monitor nodes: kubectl top nodes" -ForegroundColor White
