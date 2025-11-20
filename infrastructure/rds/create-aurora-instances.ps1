param(
    [string]$ClusterName = "ai-core-aurora-cluster"
)

Write-Host "Creating Aurora instances for cluster: $ClusterName" -ForegroundColor Cyan

# Get monitoring role ARN
$accountId = aws sts get-caller-identity --query Account --output text
$monitoringRoleArn = "arn:aws:iam::${accountId}:role/rds-enhanced-monitoring-role"

# Define instances
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

# Create each instance
foreach ($instance in $instances) {
    Write-Host "`nCreating instance: $($instance.identifier) ($($instance.instanceClass))" -ForegroundColor Yellow
    
    $existingInstance = aws rds describe-db-instances `
        --db-instance-identifier $instance.identifier `
        --query "DBInstances[0].DBInstanceIdentifier" `
        --output text 2>$null
    
    if ($existingInstance -ne $instance.identifier) {
        $createResult = aws rds create-db-instance `
            --db-instance-identifier $instance.identifier `
            --db-cluster-identifier $ClusterName `
            --engine "aurora-postgresql" `
            --db-instance-class $instance.instanceClass `
            --db-parameter-group-name "default.aurora-postgresql15" `
            --monitoring-interval 60 `
            --monitoring-role-arn $monitoringRoleArn `
            --auto-minor-version-upgrade `
            --tags "Key=Name,Value=$($instance.identifier)" "Key=Role,Value=$($instance.role)" "Key=Project,Value=AI-Core" `
            --output json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Instance creation initiated: $($instance.identifier)" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Failed to create instance: $($instance.identifier)" -ForegroundColor Red
            Write-Host $createResult
        }
    } else {
        Write-Host "✓ Instance already exists: $($instance.identifier)" -ForegroundColor Yellow
    }
}

# Wait for instances to be available
Write-Host "`nWaiting for instances to become available..." -ForegroundColor Yellow
$maxWaitMinutes = 15
$startTime = Get-Date

foreach ($instance in $instances) {
    $instanceReady = $false
    
    while (-not $instanceReady -and ((Get-Date) - $startTime).TotalMinutes -lt $maxWaitMinutes) {
        $status = aws rds describe-db-instances `
            --db-instance-identifier $instance.identifier `
            --query "DBInstances[0].DBInstanceStatus" `
            --output text 2>$null
        
        if ($status -eq "available") {
            Write-Host "✓ $($instance.identifier) is available" -ForegroundColor Green
            $instanceReady = $true
        } else {
            Write-Host -NoNewline "`r$($instance.identifier): $status" -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
    }
}

Write-Host "`n=== Aurora Instances Created Successfully ===" -ForegroundColor Green

# Display instance details
$clusterInfo = aws rds describe-db-clusters --db-cluster-identifier $ClusterName --output json | ConvertFrom-Json
$cluster = $clusterInfo.DBClusters[0]

Write-Host "`nCluster Endpoints:" -ForegroundColor Cyan
Write-Host "  Writer: $($cluster.Endpoint)" -ForegroundColor White
Write-Host "  Reader: $($cluster.ReaderEndpoint)" -ForegroundColor White

$instances = aws rds describe-db-instances --filters "Name=db-cluster-id,Values=$ClusterName" --output json | ConvertFrom-Json
Write-Host "`nInstances:" -ForegroundColor Cyan
foreach ($instance in $instances.DBInstances) {
    Write-Host "  $($instance.DBInstanceIdentifier): $($instance.DBInstanceStatus) ($($instance.DBInstanceClass))" -ForegroundColor White
}
