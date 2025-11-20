#!/usr/bin/env pwsh
# Simple NATS TLS Deployment Script

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

Write-Host "${GREEN}=== Simple NATS TLS Deployment ===${NC}"

# Get NATS instances
$instances = (aws autoscaling describe-auto-scaling-groups `
    --auto-scaling-group-names "nats-cluster-$Environment" `
    --query 'AutoScalingGroups[0].Instances[*].InstanceId' `
    --output text) -split '\s+'

Write-Host "Found $($instances.Count) instances"

# Simple TLS setup commands to run on each instance
$commands = @(
    'echo "=== Setting up NATS TLS ==="',
    'INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)',
    'echo "Instance: $INSTANCE_ID"',
    
    # Create directories
    'mkdir -p /etc/nats/tls',
    'chmod 700 /etc/nats/tls',
    
    # Get CA cert
    'aws secretsmanager get-secret-value --secret-id "nats/certs/ca-cert" --query "SecretString" --output text --region us-east-1 > /etc/nats/tls/ca-cert.pem',
    'chmod 644 /etc/nats/tls/ca-cert.pem',
    
    # Generate self-signed cert for now (we'll use proper CA later)
    'openssl req -new -x509 -nodes -days 365 -keyout /etc/nats/tls/server-key.pem -out /etc/nats/tls/server-cert.pem -subj "/C=US/O=Gaming System/OU=NATS/CN=nats-$INSTANCE_ID"',
    'chmod 600 /etc/nats/tls/server-key.pem',
    'chmod 644 /etc/nats/tls/server-cert.pem',
    
    # Create simple NATS config
    'cat > /etc/nats/nats-server.conf << EOF
# NATS Server Config
server_name: "nats-$INSTANCE_ID"
port: 4222
tls {
  cert_file: "/etc/nats/tls/server-cert.pem"
  key_file: "/etc/nats/tls/server-key.pem"
  ca_file: "/etc/nats/tls/ca-cert.pem"
}
cluster {
  port: 6222
  tls {
    cert_file: "/etc/nats/tls/server-cert.pem"
    key_file: "/etc/nats/tls/server-key.pem"
    ca_file: "/etc/nats/tls/ca-cert.pem"
  }
}
http: 0.0.0.0:8222
jetstream {
  store_dir: "/data/jetstream"
}
EOF',
    
    # Restart NATS
    'pkill -f nats-server || true',
    'sleep 2',
    'nohup nats-server -c /etc/nats/nats-server.conf > /var/log/nats-server.log 2>&1 &',
    'sleep 5',
    'pgrep -f nats-server && echo "NATS running with TLS" || echo "NATS failed to start"'
)

# Process each instance
$success = @()
$failed = @()

foreach ($instance in $instances) {
    Write-Host ""
    Write-Host "${YELLOW}Configuring $instance...${NC}"
    
    try {
        # Send commands
        $result = aws ssm send-command `
            --instance-ids $instance `
            --document-name "AWS-RunShellScript" `
            --parameters (@{commands=$commands} | ConvertTo-Json -Compress) `
            --timeout-seconds 180 `
            --output json | ConvertFrom-Json
        
        $commandId = $result.Command.CommandId
        
        # Wait for completion
        $maxWait = 120
        $waited = 0
        $status = "InProgress"
        
        while ($waited -lt $maxWait -and $status -eq "InProgress") {
            Start-Sleep -Seconds 10
            $waited += 10
            
            $status = aws ssm get-command-invocation `
                --command-id $commandId `
                --instance-id $instance `
                --query 'Status' `
                --output text 2>$null
        }
        
        if ($status -eq "Success") {
            Write-Host "${GREEN}✓ Success${NC}"
            $success += $instance
        }
        else {
            Write-Host "${RED}✗ Failed ($status)${NC}"
            $failed += $instance
            
            # Get error details
            $error = aws ssm get-command-invocation `
                --command-id $commandId `
                --instance-id $instance `
                --query 'StandardErrorContent' `
                --output text 2>$null
            
            if ($error) {
                Write-Host "Error: $error"
            }
        }
    }
    catch {
        Write-Host "${RED}✗ Exception: $_${NC}"
        $failed += $instance
    }
}

Write-Host ""
Write-Host "${GREEN}=== Summary ===${NC}"
Write-Host "Success: $($success.Count)/$($instances.Count)"
Write-Host "Failed: $($failed.Count)"

if ($failed.Count -eq 0) {
    Write-Host "${GREEN}✓ All instances configured!${NC}"
    exit 0
}
else {
    Write-Host "${RED}Some instances failed${NC}"
    exit 1
}
