param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-aurora-cluster"
)

Write-Host "=== Creating RDS Aurora PostgreSQL Cluster ===" -ForegroundColor Cyan
Write-Host "Cluster Name: $ClusterName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White

# Load existing network configuration
$dbSubnetsConfig = Get-Content "..\network\database-subnets-config.json" | ConvertFrom-Json
$securityGroupsConfig = Get-Content "..\network\security-groups-config.json" | ConvertFrom-Json
$vpcId = "vpc-0684c566fb7cc6b12"

# Get DB subnet group name - use existing group
$dbSubnetGroupName = "ai-core-database-subnet-group"  # Existing subnet group
Write-Host "`nUsing DB subnet group: $dbSubnetGroupName" -ForegroundColor Green

# Check if DB subnet group exists
Write-Host "`nChecking DB subnet group..." -ForegroundColor Yellow
$subnetGroupExists = aws rds describe-db-subnet-groups `
    --db-subnet-group-name $dbSubnetGroupName `
    --query "DBSubnetGroups[0].DBSubnetGroupName" `
    --output text 2>$null

if ($subnetGroupExists -ne $dbSubnetGroupName) {
    Write-Host "Creating DB subnet group..." -ForegroundColor Yellow
    
    # Get actual subnet IDs for database subnets
    $dbSubnetIds = aws ec2 describe-subnets `
        --filters "Name=vpc-id,Values=$vpcId" "Name=tag:Type,Values=database" `
        --query "Subnets[].SubnetId" `
        --output json | ConvertFrom-Json
    
    if ($dbSubnetIds.Count -lt 2) {
        # Use private subnets if database subnets not tagged
        $dbSubnetIds = @(
            "subnet-0b2a16f919e052e5d",  # us-east-1a
            "subnet-0005204be891dc874",  # us-east-1b
            "subnet-0a62fb83eaaa5573c"   # us-east-1c
        )
    }
    
    $subnetIdsString = $dbSubnetIds -join " "
    
    aws rds create-db-subnet-group `
        --db-subnet-group-name $dbSubnetGroupName `
        --db-subnet-group-description "Database subnet group for AI Core production RDS instances" `
        --subnet-ids $subnetIdsString `
        --tags "Key=Project,Value=AI-Core" "Key=Environment,Value=production"
    
    Write-Host "✓ DB subnet group created" -ForegroundColor Green
} else {
    Write-Host "✓ DB subnet group already exists" -ForegroundColor Green
}

# Create parameter group for Aurora PostgreSQL
Write-Host "`nCreating Aurora parameter groups..." -ForegroundColor Yellow

$clusterParameterGroupName = "ai-core-aurora-cluster-pg15"
$dbParameterGroupName = "ai-core-aurora-db-pg15"

# Cluster parameter group
$clusterPgExists = aws rds describe-db-cluster-parameter-groups `
    --db-cluster-parameter-group-name $clusterParameterGroupName `
    --query "DBClusterParameterGroups[0].DBClusterParameterGroupName" `
    --output text 2>$null

if ($clusterPgExists -ne $clusterParameterGroupName) {
    aws rds create-db-cluster-parameter-group `
        --db-cluster-parameter-group-name $clusterParameterGroupName `
        --db-parameter-group-family "aurora-postgresql15" `
        --description "Cluster parameter group for AI Core Aurora PostgreSQL 15" `
        --tags "Key=Project,Value=AI-Core"
    
    # Modify cluster parameters for ML workloads
    $clusterParams = @"
[
    {
        "ParameterName": "shared_preload_libraries",
        "ParameterValue": "pg_stat_statements,pgaudit",
        "ApplyMethod": "pending-reboot"
    },
    {
        "ParameterName": "log_statement",
        "ParameterValue": "ddl",
        "ApplyMethod": "immediate"
    },
    {
        "ParameterName": "log_connections",
        "ParameterValue": "1",
        "ApplyMethod": "immediate"
    },
    {
        "ParameterName": "log_disconnections",
        "ParameterValue": "1",
        "ApplyMethod": "immediate"
    }
]
"@
    
    $clusterParams | Out-File -FilePath "cluster-params.json" -Encoding UTF8
    
    aws rds modify-db-cluster-parameter-group `
        --db-cluster-parameter-group-name $clusterParameterGroupName `
        --parameters file://cluster-params.json
    
    Write-Host "✓ Cluster parameter group created" -ForegroundColor Green
} else {
    Write-Host "✓ Cluster parameter group already exists" -ForegroundColor Green
}

# DB parameter group
$dbPgExists = aws rds describe-db-parameter-groups `
    --db-parameter-group-name $dbParameterGroupName `
    --query "DBParameterGroups[0].DBParameterGroupName" `
    --output text 2>$null

if ($dbPgExists -ne $dbParameterGroupName) {
    aws rds create-db-parameter-group `
        --db-parameter-group-name $dbParameterGroupName `
        --db-parameter-group-family "aurora-postgresql15" `
        --description "DB parameter group for AI Core Aurora PostgreSQL 15" `
        --tags "Key=Project,Value=AI-Core"
    
    # Modify DB parameters for ML workloads
    $dbParams = @"
[
    {
        "ParameterName": "max_connections",
        "ParameterValue": "1000",
        "ApplyMethod": "pending-reboot"
    },
    {
        "ParameterName": "work_mem",
        "ParameterValue": "262144",
        "ApplyMethod": "immediate"
    },
    {
        "ParameterName": "maintenance_work_mem",
        "ParameterValue": "1048576",
        "ApplyMethod": "immediate"
    },
    {
        "ParameterName": "effective_cache_size",
        "ParameterValue": "{DBInstanceClassMemory*3/4}",
        "ApplyMethod": "immediate"
    },
    {
        "ParameterName": "random_page_cost",
        "ParameterValue": "1.1",
        "ApplyMethod": "immediate"
    }
]
"@
    
    $dbParams | Out-File -FilePath "db-params.json" -Encoding UTF8
    
    aws rds modify-db-parameter-group `
        --db-parameter-group-name $dbParameterGroupName `
        --parameters file://db-params.json
    
    Write-Host "✓ DB parameter group created" -ForegroundColor Green
} else {
    Write-Host "✓ DB parameter group already exists" -ForegroundColor Green
}

# Generate secure master password
Write-Host "`nGenerating secure master password..." -ForegroundColor Yellow
$masterPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$masterUsername = "aicore_admin"

# Store password in Secrets Manager
$secretName = "rds/$ClusterName/master-credentials"
$secretExists = aws secretsmanager describe-secret --secret-id $secretName --query "Name" --output text 2>$null

if ($secretExists -ne $secretName) {
    $secretJson = @{
        username = $masterUsername
        password = $masterPassword
        engine = "aurora-postgresql"
        host = ""
        port = 5432
        dbClusterIdentifier = $ClusterName
    } | ConvertTo-Json -Compress
    
    aws secretsmanager create-secret `
        --name $secretName `
        --description "Master credentials for $ClusterName Aurora cluster" `
        --secret-string $secretJson `
        --tags "Key=Project,Value=AI-Core" "Key=Environment,Value=production"
    
    Write-Host "✓ Master credentials stored in Secrets Manager" -ForegroundColor Green
} else {
    Write-Host "✓ Using existing credentials from Secrets Manager" -ForegroundColor Green
    # Retrieve existing password
    $existingSecret = aws secretsmanager get-secret-value --secret-id $secretName --query "SecretString" --output text | ConvertFrom-Json
    $masterPassword = $existingSecret.password
    $masterUsername = $existingSecret.username
}

# Create Aurora cluster
Write-Host "`nCreating Aurora PostgreSQL cluster..." -ForegroundColor Yellow

$rdsSecurityGroupId = "sg-0712e6d64c6b2d4fd"  # ai-core-production-rds-sg

$createClusterResult = aws rds create-db-cluster `
    --db-cluster-identifier $ClusterName `
    --engine "aurora-postgresql" `
    --engine-version "15.8" `
    --master-username $masterUsername `
    --master-user-password $masterPassword `
    --database-name "aicore" `
    --db-subnet-group-name $dbSubnetGroupName `
    --vpc-security-group-ids $rdsSecurityGroupId `
    --db-cluster-parameter-group-name $clusterParameterGroupName `
    --backup-retention-period 30 `
    --preferred-backup-window "03:00-04:00" `
    --preferred-maintenance-window "sun:04:00-sun:05:00" `
    --storage-encrypted `
    --enable-cloudwatch-logs-exports "postgresql" `
    --deletion-protection `
    --tags "Key=Name,Value=$ClusterName" "Key=Project,Value=AI-Core" "Key=Environment,Value=production" `
    --output json 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Aurora cluster creation initiated" -ForegroundColor Green
    
    # Wait for cluster to be available
    Write-Host "`nWaiting for cluster to be available..." -ForegroundColor Yellow
    aws rds wait db-cluster-available --db-cluster-identifier $ClusterName
    Write-Host "✓ Aurora cluster is available" -ForegroundColor Green
    
} else {
    if ($createClusterResult -like "*DBClusterAlreadyExistsFault*") {
        Write-Host "✓ Aurora cluster already exists" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Failed to create cluster: $createClusterResult" -ForegroundColor Red
        exit 1
    }
}

# Create Aurora instances
Write-Host "`nCreating Aurora instances..." -ForegroundColor Yellow

$instances = @(
    @{
        identifier = "$ClusterName-writer-1"
        instanceClass = "db.r6g.xlarge"
        role = "writer"
    },
    @{
        identifier = "$ClusterName-reader-1"
        instanceClass = "db.r6g.large"
        role = "reader"
    },
    @{
        identifier = "$ClusterName-reader-2"
        instanceClass = "db.r6g.large"
        role = "reader"
    }
)

foreach ($instance in $instances) {
    Write-Host "  Creating instance: $($instance.identifier) ($($instance.instanceClass))" -ForegroundColor White
    
    $createInstanceResult = aws rds create-db-instance `
        --db-instance-identifier $instance.identifier `
        --db-cluster-identifier $ClusterName `
        --engine "aurora-postgresql" `
        --db-instance-class $instance.instanceClass `
        --db-parameter-group-name $dbParameterGroupName `
        --performance-insights-enabled `
        --performance-insights-retention-period 7 `
        --monitoring-interval 60 `
        --monitoring-role-arn "arn:aws:iam::$((aws sts get-caller-identity --query Account --output text)):role/rds-enhanced-monitoring-role" `
        --enable-cloudwatch-logs-exports "postgresql" `
        --auto-minor-version-upgrade `
        --tags "Key=Name,Value=$($instance.identifier)" "Key=Role,Value=$($instance.role)" `
        --output json 2>&1
    
    if ($LASTEXITCODE -ne 0 -and $createInstanceResult -notlike "*DBInstanceAlreadyExistsFault*") {
        Write-Host "[WARNING] Failed to create instance: $($instance.identifier)" -ForegroundColor Yellow
    }
}

# Wait for instances to be available
Write-Host "`nWaiting for instances to be available..." -ForegroundColor Yellow
foreach ($instance in $instances) {
    aws rds wait db-instance-available --db-instance-identifier $instance.identifier 2>$null
}
Write-Host "✓ All instances are available" -ForegroundColor Green

# Get cluster endpoint information
$clusterInfo = aws rds describe-db-clusters --db-cluster-identifier $ClusterName --output json | ConvertFrom-Json
$cluster = $clusterInfo.DBClusters[0]

Write-Host "`n=== Aurora Cluster Created Successfully ===" -ForegroundColor Green
Write-Host "Cluster Identifier: $ClusterName" -ForegroundColor White
Write-Host "Writer Endpoint: $($cluster.Endpoint)" -ForegroundColor White
Write-Host "Reader Endpoint: $($cluster.ReaderEndpoint)" -ForegroundColor White
Write-Host "Port: $($cluster.Port)" -ForegroundColor White
Write-Host "Database Name: aicore" -ForegroundColor White
Write-Host "Master Username: $masterUsername" -ForegroundColor White
Write-Host "Secret ARN: arn:aws:secretsmanager:${Region}:$((aws sts get-caller-identity --query Account --output text)):secret:$secretName" -ForegroundColor White

# Update secret with endpoint information
$updatedSecretJson = @{
    username = $masterUsername
    password = $masterPassword
    engine = "aurora-postgresql"
    host = $cluster.Endpoint
    readerHost = $cluster.ReaderEndpoint
    port = $cluster.Port
    dbClusterIdentifier = $ClusterName
    database = "aicore"
} | ConvertTo-Json -Compress

aws secretsmanager update-secret `
    --secret-id $secretName `
    --secret-string $updatedSecretJson | Out-Null

# Save cluster configuration
$clusterConfig = @{
    clusterName = $ClusterName
    engine = "aurora-postgresql"
    engineVersion = $cluster.EngineVersion
    endpoint = $cluster.Endpoint
    readerEndpoint = $cluster.ReaderEndpoint
    port = $cluster.Port
    database = "aicore"
    masterUsername = $masterUsername
    secretArn = "arn:aws:secretsmanager:${Region}:$((aws sts get-caller-identity --query Account --output text)):secret:$secretName"
    instances = $instances
    subnetGroup = $dbSubnetGroupName
    securityGroup = $rdsSecurityGroupId
    backupRetention = 30
    encrypted = $true
    deletionProtection = $true
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$clusterConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "aurora-cluster-config.json" -Encoding UTF8

# Create connection test script
$testScript = @'
param(
    [string]$SecretName = "rds/ai-core-aurora-cluster/master-credentials"
)

# Get credentials from Secrets Manager
$secret = aws secretsmanager get-secret-value --secret-id $SecretName --query SecretString --output text | ConvertFrom-Json

# Test connection using psql
$env:PGPASSWORD = $secret.password
psql -h $secret.host -U $secret.username -d $secret.database -c "SELECT version();"
psql -h $secret.readerHost -U $secret.username -d $secret.database -c "SELECT pg_is_in_recovery();"
'@

$testScript | Out-File -FilePath "test-aurora-connection.ps1" -Encoding UTF8

# Clean up temporary files
Remove-Item -Path "cluster-params.json", "db-params.json" -ErrorAction SilentlyContinue

Write-Host "`nCluster configuration saved to: aurora-cluster-config.json" -ForegroundColor Cyan
Write-Host "Test connection script: test-aurora-connection.ps1" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Test connection: .\test-aurora-connection.ps1" -ForegroundColor White
Write-Host "  2. Create application users and databases" -ForegroundColor White
Write-Host "  3. Configure backup and monitoring" -ForegroundColor White
Write-Host "  4. Set up read replicas if needed" -ForegroundColor White
