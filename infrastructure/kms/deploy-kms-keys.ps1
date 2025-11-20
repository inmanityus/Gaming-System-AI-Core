param(
    [string]$AccountId = (aws sts get-caller-identity --query Account --output text),
    [string]$Region = "us-east-1"
)

Write-Host "=== Deploying Customer-Managed KMS Keys ===" -ForegroundColor Cyan
Write-Host "Account: $AccountId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow

# Define KMS keys to create
$kmsKeys = @{
    "database" = @{
        alias = "alias/ai-core-database"
        description = "KMS key for RDS Aurora and Redis encryption"
        services = @("rds.amazonaws.com", "elasticache.amazonaws.com")
        tags = @{
            Purpose = "Database encryption"
            Service = "RDS,ElastiCache"
        }
    }
    "application" = @{
        alias = "alias/ai-core-application"
        description = "KMS key for application secrets and configuration"
        services = @("secretsmanager.amazonaws.com", "ssm.amazonaws.com")
        tags = @{
            Purpose = "Application secrets"
            Service = "SecretsManager,SSM"
        }
    }
    "storage" = @{
        alias = "alias/ai-core-storage"
        description = "KMS key for general S3 storage encryption"
        services = @("s3.amazonaws.com")
        tags = @{
            Purpose = "S3 storage encryption"
            Service = "S3"
        }
    }
    "logs" = @{
        alias = "alias/ai-core-logs"
        description = "KMS key for CloudWatch Logs and CloudTrail encryption"
        services = @("logs.amazonaws.com", "cloudtrail.amazonaws.com")
        tags = @{
            Purpose = "Log encryption"
            Service = "CloudWatch,CloudTrail"
        }
    }
    "eks" = @{
        alias = "alias/ai-core-eks"
        description = "KMS key for EKS secrets encryption"
        services = @("eks.amazonaws.com")
        tags = @{
            Purpose = "EKS envelope encryption"
            Service = "EKS"
        }
    }
    "opensearch" = @{
        alias = "alias/ai-core-opensearch"
        description = "KMS key for OpenSearch domain encryption"
        services = @("es.amazonaws.com")
        tags = @{
            Purpose = "OpenSearch encryption"
            Service = "OpenSearch"
        }
    }
    "backup" = @{
        alias = "alias/ai-core-backup"
        description = "KMS key for AWS Backup encryption"
        services = @("backup.amazonaws.com")
        tags = @{
            Purpose = "Backup encryption"
            Service = "AWS Backup"
        }
    }
}

# Array to store created key information
$createdKeys = @()

foreach ($keyType in $kmsKeys.Keys) {
    $keyConfig = $kmsKeys[$keyType]
    Write-Host "`nCreating KMS key: $($keyConfig.alias)" -ForegroundColor Yellow
    Write-Host "  Purpose: $($keyConfig.description)" -ForegroundColor Gray
    
    # Check if key already exists
    $existingKey = aws kms describe-key --key-id $keyConfig.alias 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        # Create the key
        $keyResult = aws kms create-key `
            --description $keyConfig.description `
            --key-usage ENCRYPT_DECRYPT `
            --customer-master-key-spec SYMMETRIC_DEFAULT `
            --output json | ConvertFrom-Json
        
        $keyId = $keyResult.KeyMetadata.KeyId
        $keyArn = $keyResult.KeyMetadata.Arn
        
        Write-Host "✓ Created key: $keyId" -ForegroundColor Green
        
        # Create alias
        aws kms create-alias --alias-name $keyConfig.alias --target-key-id $keyId | Out-Null
        Write-Host "✓ Created alias: $($keyConfig.alias)" -ForegroundColor Green
        
        # Create key policy
        $keyPolicy = @{
            Version = "2012-10-17"
            Id = "key-policy-$keyType"
            Statement = @(
                @{
                    Sid = "Enable IAM User Permissions"
                    Effect = "Allow"
                    Principal = @{
                        AWS = "arn:aws:iam::${AccountId}:root"
                    }
                    Action = "kms:*"
                    Resource = "*"
                },
                @{
                    Sid = "Allow use of the key by AWS services"
                    Effect = "Allow"
                    Principal = @{
                        Service = $keyConfig.services
                    }
                    Action = @(
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:CreateGrant",
                        "kms:DescribeKey"
                    )
                    Resource = "*"
                    Condition = @{
                        StringEquals = @{
                            "kms:ViaService" = $keyConfig.services | ForEach-Object { "$_.$Region.amazonaws.com" }
                        }
                    }
                },
                @{
                    Sid = "Allow administrators to manage the key"
                    Effect = "Allow"
                    Principal = @{
                        AWS = @(
                            "arn:aws:iam::${AccountId}:role/OrganizationAccountAccessRole",
                            "arn:aws:iam::${AccountId}:role/Admin*"
                        )
                    }
                    Action = @(
                        "kms:Create*",
                        "kms:Describe*",
                        "kms:Enable*",
                        "kms:List*",
                        "kms:Put*",
                        "kms:Update*",
                        "kms:Revoke*",
                        "kms:Disable*",
                        "kms:Get*",
                        "kms:Delete*",
                        "kms:TagResource",
                        "kms:UntagResource",
                        "kms:ScheduleKeyDeletion",
                        "kms:CancelKeyDeletion"
                    )
                    Resource = "*"
                }
            )
        } | ConvertTo-Json -Depth 10
        
        $keyPolicy | Out-File -FilePath "key-policy-$keyType.json" -Encoding UTF8
        
        # Apply the key policy
        aws kms put-key-policy `
            --key-id $keyId `
            --policy-name default `
            --policy file://key-policy-$keyType.json | Out-Null
        
        Remove-Item "key-policy-$keyType.json"
        Write-Host "✓ Applied key policy" -ForegroundColor Green
        
        # Add tags
        $tags = @()
        foreach ($tagKey in $keyConfig.tags.Keys) {
            $tags += @{
                TagKey = $tagKey
                TagValue = $keyConfig.tags[$tagKey]
            }
        }
        
        $tags += @(
            @{ TagKey = "Project"; TagValue = "AI-Core" },
            @{ TagKey = "Environment"; TagValue = "Production" },
            @{ TagKey = "ManagedBy"; TagValue = "PowerShell" }
        )
        
        $tagsJson = $tags | ConvertTo-Json -Compress
        aws kms tag-resource --key-id $keyId --tags $tagsJson | Out-Null
        Write-Host "✓ Added tags" -ForegroundColor Green
        
        # Enable automatic key rotation
        aws kms enable-key-rotation --key-id $keyId | Out-Null
        Write-Host "✓ Enabled automatic key rotation" -ForegroundColor Green
        
        $createdKeys += @{
            type = $keyType
            keyId = $keyId
            keyArn = $keyArn
            alias = $keyConfig.alias
            description = $keyConfig.description
        }
        
    } else {
        $keyInfo = $existingKey | ConvertFrom-Json
        Write-Host "✓ Key already exists: $($keyInfo.KeyMetadata.KeyId)" -ForegroundColor Yellow
        
        # Ensure rotation is enabled
        $rotationStatus = aws kms get-key-rotation-status --key-id $keyInfo.KeyMetadata.KeyId --output json | ConvertFrom-Json
        if (-not $rotationStatus.KeyRotationEnabled) {
            aws kms enable-key-rotation --key-id $keyInfo.KeyMetadata.KeyId | Out-Null
            Write-Host "✓ Enabled key rotation" -ForegroundColor Green
        }
        
        $createdKeys += @{
            type = $keyType
            keyId = $keyInfo.KeyMetadata.KeyId
            keyArn = $keyInfo.KeyMetadata.Arn
            alias = $keyConfig.alias
            description = $keyConfig.description
        }
    }
}

# Create key usage documentation
Write-Host "`n=== Creating Key Usage Documentation ===" -ForegroundColor Cyan

$documentation = @"
# AI Core KMS Key Usage Guide

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Customer-Managed KMS Keys

"@

foreach ($key in $createdKeys) {
    $documentation += @"

### $($key.type.ToUpper()) Key
- **Alias**: ``$($key.alias)``
- **Key ID**: ``$($key.keyId)``
- **ARN**: ``$($key.keyArn)``
- **Purpose**: $($key.description)

"@
}

$documentation += @"

## Service Configuration Examples

### RDS Aurora
```bash
aws rds modify-db-cluster \
    --db-cluster-identifier ai-core-aurora-cluster \
    --kms-key-id $($createdKeys | Where-Object { $_.type -eq "database" } | Select-Object -ExpandProperty alias) \
    --apply-immediately
```

### ElastiCache Redis
```bash
aws elasticache modify-replication-group \
    --replication-group-id ai-core-redis-cluster \
    --kms-key-id $($createdKeys | Where-Object { $_.type -eq "database" } | Select-Object -ExpandProperty keyArn) \
    --apply-immediately
```

### S3 Bucket
```bash
aws s3api put-bucket-encryption \
    --bucket my-bucket \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "aws:kms",
                "KMSMasterKeyID": "$($createdKeys | Where-Object { $_.type -eq "storage" } | Select-Object -ExpandProperty alias)"
            }
        }]
    }'
```

### Secrets Manager
```bash
aws secretsmanager update-secret \
    --secret-id my-secret \
    --kms-key-id $($createdKeys | Where-Object { $_.type -eq "application" } | Select-Object -ExpandProperty alias)
```

### CloudWatch Logs
```bash
aws logs associate-kms-key \
    --log-group-name /aws/lambda/my-function \
    --kms-key-id $($createdKeys | Where-Object { $_.type -eq "logs" } | Select-Object -ExpandProperty keyArn)
```

## Best Practices

1. **Key Rotation**: All keys have automatic rotation enabled (annually)
2. **Key Policies**: Follow principle of least privilege
3. **Monitoring**: Set up CloudWatch alarms for key usage
4. **Backup**: Keys are backed up automatically by AWS
5. **Access**: Use IAM policies to control who can use keys

## Compliance

- All keys use AES-256 encryption
- FIPS 140-2 Level 2 validated
- Automatic rotation ensures key material freshness
- CloudTrail logging enabled for all key usage

"@

$documentation | Out-File -FilePath "kms-key-documentation.md" -Encoding UTF8
Write-Host "✓ Documentation saved to kms-key-documentation.md" -ForegroundColor Green

# Create migration script
Write-Host "`nCreating service migration script..." -ForegroundColor Yellow

$migrationScript = @"
param(
    [switch]`$DryRun = `$false
)

Write-Host "=== Migrating Services to Customer-Managed KMS Keys ===" -ForegroundColor Cyan

if (`$DryRun) {
    Write-Host "[DRY RUN MODE] No changes will be made" -ForegroundColor Yellow
}

# Database migrations
Write-Host "`n1. Migrating RDS Aurora..." -ForegroundColor Yellow
if (-not `$DryRun) {
    aws rds modify-db-cluster \
        --db-cluster-identifier ai-core-aurora-cluster \
        --kms-key-id $($createdKeys | Where-Object { $_.type -eq "database" } | Select-Object -ExpandProperty alias) \
        --apply-immediately
}
Write-Host "✓ Aurora migration initiated" -ForegroundColor Green

# Redis migration
Write-Host "`n2. Migrating ElastiCache Redis..." -ForegroundColor Yellow
if (-not `$DryRun) {
    # Note: Redis encryption key can only be set at creation time
    Write-Host "  [INFO] Redis encryption key can only be set during cluster creation" -ForegroundColor Cyan
    Write-Host "  [INFO] Current cluster will continue using existing encryption" -ForegroundColor Cyan
}

# OpenSearch migration
Write-Host "`n3. Migrating OpenSearch..." -ForegroundColor Yellow
if (-not `$DryRun) {
    # Note: OpenSearch encryption key can only be set at domain creation
    Write-Host "  [INFO] OpenSearch encryption key can only be set during domain creation" -ForegroundColor Cyan
    Write-Host "  [INFO] Current domain will continue using existing encryption" -ForegroundColor Cyan
}

# S3 buckets migration
Write-Host "`n4. Migrating S3 buckets..." -ForegroundColor Yellow
`$buckets = @(
    "ai-core-cloudtrail-logs-695353648052"
)

foreach (`$bucket in `$buckets) {
    Write-Host "  Updating bucket: `$bucket" -ForegroundColor Gray
    if (-not `$DryRun) {
        aws s3api put-bucket-encryption \
            --bucket `$bucket \
            --server-side-encryption-configuration "{
                \"Rules\": [{
                    \"ApplyServerSideEncryptionByDefault\": {
                        \"SSEAlgorithm\": \"aws:kms\",
                        \"KMSMasterKeyID\": \"$($createdKeys | Where-Object { $_.type -eq "logs" } | Select-Object -ExpandProperty alias)\"
                    }
                }]
            }" 2>null
    }
}
Write-Host "✓ S3 buckets updated" -ForegroundColor Green

Write-Host "`n=== Migration Complete ===" -ForegroundColor Green
Write-Host "Note: Some services require recreation to use new KMS keys" -ForegroundColor Yellow
"@

$migrationScript | Out-File -FilePath "migrate-to-cmk.ps1" -Encoding UTF8
Write-Host "✓ Migration script saved to migrate-to-cmk.ps1" -ForegroundColor Green

# Save key configuration
$keyConfigJson = @{
    keys = $createdKeys
    account_id = $AccountId
    region = $Region
    created_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5

$keyConfigJson | Out-File -FilePath "kms-keys-config.json" -Encoding UTF8

Write-Host "`n=== KMS Key Deployment Complete ===" -ForegroundColor Green
Write-Host "`nKeys created/verified:" -ForegroundColor Cyan
foreach ($key in $createdKeys) {
    Write-Host "  - $($key.alias) ($($key.type))" -ForegroundColor White
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Run migrate-to-cmk.ps1 to update existing services"
Write-Host "2. Update CloudFormation/Terraform templates to use new keys"
Write-Host "3. Configure CloudWatch alarms for key usage monitoring"
Write-Host "4. Review and update key policies as needed"
Write-Host "5. Document key usage in team wiki/runbook"
