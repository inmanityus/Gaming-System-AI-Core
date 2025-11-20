# PowerShell script to configure NATS without TLS on all instances
$instances = @("i-029fd07957aa43904", "i-04789e0fb640aa4f1", "i-066a13d419e8f629e", "i-081286dbf1781585a", "i-0d10ab7ef2b3ec8ed")

Write-Host "Configuring NATS without TLS on instances..." -ForegroundColor Cyan

foreach ($instanceId in $instances) {
    Write-Host "`nConfiguring instance: $instanceId" -ForegroundColor Yellow
    
    $commands = @(
        'echo "=== Configuring NATS without TLS ==="',
        'INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)',
        'PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)',
        'echo "Instance: $INSTANCE_ID at $PRIVATE_IP"',
        '',
        '# Get cluster members',
        'CLUSTER_MEMBERS=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "nats-cluster-production" --region "us-east-1" --query "AutoScalingGroups[0].Instances[?HealthStatus==\`Healthy\`].PrivateIpAddress" --output text)',
        'echo "Cluster members: $CLUSTER_MEMBERS"',
        '',
        '# Build routes',
        'ROUTES=""',
        'for IP in $CLUSTER_MEMBERS; do',
        '    if [ "$IP" != "$PRIVATE_IP" ]; then',
        '        ROUTES="${ROUTES}    nats-route://nats:natscluster@${IP}:6222\n"',
        '    fi',
        'done',
        '',
        '# Create config',
        'sudo mkdir -p /etc/nats',
        'cat <<EOF | sudo tee /etc/nats/nats-server-no-tls.conf',
        'server_name: "$INSTANCE_ID"',
        '',
        'listen: 0.0.0.0:4222',
        'max_payload: 4MB',
        '',
        'cluster {',
        '  name: "gaming-system-production"',
        '  listen: 0.0.0.0:6222',
        '  routes = [',
        '$(echo -e "$ROUTES")',
        '  ]',
        '}',
        '',
        'leafnodes {',
        '  listen: 0.0.0.0:7422',
        '}',
        '',
        'http_port: 8222',
        '',
        'jetstream {',
        '  store_dir: "/var/lib/nats/jetstream"',
        '  max_memory_store: 1GB',
        '  max_file_store: 450GB',
        '  domain: "production"',
        '}',
        '',
        'max_connections: 10000',
        'max_subscriptions: 0',
        'max_pending: 64MB',
        'max_control_line: 4096',
        '',
        'debug: false',
        'trace: false',
        'logtime: true',
        'log_file: "/var/log/nats/nats-server.log"',
        'log_size_limit: 100MB',
        '',
        'write_deadline: "5s"',
        'ping_interval: "15s"',
        'ping_max: 3',
        'lame_duck_duration: "60s"',
        'EOF',
        '',
        '# Update systemd service',
        'sudo sed -i "s|/etc/nats/nats-server.conf|/etc/nats/nats-server-no-tls.conf|g" /etc/systemd/system/nats-server.service',
        '',
        '# Start NATS',
        'sudo systemctl daemon-reload',
        'sudo systemctl enable nats-server',
        'sudo systemctl restart nats-server',
        '',
        '# Check status',
        'sleep 5',
        'sudo systemctl status nats-server --no-pager',
        'echo "NATS configured at nats://$PRIVATE_IP:4222"'
    )
    
    $result = aws ssm send-command `
        --instance-ids $instanceId `
        --document-name "AWS-RunShellScript" `
        --comment "Configure NATS without TLS" `
        --parameters "commands=$($commands | ConvertTo-Json -Compress)" `
        --output json | ConvertFrom-Json
    
    $commandId = $result.Command.CommandId
    Write-Host "Command ID: $commandId"
    
    # Wait for completion
    Write-Host "Waiting for execution..."
    Start-Sleep -Seconds 10
    
    # Check result
    $output = aws ssm get-command-invocation `
        --command-id $commandId `
        --instance-id $instanceId `
        --output json | ConvertFrom-Json
    
    if ($output.Status -eq "Success") {
        Write-Host "✅ Success on $instanceId" -ForegroundColor Green
        Write-Host "Output:" -ForegroundColor Cyan
        Write-Host $output.StandardOutputContent
    } else {
        Write-Host "❌ Failed on $instanceId" -ForegroundColor Red
        Write-Host "Error:" -ForegroundColor Red
        Write-Host $output.StandardErrorContent
    }
}

Write-Host "`nNATS configuration complete!" -ForegroundColor Green
