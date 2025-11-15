# Configure NATS instances via SSM (bypassing JSON escaping issues)
# Uses SSM Document to run shell script directly

$instanceIds = @("i-04789e0fb640aa4f1", "i-029fd07957aa43904", "i-066a13d419e8f629e", "i-081286dbf1781585a", "i-0d10ab7ef2b3ec8ed")

Write-Host "Configuring NATS instances..." -ForegroundColor Cyan

foreach ($instanceId in $instanceIds) {
    Write-Host "`nConfiguring $instanceId..."
    
    $command = @'
#!/bin/bash
set -e
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)

# Simple NATS config without TLS
sudo tee /etc/nats/nats-server-simple.conf > /dev/null <<'EOF'
server_name: "$INSTANCE_ID"
listen: 0.0.0.0:4222
http_port: 8222
jetstream {
  store_dir: "/var/lib/nats/jetstream"
  max_file_store: 100GB
}
max_connections: 10000
max_payload: 1MB
EOF

sudo sed -i "s/\$INSTANCE_ID/$INSTANCE_ID/g" /etc/nats/nats-server-simple.conf
sudo systemctl stop nats-server 2>/dev/null || true
sudo /usr/local/bin/nats-server -c /etc/nats/nats-server-simple.conf -D &
sleep 2
pgrep nats-server && echo "NATS running" || echo "NATS failed"
'@
    
    $result = aws ssm send-command `
        --instance-ids $instanceId `
        --document-name "AWS-RunShellScript" `
        --parameters commands="$command" `
        --region us-east-1 `
        --output text `
        --query 'Command.CommandId'
    
    if ($result) {
        Write-Host "  Command sent: $result" -ForegroundColor Green
    } else {
        Write-Host "  Failed to send command" -ForegroundColor Red
    }
}

Write-Host "`nWait 30 seconds, then check: aws ecs update-service --cluster gaming-system-cluster --service ai-integration-nats --force-new-deployment"

