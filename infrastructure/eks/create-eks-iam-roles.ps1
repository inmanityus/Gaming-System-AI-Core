param(
    [string]$Region = "us-east-1"
)

Write-Host "Creating IAM roles for EKS cluster and nodes..." -ForegroundColor Cyan

# Create EKS service role
Write-Host "`nCreating EKS service role..." -ForegroundColor Yellow
$eksRoleTrustPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
'@

$eksRoleTrustPolicy | Out-File -FilePath "eks-trust-policy.json" -Encoding UTF8

# Create the EKS service role
aws iam create-role `
    --role-name ai-core-eks-service-role `
    --assume-role-policy-document file://eks-trust-policy.json `
    --description "Service role for AI Core EKS cluster" 2>&1 | Out-Null

# Attach required policies to EKS service role
aws iam attach-role-policy `
    --role-name ai-core-eks-service-role `
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy 2>&1 | Out-Null

aws iam attach-role-policy `
    --role-name ai-core-eks-service-role `
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSServicePolicy 2>&1 | Out-Null

Write-Host "✓ EKS service role created: ai-core-eks-service-role" -ForegroundColor Green

# Create EKS node role
Write-Host "`nCreating EKS node role..." -ForegroundColor Yellow
$nodeRoleTrustPolicy = @'
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

$nodeRoleTrustPolicy | Out-File -FilePath "node-trust-policy.json" -Encoding UTF8

# Create the node role
aws iam create-role `
    --role-name ai-core-eks-node-role `
    --assume-role-policy-document file://node-trust-policy.json `
    --description "Node role for AI Core EKS worker nodes" 2>&1 | Out-Null

# Attach required policies to node role
$nodePolicies = @(
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
)

foreach ($policy in $nodePolicies) {
    aws iam attach-role-policy `
        --role-name ai-core-eks-node-role `
        --policy-arn $policy 2>&1 | Out-Null
}

Write-Host "✓ EKS node role created: ai-core-eks-node-role" -ForegroundColor Green

# Create OIDC role for Karpenter
Write-Host "`nCreating Karpenter controller role..." -ForegroundColor Yellow
$karpenterTrustPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
'@

$karpenterTrustPolicy | Out-File -FilePath "karpenter-trust-policy.json" -Encoding UTF8

aws iam create-role `
    --role-name ai-core-karpenter-controller `
    --assume-role-policy-document file://karpenter-trust-policy.json `
    --description "Controller role for Karpenter autoscaling" 2>&1 | Out-Null

# Create and attach Karpenter policy
$karpenterPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Karpenter",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "iam:PassRole",
        "ec2:DescribeImages",
        "ec2:RunInstances",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeInstanceTypeOfferings",
        "ec2:DescribeAvailabilityZones",
        "ec2:DeleteLaunchTemplate",
        "ec2:CreateTags",
        "ec2:CreateLaunchTemplate",
        "ec2:CreateFleet",
        "ec2:DescribeSpotPriceHistory",
        "pricing:GetProducts"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TerminateInstances",
      "Effect": "Allow",
      "Action": "ec2:TerminateInstances",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "ec2:ResourceTag/karpenter.sh/provisioner-name": "*"
        }
      }
    }
  ]
}
'@

$karpenterPolicy | Out-File -FilePath "karpenter-policy.json" -Encoding UTF8

aws iam put-role-policy `
    --role-name ai-core-karpenter-controller `
    --policy-name KarpenterControllerPolicy `
    --policy-document file://karpenter-policy.json 2>&1 | Out-Null

Write-Host "✓ Karpenter controller role created: ai-core-karpenter-controller" -ForegroundColor Green

# Get role ARNs
$accountId = aws sts get-caller-identity --query Account --output text
$eksServiceRoleArn = "arn:aws:iam::${accountId}:role/ai-core-eks-service-role"
$eksNodeRoleArn = "arn:aws:iam::${accountId}:role/ai-core-eks-node-role"
$karpenterRoleArn = "arn:aws:iam::${accountId}:role/ai-core-karpenter-controller"

Write-Host "`nIAM roles created successfully!" -ForegroundColor Green
Write-Host "  EKS Service Role ARN: $eksServiceRoleArn" -ForegroundColor White
Write-Host "  EKS Node Role ARN: $eksNodeRoleArn" -ForegroundColor White
Write-Host "  Karpenter Role ARN: $karpenterRoleArn" -ForegroundColor White

# Clean up temporary files
Remove-Item -Path "eks-trust-policy.json", "node-trust-policy.json", "karpenter-trust-policy.json", "karpenter-policy.json" -ErrorAction SilentlyContinue

# Save role ARNs to config file
$roleConfig = @{
    eksServiceRoleArn = $eksServiceRoleArn
    eksNodeRoleArn = $eksNodeRoleArn
    karpenterRoleArn = $karpenterRoleArn
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$roleConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "eks-iam-roles.json" -Encoding UTF8
Write-Host "`nRole ARNs saved to eks-iam-roles.json" -ForegroundColor Cyan
