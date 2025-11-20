param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-ml-cluster",
    [string]$KubernetesVersion = "1.28"
)

Write-Host "=== Deploying EKS Cluster for ML Workloads ===" -ForegroundColor Cyan
Write-Host "Cluster Name: $ClusterName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Kubernetes Version: $KubernetesVersion" -ForegroundColor White

# Verify AWS credentials
$identity = aws sts get-caller-identity --output json | ConvertFrom-Json
if (-not $identity) {
    Write-Host "[ERROR] AWS credentials not configured" -ForegroundColor Red
    exit 1
}
$accountId = $identity.Account
Write-Host "AWS Account: $accountId" -ForegroundColor Green

# Load existing infrastructure config
$vpcId = "vpc-0684c566fb7cc6b12"
$vpcConfigPath = Join-Path $PSScriptRoot "..\network\existing-vpc-config.json"
$vpcConfig = Get-Content $vpcConfigPath | ConvertFrom-Json -AsHashtable

# Get subnet IDs from actual AWS resources
Write-Host "`nDiscovering subnet configuration..." -ForegroundColor Yellow
$allSubnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[].{Id:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock}" --output json | ConvertFrom-Json

# Get public subnets (those with IGW routes)
$publicSubnetIds = aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$vpcId" --query "RouteTables[?Routes[?GatewayId && starts_with(GatewayId, 'igw-')]].Associations[].SubnetId" --output json | ConvertFrom-Json

# Separate private and public subnets
$publicSubnets = $allSubnets | Where-Object { $publicSubnetIds -contains $_.Id } | Select-Object -First 3
$privateSubnets = $allSubnets | Where-Object { $publicSubnetIds -notcontains $_.Id } | Select-Object -First 3

if ($privateSubnets.Count -lt 2 -or $publicSubnets.Count -lt 2) {
    Write-Host "[ERROR] Insufficient subnets found. Need at least 2 private and 2 public subnets." -ForegroundColor Red
    exit 1
}

$privateSubnetIds = ($privateSubnets | ForEach-Object { $_.Id }) -join ","
$publicSubnetIds = ($publicSubnets | ForEach-Object { $_.Id }) -join ","
$allSubnetIds = (($privateSubnets + $publicSubnets) | ForEach-Object { $_.Id }) -join ","

Write-Host "✓ Found private subnets: $($privateSubnets.Count)" -ForegroundColor Green
Write-Host "✓ Found public subnets: $($publicSubnets.Count)" -ForegroundColor Green

# Create security group for EKS control plane
Write-Host "`nCreating EKS cluster security group..." -ForegroundColor Yellow
$sgDescription = "Security group for AI Core EKS cluster control plane"
$sgResult = aws ec2 create-security-group `
    --group-name "ai-core-eks-cluster-sg" `
    --description $sgDescription `
    --vpc-id $vpcId `
    --output json 2>&1

if ($LASTEXITCODE -eq 0) {
    $eksSecurityGroupId = ($sgResult | ConvertFrom-Json).GroupId
    Write-Host "✓ Created security group: $eksSecurityGroupId" -ForegroundColor Green
} else {
    # Security group might already exist
    $eksSecurityGroupId = aws ec2 describe-security-groups `
        --filters "Name=group-name,Values=ai-core-eks-cluster-sg" "Name=vpc-id,Values=$vpcId" `
        --query "SecurityGroups[0].GroupId" `
        --output text
    Write-Host "✓ Using existing security group: $eksSecurityGroupId" -ForegroundColor Green
}

# Add ingress rules for EKS
aws ec2 authorize-security-group-ingress `
    --group-id $eksSecurityGroupId `
    --protocol tcp `
    --port 443 `
    --source-group $eksSecurityGroupId 2>&1 | Out-Null

# Check if IAM roles exist, create if needed
Write-Host "`nChecking IAM roles..." -ForegroundColor Yellow
$eksServiceRole = aws iam get-role --role-name ai-core-eks-service-role --query "Role.Arn" --output text 2>$null
if (-not $eksServiceRole -or $eksServiceRole -eq "None") {
    Write-Host "Creating IAM roles..." -ForegroundColor Yellow
    & "$PSScriptRoot\create-eks-iam-roles.ps1"
    $eksServiceRole = "arn:aws:iam::${accountId}:role/ai-core-eks-service-role"
}
Write-Host "✓ EKS Service Role: $eksServiceRole" -ForegroundColor Green

# Create EKS cluster
Write-Host "`nCreating EKS cluster..." -ForegroundColor Yellow
$clusterConfig = @{
    name = $ClusterName
    version = $KubernetesVersion
    roleArn = $eksServiceRole
    resourcesVpcConfig = @{
        subnetIds = $allSubnetIds.Split(',')
        securityGroupIds = @($eksSecurityGroupId)
        endpointPublicAccess = $true
        endpointPrivateAccess = $true
        publicAccessCidrs = @("0.0.0.0/0")
    }
    logging = @{
        clusterLogging = @(
            @{
                types = @("api", "audit", "authenticator", "controllerManager", "scheduler")
                enabled = $true
            }
        )
    }
    encryptionConfig = @(
        @{
            resources = @("secrets")
            provider = @{
                keyArn = $null  # Will be updated when KMS is configured
            }
        }
    )
    tags = @{
        Name = $ClusterName
        Environment = "production"
        Project = "AI-Core"
        Purpose = "ML-Workloads"
        ManagedBy = "PowerShell"
    }
}

# Save cluster config
$clusterConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "eks-cluster-config.json" -Encoding UTF8

# Create the cluster
$createResult = aws eks create-cluster `
    --name $ClusterName `
    --version $KubernetesVersion `
    --role-arn $eksServiceRole `
    --resources-vpc-config "subnetIds=$allSubnetIds,securityGroupIds=$eksSecurityGroupId,endpointPublicAccess=true,endpointPrivateAccess=true" `
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' `
    --tags "Name=$ClusterName,Environment=production,Project=AI-Core,Purpose=ML-Workloads" `
    --output json 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ EKS cluster creation initiated" -ForegroundColor Green
    
    # Wait for cluster to be active
    Write-Host "`nWaiting for cluster to be active (this may take 10-15 minutes)..." -ForegroundColor Yellow
    $startTime = Get-Date
    
    do {
        $clusterStatus = aws eks describe-cluster --name $ClusterName --query "cluster.status" --output text 2>$null
        $elapsedTime = [int]((Get-Date) - $startTime).TotalMinutes
        
        if ($clusterStatus -eq "ACTIVE") {
            Write-Host "`n✓ Cluster is active!" -ForegroundColor Green
            break
        } elseif ($clusterStatus -eq "FAILED") {
            Write-Host "`n[ERROR] Cluster creation failed" -ForegroundColor Red
            exit 1
        } else {
            Write-Host -NoNewline "`rCluster status: $clusterStatus (elapsed: $elapsedTime minutes)" -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
    } while ($elapsedTime -lt 30)
    
} else {
    if ($createResult -like "*ResourceInUseException*") {
        Write-Host "✓ Cluster already exists: $ClusterName" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Failed to create cluster: $createResult" -ForegroundColor Red
        exit 1
    }
}

# Get cluster details
$cluster = aws eks describe-cluster --name $ClusterName --output json | ConvertFrom-Json
$clusterEndpoint = $cluster.cluster.endpoint
$clusterCertificate = $cluster.cluster.certificateAuthority.data

Write-Host "`nCluster Details:" -ForegroundColor Cyan
Write-Host "  Endpoint: $clusterEndpoint" -ForegroundColor White
Write-Host "  Status: $($cluster.cluster.status)" -ForegroundColor White
Write-Host "  Version: $($cluster.cluster.version)" -ForegroundColor White

# Configure kubectl
Write-Host "`nConfiguring kubectl..." -ForegroundColor Yellow
aws eks update-kubeconfig --name $ClusterName --region $Region
Write-Host "✓ kubectl configured" -ForegroundColor Green

# Create OIDC provider for IRSA
Write-Host "`nCreating OIDC identity provider..." -ForegroundColor Yellow
$oidcUrl = $cluster.cluster.identity.oidc.issuer
$oidcId = $oidcUrl.Split('/')[-1]

# Check if OIDC provider already exists
$existingProvider = aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?ends_with(Arn, '$oidcId')].Arn" --output text
if (-not $existingProvider) {
    # Get thumbprint
    $thumbprint = aws eks describe-cluster --name $ClusterName --query "cluster.identity.oidc.issuer" --output text | 
        ForEach-Object { 
            $url = $_ -replace 'https://', ''
            echo | openssl s_client -servername $url -showcerts -connect "${url}:443" 2>/dev/null | 
            openssl x509 -fingerprint -noout | 
            ForEach-Object { ($_ -split '=')[1] -replace ':', '' }
        }
    
    aws iam create-open-id-connect-provider `
        --url $oidcUrl `
        --client-id-list "sts.amazonaws.com" `
        --thumbprint-list $thumbprint | Out-Null
    
    Write-Host "✓ OIDC provider created" -ForegroundColor Green
} else {
    Write-Host "✓ OIDC provider already exists" -ForegroundColor Green
}

# Save cluster configuration
$clusterInfo = @{
    clusterName = $ClusterName
    region = $Region
    endpoint = $clusterEndpoint
    certificateAuthority = $clusterCertificate
    oidcIssuer = $oidcUrl
    vpcId = $vpcId
    securityGroupId = $eksSecurityGroupId
    privateSubnetIds = $privateSubnetIds
    publicSubnetIds = $publicSubnetIds
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$clusterInfo | ConvertTo-Json -Depth 10 | Out-File -FilePath "eks-cluster-info.json" -Encoding UTF8

Write-Host "`n=== EKS Cluster Deployment Complete ===" -ForegroundColor Green
Write-Host "Cluster configuration saved to: eks-cluster-info.json" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy node groups: .\deploy-eks-node-groups.ps1" -ForegroundColor White
Write-Host "  2. Install cluster autoscaler: .\install-cluster-autoscaler.ps1" -ForegroundColor White
Write-Host "  3. Install Karpenter: .\install-karpenter.ps1" -ForegroundColor White
Write-Host "  4. Install Istio: .\install-istio.ps1" -ForegroundColor White
Write-Host "  5. Install monitoring: .\install-prometheus-grafana.ps1" -ForegroundColor White
