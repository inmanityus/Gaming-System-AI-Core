#!/bin/bash
# NATS TLS Setup Script
# This script will be executed on each NATS instance

set -e

echo "=== NATS TLS Setup Starting ==="

# Variables
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
CA_ARN="arn:aws:acm-pca:us-east-1:695353648052:certificate-authority/af7d3866-58c2-4957-9aad-5d9a5d1f7f41"

echo "Instance ID: $INSTANCE_ID"
echo "Private IP: $PRIVATE_IP"

# Create directories
echo "Creating TLS directories..."
mkdir -p /etc/nats/tls
chmod 700 /etc/nats/tls

# Get CA certificate from Secrets Manager
echo "Retrieving CA certificate..."
CA_CERT=$(aws secretsmanager get-secret-value --secret-id "nats/certs/ca-cert" --query 'SecretString' --output text --region us-east-1)

# Save CA certificate
echo "$CA_CERT" > /etc/nats/tls/ca-cert.pem
chmod 644 /etc/nats/tls/ca-cert.pem

# Generate private key
echo "Generating private key..."
openssl genrsa -out /etc/nats/tls/server-key.pem 4096
chmod 600 /etc/nats/tls/server-key.pem

# Create certificate configuration
echo "Creating certificate configuration..."
cat > /tmp/cert.conf << EOF
[req]
default_bits = 4096
prompt = no
default_md = sha512
distinguished_name = dn
req_extensions = v3_req

[dn]
CN = nats-${INSTANCE_ID}
O = Gaming System
OU = NATS Cluster
C = US

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = nats-${INSTANCE_ID}
DNS.2 = nats-${INSTANCE_ID}.internal
DNS.3 = localhost
IP.1 = ${PRIVATE_IP}
IP.2 = 127.0.0.1
EOF

# Generate CSR
echo "Generating certificate signing request..."
openssl req -new -key /etc/nats/tls/server-key.pem -out /tmp/server.csr -config /tmp/cert.conf

# Issue certificate from Private CA
echo "Requesting certificate from Private CA..."
CERT_ARN=$(aws acm-pca issue-certificate \
    --certificate-authority-arn "$CA_ARN" \
    --csr file:///tmp/server.csr \
    --signing-algorithm SHA512WITHRSA \
    --validity Value=365,Type=DAYS \
    --idempotency-token "nats-${INSTANCE_ID:0:20}" \
    --query 'CertificateArn' \
    --output text \
    --region us-east-1)

echo "Certificate ARN: $CERT_ARN"

# Wait for certificate to be issued
echo "Waiting for certificate..."
sleep 5

# Get certificate
CERT_JSON=$(aws acm-pca get-certificate \
    --certificate-authority-arn "$CA_ARN" \
    --certificate-arn "$CERT_ARN" \
    --output json \
    --region us-east-1)

# Extract certificate
echo "$CERT_JSON" | jq -r '.Certificate' > /etc/nats/tls/server-cert.pem
chmod 644 /etc/nats/tls/server-cert.pem

# Create NATS configuration with TLS
echo "Creating NATS configuration..."
cat > /etc/nats/nats-server.conf << EOF
# NATS Server Configuration with TLS
server_name: "nats-${INSTANCE_ID}"

# Client port with TLS
port: 4222
tls {
  cert_file: "/etc/nats/tls/server-cert.pem"
  key_file: "/etc/nats/tls/server-key.pem"
  ca_file: "/etc/nats/tls/ca-cert.pem"
  verify: true
}

# Cluster configuration
cluster {
  name: "nats-cluster"
  port: 6222
  
  tls {
    cert_file: "/etc/nats/tls/server-cert.pem"
    key_file: "/etc/nats/tls/server-key.pem"
    ca_file: "/etc/nats/tls/ca-cert.pem"
    verify: true
  }
  
  # Routes will be dynamically discovered
  routes: []
}

# HTTP Monitoring
http: 0.0.0.0:8222

# JetStream configuration
jetstream {
  store_dir: "/data/jetstream"
  max_memory_store: 1GB
  max_file_store: 100GB
}

# Logging
debug: false
trace: false
logtime: true
log_file: "/var/log/nats-server.log"

# System limits
max_connections: 65536
max_payload: 64MB
max_control_line: 4KB

# Authorization timeout
authorization {
  timeout: 2
}
EOF

# Set ownership
chown -R nats:nats /etc/nats/tls 2>/dev/null || chown -R root:root /etc/nats/tls

# Restart NATS server
echo "Restarting NATS server..."
if command -v systemctl &> /dev/null; then
    systemctl restart nats-server || true
else
    # Kill existing NATS process
    pkill -f nats-server || true
    sleep 2
    # Start NATS with new configuration
    nohup /usr/local/bin/nats-server -c /etc/nats/nats-server.conf > /var/log/nats-server.log 2>&1 &
fi

# Verify NATS is running
sleep 5
if pgrep -f nats-server > /dev/null; then
    echo "✓ NATS server is running with TLS"
else
    echo "✗ NATS server failed to start"
    exit 1
fi

# Clean up
rm -f /tmp/cert.conf /tmp/server.csr

echo "=== NATS TLS Setup Complete ===">
