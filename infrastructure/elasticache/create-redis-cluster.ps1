param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-redis-cluster"
)

Write-Host "=== Deploying ElastiCache Redis Cluster ===" -ForegroundColor Cyan
Write-Host "Cluster Name: $ClusterName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White

# Configuration
$vpcId = "vpc-0684c566fb7cc6b12"
$accountId = aws sts get-caller-identity --query Account --output text

# Get private subnet IDs
Write-Host "`nDiscovering subnet configuration..." -ForegroundColor Yellow
$privateSubnets = aws ec2 describe-subnets `
    --filters "Name=vpc-id,Values=$vpcId" `
    --query "Subnets[?CidrBlock=='10.0.11.0/24' || CidrBlock=='10.0.12.0/24' || CidrBlock=='10.0.13.0/24'].SubnetId" `
    --output json | ConvertFrom-Json

if ($privateSubnets.Count -lt 2) {
    Write-Host "[ERROR] Insufficient private subnets found" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Found $($privateSubnets.Count) private subnets" -ForegroundColor Green

# Use correct subnet group for our VPC
Write-Host "`nUsing ElastiCache subnet group..." -ForegroundColor Yellow
$subnetGroupName = "ai-core-redis-subnet-group-v2"  # Subnet group in correct VPC
Write-Host "✓ Using subnet group: $subnetGroupName" -ForegroundColor Green

# Get or create security group for ElastiCache
Write-Host "`nChecking ElastiCache security group..." -ForegroundColor Yellow
$sgName = "ai-core-production-elasticache-sg"
$sgExists = aws ec2 describe-security-groups `
    --filters "Name=group-name,Values=$sgName" "Name=vpc-id,Values=$vpcId" `
    --query "SecurityGroups[0].GroupId" `
    --output text 2>$null

if ($sgExists -eq "None" -or -not $sgExists) {
    Write-Host "Creating ElastiCache security group..." -ForegroundColor Yellow
    
    $sgId = aws ec2 create-security-group `
        --group-name $sgName `
        --description "Security group for AI Core ElastiCache Redis cluster" `
        --vpc-id $vpcId `
        --query "GroupId" `
        --output text
    
    # Add ingress rule for Redis port from ECS security group
    $ecsSecurityGroup = aws ec2 describe-security-groups `
        --filters "Name=group-name,Values=ai-core-production-ecs-sg" "Name=vpc-id,Values=$vpcId" `
        --query "SecurityGroups[0].GroupId" `
        --output text
    
    if ($ecsSecurityGroup -and $ecsSecurityGroup -ne "None") {
        aws ec2 authorize-security-group-ingress `
            --group-id $sgId `
            --protocol tcp `
            --port 6379 `
            --source-group $ecsSecurityGroup
    }
    
    # Add self-referencing rule for cluster communication
    aws ec2 authorize-security-group-ingress `
        --group-id $sgId `
        --protocol tcp `
        --port 6379 `
        --source-group $sgId
    
    Write-Host "✓ Security group created: $sgId" -ForegroundColor Green
} else {
    $sgId = $sgExists
    Write-Host "✓ Security group already exists: $sgId" -ForegroundColor Green
}

# Create parameter group
Write-Host "`nCreating Redis parameter group..." -ForegroundColor Yellow
$parameterGroupName = "ai-core-redis7-params"

$pgExists = aws elasticache describe-cache-parameter-groups `
    --cache-parameter-group-name $parameterGroupName `
    --query "CacheParameterGroups[0].CacheParameterGroupName" `
    --output text 2>$null

if ($pgExists -ne $parameterGroupName) {
    aws elasticache create-cache-parameter-group `
        --cache-parameter-group-name $parameterGroupName `
        --cache-parameter-group-family "redis7" `
        --description "Parameter group for AI Core Redis 7"
    
    # Modify parameters for ML workloads
    $parameters = @"
[
    {
        "ParameterName": "maxmemory-policy",
        "ParameterValue": "allkeys-lru"
    },
    {
        "ParameterName": "timeout",
        "ParameterValue": "300"
    },
    {
        "ParameterName": "tcp-keepalive",
        "ParameterValue": "300"
    },
    {
        "ParameterName": "notify-keyspace-events",
        "ParameterValue": "Ex"
    }
]
"@
    
    $parameters | Out-File -FilePath "redis-params.json" -Encoding UTF8
    
    aws elasticache modify-cache-parameter-group `
        --cache-parameter-group-name $parameterGroupName `
        --parameter-name-values file://redis-params.json
    
    Write-Host "✓ Parameter group created" -ForegroundColor Green
} else {
    Write-Host "✓ Parameter group already exists" -ForegroundColor Green
}

# Generate auth token (password) for Redis
Write-Host "`nGenerating Redis auth token..." -ForegroundColor Yellow
$authToken = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Store auth token in Secrets Manager
$secretName = "elasticache/$ClusterName/auth-token"
$secretExists = aws secretsmanager describe-secret --secret-id $secretName --query "Name" --output text 2>$null

if ($secretExists -ne $secretName) {
    $secretJson = @{
        authToken = $authToken
        engine = "redis"
        clusterName = $ClusterName
    } | ConvertTo-Json -Compress
    
    aws secretsmanager create-secret `
        --name $secretName `
        --description "Auth token for $ClusterName Redis cluster" `
        --secret-string $secretJson `
        --tags "Key=Project,Value=AI-Core" "Key=Environment,Value=production"
    
    Write-Host "✓ Auth token stored in Secrets Manager" -ForegroundColor Green
} else {
    Write-Host "✓ Using existing auth token from Secrets Manager" -ForegroundColor Green
    $existingSecret = aws secretsmanager get-secret-value --secret-id $secretName --query "SecretString" --output text | ConvertFrom-Json
    $authToken = $existingSecret.authToken
}

# Create Redis replication group (with failover, non-cluster mode)
Write-Host "`nCreating Redis cluster with replication..." -ForegroundColor Yellow

$createResult = aws elasticache create-replication-group `
    --replication-group-id $ClusterName `
    --replication-group-description "AI Core Redis cluster with automatic failover" `
    --engine "redis" `
    --engine-version "7.1" `
    --cache-node-type "cache.r7g.xlarge" `
    --cache-parameter-group-name $parameterGroupName `
    --cache-subnet-group-name $subnetGroupName `
    --security-group-ids $sgId `
    --num-cache-clusters 3 `
    --automatic-failover-enabled `
    --multi-az-enabled `
    --auth-token $authToken `
    --transit-encryption-enabled `
    --at-rest-encryption-enabled `
    --snapshot-retention-limit 7 `
    --snapshot-window "03:00-05:00" `
    --preferred-maintenance-window "sun:05:00-sun:07:00" `
    --auto-minor-version-upgrade `
    --tags "Key=Name,Value=$ClusterName" "Key=Project,Value=AI-Core" "Key=Environment,Value=production" `
    --output json 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Redis cluster creation initiated" -ForegroundColor Green
    
    # Wait for cluster to be available
    Write-Host "`nWaiting for Redis cluster to be available (this may take 10-15 minutes)..." -ForegroundColor Yellow
    
    $maxWaitMinutes = 20
    $startTime = Get-Date
    
    do {
        $status = aws elasticache describe-replication-groups `
            --replication-group-id $ClusterName `
            --query "ReplicationGroups[0].Status" `
            --output text 2>$null
        
        $elapsedMinutes = [int]((Get-Date) - $startTime).TotalMinutes
        
        if ($status -eq "available") {
            Write-Host "`n✓ Redis cluster is available!" -ForegroundColor Green
            break
        } elseif ($status -eq "creating" -or $status -eq "modifying") {
            Write-Host -NoNewline "`rStatus: $status (elapsed: $elapsedMinutes minutes)" -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        } else {
            Write-Host "`n[ERROR] Unexpected status: $status" -ForegroundColor Red
            break
        }
    } while ($elapsedMinutes -lt $maxWaitMinutes)
    
} else {
    if ($createResult -like "*ReplicationGroupAlreadyExistsFault*") {
        Write-Host "✓ Redis cluster already exists" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Failed to create cluster: $createResult" -ForegroundColor Red
        exit 1
    }
}

# Get cluster information
$clusterInfo = aws elasticache describe-replication-groups `
    --replication-group-id $ClusterName `
    --output json | ConvertFrom-Json

$cluster = $clusterInfo.ReplicationGroups[0]

# Get primary endpoint for non-cluster mode
$primaryEndpoint = $cluster.NodeGroups[0].PrimaryEndpoint.Address
$primaryPort = $cluster.NodeGroups[0].PrimaryEndpoint.Port
$readerEndpoint = $cluster.NodeGroups[0].ReaderEndpoint.Address
$readerPort = $cluster.NodeGroups[0].ReaderEndpoint.Port

Write-Host "`n=== Redis Cluster Created Successfully ===" -ForegroundColor Green
Write-Host "Cluster ID: $ClusterName" -ForegroundColor White
Write-Host "Primary Endpoint: ${primaryEndpoint}:${primaryPort}" -ForegroundColor White
Write-Host "Reader Endpoint: ${readerEndpoint}:${readerPort}" -ForegroundColor White
Write-Host "Engine: Redis $($cluster.CacheNodeType)" -ForegroundColor White
Write-Host "Node Type: $($cluster.CacheNodeType)" -ForegroundColor White
Write-Host "Cluster Mode: Disabled (1 primary, 2 replicas)" -ForegroundColor White
Write-Host "Encryption: Transit & At-Rest" -ForegroundColor White
Write-Host "Multi-AZ: Enabled" -ForegroundColor White
Write-Host "Automatic Failover: Enabled" -ForegroundColor White
Write-Host "Secret ARN: arn:aws:secretsmanager:${Region}:${accountId}:secret:$secretName" -ForegroundColor White

# Update secret with endpoint information
$updatedSecretJson = @{
    authToken = $authToken
    engine = "redis"
    clusterName = $ClusterName
    primaryEndpoint = $primaryEndpoint
    readerEndpoint = $readerEndpoint
    port = $primaryPort
    clusterModeEnabled = $false
    numReplicas = 2
} | ConvertTo-Json -Compress

aws secretsmanager update-secret `
    --secret-id $secretName `
    --secret-string $updatedSecretJson | Out-Null

# Save cluster configuration
$redisConfig = @{
    clusterName = $ClusterName
    replicationGroupId = $ClusterName
    engine = "redis"
    engineVersion = $cluster.EngineVersion
    configurationEndpoint = @{
        address = $configEndpoint
        port = $configPort
    }
    nodeType = $cluster.CacheNodeType
    clusterMode = @{
        enabled = $true
        numNodeGroups = 3
        replicasPerNodeGroup = 2
    }
    multiAZ = $true
    automaticFailover = $true
    encryption = @{
        transit = $true
        atRest = $true
    }
    authEnabled = $true
    secretArn = "arn:aws:secretsmanager:${Region}:${accountId}:secret:$secretName"
    subnetGroup = $subnetGroupName
    securityGroup = $sgId
    parameterGroup = $parameterGroupName
    snapshotRetention = 7
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$redisConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath "redis-cluster-config.json" -Encoding UTF8

# Create connection test script
$testScript = @'
param(
    [string]$SecretName = "elasticache/ai-core-redis-cluster/auth-token"
)

# Get credentials from Secrets Manager
$secret = aws secretsmanager get-secret-value --secret-id $SecretName --query SecretString --output text | ConvertFrom-Json

# Install redis-cli if needed
if (-not (Get-Command redis-cli -ErrorAction SilentlyContinue)) {
    Write-Host "Installing redis-cli..." -ForegroundColor Yellow
    # For Windows, use WSL or download Redis for Windows
    Write-Host "Please install redis-cli manually or use WSL" -ForegroundColor Red
    exit 1
}

# Test connection
Write-Host "Testing Redis cluster connection..." -ForegroundColor Cyan
Write-Host "Endpoint: $($secret.configurationEndpoint):$($secret.port)" -ForegroundColor White

# Test with redis-cli
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning CLUSTER INFO

# Test basic operations
Write-Host "`nTesting basic operations..." -ForegroundColor Cyan
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning SET test:key "Hello from AI Core"
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning GET test:key
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning DEL test:key

Write-Host "`n✓ Connection test complete" -ForegroundColor Green
'@

$testScript | Out-File -FilePath "test-redis-connection.ps1" -Encoding UTF8

# Create Python connection example
$pythonExample = @'
import json
import boto3
import redis
from rediscluster import RedisCluster

# Get credentials from Secrets Manager
def get_redis_credentials(secret_name="elasticache/ai-core-redis-cluster/auth-token"):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Connect to Redis cluster
def connect_redis_cluster():
    credentials = get_redis_credentials()
    
    startup_nodes = [{
        "host": credentials['configurationEndpoint'],
        "port": credentials['port']
    }]
    
    rc = RedisCluster(
        startup_nodes=startup_nodes,
        password=credentials['authToken'],
        decode_responses=True,
        skip_full_coverage_check=True,
        ssl=True,
        ssl_cert_reqs=None
    )
    
    return rc

# Example usage
if __name__ == "__main__":
    redis_client = connect_redis_cluster()
    
    # Test operations
    redis_client.set("test:ml:model", "model-v1.0")
    value = redis_client.get("test:ml:model")
    print(f"Retrieved value: {value}")
    
    # Cluster info
    info = redis_client.info()
    print(f"Cluster nodes: {len(info)}")
    
    redis_client.close()
'@

$pythonExample | Out-File -FilePath "redis_connection_example.py" -Encoding UTF8

# Clean up temporary files
Remove-Item -Path "redis-params.json" -ErrorAction SilentlyContinue

Write-Host "`nCluster configuration saved to: redis-cluster-config.json" -ForegroundColor Cyan
Write-Host "Test connection script: test-redis-connection.ps1" -ForegroundColor Cyan
Write-Host "Python example: redis_connection_example.py" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Test connection (requires redis-cli or Python redis-py-cluster)" -ForegroundColor White
Write-Host "  2. Configure cache eviction policies" -ForegroundColor White
Write-Host "  3. Set up CloudWatch alarms for memory and CPU" -ForegroundColor White
Write-Host "  4. Implement cache warming strategies" -ForegroundColor White
Write-Host "  5. Configure backup and recovery procedures" -ForegroundColor White
