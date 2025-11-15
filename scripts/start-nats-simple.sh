#!/bin/bash
# Simple NATS startup script - no TLS
set -e

echo "=== Starting NATS Server (Simple Mode) ==="

# Get instance metadata
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)

echo "Instance: $INSTANCE_ID"
echo "IP: $PRIVATE_IP"

# Create JetStream directory
sudo mkdir -p /var/lib/nats/jetstream
sudo chown -R ec2-user:ec2-user /var/lib/nats 2>/dev/null || sudo chown -R ubuntu:ubuntu /var/lib/nats

# Create simple config
cat > /tmp/nats-simple.conf <<EOF
server_name: "$INSTANCE_ID"
listen: 0.0.0.0:4222
http_port: 8222
jetstream {
  store_dir: "/var/lib/nats/jetstream"
  max_file_store: 100GB
}
max_connections: 10000
max_payload: 1MB
ping_interval: 15s
ping_max: 3
EOF

# Stop any existing NATS
sudo pkill nats-server 2>/dev/null || true
sleep 2

# Start NATS
echo "Starting NATS..."
sudo /usr/local/bin/nats-server -c /tmp/nats-simple.conf -D > /var/log/nats-startup.log 2>&1 &

sleep 3

# Verify
if pgrep nats-server > /dev/null; then
    echo "✅ NATS running"
    curl -s http://localhost:8222/healthz && echo " (healthy)"
else
    echo "❌ NATS failed to start"
    cat /var/log/nats-startup.log
    exit 1
fi

