param(
    [string]$BucketPrefix = "ai-core-datalake",
    [string]$AccountId = (aws sts get-caller-identity --query Account --output text),
    [string]$Region = "us-east-1"
)

Write-Host "=== Deploying S3 Data Lake Architecture ===" -ForegroundColor Cyan
Write-Host "Account: $AccountId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow

# Define bucket structure
$buckets = @{
    "raw" = @{
        name = "$BucketPrefix-raw-$AccountId"
        description = "Landing zone for raw data ingestion"
        lifecycle = @{
            transition_days = 30
            storage_class = "STANDARD_IA"
            archive_days = 90
            archive_class = "GLACIER"
            delete_days = 365
        }
    }
    "processed" = @{
        name = "$BucketPrefix-processed-$AccountId"
        description = "Cleaned and transformed data ready for analysis"
        lifecycle = @{
            transition_days = 60
            storage_class = "STANDARD_IA"
            archive_days = 180
            archive_class = "GLACIER"
            delete_days = 730
        }
    }
    "curated" = @{
        name = "$BucketPrefix-curated-$AccountId"
        description = "Business-ready datasets and data products"
        lifecycle = @{
            transition_days = 90
            storage_class = "STANDARD_IA"
            archive_days = 365
            archive_class = "DEEP_ARCHIVE"
            delete_days = 2555  # 7 years
        }
    }
    "ml-artifacts" = @{
        name = "$BucketPrefix-ml-artifacts-$AccountId"
        description = "ML models, training data, and experiment results"
        lifecycle = @{
            transition_days = 30
            storage_class = "INTELLIGENT_TIERING"
            archive_days = $null  # Use Intelligent-Tiering instead
            archive_class = $null
            delete_days = 180
        }
    }
    "logs" = @{
        name = "$BucketPrefix-logs-$AccountId"
        description = "Application and system logs"
        lifecycle = @{
            transition_days = 7
            storage_class = "STANDARD_IA"
            archive_days = 30
            archive_class = "GLACIER"
            delete_days = 90
        }
    }
}

# Create KMS key for data lake encryption
Write-Host "`nCreating KMS key for data lake encryption..." -ForegroundColor Yellow
$keyAlias = "alias/ai-core-datalake"

# Check if key already exists
$existingKey = aws kms describe-key --key-id $keyAlias 2>$null

if ($LASTEXITCODE -ne 0) {
    # Create key policy
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
                    "kms:GenerateDataKey"
                )
                Resource = "*"
            },
            @{
                Sid = "Allow CloudTrail to encrypt logs"
                Effect = "Allow"
                Principal = @{
                    Service = "cloudtrail.amazonaws.com"
                }
                Action = @(
                    "kms:GenerateDataKey",
                    "kms:DescribeKey"
                )
                Resource = "*"
                Condition = @{
                    StringLike = @{
                        "kms:EncryptionContext:aws:cloudtrail:arn" = "arn:aws:cloudtrail:*:${AccountId}:trail/*"
                    }
                }
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress

    $keyResult = aws kms create-key `
        --description "KMS key for AI Core Data Lake encryption" `
        --key-policy $keyPolicy `
        --output json | ConvertFrom-Json
    
    $keyId = $keyResult.KeyMetadata.KeyId
    
    # Create alias
    aws kms create-alias --alias-name $keyAlias --target-key-id $keyId | Out-Null
    Write-Host "✓ Created KMS key: $keyId" -ForegroundColor Green
} else {
    $keyId = ($existingKey | ConvertFrom-Json).KeyMetadata.KeyId
    Write-Host "✓ Using existing KMS key: $keyId" -ForegroundColor Yellow
}

# Create each bucket
foreach ($bucketType in $buckets.Keys) {
    $bucket = $buckets[$bucketType]
    Write-Host "`nCreating bucket: $($bucket.name)" -ForegroundColor Yellow
    Write-Host "  Purpose: $($bucket.description)" -ForegroundColor Gray
    
    # Check if bucket exists
    $bucketExists = aws s3api head-bucket --bucket $bucket.name 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        # Create bucket
        if ($Region -eq "us-east-1") {
            aws s3api create-bucket `
                --bucket $bucket.name `
                --output json | Out-Null
        } else {
            aws s3api create-bucket `
                --bucket $bucket.name `
                --region $Region `
                --create-bucket-configuration LocationConstraint=$Region `
                --output json | Out-Null
        }
        Write-Host "✓ Bucket created" -ForegroundColor Green
    } else {
        Write-Host "✓ Bucket already exists" -ForegroundColor Yellow
    }
    
    # Enable versioning
    Write-Host "  Enabling versioning..." -ForegroundColor Yellow
    aws s3api put-bucket-versioning `
        --bucket $bucket.name `
        --versioning-configuration Status=Enabled | Out-Null
    
    # Enable encryption
    Write-Host "  Enabling encryption..." -ForegroundColor Yellow
    $encryptionConfig = @{
        Rules = @(
            @{
                ApplyServerSideEncryptionByDefault = @{
                    SSEAlgorithm = "aws:kms"
                    KMSMasterKeyID = $keyId
                }
                BucketKeyEnabled = $true
            }
        )
    } | ConvertTo-Json -Depth 5 -Compress
    
    aws s3api put-bucket-encryption `
        --bucket $bucket.name `
        --server-side-encryption-configuration $encryptionConfig | Out-Null
    
    # Block public access
    Write-Host "  Blocking public access..." -ForegroundColor Yellow
    aws s3api put-public-access-block `
        --bucket $bucket.name `
        --public-access-block-configuration `
            BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true | Out-Null
    
    # Create lifecycle policy
    Write-Host "  Creating lifecycle policy..." -ForegroundColor Yellow
    $lifecycle = $bucket.lifecycle
    $rules = @()
    
    # Add transition rule
    if ($lifecycle.transition_days) {
        $rules += @{
            ID = "TransitionToIA"
            Status = "Enabled"
            Transitions = @(
                @{
                    Days = $lifecycle.transition_days
                    StorageClass = $lifecycle.storage_class
                }
            )
        }
    }
    
    # Add archive rule
    if ($lifecycle.archive_days -and $lifecycle.archive_class) {
        $rules += @{
            ID = "ArchiveOldData"
            Status = "Enabled"
            Transitions = @(
                @{
                    Days = $lifecycle.archive_days
                    StorageClass = $lifecycle.archive_class
                }
            )
        }
    }
    
    # Add deletion rule
    if ($lifecycle.delete_days) {
        $rules += @{
            ID = "DeleteExpiredData"
            Status = "Enabled"
            Expiration = @{
                Days = $lifecycle.delete_days
            }
            NoncurrentVersionExpiration = @{
                NoncurrentDays = [Math]::Min($lifecycle.delete_days, 90)
            }
        }
    }
    
    if ($rules.Count -gt 0) {
        $lifecycleConfig = @{
            Rules = $rules
        } | ConvertTo-Json -Depth 5 -Compress
        
        $lifecycleConfig | Out-File -FilePath "temp-lifecycle.json" -Encoding UTF8
        
        aws s3api put-bucket-lifecycle-configuration `
            --bucket $bucket.name `
            --lifecycle-configuration file://temp-lifecycle.json | Out-Null
        
        Remove-Item "temp-lifecycle.json"
    }
    
    # Enable S3 Inventory
    Write-Host "  Configuring inventory..." -ForegroundColor Yellow
    $inventoryConfig = @{
        Destination = @{
            S3BucketDestination = @{
                AccountId = $AccountId
                Bucket = "arn:aws:s3:::$BucketPrefix-logs-$AccountId"
                Format = "Parquet"
                Prefix = "inventory/$($bucket.name)/"
                Encryption = @{
                    SSEKMS = @{
                        KeyId = $keyId
                    }
                }
            }
        }
        IsEnabled = $true
        Filter = @{
            Prefix = "*"
        }
        Id = "daily-inventory"
        IncludedObjectVersions = "Current"
        OptionalFields = @(
            "Size",
            "LastModifiedDate",
            "StorageClass",
            "ETag",
            "IsMultipartUploaded",
            "ReplicationStatus",
            "EncryptionStatus"
        )
        Schedule = @{
            Frequency = "Daily"
        }
    } | ConvertTo-Json -Depth 10 -Compress
    
    $inventoryConfig | Out-File -FilePath "temp-inventory.json" -Encoding UTF8
    
    aws s3api put-bucket-inventory-configuration `
        --bucket $bucket.name `
        --id "daily-inventory" `
        --inventory-configuration file://temp-inventory.json 2>$null | Out-Null
    
    Remove-Item "temp-inventory.json"
    
    # Add bucket tags
    Write-Host "  Adding tags..." -ForegroundColor Yellow
    $tags = @(
        @{Key="Project"; Value="AI-Core"},
        @{Key="Environment"; Value="Production"},
        @{Key="DataLakeLayer"; Value=$bucketType},
        @{Key="ManagedBy"; Value="PowerShell"},
        @{Key="CostCenter"; Value="AI-Infrastructure"}
    )
    
    $tagging = @{
        TagSet = $tags
    } | ConvertTo-Json -Depth 3 -Compress
    
    aws s3api put-bucket-tagging `
        --bucket $bucket.name `
        --tagging $tagging | Out-Null
    
    Write-Host "✓ Bucket configured successfully" -ForegroundColor Green
}

# Create data partitioning structure
Write-Host "`n=== Creating Data Partitioning Structure ===" -ForegroundColor Cyan

$partitionStructure = @{
    "raw" = @(
        "source=api/",
        "source=streaming/",
        "source=batch/",
        "source=external/"
    )
    "processed" = @(
        "domain=user/",
        "domain=game/",
        "domain=npc/",
        "domain=analytics/",
        "domain=ml/"
    )
    "curated" = @(
        "dataset=user-behavior/",
        "dataset=game-metrics/",
        "dataset=npc-interactions/",
        "dataset=performance-analytics/",
        "dataset=ml-features/"
    )
    "ml-artifacts" = @(
        "models/",
        "experiments/",
        "training-data/",
        "predictions/",
        "evaluations/"
    )
}

foreach ($bucketType in $partitionStructure.Keys) {
    $bucket = $buckets[$bucketType]
    Write-Host "`nCreating partition structure for: $($bucket.name)" -ForegroundColor Yellow
    
    foreach ($partition in $partitionStructure[$bucketType]) {
        # Create year/month/day/hour partitions for time-series data
        $fullPath = "$partition`year=2025/month=11/day=19/hour=00/_placeholder.txt"
        
        # Create placeholder file to establish directory structure
        "This is a placeholder file to establish the partition structure." | `
            Out-File -FilePath "placeholder.txt" -Encoding UTF8
        
        aws s3 cp placeholder.txt "s3://$($bucket.name)/$fullPath" `
            --sse aws:kms --sse-kms-key-id $keyId 2>$null | Out-Null
        
        Write-Host "  ✓ Created partition: $partition" -ForegroundColor Gray
    }
    
    Remove-Item "placeholder.txt" -ErrorAction SilentlyContinue
}

# Create Athena database for data lake
Write-Host "`n=== Setting up Athena Database ===" -ForegroundColor Cyan

$athenaBucket = "$BucketPrefix-athena-results-$AccountId"

# Create Athena results bucket
$bucketExists = aws s3api head-bucket --bucket $athenaBucket 2>$null

if ($LASTEXITCODE -ne 0) {
    if ($Region -eq "us-east-1") {
        aws s3api create-bucket --bucket $athenaBucket --output json | Out-Null
    } else {
        aws s3api create-bucket `
            --bucket $athenaBucket `
            --region $Region `
            --create-bucket-configuration LocationConstraint=$Region `
            --output json | Out-Null
    }
    Write-Host "✓ Created Athena results bucket" -ForegroundColor Green
}

# Enable encryption on Athena bucket
aws s3api put-bucket-encryption `
    --bucket $athenaBucket `
    --server-side-encryption-configuration `
        '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms","KMSMasterKeyID":"'$keyId'"},"BucketKeyEnabled":true}]}' | Out-Null

# Block public access on Athena bucket
aws s3api put-public-access-block `
    --bucket $athenaBucket `
    --public-access-block-configuration `
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true | Out-Null

# Create Glue database
Write-Host "Creating Glue database..." -ForegroundColor Yellow
$databaseName = "ai_core_datalake"

aws glue create-database `
    --database-input `
        Name=$databaseName,Description="AI Core Data Lake Analytics Database" `
    --region $Region 2>$null | Out-Null

Write-Host "✓ Glue database ready: $databaseName" -ForegroundColor Green

# Create data lake configuration file
$dataLakeConfig = @{
    buckets = $buckets.GetEnumerator() | ForEach-Object {
        @{
            type = $_.Key
            name = $_.Value.name
            description = $_.Value.description
        }
    }
    kms_key = @{
        id = $keyId
        alias = $keyAlias
    }
    athena = @{
        database = $databaseName
        results_bucket = "s3://$athenaBucket/query-results/"
    }
    region = $Region
    account_id = $AccountId
    created_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5

$dataLakeConfig | Out-File -FilePath "datalake-config.json" -Encoding UTF8

Write-Host "`n=== Data Lake Deployment Complete ===" -ForegroundColor Green
Write-Host "Configuration saved to: datalake-config.json" -ForegroundColor White
Write-Host "`nBuckets created:" -ForegroundColor Cyan
foreach ($bucketType in $buckets.Keys) {
    Write-Host "  - $($buckets[$bucketType].name) ($bucketType)" -ForegroundColor White
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Configure AWS Glue crawlers for automatic schema discovery"
Write-Host "2. Set up AWS Lake Formation for fine-grained access control"
Write-Host "3. Create Athena tables and views for your datasets"
Write-Host "4. Configure data ingestion pipelines (Kinesis, Glue ETL, etc.)"
Write-Host "5. Set up data quality rules and monitoring"
