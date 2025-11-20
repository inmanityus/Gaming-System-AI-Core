# Setup Comprehensive CloudWatch Alarms for All AWS Infrastructure
# Creates alarms for Aurora, ElastiCache, OpenSearch, ECS Services

param(
    [string]$Region = "us-east-1",
    [string]$SnsTopicName = "gaming-system-alerts",
    [string]$EmailAddress = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Setting Up Comprehensive CloudWatch Monitoring ===" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Yellow

# Create SNS topic if doesn't exist
Write-Host "`nCreating SNS topic for alerts..." -ForegroundColor Yellow
$topicResult = aws sns create-topic --name $SnsTopicName --region $Region --query 'TopicArn' --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    $snsTopicArn = $topicResult
    Write-Host "✓ SNS topic: $snsTopicArn" -ForegroundColor Green
} else {
    # Get existing topic ARN
    $snsTopicArn = aws sns list-topics --region $Region --query "Topics[?contains(TopicArn, '$SnsTopicName')].TopicArn" --output text
    Write-Host "✓ Using existing SNS topic: $snsTopicArn" -ForegroundColor Green
}

# Subscribe email if provided
if ($EmailAddress) {
    Write-Host "Subscribing $EmailAddress to alerts..." -ForegroundColor Yellow
    aws sns subscribe --topic-arn $snsTopicArn --protocol email --notification-endpoint $EmailAddress --region $Region
}

$alarmsCreated = 0

# ===== AURORA ALARMS =====
Write-Host "`n=== Setting up Aurora Alarms ===" -ForegroundColor Cyan

# Get AI Core Aurora cluster specifically
$auroraCluster = "ai-core-aurora-cluster"

# Verify it exists
$clusterExists = aws rds describe-db-clusters `
    --db-cluster-identifier $auroraCluster `
    --region $Region `
    --query 'DBClusters[0].DBClusterIdentifier' `
    --output text 2>$null

if ($clusterExists) {
    Write-Host "Found Aurora cluster: $auroraCluster" -ForegroundColor Yellow
    
    # CPU Utilization
    aws cloudwatch put-metric-alarm `
        --alarm-name "Aurora-$auroraCluster-CPU-High" `
        --alarm-description "Aurora CPU > 80%" `
        --metric-name CPUUtilization `
        --namespace AWS/RDS `
        --statistic Average `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 80 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=DBClusterIdentifier,Value=$auroraCluster `
        --alarm-actions $snsTopicArn `
        --region $Region | Out-Null
    $alarmsCreated++
    Write-Host "  ✓ CPU alarm created" -ForegroundColor Green
    
    # Database Connections
    aws cloudwatch put-metric-alarm `
        --alarm-name "Aurora-$auroraCluster-Connections-High" `
        --alarm-description "Aurora connections > 80% of max" `
        --metric-name DatabaseConnections `
        --namespace AWS/RDS `
        --statistic Average `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 400 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=DBClusterIdentifier,Value=$auroraCluster `
        --alarm-actions $snsTopicArn `
        --region $Region | Out-Null
    $alarmsCreated++
    Write-Host "  ✓ Connection alarm created" -ForegroundColor Green
    
    # Replica Lag (for read replicas)
    aws cloudwatch put-metric-alarm `
        --alarm-name "Aurora-$auroraCluster-ReplicaLag-High" `
        --alarm-description "Aurora replica lag > 1000ms" `
        --metric-name AuroraReplicaLag `
        --namespace AWS/RDS `
        --statistic Average `
        --period 60 `
        --evaluation-periods 3 `
        --threshold 1000 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=DBClusterIdentifier,Value=$auroraCluster `
        --alarm-actions $snsTopicArn `
        --treat-missing-data notBreaching `
        --region $Region | Out-Null
    $alarmsCreated++
    Write-Host "  ✓ Replica lag alarm created" -ForegroundColor Green
}

# ===== ELASTICACHE ALARMS =====
Write-Host "`n=== Setting up ElastiCache Alarms ===" -ForegroundColor Cyan

# Get ElastiCache cluster identifiers
$cacheCluster = aws elasticache describe-cache-clusters `
    --region $Region `
    --query 'CacheClusters[?Engine==`redis`].CacheClusterId' `
    --output text

if ($cacheCluster) {
    foreach ($cluster in $cacheCluster -split "`t") {
        Write-Host "Setting up alarms for cache cluster: $cluster" -ForegroundColor Yellow
        
        # CPU Utilization
        aws cloudwatch put-metric-alarm `
            --alarm-name "ElastiCache-$cluster-CPU-High" `
            --alarm-description "ElastiCache CPU > 80%" `
            --metric-name CPUUtilization `
            --namespace AWS/ElastiCache `
            --statistic Average `
            --period 300 `
            --evaluation-periods 2 `
            --threshold 80 `
            --comparison-operator GreaterThanThreshold `
            --dimensions Name=CacheClusterId,Value=$cluster `
            --alarm-actions $snsTopicArn `
            --region $Region | Out-Null
        $alarmsCreated++
        Write-Host "  ✓ CPU alarm created" -ForegroundColor Green
        
        # Memory Usage
        aws cloudwatch put-metric-alarm `
            --alarm-name "ElastiCache-$cluster-Memory-High" `
            --alarm-description "ElastiCache memory > 80%" `
            --metric-name DatabaseMemoryUsagePercentage `
            --namespace AWS/ElastiCache `
            --statistic Average `
            --period 300 `
            --evaluation-periods 2 `
            --threshold 80 `
            --comparison-operator GreaterThanThreshold `
            --dimensions Name=CacheClusterId,Value=$cluster `
            --alarm-actions $snsTopicArn `
            --region $Region | Out-Null
        $alarmsCreated++
        Write-Host "  ✓ Memory alarm created" -ForegroundColor Green
        
        # Evictions (indicates memory pressure)
        aws cloudwatch put-metric-alarm `
            --alarm-name "ElastiCache-$cluster-Evictions" `
            --alarm-description "ElastiCache evictions > 100/min" `
            --metric-name Evictions `
            --namespace AWS/ElastiCache `
            --statistic Average `
            --period 300 `
            --evaluation-periods 2 `
            --threshold 100 `
            --comparison-operator GreaterThanThreshold `
            --dimensions Name=CacheClusterId,Value=$cluster `
            --alarm-actions $snsTopicArn `
            --region $Region | Out-Null
        $alarmsCreated++
        Write-Host "  ✓ Evictions alarm created" -ForegroundColor Green
    }
}

# ===== OPENSEARCH ALARMS =====
Write-Host "`n=== Setting up OpenSearch Alarms ===" -ForegroundColor Cyan

$opensearchDomain = "ai-core-opensearch"
Write-Host "Setting up alarms for OpenSearch domain: $opensearchDomain" -ForegroundColor Yellow

# Cluster Status
aws cloudwatch put-metric-alarm `
    --alarm-name "OpenSearch-$opensearchDomain-ClusterStatus-Red" `
    --alarm-description "OpenSearch cluster status is RED" `
    --metric-name ClusterStatus.red `
    --namespace AWS/ES `
    --statistic Maximum `
    --period 60 `
    --evaluation-periods 2 `
    --threshold 1 `
    --comparison-operator GreaterThanOrEqualToThreshold `
    --dimensions Name=DomainName,Value=$opensearchDomain `
    --alarm-actions $snsTopicArn `
    --region $Region | Out-Null
$alarmsCreated++
Write-Host "  ✓ Cluster status RED alarm created" -ForegroundColor Green

# Cluster Status Yellow
aws cloudwatch put-metric-alarm `
    --alarm-name "OpenSearch-$opensearchDomain-ClusterStatus-Yellow" `
    --alarm-description "OpenSearch cluster status is YELLOW" `
    --metric-name ClusterStatus.yellow `
    --namespace AWS/ES `
    --statistic Maximum `
    --period 300 `
    --evaluation-periods 3 `
    --threshold 1 `
    --comparison-operator GreaterThanOrEqualToThreshold `
    --dimensions Name=DomainName,Value=$opensearchDomain `
    --alarm-actions $snsTopicArn `
    --region $Region | Out-Null
$alarmsCreated++
Write-Host "  ✓ Cluster status YELLOW alarm created" -ForegroundColor Green

# CPU Utilization
aws cloudwatch put-metric-alarm `
    --alarm-name "OpenSearch-$opensearchDomain-CPU-High" `
    --alarm-description "OpenSearch CPU > 80%" `
    --metric-name CPUUtilization `
    --namespace AWS/ES `
    --statistic Average `
    --period 300 `
    --evaluation-periods 2 `
    --threshold 80 `
    --comparison-operator GreaterThanThreshold `
    --dimensions Name=DomainName,Value=$opensearchDomain `
    --alarm-actions $snsTopicArn `
    --region $Region | Out-Null
$alarmsCreated++
Write-Host "  ✓ CPU alarm created" -ForegroundColor Green

# JVM Memory Pressure
aws cloudwatch put-metric-alarm `
    --alarm-name "OpenSearch-$opensearchDomain-JVMMemory-High" `
    --alarm-description "OpenSearch JVM memory pressure > 80%" `
    --metric-name JVMMemoryPressure `
    --namespace AWS/ES `
    --statistic Maximum `
    --period 300 `
    --evaluation-periods 2 `
    --threshold 80 `
    --comparison-operator GreaterThanThreshold `
    --dimensions Name=DomainName,Value=$opensearchDomain `
    --alarm-actions $snsTopicArn `
    --region $Region | Out-Null
$alarmsCreated++
Write-Host "  ✓ JVM memory pressure alarm created" -ForegroundColor Green

# Free Storage Space
aws cloudwatch put-metric-alarm `
    --alarm-name "OpenSearch-$opensearchDomain-Storage-Low" `
    --alarm-description "OpenSearch free storage < 10GB" `
    --metric-name FreeStorageSpace `
    --namespace AWS/ES `
    --statistic Minimum `
    --period 300 `
    --evaluation-periods 1 `
    --threshold 10000 `
    --comparison-operator LessThanThreshold `
    --dimensions Name=DomainName,Value=$opensearchDomain `
    --alarm-actions $snsTopicArn `
    --region $Region | Out-Null
$alarmsCreated++
Write-Host "  ✓ Storage alarm created" -ForegroundColor Green

# ===== ECS SERVICE ALARMS =====
Write-Host "`n=== Setting up ECS Service Alarms ===" -ForegroundColor Cyan

$cluster = "gaming-system-cluster"
$services = @(
    "ai-integration-nats", "model-management-nats", "state-manager-nats", "quest-system-nats",
    "npc-behavior-nats", "world-state-nats", "orchestration-nats", "router-nats",
    "event-bus-nats", "time-manager-nats", "weather-manager-nats", "auth-nats",
    "settings-nats", "payment-nats", "performance-mode-nats", "capability-registry-nats",
    "ai-router-nats", "knowledge-base-nats", "environmental-narrative-nats",
    "story-teller-nats", "body-broker-integration-nats", "http-nats-gateway"
)

Write-Host "Setting up alarms for $($services.Count) ECS services..." -ForegroundColor Yellow

foreach ($service in $services) {
    # CPU Utilization
    aws cloudwatch put-metric-alarm `
        --alarm-name "ECS-$service-CPU-High" `
        --alarm-description "ECS service $service CPU > 80%" `
        --metric-name CPUUtilization `
        --namespace AWS/ECS `
        --statistic Average `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 80 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
        --alarm-actions $snsTopicArn `
        --region $Region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $alarmsCreated++
    }
    
    # Memory Utilization
    aws cloudwatch put-metric-alarm `
        --alarm-name "ECS-$service-Memory-High" `
        --alarm-description "ECS service $service Memory > 80%" `
        --metric-name MemoryUtilization `
        --namespace AWS/ECS `
        --statistic Average `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 80 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
        --alarm-actions $snsTopicArn `
        --region $Region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $alarmsCreated++
    }
    
    # Running Task Count (ensure service has at least 1 task)
    aws cloudwatch put-metric-alarm `
        --alarm-name "ECS-$service-TaskCount-Low" `
        --alarm-description "ECS service $service has < 1 running task" `
        --metric-name RunningTaskCount `
        --namespace ECS/ContainerInsights `
        --statistic Average `
        --period 60 `
        --evaluation-periods 3 `
        --threshold 1 `
        --comparison-operator LessThanThreshold `
        --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
        --alarm-actions $snsTopicArn `
        --region $Region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $alarmsCreated++
    }
}

Write-Host "  ✓ Created alarms for $($services.Count) ECS services" -ForegroundColor Green

# ===== SUMMARY =====
Write-Host "`n=== CloudWatch Alarms Summary ===" -ForegroundColor Cyan
Write-Host "Total alarms created: $alarmsCreated" -ForegroundColor Green
Write-Host "SNS topic: $snsTopicArn" -ForegroundColor White

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Subscribe to email alerts:"
Write-Host "   aws sns subscribe --topic-arn $snsTopicArn --protocol email --notification-endpoint your@email.com" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. View alarms in console:"
Write-Host "   https://console.aws.amazon.com/cloudwatch/home?region=$Region#alarmsV2:" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Configure alarm actions (auto-scaling, etc.) as needed" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ CloudWatch monitoring setup complete!" -ForegroundColor Green
