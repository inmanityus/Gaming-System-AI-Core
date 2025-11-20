# Simple script to configure NATS on all instances
param(
    [string[]]$InstanceIds = @(
        "i-029fd07957aa43904",
        "i-04789e0fb640aa4f1",
        "i-066a13d419e8f629e",
        "i-081286dbf1781585a",
        "i-0d10ab7ef2b3ec8ed"
    )
)

Write-Host "Configuring NATS on $($InstanceIds.Count) instances..." -ForegroundColor Cyan

foreach ($instanceId in $InstanceIds) {
    Write-Host "`nConfiguring $instanceId..." -ForegroundColor Yellow
    
    # Step 1: Create systemd service
    Write-Host "  Creating systemd service..."
    $cmd1 = aws ssm send-command `
        --instance-ids $instanceId `
        --document-name "AWS-RunShellScript" `
        --comment "Create NATS systemd service" `
        --parameters 'commands=["cat > /tmp/nats-server.service << EOF
[Unit]
Description=NATS Server
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/nats-server -c /etc/nats/nats-server.conf
Restart=always
RestartSec=5
User=root
Group=root
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF","sudo mv /tmp/nats-server.service /etc/systemd/system/"]' `
        --query 'Command.CommandId' `
        --output text
    
    Start-Sleep -Seconds 3
    
    # Step 2: Create NATS config
    Write-Host "  Creating NATS configuration..."
    $cmd2 = aws ssm send-command `
        --instance-ids $instanceId `
        --document-name "AWS-RunShellScript" `
        --comment "Create NATS config" `
        --parameters 'commands=["sudo mkdir -p /etc/nats /var/log/nats","cat > /tmp/nats-server.conf << EOF
# NATS Server Configuration
listen: 0.0.0.0:4222
max_payload: 4MB
http_port: 8222
jetstream {
  store_dir: \"/var/lib/nats/jetstream\"
  max_memory_store: 1GB
  max_file_store: 450GB
}
max_connections: 10000
logtime: true
log_file: \"/var/log/nats/nats-server.log\"
EOF","sudo mv /tmp/nats-server.conf /etc/nats/"]' `
        --query 'Command.CommandId' `
        --output text
    
    Start-Sleep -Seconds 3
    
    # Step 3: Start NATS
    Write-Host "  Starting NATS server..."
    $cmd3 = aws ssm send-command `
        --instance-ids $instanceId `
        --document-name "AWS-RunShellScript" `
        --comment "Start NATS" `
        --parameters 'commands=["sudo systemctl daemon-reload","sudo systemctl enable nats-server","sudo systemctl restart nats-server"]' `
        --query 'Command.CommandId' `
        --output text
    
    Start-Sleep -Seconds 5
    
    # Check status
    $status = aws ssm get-command-invocation `
        --command-id $cmd3 `
        --instance-id $instanceId `
        --query 'Status' `
        --output text
    
    if ($status -eq "Success") {
        Write-Host "  ✅ NATS configured on $instanceId" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed on $instanceId" -ForegroundColor Red
    }
}

Write-Host "`nWaiting 10 seconds for all NATS services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Test connectivity
Write-Host "`nTesting NATS connectivity..." -ForegroundColor Cyan
$testResult = Test-NetConnection -ComputerName nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com -Port 4222 -InformationLevel Quiet

if ($testResult) {
    Write-Host "✅ NATS is accessible through load balancer!" -ForegroundColor Green
} else {
    Write-Host "❌ NATS is not accessible through load balancer" -ForegroundColor Red
    Write-Host "   This might be a security group or NLB health check issue" -ForegroundColor Yellow
}

