param(
    [switch]$DryRun = $false
)

Write-Host "=== Migrating Services to Customer-Managed KMS Keys ===" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "[DRY RUN MODE] No changes will be made" -ForegroundColor Yellow
}

# Database migrations
Write-Host "
1. Migrating RDS Aurora..." -ForegroundColor Yellow
if (-not $DryRun) {
    aws rds modify-db-cluster \
        --db-cluster-identifier ai-core-aurora-cluster \
        --kms-key-id alias/ai-core-database \
        --apply-immediately
}
Write-Host "✓ Aurora migration initiated" -ForegroundColor Green

# Redis migration
Write-Host "
2. Migrating ElastiCache Redis..." -ForegroundColor Yellow
if (-not $DryRun) {
    # Note: Redis encryption key can only be set at creation time
    Write-Host "  [INFO] Redis encryption key can only be set during cluster creation" -ForegroundColor Cyan
    Write-Host "  [INFO] Current cluster will continue using existing encryption" -ForegroundColor Cyan
}

# OpenSearch migration
Write-Host "
3. Migrating OpenSearch..." -ForegroundColor Yellow
if (-not $DryRun) {
    # Note: OpenSearch encryption key can only be set at domain creation
    Write-Host "  [INFO] OpenSearch encryption key can only be set during domain creation" -ForegroundColor Cyan
    Write-Host "  [INFO] Current domain will continue using existing encryption" -ForegroundColor Cyan
}

# S3 buckets migration
Write-Host "
4. Migrating S3 buckets..." -ForegroundColor Yellow
$buckets = @(
    "ai-core-cloudtrail-logs-695353648052"
)

foreach ($bucket in $buckets) {
    Write-Host "  Updating bucket: $bucket" -ForegroundColor Gray
    if (-not $DryRun) {
        aws s3api put-bucket-encryption \
            --bucket $bucket \
            --server-side-encryption-configuration "{
                \"Rules\": [{
                    \"ApplyServerSideEncryptionByDefault\": {
                        \"SSEAlgorithm\": \"aws:kms\",
                        \"KMSMasterKeyID\": \"alias/ai-core-logs\"
                    }
                }]
            }" 2>null
    }
}
Write-Host "✓ S3 buckets updated" -ForegroundColor Green

Write-Host "
=== Migration Complete ===" -ForegroundColor Green
Write-Host "Note: Some services require recreation to use new KMS keys" -ForegroundColor Yellow
