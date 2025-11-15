#!/bin/bash
# NATS Server Installation and Configuration
# Peer Reviewed: Pending
# Purpose: Bootstrap NATS server on EC2 with JetStream enabled

set -euo pipefail

# Variables from Terraform
NATS_VERSION="${nats_version}"
ENVIRONMENT="${environment}"
CLUSTER_SIZE="${cluster_size}"
AWS_REGION="${aws_region}"

# Logging
exec > >(tee /var/log/nats-bootstrap.log)
exec 2>&1

echo "=== NATS Bootstrap Started ==="
echo "Version: $NATS_VERSION"
echo "Environment: $ENVIRONMENT"
echo "Cluster Size: $CLUSTER_SIZE"

# Update system
sudo dnf update -y

# Install dependencies
sudo dnf install -y wget tar gzip jq

# Mount JetStream data volume
echo "=== Mounting JetStream Volume ==="
DATA_DEVICE="/dev/nvme1n1"
MOUNT_POINT="/var/lib/nats/jetstream"

if [ ! -b "$DATA_DEVICE" ]; then
    echo "ERROR: JetStream data device $DATA_DEVICE not found"
    exit 1
fi

# Format if not formatted
if ! sudo blkid "$DATA_DEVICE" | grep -q "TYPE="; then
    echo "Formatting $DATA_DEVICE..."
    sudo mkfs.xfs "$DATA_DEVICE"
fi

# Create mount point
sudo mkdir -p "$MOUNT_POINT"

# Get UUID
UUID=$(sudo blkid -s UUID -o value "$DATA_DEVICE")

# Add to fstab
if ! grep -q "$UUID" /etc/fstab; then
    echo "UUID=$UUID $MOUNT_POINT xfs defaults,nofail 0 2" | sudo tee -a /etc/fstab
fi

# Mount
sudo mount -a
sudo chown -R nats:nats "$MOUNT_POINT" 2>/dev/null || true

echo "JetStream volume mounted at $MOUNT_POINT"

# Install NATS Server
echo "=== Installing NATS Server $${NATS_VERSION} ==="
cd /tmp
wget "https://github.com/nats-io/nats-server/releases/download/v$${NATS_VERSION}/nats-server-v$${NATS_VERSION}-linux-amd64.tar.gz"
tar -xzf "nats-server-v$${NATS_VERSION}-linux-amd64.tar.gz"
sudo mv "nats-server-v$${NATS_VERSION}-linux-amd64/nats-server" /usr/local/bin/
sudo chmod +x /usr/local/bin/nats-server

# Verify installation
/usr/local/bin/nats-server --version

# Create nats user
sudo useradd --system --no-create-home --shell /bin/false nats 2>/dev/null || true

# Create directories
sudo mkdir -p /etc/nats
sudo mkdir -p /var/log/nats
sudo mkdir -p "$MOUNT_POINT"
sudo chown -R nats:nats /var/log/nats
sudo chown -R nats:nats "$MOUNT_POINT"

# Get instance metadata
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)
AZ=$(ec2-metadata --availability-zone | cut -d " " -f 2)

echo "Instance ID: $INSTANCE_ID"
echo "Private IP: $PRIVATE_IP"
echo "Availability Zone: $AZ"

# Discover other cluster members via ASG
echo "=== Discovering Cluster Members ==="
ASG_NAME="nats-cluster-$${ENVIRONMENT}"
CLUSTER_MEMBERS=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$${ASG_NAME}" \
    --region "$${AWS_REGION}" \
    --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`].PrivateIpAddress' \
    --output text)

# Build cluster routes
ROUTES=""
for IP in $${CLUSTER_MEMBERS}; do
    if [ "$${IP}" != "$${PRIVATE_IP}" ]; then
        ROUTES="$${ROUTES}    nats-route://nats:natscluster@$${IP}:6222\n"
    fi
done

# Generate NATS Configuration
echo "=== Generating NATS Configuration ==="
cat <<EOF | sudo tee /etc/nats/nats-server.conf
# NATS Server Configuration
# Environment: $${ENVIRONMENT}
# Instance: $${INSTANCE_ID}

server_name: "$${INSTANCE_ID}"

# Client Connections
listen: 0.0.0.0:4222
max_payload: 4MB

# TLS Configuration (mTLS)
tls {
  cert_file: "/etc/nats/certs/server-cert.pem"
  key_file: "/etc/nats/certs/server-key.pem"
  ca_file: "/etc/nats/certs/ca-cert.pem"
  verify: true
  timeout: 5
}

# Cluster Configuration
cluster {
  name: "gaming-system-$${ENVIRONMENT}"
  listen: 0.0.0.0:6222
  
  routes = [
$(echo -e "$${ROUTES}")
  ]
  
  tls {
    cert_file: "/etc/nats/certs/server-cert.pem"
    key_file: "/etc/nats/certs/server-key.pem"
    ca_file: "/etc/nats/certs/ca-cert.pem"
    verify: true
    timeout: 5
  }
}

# Leafnode Configuration
leafnodes {
  listen: 0.0.0.0:7422
  
  tls {
    cert_file: "/etc/nats/certs/server-cert.pem"
    key_file: "/etc/nats/certs/server-key.pem"
    ca_file: "/etc/nats/certs/ca-cert.pem"
    verify: true
    timeout: 5
  }
}

# HTTP Monitoring
http_port: 8222

# JetStream Configuration
jetstream {
  store_dir: "$${MOUNT_POINT}"
  max_memory_store: 1GB
  max_file_store: 450GB
  domain: "$${ENVIRONMENT}"
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

# Accounts (JWT-based authentication)
# Note: Will be configured via resolver after initial deployment
EOF

echo "Configuration generated at /etc/nats/nats-server.conf"

# Create systemd service
echo "=== Creating systemd Service ==="
cat <<EOF | sudo tee /etc/systemd/system/nats-server.service
[Unit]
Description=NATS Server
After=network.target

[Service]
Type=simple
User=nats
Group=nats
ExecStart=/usr/local/bin/nats-server -c /etc/nats/nats-server.conf
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

# Note: Service won't start until TLS certs are provisioned
# This will be done by configuration management after Terraform applies

echo "=== NATS Bootstrap Complete ==="
echo "Status: Ready for certificate provisioning"
echo "Next: Deploy TLS certificates to /etc/nats/certs/"
echo "Then: sudo systemctl enable nats-server && sudo systemctl start nats-server"

