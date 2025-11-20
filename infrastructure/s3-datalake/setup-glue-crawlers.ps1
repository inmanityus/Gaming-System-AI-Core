param(
    [string]$ConfigFile = "datalake-config.json"
)

Write-Host "=== Setting up AWS Glue Crawlers for Data Lake ===" -ForegroundColor Cyan

# Load configuration
if (-not (Test-Path $ConfigFile)) {
    Write-Host "[ERROR] Configuration file not found: $ConfigFile" -ForegroundColor Red
    Write-Host "Please run deploy-s3-datalake.ps1 first" -ForegroundColor Yellow
    exit 1
}

$config = Get-Content -Path $ConfigFile | ConvertFrom-Json
$databaseName = $config.athena.database
$accountId = $config.account_id

# Create IAM role for Glue
Write-Host "`nCreating IAM role for Glue crawlers..." -ForegroundColor Yellow
$roleName = "AICoreGlueCrawlerRole"

# Create trust policy
$trustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Service = "glue.amazonaws.com"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 5 -Compress

$trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding UTF8

# Check if role exists
$existingRole = aws iam get-role --role-name $roleName 2>$null

if ($LASTEXITCODE -ne 0) {
    # Create role
    aws iam create-role `
        --role-name $roleName `
        --assume-role-policy-document file://trust-policy.json `
        --description "Role for AI Core Glue Crawlers" `
        --output json | Out-Null
    
    Write-Host "✓ Created IAM role: $roleName" -ForegroundColor Green
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name $roleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole" | Out-Null
    
    # Create custom policy for S3 and KMS access
    $customPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Action = @(
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:GetBucketAcl"
                )
                Resource = @(
                    "arn:aws:s3:::ai-core-datalake-*",
                    "arn:aws:s3:::ai-core-datalake-*/*"
                )
            },
            @{
                Effect = "Allow"
                Action = @(
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:GenerateDataKey"
                )
                Resource = "arn:aws:kms:*:${accountId}:key/*"
                Condition = @{
                    StringLike = @{
                        "kms:ViaService" = "s3.*.amazonaws.com"
                    }
                }
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    
    $customPolicy | Out-File -FilePath "glue-s3-policy.json" -Encoding UTF8
    
    aws iam put-role-policy `
        --role-name $roleName `
        --policy-name "GlueS3Access" `
        --policy-document file://glue-s3-policy.json | Out-Null
    
    Write-Host "✓ Attached policies to role" -ForegroundColor Green
    
    # Wait for role to be available
    Start-Sleep -Seconds 10
} else {
    Write-Host "✓ Using existing IAM role: $roleName" -ForegroundColor Yellow
}

Remove-Item "trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item "glue-s3-policy.json" -ErrorAction SilentlyContinue

$roleArn = "arn:aws:iam::${accountId}:role/$roleName"

# Define crawlers for each bucket layer
$crawlers = @(
    @{
        name = "ai-core-raw-data-crawler"
        bucket = $config.buckets | Where-Object { $_.type -eq "raw" } | Select-Object -ExpandProperty name
        tablePrefix = "raw_"
        description = "Crawler for raw data landing zone"
        schedule = "cron(0 */6 * * ? *)"  # Every 6 hours
    },
    @{
        name = "ai-core-processed-data-crawler"
        bucket = $config.buckets | Where-Object { $_.type -eq "processed" } | Select-Object -ExpandProperty name
        tablePrefix = "processed_"
        description = "Crawler for processed data"
        schedule = "cron(0 2 * * ? *)"  # Daily at 2 AM
    },
    @{
        name = "ai-core-curated-data-crawler"
        bucket = $config.buckets | Where-Object { $_.type -eq "curated" } | Select-Object -ExpandProperty name
        tablePrefix = "curated_"
        description = "Crawler for curated datasets"
        schedule = "cron(0 4 * * ? *)"  # Daily at 4 AM
    },
    @{
        name = "ai-core-ml-artifacts-crawler"
        bucket = $config.buckets | Where-Object { $_.type -eq "ml-artifacts" } | Select-Object -ExpandProperty name
        tablePrefix = "ml_"
        description = "Crawler for ML artifacts and models"
        schedule = "cron(0 */12 * * ? *)"  # Every 12 hours
    }
)

# Create each crawler
foreach ($crawler in $crawlers) {
    Write-Host "`nCreating crawler: $($crawler.name)" -ForegroundColor Yellow
    
    # Check if crawler exists
    $existingCrawler = aws glue get-crawler --name $crawler.name 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        # Create crawler configuration
        $crawlerConfig = @{
            Name = $crawler.name
            Role = $roleArn
            DatabaseName = $databaseName
            Description = $crawler.description
            TablePrefix = $crawler.tablePrefix
            Targets = @{
                S3Targets = @(
                    @{
                        Path = "s3://$($crawler.bucket)/"
                        Exclusions = @(
                            "**/_placeholder.txt",
                            "**/.*",
                            "**/_temporary/**"
                        )
                    }
                )
            }
            SchemaChangePolicy = @{
                UpdateBehavior = "UPDATE_IN_DATABASE"
                DeleteBehavior = "DEPRECATE_IN_DATABASE"
            }
            RecrawlPolicy = @{
                RecrawlBehavior = "CRAWL_NEW_FOLDERS_ONLY"
            }
            Configuration = (@{
                Version = 1.0
                CrawlerOutput = @{
                    Partitions = @{
                        AddOrUpdateBehavior = "InheritFromTable"
                    }
                }
                Grouping = @{
                    TableGroupingPolicy = "CombineCompatibleSchemas"
                }
            } | ConvertTo-Json -Depth 5 -Compress)
        } | ConvertTo-Json -Depth 10
        
        $crawlerConfig | Out-File -FilePath "temp-crawler.json" -Encoding UTF8
        
        aws glue create-crawler --cli-input-json file://temp-crawler.json --output json | Out-Null
        
        Remove-Item "temp-crawler.json"
        
        Write-Host "✓ Created crawler: $($crawler.name)" -ForegroundColor Green
        
        # Create schedule
        if ($crawler.schedule) {
            Write-Host "  Setting up schedule: $($crawler.schedule)" -ForegroundColor Yellow
            
            aws glue update-crawler-schedule `
                --crawler-name $crawler.name `
                --schedule $crawler.schedule | Out-Null
            
            Write-Host "  ✓ Schedule configured" -ForegroundColor Green
        }
    } else {
        Write-Host "✓ Crawler already exists: $($crawler.name)" -ForegroundColor Yellow
    }
}

# Create sample Athena views
Write-Host "`n=== Creating Sample Athena Views ===" -ForegroundColor Cyan

$views = @{
    "user_activity_daily" = @"
CREATE OR REPLACE VIEW user_activity_daily AS
SELECT 
    DATE_FORMAT(timestamp, '%Y-%m-%d') as activity_date,
    user_id,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(*) as total_events,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchases,
    AVG(CASE WHEN event_type = 'page_view' THEN duration_ms ELSE NULL END) as avg_page_time_ms
FROM processed_user_events
WHERE year = YEAR(CURRENT_DATE)
  AND month = MONTH(CURRENT_DATE)
GROUP BY 1, 2
"@
    
    "npc_interaction_summary" = @"
CREATE OR REPLACE VIEW npc_interaction_summary AS
SELECT 
    npc_id,
    npc_type,
    DATE_FORMAT(interaction_time, '%Y-%m-%d %H:00:00') as hour,
    COUNT(DISTINCT player_id) as unique_players,
    COUNT(*) as total_interactions,
    AVG(interaction_duration_seconds) as avg_duration,
    SUM(CASE WHEN outcome = 'positive' THEN 1 ELSE 0 END) as positive_outcomes
FROM processed_npc_interactions
WHERE year >= YEAR(CURRENT_DATE - INTERVAL '7' DAY)
GROUP BY 1, 2, 3
"@
    
    "ml_model_performance" = @"
CREATE OR REPLACE VIEW ml_model_performance AS
SELECT 
    model_id,
    model_version,
    deployment_date,
    AVG(inference_time_ms) as avg_inference_time,
    PERCENTILE(inference_time_ms, 0.95) as p95_inference_time,
    AVG(accuracy) as avg_accuracy,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN error_flag = true THEN 1 ELSE 0 END) as error_count
FROM ml_predictions
WHERE deployment_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY 1, 2, 3
"@
}

Write-Host "Note: Views will be created after crawlers run and discover tables" -ForegroundColor Yellow

# Save view definitions
$viewsContent = $views.GetEnumerator() | ForEach-Object {
    "-- View: $($_.Key)`n$($_.Value)`n`n"
} -join ""

$viewsContent | Out-File -FilePath "athena-views.sql" -Encoding UTF8
Write-Host "✓ View definitions saved to athena-views.sql" -ForegroundColor Green

# Create Lake Formation setup script
Write-Host "`nCreating Lake Formation setup script..." -ForegroundColor Yellow

$lakeFormationScript = @'
# AWS Lake Formation Setup for AI Core Data Lake

## Prerequisites
- Ensure Lake Formation is enabled in your account
- Administrator must grant initial permissions

## Steps:

### 1. Register Data Lake Storage
aws lakeformation register-resource \
    --resource-arn arn:aws:s3:::ai-core-datalake-raw-* \
    --use-service-linked-role

aws lakeformation register-resource \
    --resource-arn arn:aws:s3:::ai-core-datalake-processed-* \
    --use-service-linked-role

aws lakeformation register-resource \
    --resource-arn arn:aws:s3:::ai-core-datalake-curated-* \
    --use-service-linked-role

### 2. Grant Permissions to Data Scientists
aws lakeformation grant-permissions \
    --principal DataLakePrincipalIdentifier=arn:aws:iam::ACCOUNT_ID:role/DataScientistRole \
    --permissions "SELECT" "DESCRIBE" \
    --resource '{"Database":{"Name":"ai_core_datalake"}}'

### 3. Grant Permissions to Data Engineers
aws lakeformation grant-permissions \
    --principal DataLakePrincipalIdentifier=arn:aws:iam::ACCOUNT_ID:role/DataEngineerRole \
    --permissions "ALL" \
    --resource '{"Database":{"Name":"ai_core_datalake"}}'

### 4. Enable Column-Level Security (Example)
aws lakeformation grant-permissions \
    --principal DataLakePrincipalIdentifier=arn:aws:iam::ACCOUNT_ID:role/AnalystRole \
    --permissions "SELECT" \
    --resource '{"TableWithColumns":{"DatabaseName":"ai_core_datalake","Name":"processed_user_events","ColumnNames":["user_id","event_type","timestamp"]}}'
'@

$lakeFormationScript | Out-File -FilePath "setup-lake-formation.md" -Encoding UTF8

# Run initial crawler
Write-Host "`n=== Starting Initial Crawl ===" -ForegroundColor Cyan
$response = Read-Host "Do you want to run an initial crawl now? (yes/no)"

if ($response -eq "yes") {
    foreach ($crawler in $crawlers) {
        Write-Host "Starting crawler: $($crawler.name)" -ForegroundColor Yellow
        aws glue start-crawler --name $crawler.name 2>$null | Out-Null
        Write-Host "✓ Crawler started" -ForegroundColor Green
    }
    
    Write-Host "`nCrawlers are running. Check progress in AWS Glue Console." -ForegroundColor Cyan
}

Write-Host "`n=== Glue Crawler Setup Complete ===" -ForegroundColor Green
Write-Host "`nCrawlers created:" -ForegroundColor Cyan
foreach ($crawler in $crawlers) {
    Write-Host "  - $($crawler.name)" -ForegroundColor White
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Wait for crawlers to complete initial run"
Write-Host "2. Review discovered tables in Glue Data Catalog"
Write-Host "3. Create Athena views using athena-views.sql"
Write-Host "4. Configure Lake Formation permissions (see setup-lake-formation.md)"
Write-Host "5. Set up data quality rules in AWS Glue DataBrew"
