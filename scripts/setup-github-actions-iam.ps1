# Setup IAM roles for GitHub Actions OIDC authentication
param(
    [string]$GitHubOrg = "your-github-org",
    [string]$GitHubRepo = "your-repo-name",
    [string]$AWSAccountId = "695353648052",
    [string]$AWSRegion = "us-east-1"
)

Write-Host "Setting up IAM roles for GitHub Actions..." -ForegroundColor Green
Write-Host "Repository: $GitHubOrg/$GitHubRepo" -ForegroundColor Cyan
Write-Host "AWS Account: $AWSAccountId" -ForegroundColor Cyan

# Create OIDC provider if it doesn't exist
$oidcProviderArn = "arn:aws:iam::${AWSAccountId}:oidc-provider/token.actions.githubusercontent.com"
$existingProvider = aws iam get-open-id-connect-provider --open-id-connect-provider-arn $oidcProviderArn 2>$null

if (-not $existingProvider) {
    Write-Host "Creating OIDC provider..." -ForegroundColor Yellow
    aws iam create-open-id-connect-provider `
        --url https://token.actions.githubusercontent.com `
        --client-id-list sts.amazonaws.com `
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 `
        --region $AWSRegion
} else {
    Write-Host "OIDC provider already exists" -ForegroundColor Green
}

# Function to create IAM role
function New-GitHubActionsRole {
    param(
        [string]$RoleName,
        [string]$PolicyName,
        [string]$PolicyDocument,
        [string]$TrustPolicyDocument,
        [string]$Description
    )
    
    Write-Host "`nCreating role: $RoleName" -ForegroundColor Yellow
    
    # Check if role exists
    $existingRole = aws iam get-role --role-name $RoleName 2>$null
    
    if ($existingRole) {
        Write-Host "Role $RoleName already exists, updating..." -ForegroundColor Cyan
        
        # Update trust policy
        aws iam update-assume-role-policy `
            --role-name $RoleName `
            --policy-document $TrustPolicyDocument `
            --region $AWSRegion
    } else {
        # Create role
        aws iam create-role `
            --role-name $RoleName `
            --assume-role-policy-document $TrustPolicyDocument `
            --description $Description `
            --region $AWSRegion
    }
    
    # Attach or update inline policy
    aws iam put-role-policy `
        --role-name $RoleName `
        --policy-name $PolicyName `
        --policy-document $PolicyDocument `
        --region $AWSRegion
    
    Write-Host "Role $RoleName configured successfully" -ForegroundColor Green
}

# Trust policy for GitHub Actions
$trustPolicyTemplate = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Federated = $oidcProviderArn
            }
            Action = "sts:AssumeRoleWithWebIdentity"
            Condition = @{
                StringEquals = @{
                    "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
                }
                StringLike = @{
                    "token.actions.githubusercontent.com:sub" = "repo:$GitHubOrg/${GitHubRepo}:*"
                }
            }
        }
    )
}

# ECR Push Role
$ecrPushPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:CreateRepository",
                "ecr:DescribeRepositories"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

$trustPolicy = $trustPolicyTemplate | ConvertTo-Json -Depth 10 -Compress

New-GitHubActionsRole `
    -RoleName "github-actions-ecr-push" `
    -PolicyName "ECRPushPolicy" `
    -PolicyDocument $ecrPushPolicy `
    -TrustPolicyDocument $trustPolicy `
    -Description "Allows GitHub Actions to push images to ECR"

# Staging Deploy Role
$stagingDeployPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ecs:UpdateService",
                "ecs:DescribeServices",
                "ecs:RegisterTaskDefinition",
                "ecs:DescribeTaskDefinition",
                "ecs:ListTasks",
                "ecs:DescribeTasks",
                "ecs:ListServices",
                "ecs:DescribeClusters"
            )
            Resource = "*"
            Condition = @{
                StringEquals = @{
                    "ecs:cluster" = "arn:aws:ecs:${AWSRegion}:${AWSAccountId}:cluster/gaming-system-cluster-staging"
                }
            }
        },
        @{
            Effect = "Allow"
            Action = @(
                "ecs:RegisterTaskDefinition",
                "ecs:DescribeTaskDefinition"
            )
            Resource = "*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DescribeAlarms",
                "cloudwatch:DeleteAlarms"
            )
            Resource = "arn:aws:cloudwatch:${AWSRegion}:${AWSAccountId}:alarm:*-staging-*"
        },
        @{
            Effect = "Allow"
            Action = "iam:PassRole"
            Resource = @(
                "arn:aws:iam::${AWSAccountId}:role/ecsTaskExecutionRole",
                "arn:aws:iam::${AWSAccountId}:role/ecsTaskRole"
            )
        },
        @{
            Effect = "Allow"
            Action = @(
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

New-GitHubActionsRole `
    -RoleName "github-actions-deploy-staging" `
    -PolicyName "StagingDeployPolicy" `
    -PolicyDocument $stagingDeployPolicy `
    -TrustPolicyDocument $trustPolicy `
    -Description "Allows GitHub Actions to deploy to staging environment"

# Production Deploy Role (more restrictive)
$productionTrustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Federated = $oidcProviderArn
            }
            Action = "sts:AssumeRoleWithWebIdentity"
            Condition = @{
                StringEquals = @{
                    "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
                    "token.actions.githubusercontent.com:sub" = "repo:$GitHubOrg/${GitHubRepo}:environment:production"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

$productionDeployPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ecs:UpdateService",
                "ecs:DescribeServices",
                "ecs:RegisterTaskDefinition",
                "ecs:DescribeTaskDefinition",
                "ecs:ListTasks",
                "ecs:DescribeTasks",
                "ecs:ListServices",
                "ecs:DescribeClusters"
            )
            Resource = "*"
            Condition = @{
                StringEquals = @{
                    "ecs:cluster" = "arn:aws:ecs:${AWSRegion}:${AWSAccountId}:cluster/gaming-system-cluster"
                }
            }
        },
        @{
            Effect = "Allow"
            Action = @(
                "ecs:RegisterTaskDefinition",
                "ecs:DescribeTaskDefinition"
            )
            Resource = "*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DescribeAlarms",
                "cloudwatch:GetMetricStatistics"
            )
            Resource = "arn:aws:cloudwatch:${AWSRegion}:${AWSAccountId}:alarm:*-production-*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "codedeploy:CreateDeployment",
                "codedeploy:GetDeployment",
                "codedeploy:GetDeploymentConfig",
                "codedeploy:RegisterApplicationRevision"
            )
            Resource = @(
                "arn:aws:codedeploy:${AWSRegion}:${AWSAccountId}:deploymentgroup:gaming-system-*/production-*",
                "arn:aws:codedeploy:${AWSRegion}:${AWSAccountId}:application:gaming-system-*",
                "arn:aws:codedeploy:${AWSRegion}:${AWSAccountId}:deploymentconfig:*"
            )
        },
        @{
            Effect = "Allow"
            Action = "iam:PassRole"
            Resource = @(
                "arn:aws:iam::${AWSAccountId}:role/ecsTaskExecutionRole",
                "arn:aws:iam::${AWSAccountId}:role/ecsTaskRole"
            )
        },
        @{
            Effect = "Allow"
            Action = @(
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:ListImages"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

New-GitHubActionsRole `
    -RoleName "github-actions-deploy-production" `
    -PolicyName "ProductionDeployPolicy" `
    -PolicyDocument $productionDeployPolicy `
    -TrustPolicyDocument $productionTrustPolicy `
    -Description "Allows GitHub Actions to deploy to production environment"

Write-Host "`nIAM setup complete!" -ForegroundColor Green
Write-Host "`nRole ARNs:" -ForegroundColor Cyan
Write-Host "  ECR Push: arn:aws:iam::${AWSAccountId}:role/github-actions-ecr-push"
Write-Host "  Staging Deploy: arn:aws:iam::${AWSAccountId}:role/github-actions-deploy-staging"
Write-Host "  Production Deploy: arn:aws:iam::${AWSAccountId}:role/github-actions-deploy-production"

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Update workflow files with your GitHub org/repo: $GitHubOrg/$GitHubRepo"
Write-Host "2. Configure GitHub environments (staging, production)"
Write-Host "3. Commit and push workflow files to repository"
Write-Host "4. Test with a simple workflow run"
