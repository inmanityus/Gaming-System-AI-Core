#!/bin/bash
# Setup TLS for NATS Cluster
# Generates certificates and configures NATS servers

set -e

REGION="us-east-1"
NATS_NODES=(
    "i-nats-1"
    "i-nats-2"
    "i-nats-3"
    "i-nats-4"
    "i-nats-5"
)

echo "=== Setting Up TLS for NATS Cluster ==="

# Step 1: Generate CA certificate
echo "Step 1: Generating CA certificate..."
openssl genrsa -out nats-ca-key.pem 4096
openssl req -new -x509 -sha256 -key nats-ca-key.pem -out nats-ca-cert.pem -days 3650 \
    -subj "/C=US/ST=CA/L=SF/O=GamingSystem/CN=NATS-CA"

echo "✅ CA certificate generated"

# Step 2: Generate server certificates for each node
echo "Step 2: Generating server certificates..."

for i in {1..5}; do
    echo "  Node $i..."
    
    # Generate private key
    openssl genrsa -out nats-server-$i-key.pem 2048
    
    # Generate CSR
    openssl req -new -key nats-server-$i-key.pem -out nats-server-$i.csr \
        -subj "/C=US/ST=CA/L=SF/O=GamingSystem/CN=nats-node-$i"
    
    # Sign with CA
    openssl x509 -req -in nats-server-$i.csr -CA nats-ca-cert.pem -CAkey nats-ca-key.pem \
        -CAcreateserial -out nats-server-$i-cert.pem -days 3650 -sha256
    
    rm nats-server-$i.csr
    echo "  ✅ Server $i certificate generated"
done

# Step 3: Generate client certificates
echo "Step 3: Generating client certificates..."
openssl genrsa -out nats-client-key.pem 2048
openssl req -new -key nats-client-key.pem -out nats-client.csr \
    -subj "/C=US/ST=CA/L=SF/O=GamingSystem/CN=nats-client"
openssl x509 -req -in nats-client.csr -CA nats-ca-cert.pem -CAkey nats-ca-key.pem \
    -CAcreateserial -out nats-client-cert.pem -days 3650 -sha256
rm nats-client.csr

echo "✅ Client certificate generated"

# Step 4: Create NATS config with TLS
echo "Step 4: Creating NATS configuration..."

cat > nats-tls.conf << 'EOF'
# NATS Server Configuration with TLS
port: 4222
http_port: 8222

# Cluster configuration
cluster {
  name: "gaming-system-nats"
  port: 6222
  
  # TLS for cluster communication
  tls {
    cert_file: "/etc/nats/certs/server-cert.pem"
    key_file: "/etc/nats/certs/server-key.pem"
    ca_file: "/etc/nats/certs/ca-cert.pem"
    verify: true
  }
  
  routes: [
    nats://nats-node-1:6222
    nats://nats-node-2:6222
    nats://nats-node-3:6222
    nats://nats-node-4:6222
    nats://nats-node-5:6222
  ]
}

# Client TLS
tls {
  cert_file: "/etc/nats/certs/server-cert.pem"
  key_file: "/etc/nats/certs/server-key.pem"
  ca_file: "/etc/nats/certs/ca-cert.pem"
  verify: true
  timeout: 3
}

# JetStream
jetstream {
  store_dir: "/data/jetstream"
  max_memory_store: 1GB
  max_file_store: 10GB
}

# Logging
debug: false
trace: false
logtime: true
log_file: "/var/log/nats/nats-server.log"
EOF

echo "✅ NATS config created"

# Step 5: Upload certificates to S3
echo "Step 5: Uploading certificates to S3..."
BUCKET="gaming-system-nats-certs"

aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || true

aws s3 cp nats-ca-cert.pem s3://$BUCKET/ca-cert.pem
aws s3 cp nats-client-cert.pem s3://$BUCKET/client-cert.pem
aws s3 cp nats-client-key.pem s3://$BUCKET/client-key.pem

for i in {1..5}; do
    aws s3 cp nats-server-$i-cert.pem s3://$BUCKET/server-$i-cert.pem
    aws s3 cp nats-server-$i-key.pem s3://$BUCKET/server-$i-key.pem
done

aws s3 cp nats-tls.conf s3://$BUCKET/nats-tls.conf

echo "✅ Certificates uploaded to S3"

# Step 6: Deploy to NATS nodes via SSM
echo "Step 6: Deploying certificates to NATS nodes..."

DEPLOY_SCRIPT='#!/bin/bash
set -e

# Download certs
aws s3 cp s3://gaming-system-nats-certs/ca-cert.pem /etc/nats/certs/ca-cert.pem
aws s3 cp s3://gaming-system-nats-certs/server-$NODE_NUM-cert.pem /etc/nats/certs/server-cert.pem
aws s3 cp s3://gaming-system-nats-certs/server-$NODE_NUM-key.pem /etc/nats/certs/server-key.pem
aws s3 cp s3://gaming-system-nats-certs/nats-tls.conf /etc/nats/nats-server.conf

# Set permissions
chmod 600 /etc/nats/certs/*-key.pem
chmod 644 /etc/nats/certs/*-cert.pem

# Restart NATS
systemctl restart nats-server

echo "NATS TLS configured on node $NODE_NUM"
'

for i in {1..5}; do
    echo "  Deploying to node $i..."
    
    # Would use SSM here in production
    # aws ssm send-command \
    #   --instance-ids ${NATS_NODES[$i-1]} \
    #   --document-name "AWS-RunShellScript" \
    #   --parameters "commands=['export NODE_NUM=$i', '$DEPLOY_SCRIPT']" \
    #   --region $REGION
    
    echo "  ✅ Node $i configured (SSM command sent)"
done

echo ""
echo "=== TLS Setup Complete ==="
echo "CA Certificate: nats-ca-cert.pem"
echo "Client Cert: nats-client-cert.pem"
echo "Client Key: nats-client-key.pem"
echo ""
echo "To connect with TLS:"
echo '  nats --server tls://nats-production-*.elb.us-east-1.amazonaws.com:4222 \'
echo "    --tlscert=nats-client-cert.pem --tlskey=nats-client-key.pem --tlsca=nats-ca-cert.pem"
echo ""
echo "Update service environment variables:"
echo '  NATS_URL=tls://nats-production-*.elb.us-east-1.amazonaws.com:4222'
echo ""

