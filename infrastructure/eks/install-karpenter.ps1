param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-ml-cluster",
    [string]$KarpenterVersion = "v0.33.0"
)

Write-Host "=== Installing Karpenter for Advanced Autoscaling ===" -ForegroundColor Cyan

# Load cluster configuration
if (-not (Test-Path "eks-cluster-info.json")) {
    Write-Host "[ERROR] eks-cluster-info.json not found. Run deploy-eks-cluster.ps1 first." -ForegroundColor Red
    exit 1
}

$clusterInfo = Get-Content "eks-cluster-info.json" | ConvertFrom-Json
$accountId = aws sts get-caller-identity --query Account --output text
$oidcProvider = ($clusterInfo.oidcIssuer -replace 'https://', '')

Write-Host "Installing Karpenter version: $KarpenterVersion" -ForegroundColor White

# Create Karpenter namespace
Write-Host "`nCreating Karpenter namespace..." -ForegroundColor Yellow
kubectl create namespace karpenter 2>$null

# Tag subnets for Karpenter discovery
Write-Host "`nTagging subnets for Karpenter..." -ForegroundColor Yellow
$privateSubnetIds = $clusterInfo.privateSubnetIds.Split(',')

foreach ($subnetId in $privateSubnetIds) {
    aws ec2 create-tags `
        --resources $subnetId `
        --tags "Key=karpenter.sh/discovery,Value=$ClusterName" 2>&1 | Out-Null
}
Write-Host "✓ Tagged $($privateSubnetIds.Count) subnets" -ForegroundColor Green

# Tag security groups
aws ec2 create-tags `
    --resources $clusterInfo.securityGroupId `
    --tags "Key=karpenter.sh/discovery,Value=$ClusterName" 2>&1 | Out-Null

# Create IAM resources for Karpenter
Write-Host "`nCreating IAM resources for Karpenter..." -ForegroundColor Yellow

# Create Karpenter controller policy
$karpenterControllerPolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowScopedEC2InstanceActions",
            "Effect": "Allow",
            "Resource": [
                "arn:aws:ec2:*::image/*",
                "arn:aws:ec2:*::snapshot/*",
                "arn:aws:ec2:*:*:spot-instances-request/*",
                "arn:aws:ec2:*:*:security-group/*",
                "arn:aws:ec2:*:*:subnet/*",
                "arn:aws:ec2:*:*:launch-template/*"
            ],
            "Action": [
                "ec2:RunInstances",
                "ec2:CreateFleet"
            ]
        },
        {
            "Sid": "AllowScopedEC2InstanceActionsWithTags",
            "Effect": "Allow",
            "Resource": [
                "arn:aws:ec2:*:*:fleet/*",
                "arn:aws:ec2:*:*:instance/*",
                "arn:aws:ec2:*:*:volume/*",
                "arn:aws:ec2:*:*:network-interface/*",
                "arn:aws:ec2:*:*:launch-template/*"
            ],
            "Action": [
                "ec2:RunInstances",
                "ec2:CreateFleet",
                "ec2:CreateLaunchTemplate"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:RequestTag/karpenter.sh/cluster": "CLUSTER_NAME"
                }
            }
        },
        {
            "Sid": "AllowScopedResourceCreationTagging",
            "Effect": "Allow",
            "Resource": [
                "arn:aws:ec2:*:*:fleet/*",
                "arn:aws:ec2:*:*:instance/*",
                "arn:aws:ec2:*:*:volume/*",
                "arn:aws:ec2:*:*:network-interface/*",
                "arn:aws:ec2:*:*:launch-template/*"
            ],
            "Action": "ec2:CreateTags",
            "Condition": {
                "StringEquals": {
                    "aws:RequestTag/karpenter.sh/cluster": "CLUSTER_NAME",
                    "ec2:CreateAction": [
                        "RunInstances",
                        "CreateFleet",
                        "CreateLaunchTemplate"
                    ]
                }
            }
        },
        {
            "Sid": "AllowMachineMigrationTagging",
            "Effect": "Allow",
            "Resource": "arn:aws:ec2:*:*:instance/*",
            "Action": "ec2:CreateTags",
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/karpenter.sh/cluster": "CLUSTER_NAME",
                    "aws:RequestTag/karpenter.sh/cluster": "CLUSTER_NAME"
                }
            }
        },
        {
            "Sid": "AllowScopedDeletion",
            "Effect": "Allow",
            "Resource": [
                "arn:aws:ec2:*:*:instance/*",
                "arn:aws:ec2:*:*:launch-template/*"
            ],
            "Action": [
                "ec2:TerminateInstances",
                "ec2:DeleteLaunchTemplate"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/karpenter.sh/cluster": "CLUSTER_NAME"
                }
            }
        },
        {
            "Sid": "AllowRegionalReadActions",
            "Effect": "Allow",
            "Resource": "*",
            "Action": [
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeImages",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceTypeOfferings",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeLaunchTemplates",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSpotPriceHistory",
                "ec2:DescribeSubnets",
                "pricing:GetProducts",
                "ssm:GetParameter"
            ]
        },
        {
            "Sid": "AllowSSMReadActions",
            "Effect": "Allow",
            "Resource": "arn:aws:ssm:*:*:parameter/aws/service/*",
            "Action": "ssm:GetParameter"
        },
        {
            "Sid": "AllowPassingInstanceRole",
            "Effect": "Allow",
            "Resource": "arn:aws:iam::*:role/KarpenterNodeRole-*",
            "Action": "iam:PassRole"
        },
        {
            "Sid": "AllowScopedInstanceProfileCreationActions",
            "Effect": "Allow",
            "Resource": "*",
            "Action": "iam:CreateInstanceProfile"
        },
        {
            "Sid": "AllowScopedInstanceProfileTagActions",
            "Effect": "Allow",
            "Resource": "*",
            "Action": "iam:TagInstanceProfile",
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/karpenter.sh/cluster": "CLUSTER_NAME",
                    "aws:RequestTag/karpenter.sh/cluster": "CLUSTER_NAME"
                }
            }
        },
        {
            "Sid": "AllowScopedInstanceProfileActions",
            "Effect": "Allow",
            "Resource": "*",
            "Action": [
                "iam:AddRoleToInstanceProfile",
                "iam:RemoveRoleFromInstanceProfile",
                "iam:DeleteInstanceProfile"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/karpenter.sh/cluster": "CLUSTER_NAME"
                }
            }
        },
        {
            "Sid": "AllowInterruptionQueueActions",
            "Effect": "Allow",
            "Resource": "arn:aws:sqs:*:*:Karpenter-*",
            "Action": [
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage"
            ]
        }
    ]
}
'@.Replace('CLUSTER_NAME', $ClusterName)

$karpenterControllerPolicy | Out-File -FilePath "karpenter-controller-policy.json" -Encoding UTF8

# Create the policy
$policyArn = aws iam create-policy `
    --policy-name "KarpenterControllerPolicy-$ClusterName" `
    --policy-document file://karpenter-controller-policy.json `
    --query "Policy.Arn" `
    --output text 2>$null

if (-not $policyArn -or $policyArn -eq "None") {
    $policyArn = "arn:aws:iam::${accountId}:policy/KarpenterControllerPolicy-$ClusterName"
    Write-Host "✓ Using existing policy: $policyArn" -ForegroundColor Green
} else {
    Write-Host "✓ Created controller policy" -ForegroundColor Green
}

# Create Karpenter controller role with IRSA
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
                    "${oidcProvider}:sub": "system:serviceaccount:karpenter:karpenter",
                    "${oidcProvider}:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
"@

$trustPolicy | Out-File -FilePath "karpenter-trust-policy.json" -Encoding UTF8

aws iam create-role `
    --role-name "KarpenterControllerRole-$ClusterName" `
    --assume-role-policy-document file://karpenter-trust-policy.json `
    --description "Karpenter controller role for $ClusterName" 2>&1 | Out-Null

aws iam attach-role-policy `
    --role-name "KarpenterControllerRole-$ClusterName" `
    --policy-arn $policyArn

$controllerRoleArn = "arn:aws:iam::${accountId}:role/KarpenterControllerRole-$ClusterName"
Write-Host "✓ Created controller role" -ForegroundColor Green

# Create Karpenter node instance profile
Write-Host "`nCreating Karpenter node instance profile..." -ForegroundColor Yellow

# Create node role trust policy
$nodeTrustPolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
'@

$nodeTrustPolicy | Out-File -FilePath "karpenter-node-trust-policy.json" -Encoding UTF8

aws iam create-role `
    --role-name "KarpenterNodeRole-$ClusterName" `
    --assume-role-policy-document file://karpenter-node-trust-policy.json `
    --description "Karpenter node role for $ClusterName" 2>&1 | Out-Null

# Attach required policies to node role
$nodePolicies = @(
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
)

foreach ($policy in $nodePolicies) {
    aws iam attach-role-policy `
        --role-name "KarpenterNodeRole-$ClusterName" `
        --policy-arn $policy 2>&1 | Out-Null
}

# Create instance profile
aws iam create-instance-profile `
    --instance-profile-name "KarpenterNodeInstanceProfile-$ClusterName" 2>&1 | Out-Null

aws iam add-role-to-instance-profile `
    --instance-profile-name "KarpenterNodeInstanceProfile-$ClusterName" `
    --role-name "KarpenterNodeRole-$ClusterName" 2>&1 | Out-Null

$instanceProfileArn = "arn:aws:iam::${accountId}:instance-profile/KarpenterNodeInstanceProfile-$ClusterName"
Write-Host "✓ Created node instance profile" -ForegroundColor Green

# Create aws-auth ConfigMap entry for Karpenter nodes
Write-Host "`nUpdating aws-auth ConfigMap..." -ForegroundColor Yellow
$nodeRoleArn = "arn:aws:iam::${accountId}:role/KarpenterNodeRole-$ClusterName"

$awsAuthPatch = @"
- groups:
  - system:bootstrappers
  - system:nodes
  rolearn: $nodeRoleArn
  username: system:node:{{EC2PrivateDNSName}}
"@

# Save current aws-auth
kubectl get configmap aws-auth -n kube-system -o yaml > aws-auth-backup.yaml

# Update aws-auth (manual step for now)
Write-Host "[ACTION REQUIRED] Add the following to aws-auth ConfigMap mapRoles:" -ForegroundColor Yellow
Write-Host $awsAuthPatch -ForegroundColor White

# Install Karpenter using Helm
Write-Host "`nInstalling Karpenter via Helm..." -ForegroundColor Yellow

# Add Karpenter Helm repository
helm repo add karpenter https://charts.karpenter.sh/
helm repo update

# Install Karpenter
helm upgrade --install karpenter karpenter/karpenter `
    --version $KarpenterVersion `
    --namespace karpenter `
    --create-namespace `
    --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$controllerRoleArn `
    --set settings.aws.clusterName=$ClusterName `
    --set settings.aws.defaultInstanceProfile=$instanceProfileArn `
    --set settings.aws.interruptionQueueName="Karpenter-$ClusterName" `
    --wait

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Karpenter installed successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to install Karpenter" -ForegroundColor Red
    exit 1
}

# Create default Karpenter provisioners
Write-Host "`nCreating Karpenter provisioners..." -ForegroundColor Yellow

# General purpose provisioner
$generalProvisioner = @"
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: general-purpose
spec:
  template:
    metadata:
      labels:
        karpenter.sh/cluster: $ClusterName
        node-type: general
      annotations:
        karpenter.sh/do-not-disrupt: "false"
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: kubernetes.io/os
          operator: In
          values: ["linux"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
            - t3.medium
            - t3.large
            - t3.xlarge
            - t3a.medium
            - t3a.large
            - t3a.xlarge
            - m5.large
            - m5.xlarge
            - m5a.large
            - m5a.xlarge
      userData: |
        #!/bin/bash
        /etc/eks/bootstrap.sh $ClusterName
      amiFamily: AL2
      subnetSelectorTerms:
        - tags:
            karpenter.sh/discovery: $ClusterName
      securityGroupSelectorTerms:
        - tags:
            karpenter.sh/discovery: $ClusterName
      instanceStorePolicy: RAID0
  limits:
    cpu: 1000
    memory: 1000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 5m
---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  instanceStorePolicy: RAID0
  amiFamily: AL2
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: $ClusterName
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: $ClusterName
  instanceProfile: KarpenterNodeInstanceProfile-$ClusterName
  userData: |
    #!/bin/bash
    /etc/eks/bootstrap.sh $ClusterName
"@

# GPU provisioner for ML workloads
$gpuProvisioner = @"
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: ml-gpu
spec:
  template:
    metadata:
      labels:
        karpenter.sh/cluster: $ClusterName
        node-type: ml-gpu
        workload-type: gpu-intensive
      annotations:
        karpenter.sh/do-not-disrupt: "true"
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]  # GPUs typically on-demand for reliability
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: kubernetes.io/os
          operator: In
          values: ["linux"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
            - p3.2xlarge
            - p3.8xlarge
            - g4dn.xlarge
            - g4dn.2xlarge
            - g5.xlarge
            - g5.2xlarge
            - g6.xlarge
            - g6.2xlarge
      taints:
        - key: nvidia.com/gpu
          value: "true"
          effect: NoSchedule
      userData: |
        #!/bin/bash
        /etc/eks/bootstrap.sh $ClusterName
        # Install NVIDIA drivers
        sudo yum install -y kernel-devel-$(uname -r) kernel-headers-$(uname -r)
      amiFamily: AL2_x86_64_GPU
      subnetSelectorTerms:
        - tags:
            karpenter.sh/discovery: $ClusterName
      securityGroupSelectorTerms:
        - tags:
            karpenter.sh/discovery: $ClusterName
      instanceStorePolicy: RAID0
  limits:
    cpu: 500
    memory: 2000Gi
    nvidia.com/gpu: 50
  disruption:
    consolidationPolicy: WhenEmpty
    expireAfter: 30m
"@

$generalProvisioner | kubectl apply -f -
$gpuProvisioner | kubectl apply -f -

# Clean up temporary files
Remove-Item -Path "karpenter-controller-policy.json", "karpenter-trust-policy.json", "karpenter-node-trust-policy.json", "aws-auth-backup.yaml" -ErrorAction SilentlyContinue

# Verify Karpenter installation
Write-Host "`nVerifying Karpenter installation..." -ForegroundColor Yellow
kubectl get pods -n karpenter

# Save Karpenter configuration
$karpenterInfo = @{
    clusterName = $ClusterName
    controllerRoleArn = $controllerRoleArn
    instanceProfileArn = $instanceProfileArn
    nodeRoleArn = $nodeRoleArn
    version = $KarpenterVersion
    provisioners = @("general-purpose", "ml-gpu")
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$karpenterInfo | ConvertTo-Json -Depth 10 | Out-File -FilePath "karpenter-config.json" -Encoding UTF8

Write-Host "`n=== Karpenter Installation Complete ===" -ForegroundColor Green
Write-Host "Configuration saved to: karpenter-config.json" -ForegroundColor Cyan

Write-Host "`nKarpenter is now managing:" -ForegroundColor Yellow
Write-Host "  - General purpose nodes (spot + on-demand)" -ForegroundColor White
Write-Host "  - GPU nodes for ML workloads" -ForegroundColor White

Write-Host "`nMonitoring commands:" -ForegroundColor Yellow
Write-Host "  - Check Karpenter logs: kubectl logs -n karpenter -l app.kubernetes.io/name=karpenter -f" -ForegroundColor White
Write-Host "  - View provisioned nodes: kubectl get nodes -L karpenter.sh/cluster,node-type" -ForegroundColor White
Write-Host "  - Check node pools: kubectl get nodepool" -ForegroundColor White
Write-Host "  - View metrics: kubectl top nodes" -ForegroundColor White
