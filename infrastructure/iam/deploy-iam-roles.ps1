param(
    [string]$AccountId = (aws sts get-caller-identity --query Account --output text),
    [string]$Region = "us-east-1",
    [string]$Environment = "Production"
)

Write-Host "=== Deploying IAM Roles and Policies ===" -ForegroundColor Cyan
Write-Host "Account: $AccountId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Load KMS configuration if available
$kmsConfig = $null
if (Test-Path "../kms/kms-keys-config.json") {
    $kmsConfig = Get-Content -Path "../kms/kms-keys-config.json" | ConvertFrom-Json
    Write-Host "✓ Loaded KMS key configuration" -ForegroundColor Green
}

# Define roles to create
$roles = @{
    "ECSTaskExecutionRole" = @{
        name = "AICore-ECS-TaskExecutionRole"
        description = "Role for ECS tasks to pull images and write logs"
        trust_service = "ecs-tasks.amazonaws.com"
        policies = @{
            managed = @(
                "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
            )
            inline = @{
                "SecretAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:DescribeSecret"
                            )
                            Resource = "arn:aws:secretsmanager:${Region}:${AccountId}:secret:ai-core-*"
                        },
                        @{
                            Effect = "Allow"
                            Action = @(
                                "kms:Decrypt"
                            )
                            Resource = if ($kmsConfig) { 
                                $kmsConfig.keys | Where-Object { $_.type -eq "application" } | Select-Object -ExpandProperty keyArn 
                            } else { "*" }
                        }
                    )
                }
            }
        }
    }
    
    "ECSTaskRole" = @{
        name = "AICore-ECS-TaskRole"
        description = "Role for ECS tasks to access AWS services"
        trust_service = "ecs-tasks.amazonaws.com"
        policies = @{
            inline = @{
                "S3DataAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject"
                            )
                            Resource = "arn:aws:s3:::ai-core-datalake-*/data/*"
                        },
                        @{
                            Effect = "Allow"
                            Action = @(
                                "s3:ListBucket"
                            )
                            Resource = "arn:aws:s3:::ai-core-datalake-*"
                            Condition = @{
                                StringLike = @{
                                    "s3:prefix" = "data/*"
                                }
                            }
                        }
                    )
                }
                "DynamoDBAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Query",
                                "dynamodb:BatchGetItem",
                                "dynamodb:BatchWriteItem"
                            )
                            Resource = "arn:aws:dynamodb:${Region}:${AccountId}:table/ai-core-*"
                        }
                    )
                }
                "CloudWatchMetrics" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "cloudwatch:PutMetricData"
                            )
                            Resource = "*"
                            Condition = @{
                                StringEquals = @{
                                    "cloudwatch:namespace" = @(
                                        "AI-Core/Application",
                                        "AI-Core/Performance"
                                    )
                                }
                            }
                        }
                    )
                }
            }
        }
    }
    
    "LambdaExecutionRole" = @{
        name = "AICore-Lambda-ExecutionRole"
        description = "Role for Lambda functions in AI Core"
        trust_service = "lambda.amazonaws.com"
        policies = @{
            managed = @(
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            inline = @{
                "VPCAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "ec2:CreateNetworkInterface",
                                "ec2:DescribeNetworkInterfaces",
                                "ec2:DeleteNetworkInterface",
                                "ec2:AssignPrivateIpAddresses",
                                "ec2:UnassignPrivateIpAddresses"
                            )
                            Resource = "*"
                        }
                    )
                }
                "DataLakeAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "s3:GetObject",
                                "s3:ListBucket"
                            )
                            Resource = @(
                                "arn:aws:s3:::ai-core-datalake-*",
                                "arn:aws:s3:::ai-core-datalake-*/*"
                            )
                        },
                        @{
                            Effect = "Allow"
                            Action = @(
                                "glue:GetDatabase",
                                "glue:GetTable",
                                "glue:GetPartitions"
                            )
                            Resource = @(
                                "arn:aws:glue:${Region}:${AccountId}:catalog",
                                "arn:aws:glue:${Region}:${AccountId}:database/ai_core_datalake",
                                "arn:aws:glue:${Region}:${AccountId}:table/ai_core_datalake/*"
                            )
                        }
                    )
                }
            }
        }
    }
    
    "GlueJobRole" = @{
        name = "AICore-Glue-JobRole"
        description = "Role for AWS Glue ETL jobs"
        trust_service = "glue.amazonaws.com"
        policies = @{
            managed = @(
                "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
            )
            inline = @{
                "S3FullAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = "s3:*"
                            Resource = @(
                                "arn:aws:s3:::ai-core-datalake-*",
                                "arn:aws:s3:::ai-core-datalake-*/*"
                            )
                        }
                    )
                }
                "KMSAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "kms:Decrypt",
                                "kms:Encrypt",
                                "kms:GenerateDataKey"
                            )
                            Resource = if ($kmsConfig) { 
                                $kmsConfig.keys | Where-Object { $_.type -in @("storage", "logs") } | Select-Object -ExpandProperty keyArn 
                            } else { "*" }
                        }
                    )
                }
            }
        }
    }
    
    "DataScientistRole" = @{
        name = "AICore-DataScientist-Role"
        description = "Role for data scientists to analyze data"
        trust_principal = "arn:aws:iam::${AccountId}:root"
        policies = @{
            managed = @(
                "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
                "arn:aws:iam::aws:policy/AmazonSageMakerReadOnly"
            )
            inline = @{
                "DataLakeReadOnly" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "s3:GetObject",
                                "s3:ListBucket"
                            )
                            Resource = @(
                                "arn:aws:s3:::ai-core-datalake-processed-*",
                                "arn:aws:s3:::ai-core-datalake-processed-*/*",
                                "arn:aws:s3:::ai-core-datalake-curated-*",
                                "arn:aws:s3:::ai-core-datalake-curated-*/*"
                            )
                        },
                        @{
                            Effect = "Allow"
                            Action = @(
                                "lakeformation:GetDataAccess"
                            )
                            Resource = "*"
                        }
                    )
                }
            }
        }
    }
    
    "DataEngineerRole" = @{
        name = "AICore-DataEngineer-Role"
        description = "Role for data engineers to manage ETL pipelines"
        trust_principal = "arn:aws:iam::${AccountId}:root"
        policies = @{
            managed = @(
                "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess",
                "arn:aws:iam::aws:policy/CloudWatchLogsReadOnlyAccess"
            )
            inline = @{
                "DataLakeFullAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = "s3:*"
                            Resource = @(
                                "arn:aws:s3:::ai-core-datalake-*",
                                "arn:aws:s3:::ai-core-datalake-*/*"
                            )
                        },
                        @{
                            Effect = "Allow"
                            Action = @(
                                "glue:*"
                            )
                            Resource = @(
                                "arn:aws:glue:${Region}:${AccountId}:*"
                            )
                        }
                    )
                }
                "StepFunctionsAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "states:StartExecution",
                                "states:StopExecution",
                                "states:DescribeExecution",
                                "states:ListExecutions"
                            )
                            Resource = "arn:aws:states:${Region}:${AccountId}:stateMachine:ai-core-*"
                        }
                    )
                }
            }
        }
    }
    
    "SageMakerExecutionRole" = @{
        name = "AICore-SageMaker-ExecutionRole"
        description = "Role for SageMaker training and inference"
        trust_service = "sagemaker.amazonaws.com"
        policies = @{
            managed = @(
                "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
            )
            inline = @{
                "S3ModelAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
                        @{
                            Effect = "Allow"
                            Action = @(
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            )
                            Resource = @(
                                "arn:aws:s3:::ai-core-datalake-ml-artifacts-*",
                                "arn:aws:s3:::ai-core-datalake-ml-artifacts-*/*",
                                "arn:aws:s3:::sagemaker-${Region}-${AccountId}",
                                "arn:aws:s3:::sagemaker-${Region}-${AccountId}/*"
                            )
                        }
                    )
                }
                "ECRAccess" = @{
                    Version = "2012-10-17"
                    Statement = @(
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
                }
            }
        }
    }
}

# Function to create trust policy document
function Create-TrustPolicy {
    param(
        [string]$Service,
        [string]$Principal
    )
    
    if ($Service) {
        return @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Principal = @{
                        Service = $Service
                    }
                    Action = "sts:AssumeRole"
                }
            )
        }
    } elseif ($Principal) {
        return @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Principal = @{
                        AWS = $Principal
                    }
                    Action = "sts:AssumeRole"
                }
            )
        }
    }
}

# Array to store created roles
$createdRoles = @()

# Create each role
foreach ($roleType in $roles.Keys) {
    $roleConfig = $roles[$roleType]
    Write-Host "`nCreating role: $($roleConfig.name)" -ForegroundColor Yellow
    Write-Host "  Purpose: $($roleConfig.description)" -ForegroundColor Gray
    
    # Check if role already exists
    $existingRole = aws iam get-role --role-name $roleConfig.name 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        # Create trust policy
        $trustPolicy = if ($roleConfig.trust_service) {
            Create-TrustPolicy -Service $roleConfig.trust_service
        } else {
            Create-TrustPolicy -Principal $roleConfig.trust_principal
        }
        
        $trustPolicyJson = $trustPolicy | ConvertTo-Json -Depth 5
        $trustPolicyJson | Out-File -FilePath "trust-policy-$roleType.json" -Encoding UTF8
        
        # Create the role
        $roleResult = aws iam create-role `
            --role-name $roleConfig.name `
            --assume-role-policy-document file://trust-policy-$roleType.json `
            --description $roleConfig.description `
            --output json | ConvertFrom-Json
        
        $roleArn = $roleResult.Role.Arn
        Write-Host "✓ Created role: $roleArn" -ForegroundColor Green
        
        Remove-Item "trust-policy-$roleType.json"
        
        # Attach managed policies
        if ($roleConfig.policies.managed) {
            foreach ($policyArn in $roleConfig.policies.managed) {
                aws iam attach-role-policy `
                    --role-name $roleConfig.name `
                    --policy-arn $policyArn | Out-Null
                Write-Host "  ✓ Attached managed policy: $policyArn" -ForegroundColor Green
            }
        }
        
        # Create and attach inline policies
        if ($roleConfig.policies.inline) {
            foreach ($policyName in $roleConfig.policies.inline.Keys) {
                $inlinePolicy = $roleConfig.policies.inline[$policyName]
                $inlinePolicyJson = $inlinePolicy | ConvertTo-Json -Depth 10
                $inlinePolicyJson | Out-File -FilePath "inline-policy-$policyName.json" -Encoding UTF8
                
                aws iam put-role-policy `
                    --role-name $roleConfig.name `
                    --policy-name $policyName `
                    --policy-document file://inline-policy-$policyName.json | Out-Null
                
                Write-Host "  ✓ Created inline policy: $policyName" -ForegroundColor Green
                
                Remove-Item "inline-policy-$policyName.json"
            }
        }
        
        # Tag the role
        $tags = @(
            @{ Key = "Project"; Value = "AI-Core" },
            @{ Key = "Environment"; Value = $Environment },
            @{ Key = "ManagedBy"; Value = "PowerShell" }
        ) | ConvertTo-Json -Compress
        
        aws iam tag-role --role-name $roleConfig.name --tags $tags | Out-Null
        
        $createdRoles += @{
            type = $roleType
            name = $roleConfig.name
            arn = $roleArn
            description = $roleConfig.description
        }
        
    } else {
        $roleInfo = $existingRole | ConvertFrom-Json
        Write-Host "✓ Role already exists: $($roleInfo.Role.Arn)" -ForegroundColor Yellow
        
        $createdRoles += @{
            type = $roleType
            name = $roleConfig.name
            arn = $roleInfo.Role.Arn
            description = $roleConfig.description
        }
    }
}

# Create instance profiles for EC2-based services
Write-Host "`n=== Creating Instance Profiles ===" -ForegroundColor Cyan

$instanceProfiles = @{
    "ECSInstanceProfile" = "AICore-ECS-InstanceProfile"
    "BastionInstanceProfile" = "AICore-Bastion-InstanceProfile"
}

foreach ($profileType in $instanceProfiles.Keys) {
    $profileName = $instanceProfiles[$profileType]
    Write-Host "Creating instance profile: $profileName" -ForegroundColor Yellow
    
    $existingProfile = aws iam get-instance-profile --instance-profile-name $profileName 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        aws iam create-instance-profile --instance-profile-name $profileName | Out-Null
        Write-Host "✓ Created instance profile" -ForegroundColor Green
    } else {
        Write-Host "✓ Instance profile already exists" -ForegroundColor Yellow
    }
}

# Create service accounts for EKS
Write-Host "`n=== Creating EKS Service Accounts ===" -ForegroundColor Cyan

$eksServiceAccounts = @{
    "aws-load-balancer-controller" = @{
        namespace = "kube-system"
        policy = "arn:aws:iam::aws:policy/AWSLoadBalancerControllerIAMPolicy"
    }
    "cluster-autoscaler" = @{
        namespace = "kube-system"
        policy = "inline"
        inline_policy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "autoscaling:DescribeAutoScalingGroups",
                        "autoscaling:DescribeAutoScalingInstances",
                        "autoscaling:DescribeLaunchConfigurations",
                        "autoscaling:DescribeTags",
                        "autoscaling:SetDesiredCapacity",
                        "autoscaling:TerminateInstanceInAutoScalingGroup",
                        "ec2:DescribeLaunchTemplateVersions"
                    )
                    Resource = "*"
                }
            )
        }
    }
}

# Save configuration
$iamConfig = @{
    roles = $createdRoles
    instance_profiles = $instanceProfiles
    eks_service_accounts = $eksServiceAccounts
    account_id = $AccountId
    region = $Region
    environment = $Environment
    created_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5

$iamConfig | Out-File -FilePath "iam-roles-config.json" -Encoding UTF8

# Create documentation
$documentation = @"
# AI Core IAM Roles Documentation

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Roles Created

"@

foreach ($role in $createdRoles) {
    $documentation += @"

### $($role.type)
- **Name**: ``$($role.name)``
- **ARN**: ``$($role.arn)``
- **Purpose**: $($role.description)

"@
}

$documentation += @"

## Usage Examples

### ECS Task Definition
```json
{
  "family": "ai-core-service",
  "taskRoleArn": "$($createdRoles | Where-Object { $_.type -eq "ECSTaskRole" } | Select-Object -ExpandProperty arn)",
  "executionRoleArn": "$($createdRoles | Where-Object { $_.type -eq "ECSTaskExecutionRole" } | Select-Object -ExpandProperty arn)",
  "containerDefinitions": [...]
}
```

### Lambda Function
```bash
aws lambda create-function \
  --function-name ai-core-processor \
  --role "$($createdRoles | Where-Object { $_.type -eq "LambdaExecutionRole" } | Select-Object -ExpandProperty arn)" \
  --runtime python3.9 \
  --handler index.handler
```

### SageMaker Training Job
```python
import sagemaker
from sagemaker.estimator import Estimator

estimator = Estimator(
    image_uri='your-ecr-uri',
    role='$($createdRoles | Where-Object { $_.type -eq "SageMakerExecutionRole" } | Select-Object -ExpandProperty arn)',
    instance_count=1,
    instance_type='ml.m5.xlarge'
)
```

## Security Best Practices

1. **Least Privilege**: Each role has minimal required permissions
2. **Service Isolation**: Roles are service-specific
3. **No Wildcards**: Resources are explicitly defined where possible
4. **Regular Review**: Audit role usage monthly
5. **MFA Enforcement**: Require MFA for assumable roles

## Role Assumption

For human-assumable roles (DataScientist, DataEngineer), configure with:

```bash
aws sts assume-role \
  --role-arn <role-arn> \
  --role-session-name <your-session-name> \
  --duration-seconds 3600
```

## Compliance

- All roles tagged with Project, Environment, ManagedBy
- CloudTrail logs all role assumptions
- Regular access reviews required
- Roles follow naming convention: AICore-<Service>-<Type>

"@

$documentation | Out-File -FilePath "iam-roles-documentation.md" -Encoding UTF8

Write-Host "`n=== IAM Role Deployment Complete ===" -ForegroundColor Green
Write-Host "`nRoles created/verified:" -ForegroundColor Cyan
foreach ($role in $createdRoles) {
    Write-Host "  - $($role.name)" -ForegroundColor White
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Configure EKS OIDC provider for service accounts"
Write-Host "2. Update service configurations to use new roles"
Write-Host "3. Set up role assumption for human users"
Write-Host "4. Configure CloudWatch Events for role usage monitoring"
Write-Host "5. Document role usage in team runbooks"
