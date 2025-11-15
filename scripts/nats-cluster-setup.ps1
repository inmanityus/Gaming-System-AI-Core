# Configure all NATS instances without TLS for development
# Uses AWS Systems Manager to run commands on all instances

param(
    [string]$AsgName = "nats-cluster-production",
    [string]$Region = "us-east-1"
)

Write-Host "=== Configuring NATS Cluster (No TLS - Dev/Test) ===" -ForegroundColor Cyan

# Get instance IDs from ASG
Write-Host "Getting NATS instance IDs from ASG..."
$instances = aws autoscaling describe-auto-scaling-groups `
    --auto-scaling-group-names $AsgName `
    --region $Region `
    --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`].InstanceId' `
    --output json | ConvertFrom-Json

if (-not $instances -or $instances.Count -eq 0) {
    Write-Error "No healthy instances found in ASG $AsgName"
    exit 1
}

Write-Host "Found $($instances.Count) healthy instances"

# Read configuration script
$scriptPath = Join-Path $PSScriptRoot "nats-configure-no-tls.sh"
if (-not (Test-Path $scriptPath)) {
    Write-Error "Script not found: $scriptPath"
    exit 1
}

$scriptContent = Get-Content $scriptPath -Raw

# Run on each instance via SSM
foreach ($instanceId in $instances) {
    Write-Host "`nConfiguring instance $instanceId..." -ForegroundColor Yellow
    
    # Send command via SSM
    $commandId = aws ssm send-command `
        --instance-ids $instanceId `
        --document-name "AWS-RunShellScript" `
        --parameters "commands=`"$scriptContent`"" `
        --region $Region `
        --query 'Command.CommandId' `
        --output text
    
    Write-Host "  Command ID: $commandId"
    
    # Wait for command to complete
    Write-Host "  Waiting for command to complete..."
    Start-Sleep -Seconds 10
    
    $status = aws ssm get-command-invocation `
        --command-id $commandId `
        --instance-id $instanceId `
        --region $Region `
        --query 'Status' `
        --output text
    
    Write-Host "  Status: $status" -ForegroundColor $(if ($status -eq "Success") { "Green" } else { "Red" })
    
    # Get output
    if ($status -eq "Success") {
        $output = aws ssm get-command-invocation `
            --command-id $commandId `
            --instance-id $instanceId `
            --region $Region `
            --query 'StandardOutputContent' `
            --output text
        
        Write-Host "  Output (last 500 chars):"
        Write-Host "  $($output.Substring([Math]::Max(0, $output.Length - 500)))" -ForegroundColor Gray
    } else {
        $errorOutput = aws ssm get-command-invocation `
            --command-id $commandId `
            --instance-id $instanceId `
            --region $Region `
            --query 'StandardErrorContent' `
            --output text
        
        Write-Host "  Error: $errorOutput" -ForegroundColor Red
    }
}

Write-Host "`n=== NATS Cluster Configuration Complete ===" -ForegroundColor Green
Write-Host "All $($instances.Count) instances configured"
Write-Host "`nConnection details:"
Write-Host "  Internal NLB: nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
Write-Host "  Protocol: NATS (NO TLS - dev/test only)"
Write-Host "`nNext: Update ECS services to use NATS_URL environment variable"

