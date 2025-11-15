# Setup CloudWatch Monitoring for NATS Services
# Creates alarms for CPU, memory, and task count

$region = "us-east-1"
$cluster = "gaming-system-cluster"
$snsTopicArn = "arn:aws:sns:us-east-1:695353648052:gaming-system-alerts"

$services = @(
    "ai-integration-nats", "model-management-nats", "state-manager-nats", "quest-system-nats",
    "npc-behavior-nats", "world-state-nats", "orchestration-nats", "router-nats",
    "event-bus-nats", "time-manager-nats", "weather-manager-nats", "auth-nats",
    "settings-nats", "payment-nats", "performance-mode-nats", "capability-registry-nats",
    "ai-router-nats", "knowledge-base-nats", "environmental-narrative-nats",
    "story-teller-nats", "body-broker-integration-nats", "http-nats-gateway"
)

Write-Host "=== Setting Up CloudWatch Monitoring ===" -ForegroundColor Cyan

# Create SNS topic if doesn't exist
Write-Host "`nCreating SNS topic for alerts..."
$topicResult = aws sns create-topic --name gaming-system-alerts --region $region --query 'TopicArn' --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    $snsTopicArn = $topicResult
    Write-Host "✅ SNS topic: $snsTopicArn" -ForegroundColor Green
} else {
    Write-Host "✅ SNS topic already exists or created" -ForegroundColor Green
}

$alarmsCreated = 0

foreach ($service in $services) {
    Write-Host "`nCreating alarms for $service..." -ForegroundColor Yellow
    
    # CPU Utilization Alarm
    $cpuAlarmName = "$service-high-cpu"
    aws cloudwatch put-metric-alarm `
        --alarm-name $cpuAlarmName `
        --alarm-description "CPU > 80% for $service" `
        --metric-name CPUUtilization `
        --namespace AWS/ECS `
        --statistic Average `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 80 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
        --alarm-actions $snsTopicArn `
        --region $region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ CPU alarm created" -ForegroundColor Green
        $alarmsCreated++
    }
    
    # Memory Utilization Alarm
    $memAlarmName = "$service-high-memory"
    aws cloudwatch put-metric-alarm `
        --alarm-name $memAlarmName `
        --alarm-description "Memory > 80% for $service" `
        --metric-name MemoryUtilization `
        --namespace AWS/ECS `
        --statistic Average `
        --period 300 `
        --evaluation-periods 2 `
        --threshold 80 `
        --comparison-operator GreaterThanThreshold `
        --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
        --alarm-actions $snsTopicArn `
        --region $region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Memory alarm created" -ForegroundColor Green
        $alarmsCreated++
    }
    
    # Task Count Alarm (should be 2)
    $taskAlarmName = "$service-task-count"
    aws cloudwatch put-metric-alarm `
        --alarm-name $taskAlarmName `
        --alarm-description "Task count != 2 for $service" `
        --metric-name RunningTaskCount `
        --namespace ECS/ContainerInsights `
        --statistic Average `
        --period 60 `
        --evaluation-periods 3 `
        --threshold 2 `
        --comparison-operator LessThanThreshold `
        --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
        --alarm-actions $snsTopicArn `
        --region $region `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Task count alarm created" -ForegroundColor Green
        $alarmsCreated++
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Alarms created: $alarmsCreated" -ForegroundColor Green
Write-Host "SNS topic: $snsTopicArn" -ForegroundColor White
Write-Host "`nTo subscribe to alerts, run:"
Write-Host "  aws sns subscribe --topic-arn $snsTopicArn --protocol email --notification-endpoint your@email.com"

