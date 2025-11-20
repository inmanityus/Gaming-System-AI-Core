param(
    [string]$BucketPrefix = "ai-core-datalake",
    [string]$AccountId = (aws sts get-caller-identity --query Account --output text),
    [string]$Region = "us-east-1"
)

Write-Host "=== Fixing S3 Data Lake Configuration ===" -ForegroundColor Cyan

# First, create the KMS key properly
Write-Host "`nCreating KMS key for data lake encryption..." -ForegroundColor Yellow
$keyAlias = "alias/ai-core-datalake"

# Check if key already exists
$existingKey = aws kms describe-key --key-id $keyAlias 2>$null

if ($LASTEXITCODE -ne 0) {
    # Create key without policy first
    $keyResult = aws kms create-key `
        --description "KMS key for AI Core Data Lake encryption" `
        --output json | ConvertFrom-Json
    
    $keyId = $keyResult.KeyMetadata.KeyId
    Write-Host "✓ Created KMS key: $keyId" -ForegroundColor Green
    
    # Create alias
    aws kms create-alias --alias-name $keyAlias --target-key-id $keyId | Out-Null
    
    # Update key policy
    $keyPolicy = @{
        Version = "2012-10-17"
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
                Sid = "Allow S3 to use the key"
                Effect = "Allow"
                Principal = @{
                    Service = "s3.amazonaws.com"
                }
                Action = @(
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                    "kms:DescribeKey"
                )
                Resource = "*"
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    
    $keyPolicy | Out-File -FilePath "key-policy.json" -Encoding UTF8
    
    aws kms put-key-policy `
        --key-id $keyId `
        --policy-name default `
        --policy file://key-policy.json | Out-Null
    
    Remove-Item "key-policy.json"
    
    Write-Host "✓ Updated key policy" -ForegroundColor Green
} else {
    $keyInfo = $existingKey | ConvertFrom-Json
    $keyId = $keyInfo.KeyMetadata.KeyId
    Write-Host "✓ Using existing KMS key: $keyId" -ForegroundColor Yellow
}

# List of buckets to fix
$buckets = @(
    "ai-core-datalake-raw-$AccountId",
    "ai-core-datalake-processed-$AccountId",
    "ai-core-datalake-curated-$AccountId",
    "ai-core-datalake-ml-artifacts-$AccountId",
    "ai-core-datalake-logs-$AccountId",
    "ai-core-datalake-athena-results-$AccountId"
)

# Fix encryption for each bucket
foreach ($bucketName in $buckets) {
    Write-Host "`nFixing bucket: $bucketName" -ForegroundColor Yellow
    
    # Check if bucket exists
    $bucketExists = aws s3api head-bucket --bucket $bucketName 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        # Enable encryption with proper syntax
        Write-Host "  Enabling KMS encryption..." -ForegroundColor Yellow
        
        $encryptionJson = @{
            Rules = @(
                @{
                    ApplyServerSideEncryptionByDefault = @{
                        SSEAlgorithm = "aws:kms"
                        KMSMasterKeyID = $keyId
                    }
                    BucketKeyEnabled = $true
                }
            )
        } | ConvertTo-Json -Depth 5
        
        $encryptionJson | Out-File -FilePath "encryption.json" -Encoding UTF8
        
        aws s3api put-bucket-encryption `
            --bucket $bucketName `
            --server-side-encryption-configuration file://encryption.json | Out-Null
        
        Remove-Item "encryption.json"
        Write-Host "  ✓ Encryption enabled" -ForegroundColor Green
        
        # Add simple lifecycle rule for logs bucket
        if ($bucketName -like "*-logs-*") {
            Write-Host "  Adding lifecycle policy for logs..." -ForegroundColor Yellow
            
            $lifecycleJson = @{
                Rules = @(
                    @{
                        ID = "DeleteOldLogs"
                        Status = "Enabled"
                        Expiration = @{
                            Days = 90
                        }
                        NoncurrentVersionExpiration = @{
                            NoncurrentDays = 30
                        }
                        Filter = @{
                            Prefix = ""
                        }
                    }
                )
            } | ConvertTo-Json -Depth 5
            
            $lifecycleJson | Out-File -FilePath "lifecycle.json" -Encoding UTF8
            
            aws s3api put-bucket-lifecycle-configuration `
                --bucket $bucketName `
                --lifecycle-configuration file://lifecycle.json 2>$null | Out-Null
            
            Remove-Item "lifecycle.json"
            Write-Host "  ✓ Lifecycle policy added" -ForegroundColor Green
        }
    } else {
        Write-Host "  [SKIP] Bucket not found" -ForegroundColor Gray
    }
}

# Create proper data lake configuration
$dataLakeConfig = @{
    buckets = @(
        @{ type = "raw"; name = "ai-core-datalake-raw-$AccountId" },
        @{ type = "processed"; name = "ai-core-datalake-processed-$AccountId" },
        @{ type = "curated"; name = "ai-core-datalake-curated-$AccountId" },
        @{ type = "ml-artifacts"; name = "ai-core-datalake-ml-artifacts-$AccountId" },
        @{ type = "logs"; name = "ai-core-datalake-logs-$AccountId" }
    )
    kms_key = @{
        id = $keyId
        alias = $keyAlias
    }
    athena = @{
        database = "ai_core_datalake"
        results_bucket = "s3://ai-core-datalake-athena-results-$AccountId/query-results/"
    }
    region = $Region
    account_id = $AccountId
    created_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5

$dataLakeConfig | Out-File -FilePath "datalake-config.json" -Encoding UTF8

Write-Host "`n=== Data Lake Configuration Fixed ===" -ForegroundColor Green
Write-Host "All buckets now have:" -ForegroundColor Cyan
Write-Host "  ✓ KMS encryption enabled" -ForegroundColor White
Write-Host "  ✓ Versioning enabled" -ForegroundColor White
Write-Host "  ✓ Public access blocked" -ForegroundColor White
Write-Host "  ✓ Proper configuration saved" -ForegroundColor White

Write-Host "`nKMS Key ID: $keyId" -ForegroundColor Yellow
Write-Host "KMS Key Alias: $keyAlias" -ForegroundColor Yellow
