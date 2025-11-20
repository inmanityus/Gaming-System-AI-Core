param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-ml-cluster"
)

Write-Host "=== Installing Cluster Autoscaler ===" -ForegroundColor Cyan

# Load cluster configuration
if (-not (Test-Path "eks-cluster-info.json")) {
    Write-Host "[ERROR] eks-cluster-info.json not found. Run deploy-eks-cluster.ps1 first." -ForegroundColor Red
    exit 1
}

$clusterInfo = Get-Content "eks-cluster-info.json" | ConvertFrom-Json
$accountId = aws sts get-caller-identity --query Account --output text
$oidcProvider = ($clusterInfo.oidcIssuer -replace 'https://', '')

# Create IAM policy for Cluster Autoscaler
Write-Host "Creating IAM policy for Cluster Autoscaler..." -ForegroundColor Yellow

$autoscalerPolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeTags",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeLaunchTemplateVersions",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup"
            ],
            "Resource": ["*"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "eks:DescribeNodegroup"
            ],
            "Resource": ["*"]
        }
    ]
}
'@

$autoscalerPolicy | Out-File -FilePath "cluster-autoscaler-policy.json" -Encoding UTF8

# Create the policy
$policyArn = aws iam create-policy `
    --policy-name AmazonEKSClusterAutoscalerPolicy `
    --policy-document file://cluster-autoscaler-policy.json `
    --query "Policy.Arn" `
    --output text 2>$null

if (-not $policyArn -or $policyArn -eq "None") {
    $policyArn = "arn:aws:iam::${accountId}:policy/AmazonEKSClusterAutoscalerPolicy"
    Write-Host "✓ Using existing policy: $policyArn" -ForegroundColor Green
} else {
    Write-Host "✓ Created policy: $policyArn" -ForegroundColor Green
}

# Create IAM role for Cluster Autoscaler with IRSA
Write-Host "`nCreating IAM role for Cluster Autoscaler..." -ForegroundColor Yellow

$trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${accountId}:oidc-provider/${oidcProvider}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${oidcProvider}:sub": "system:serviceaccount:kube-system:cluster-autoscaler",
          "${oidcProvider}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
"@

$trustPolicy | Out-File -FilePath "autoscaler-trust-policy.json" -Encoding UTF8

# Create the role
aws iam create-role `
    --role-name AmazonEKSClusterAutoscalerRole `
    --assume-role-policy-document file://autoscaler-trust-policy.json `
    --description "IAM role for EKS Cluster Autoscaler" 2>&1 | Out-Null

# Attach the policy to the role
aws iam attach-role-policy `
    --role-name AmazonEKSClusterAutoscalerRole `
    --policy-arn $policyArn

$roleArn = "arn:aws:iam::${accountId}:role/AmazonEKSClusterAutoscalerRole"
Write-Host "✓ Created role: $roleArn" -ForegroundColor Green

# Create service account with IAM role annotation
Write-Host "`nCreating Kubernetes service account..." -ForegroundColor Yellow

$serviceAccount = @"
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    k8s-addon: cluster-autoscaler.addons.k8s.io
    k8s-app: cluster-autoscaler
  annotations:
    eks.amazonaws.com/role-arn: ${roleArn}
"@

$serviceAccount | kubectl apply -f -

# Deploy Cluster Autoscaler
Write-Host "`nDeploying Cluster Autoscaler..." -ForegroundColor Yellow

# Download and modify the deployment manifest
$autoscalerVersion = "v1.28.0"  # Match with EKS version
$manifestUrl = "https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml"

# Download the manifest
Invoke-WebRequest -Uri $manifestUrl -OutFile "cluster-autoscaler-autodiscover.yaml"

# Read and modify the manifest
$manifest = Get-Content "cluster-autoscaler-autodiscover.yaml" -Raw

# Replace the cluster name placeholder
$manifest = $manifest -replace '<YOUR CLUSTER NAME>', $ClusterName

# Add the balance-similar-node-groups and skip-nodes-with-system-pods flags
$manifest = $manifest -replace '(- --node-group-auto-discovery.*)', @"
`$1
        - --balance-similar-node-groups=true
        - --skip-nodes-with-system-pods=false
        - --scale-down-utilization-threshold=0.7
        - --scale-down-delay-after-add=10m
        - --scale-down-unneeded-time=10m
        - --max-node-provision-time=15m
"@

# Set the image to match cluster version
$manifest = $manifest -replace 'image: k8s.gcr.io/autoscaling/cluster-autoscaler:.*', "image: registry.k8s.io/autoscaling/cluster-autoscaler:${autoscalerVersion}"

# Save the modified manifest
$manifest | Out-File -FilePath "cluster-autoscaler-deployment.yaml" -Encoding UTF8

# Apply the deployment
kubectl apply -f cluster-autoscaler-deployment.yaml

# Add pod disruption budget
Write-Host "`nCreating Pod Disruption Budget..." -ForegroundColor Yellow
$pdb = @"
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
"@

$pdb | kubectl apply -f -

# Create horizontal pod autoscaler for the deployment
Write-Host "`nCreating Horizontal Pod Autoscaler..." -ForegroundColor Yellow
kubectl autoscale deployment cluster-autoscaler `
    -n kube-system `
    --min=1 `
    --max=3 `
    --cpu-percent=80

# Verify deployment
Write-Host "`nVerifying Cluster Autoscaler deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$deployment = kubectl get deployment cluster-autoscaler -n kube-system -o json | ConvertFrom-Json
$ready = $deployment.status.readyReplicas
$desired = $deployment.spec.replicas

if ($ready -eq $desired) {
    Write-Host "✓ Cluster Autoscaler is running ($ready/$desired replicas ready)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Cluster Autoscaler not fully ready ($ready/$desired replicas ready)" -ForegroundColor Yellow
}

# Check logs
Write-Host "`nChecking Cluster Autoscaler logs..." -ForegroundColor Yellow
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=20

# Create monitoring configmap
Write-Host "`nCreating monitoring configuration..." -ForegroundColor Yellow
$monitoringConfig = @"
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-status
  namespace: kube-system
data:
  autoscaler.yaml: |
    metrics:
      - nodes.count
      - nodes.ready
      - nodes.notready
      - unschedulable.pods.count
      - nodegroups.*.min_size
      - nodegroups.*.max_size
      - nodegroups.*.desired_capacity
      - scale_up.count
      - scale_down.count
      - failed_scale_ups.count
      - evicted_pods.count
"@

$monitoringConfig | kubectl apply -f -

# Clean up temporary files
Remove-Item -Path "cluster-autoscaler-policy.json", "autoscaler-trust-policy.json", "cluster-autoscaler-autodiscover.yaml" -ErrorAction SilentlyContinue

Write-Host "`n=== Cluster Autoscaler Installation Complete ===" -ForegroundColor Green
Write-Host "Cluster Autoscaler is monitoring node groups with tags:" -ForegroundColor Cyan
Write-Host "  - k8s.io/cluster-autoscaler/${ClusterName}: owned" -ForegroundColor White
Write-Host "  - k8s.io/cluster-autoscaler/enabled: true" -ForegroundColor White

Write-Host "`nMonitoring commands:" -ForegroundColor Yellow
Write-Host "  - Check status: kubectl get pods -n kube-system | grep cluster-autoscaler" -ForegroundColor White
Write-Host "  - View logs: kubectl logs -n kube-system -l app=cluster-autoscaler -f" -ForegroundColor White
Write-Host "  - Check metrics: kubectl top nodes" -ForegroundColor White
Write-Host "  - Test scaling: kubectl scale deployment <name> --replicas=<number>" -ForegroundColor White
