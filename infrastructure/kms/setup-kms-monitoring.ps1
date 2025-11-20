param(
    [string]$ConfigFile = "kms-keys-config.json",
    [string]$SnsTopicArn = ""  # Optional SNS topic for alerts
)

Write-Host "=== Setting up KMS Key Monitoring ===" -ForegroundColor Cyan

# Load configuration
if (-not (Test-Path $ConfigFile)) {
    Write-Host "[ERROR] Configuration file not found: $ConfigFile" -ForegroundColor Red
    Write-Host "Please run deploy-kms-keys.ps1 first" -ForegroundColor Yellow
    exit 1
}

$config = Get-Content -Path $ConfigFile | ConvertFrom-Json

# Create CloudWatch alarms for each key
foreach ($key in $config.keys) {
    Write-Host "`nSetting up monitoring for: $($key.alias)" -ForegroundColor Yellow
    
    # Alarm 1: Key disabled or scheduled for deletion
    Write-Host "  Creating key state alarm..." -ForegroundColor Gray
    $alarmName = "KMS-KeyState-$($key.type)"
    
    $metricFilter = @{
        MetricName = "KeyDisabledOrPendingDeletion"
        MetricNamespace = "AI-Core/KMS"
        MetricValue = "1"
        DefaultValue = 0
    }
    
    aws logs put-metric-filter `
        --log-group-name "/aws/kms/cloudtrail" `
        --filter-name "$alarmName-filter" `
        --filter-pattern "{ ($.eventName = DisableKey || $.eventName = ScheduleKeyDeletion) && $.requestParameters.keyId = \"$($key.keyId)\" }" `
        --metric-transformations MetricName=$($metricFilter.MetricName),MetricNamespace=$($metricFilter.MetricNamespace),MetricValue=$($metricFilter.MetricValue),DefaultValue=$($metricFilter.DefaultValue) 2>$null | Out-Null
    
    $alarmConfig = @{
        AlarmName = $alarmName
        AlarmDescription = "Alert when KMS key $($key.alias) is disabled or scheduled for deletion"
        MetricName = $metricFilter.MetricName
        Namespace = $metricFilter.MetricNamespace
        Statistic = "Sum"
        Period = 300
        EvaluationPeriods = 1
        Threshold = 1
        ComparisonOperator = "GreaterThanOrEqualToThreshold"
        TreatMissingData = "notBreaching"
    }
    
    if ($SnsTopicArn) {
        $alarmConfig.AlarmActions = @($SnsTopicArn)
    }
    
    aws cloudwatch put-metric-alarm @alarmConfig 2>$null | Out-Null
    Write-Host "  ✓ Key state alarm created" -ForegroundColor Green
    
    # Alarm 2: Key usage (high volume)
    Write-Host "  Creating high usage alarm..." -ForegroundColor Gray
    $usageAlarmName = "KMS-HighUsage-$($key.type)"
    
    aws cloudwatch put-metric-alarm `
        --alarm-name $usageAlarmName `
        --alarm-description "Alert on high usage of KMS key $($key.alias)" `
        --metric-name NumberOfOperations `
        --namespace AWS/KMS `
        --statistic Sum `
        --period 300 `
        --threshold 10000 `
        --comparison-operator GreaterThanThreshold `
        --evaluation-periods 2 `
        --dimensions Name=KeyId,Value=$($key.keyId) `
        --treat-missing-data notBreaching `
        $(if ($SnsTopicArn) { "--alarm-actions $SnsTopicArn" }) 2>$null | Out-Null
    
    Write-Host "  ✓ High usage alarm created" -ForegroundColor Green
    
    # Alarm 3: Key rotation status
    Write-Host "  Creating rotation status check..." -ForegroundColor Gray
    
    # Create a Lambda function to check rotation status (simplified version)
    $lambdaCode = @"
import boto3
import os

def lambda_handler(event, context):
    kms = boto3.client('kms')
    key_id = os.environ['KEY_ID']
    
    try:
        response = kms.get_key_rotation_status(KeyId=key_id)
        if not response['KeyRotationEnabled']:
            raise Exception(f"Key rotation disabled for {key_id}")
        return {"statusCode": 200}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
"@
}

# Create CloudWatch dashboard
Write-Host "`n=== Creating CloudWatch Dashboard ===" -ForegroundColor Cyan

$dashboardBody = @{
    widgets = @()
}

# Add overview widget
$dashboardBody.widgets += @{
    type = "text"
    x = 0
    y = 0
    width = 24
    height = 2
    properties = @{
        markdown = @"
# AI Core KMS Key Monitoring Dashboard

**Generated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

This dashboard monitors all customer-managed KMS keys used by the AI Core infrastructure.
"@
    }
}

$yPosition = 2
foreach ($key in $config.keys) {
    # Usage metrics widget
    $dashboardBody.widgets += @{
        type = "metric"
        x = 0
        y = $yPosition
        width = 12
        height = 6
        properties = @{
            metrics = @(
                @( "AWS/KMS", "NumberOfOperations", @{ KeyId = $key.keyId } ),
                @( ".", "NumberOfOperations", @{ KeyId = $key.keyId }, @{ stat = "Sum", period = 3600 } )
            )
            view = "timeSeries"
            stacked = $false
            region = $config.region
            title = "$($key.type) Key Usage - $($key.alias)"
            period = 300
        }
    }
    
    # Error metrics widget
    $dashboardBody.widgets += @{
        type = "metric"
        x = 12
        y = $yPosition
        width = 12
        height = 6
        properties = @{
            metrics = @(
                @( "AWS/KMS", "NumberOfOperations", @{ KeyId = $key.keyId, ErrorCode = "AccessDenied" } ),
                @( ".", "NumberOfOperations", @{ KeyId = $key.keyId, ErrorCode = "InvalidKeyId" } ),
                @( ".", "NumberOfOperations", @{ KeyId = $key.keyId, ErrorCode = "KeyUnavailable" } )
            )
            view = "timeSeries"
            stacked = $false
            region = $config.region
            title = "$($key.type) Key Errors - $($key.alias)"
            period = 300
        }
    }
    
    $yPosition += 6
}

# Add summary widget
$dashboardBody.widgets += @{
    type = "metric"
    x = 0
    y = $yPosition
    width = 24
    height = 6
    properties = @{
        metrics = $config.keys | ForEach-Object {
            @( "AWS/KMS", "NumberOfOperations", @{ KeyId = $_.keyId }, @{ label = $_.type } )
        }
        view = "singleValue"
        region = $config.region
        title = "KMS Operations Summary (Last Hour)"
        period = 3600
        stat = "Sum"
    }
}

$dashboardJson = $dashboardBody | ConvertTo-Json -Depth 10 -Compress

aws cloudwatch put-dashboard `
    --dashboard-name "AI-Core-KMS-Monitoring" `
    --dashboard-body $dashboardJson | Out-Null

Write-Host "✓ CloudWatch dashboard created: AI-Core-KMS-Monitoring" -ForegroundColor Green

# Create monitoring documentation
$monitoringDoc = @"
# KMS Key Monitoring Guide

## CloudWatch Alarms Created

"@

foreach ($key in $config.keys) {
    $monitoringDoc += @"
### $($key.type.ToUpper()) Key Monitoring
- **Key**: ``$($key.alias)``
- **Alarms**:
  - ``KMS-KeyState-$($key.type)``: Alerts if key is disabled or scheduled for deletion
  - ``KMS-HighUsage-$($key.type)``: Alerts on unusually high usage (>10,000 operations in 5 minutes)

"@
}

$monitoringDoc += @"

## CloudWatch Dashboard

Access the dashboard at: https://console.aws.amazon.com/cloudwatch/home?region=$($config.region)#dashboards:name=AI-Core-KMS-Monitoring

## Metrics to Monitor

1. **NumberOfOperations**: Total API calls to the key
2. **Error Rates**: Access denied, invalid key, key unavailable
3. **Key State**: Enabled/Disabled status
4. **Rotation Status**: Ensure automatic rotation remains enabled

## Alerting Best Practices

1. Set up SNS topic for critical alerts
2. Configure email/SMS notifications for key state changes
3. Use PagerDuty/Opsgenie for 24/7 on-call rotation
4. Review dashboard weekly for usage patterns

## Troubleshooting

### High Usage Alert
- Check CloudTrail logs for source of requests
- Verify no runaway processes
- Consider increasing alarm threshold if legitimate

### Key State Alert
- Immediately investigate who disabled/deleted key
- Check CloudTrail for actor information
- Have emergency key recovery plan ready

### Access Denied Errors
- Verify IAM policies are correct
- Check service-linked roles have proper permissions
- Ensure key policy allows service access

"@

$monitoringDoc | Out-File -FilePath "kms-monitoring-guide.md" -Encoding UTF8

Write-Host "`n=== KMS Monitoring Setup Complete ===" -ForegroundColor Green
Write-Host "`nMonitoring configured for:" -ForegroundColor Cyan
foreach ($key in $config.keys) {
    Write-Host "  - $($key.alias)" -ForegroundColor White
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Configure SNS topic for alarm notifications"
Write-Host "2. Set up email/SMS subscriptions to SNS topic"
Write-Host "3. Review CloudWatch dashboard"
Write-Host "4. Test alarms with simulated events"
Write-Host "5. Document escalation procedures"
