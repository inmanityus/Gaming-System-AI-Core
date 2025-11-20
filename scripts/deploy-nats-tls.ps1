#!/usr/bin/env pwsh
# Deploy NATS TLS configuration to all instances

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Deploying NATS TLS Configuration ===${NC}"

# Read the setup script
$scriptPath = Join-Path $PSScriptRoot "nats-tls-setup.sh"
if (-not (Test-Path $scriptPath)) {
    Write-Host "${RED}ERROR: nats-tls-setup.sh not found${NC}"
    exit 1
}

$scriptContent = Get-Content -Path $scriptPath -Raw

# Get NATS instance IDs
Write-Host "${YELLOW}Getting NATS instance IDs...${NC}"
$instanceIds = aws autoscaling describe-auto-scaling-groups `
    --auto-scaling-group-names "nats-cluster-$Environment" `
    --query 'AutoScalingGroups[0].Instances[*].InstanceId' `
    --output text

if (-not $instanceIds) {
    Write-Host "${RED}ERROR: No NATS instances found${NC}"
    exit 1
}

$instances = $instanceIds -split '\s+'
Write-Host "Found $($instances.Count) NATS instances"

# Deploy to all instances
Write-Host "${YELLOW}Deploying TLS configuration script...${NC}"

# Create temporary file for script
$tempScript = New-TemporaryFile
Set-Content -Path $tempScript -Value $scriptContent -NoNewline

# Send command to all instances at once
$instanceList = $instances -join ","
$result = aws ssm send-command `
    --instance-ids $instances `
    --document-name "AWS-RunShellScript" `
    --parameters "commands=['$(Get-Content $tempScript -Raw)']" `
    --timeout-seconds 300 `
    --output json | ConvertFrom-Json

# Clean up temp file
Remove-Item -Path $tempScript -Force

if ($LASTEXITCODE -ne 0) {
    Write-Host "${RED}ERROR: Failed to send SSM command${NC}"
    exit 1
}

$commandId = $result.Command.CommandId
Write-Host "Command ID: $commandId"
Write-Host "Waiting for deployment to complete on all instances..."

# Wait for command to complete on all instances
$maxWait = 300  # 5 minutes
$checkInterval = 10
$elapsed = 0

while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds $checkInterval
    $elapsed += $checkInterval
    
    # Check command status
    $invocations = aws ssm list-command-invocations `
        --command-id $commandId `
        --details `
        --output json | ConvertFrom-Json
    
    $statuses = $invocations.CommandInvocations | ForEach-Object {
        @{
            InstanceId = $_.InstanceId
            Status = $_.Status
            StatusDetails = $_.StatusDetails
        }
    }
    
    $completed = $statuses | Where-Object { $_.Status -in @("Success", "Failed", "TimedOut", "Cancelled") }
    $pending = $statuses | Where-Object { $_.Status -in @("Pending", "InProgress", "Delayed") }
    
    Write-Host "Status: $($completed.Count) completed, $($pending.Count) pending"
    
    if ($pending.Count -eq 0) {
        break
    }
}

# Get final results
Write-Host ""
Write-Host "${GREEN}=== Deployment Results ===${NC}"

$success = @()
$failed = @()

foreach ($instanceId in $instances) {
    $status = aws ssm get-command-invocation `
        --command-id $commandId `
        --instance-id $instanceId `
        --query 'Status' `
        --output text 2>$null
    
    if ($status -eq "Success") {
        Write-Host "${GREEN}✓ $instanceId : TLS configured successfully${NC}"
        $success += $instanceId
    }
    else {
        $error = aws ssm get-command-invocation `
            --command-id $commandId `
            --instance-id $instanceId `
            --query 'StandardErrorContent' `
            --output text 2>$null
        
        Write-Host "${RED}✗ $instanceId : Failed - $status${NC}"
        if ($error) {
            Write-Host "  Error: $error"
        }
        $failed += $instanceId
    }
}

Write-Host ""
Write-Host "${GREEN}=== Summary ===${NC}"
Write-Host "Total instances: $($instances.Count)"
Write-Host "Successful: $($success.Count)"
Write-Host "Failed: $($failed.Count)"

if ($failed.Count -eq 0) {
    Write-Host ""
    Write-Host "${GREEN}✓ All NATS instances configured with TLS successfully!${NC}"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Update ECS services to use TLS connection strings"
    Write-Host "2. Configure public ALB for gateway"
    Write-Host "3. Run end-to-end tests"
    exit 0
}
else {
    Write-Host ""
    Write-Host "${RED}Some instances failed to configure TLS${NC}"
    Write-Host "Failed instances:"
    foreach ($id in $failed) {
        Write-Host "  - $id"
    }
    exit 1
}
