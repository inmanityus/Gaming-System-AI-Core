#!/bin/bash
# Configure NATS cluster without TLS for development/testing
# Run this on each NATS instance via SSM

set -euo pipefail

echo "=== Configuring NATS without TLS for dev/testing ==="

# Get instance metadata
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)
AZ=$(ec2-metadata --availability-zone | cut -d " " -f 2)

echo "Instance ID: $INSTANCE_ID"
echo "Private IP: $PRIVATE_IP"
echo "AZ: $AZ"

# Discover cluster members
ASG_NAME="nats-cluster-production"
AWS_REGION="us-east-1"

CLUSTER_MEMBERS=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$ASG_NAME" \
    --region "$AWS_REGION" \
    --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`].PrivateIpAddress' \
    --output text)

echo "Cluster members: $CLUSTER_MEMBERS"

# Build cluster routes
ROUTES=""
for IP in $CLUSTER_MEMBERS; do
    if [ "$IP" != "$PRIVATE_IP" ]; then
        ROUTES="${ROUTES}    nats-route://nats:natscluster@${IP}:6222\n"
    fi
done

# Generate NATS Configuration (NO TLS)
echo "=== Generating NATS Configuration (NO TLS) ==="
cat <<'EOF' | sudo tee /etc/nats/nats-server-no-tls.conf
# NATS Server Configuration - Development/Testing (NO TLS)
# WARNING: For development only - production MUST use TLS

server_name: "ENV_INSTANCE_ID"

# Client Connections (NO TLS)
listen: 0.0.0.0:4222
max_payload: 4MB

# Cluster Configuration (NO TLS)
cluster {
  name: "gaming-system-production"
  listen: 0.0.0.0:6222
  
  routes = [
ENV_ROUTES
  ]
}

# Leafnode Configuration (NO TLS)
leafnodes {
  listen: 0.0.0.0:7422
}

# HTTP Monitoring
http_port: 8222

# JetStream Configuration
jetstream {
  store_dir: "/var/lib/nats/jetstream"
  max_memory_store: 1GB
  max_file_store: 450GB
  domain: "production"
}

# Limits
max_connections: 10000
max_subscriptions: 0
max_pending: 64MB
max_control_line: 4096

# Logging
debug: false
trace: false
logtime: true
log_file: "/var/log/nats/nats-server.log"
log_size_limit: 100MB

# Performance
write_deadline: "5s"
ping_interval: "15s"
ping_max: 3
lame_duck_duration: "60s"
EOF

# Replace placeholders
sudo sed -i "s/ENV_INSTANCE_ID/$INSTANCE_ID/g" /etc/nats/nats-server-no-tls.conf
sudo sed -i "s|ENV_ROUTES|$(echo -e "$ROUTES")|g" /etc/nats/nats-server-no-tls.conf

echo "Configuration generated"

# Update systemd service to use no-TLS config
sudo sed -i 's|/etc/nats/nats-server.conf|/etc/nats/nats-server-no-tls.conf|g' /etc/systemd/system/nats-server.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start NATS
sudo systemctl enable nats-server
sudo systemctl start nats-server

# Wait for startup
sleep 5

# Check status
sudo systemctl status nats-server --no-pager

echo "=== NATS Configuration Complete ==="
echo "Status: Running without TLS (dev/test only)"
echo "Connection: nats://$PRIVATE_IP:4222"
echo "Monitoring: http://$PRIVATE_IP:8222"

