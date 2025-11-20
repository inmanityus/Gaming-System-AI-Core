#!/usr/bin/env pwsh
# Configure NATS TLS Certificates - Simple approach
# Generates certificates and deploys via SSM Parameter Store

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

# Exit on any error
$ErrorActionPreference = "Stop"

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== NATS TLS Certificate Configuration (Simple) ===${NC}"
Write-Host "Environment: $Environment"

# Get Private CA ARN from terraform output
Write-Host "${YELLOW}Getting Private CA ARN...${NC}"
$caArn = terraform output -raw nats_ca_arn 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "${RED}ERROR: Failed to get CA ARN from terraform output${NC}"
    Write-Host "Make sure you're in the terraform directory and have run terraform apply"
    exit 1
}
Write-Host "CA ARN: $caArn"

# Get CA Certificate from Secrets Manager
Write-Host "${YELLOW}Getting CA Certificate from Secrets Manager...${NC}"
$caCertSecretArn = terraform output -raw nats_ca_cert_secret_arn 2>$null
$caCert = aws secretsmanager get-secret-value --secret-id $caCertSecretArn --query 'SecretString' --output text

# Save CA certificate locally temporarily
$tempDir = New-TemporaryFile | % { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
$caCertPath = Join-Path $tempDir "ca-cert.pem"
Set-Content -Path $caCertPath -Value $caCert -NoNewline

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

# Create a simple shell script that will be uploaded to instances
$tlsSetupScript = @'
#!/bin/bash
set -e

echo "Setting up TLS for NATS..."

# Create directories
mkdir -p /etc/nats/tls
chmod 700 /etc/nats/tls

# Get certificates from SSM Parameter Store
CA_CERT=$(aws ssm get-parameter --name /nats/tls/ca-cert --with-decryption --query 'Parameter.Value' --output text)
SERVER_CERT=$(aws ssm get-parameter --name /nats/tls/${INSTANCE_ID}/server-cert --with-decryption --query 'Parameter.Value' --output text)
SERVER_KEY=$(aws ssm get-parameter --name /nats/tls/${INSTANCE_ID}/server-key --with-decryption --query 'Parameter.Value' --output text)

# Write certificates
echo "$CA_CERT" > /etc/nats/tls/ca-cert.pem
echo "$SERVER_CERT" > /etc/nats/tls/server-cert.pem
echo "$SERVER_KEY" > /etc/nats/tls/server-key.pem

# Set permissions
chmod 600 /etc/nats/tls/server-key.pem
chmod 644 /etc/nats/tls/server-cert.pem /etc/nats/tls/ca-cert.pem
chown -R nats:nats /etc/nats/tls 2>/dev/null || chown -R root:root /etc/nats/tls

# Create NATS configuration with TLS
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
  
  # Routes will be populated by discovery
  routes: []
}

# Monitoring
http: 0.0.0.0:8222

# JetStream
jetstream {
  store_dir: "/data/jetstream"
  max_memory_store: 1GB
  max_file_store: 100GB
}

# Logging
debug: false
trace: false
logtime: true

# Limits
max_connections: 65536
max_payload: 64MB
EOF

echo "TLS configuration created successfully"

# Restart NATS service
if command -v systemctl &> /dev/null; then
    systemctl restart nats-server || true
else
    pkill -f nats-server || true
    nohup /usr/local/bin/nats-server -c /etc/nats/nats-server.conf > /var/log/nats-server.log 2>&1 &
fi

echo "NATS server restarted with TLS"
'@

# Store CA certificate in SSM Parameter Store (shared across all instances)
Write-Host "${YELLOW}Storing CA certificate in SSM Parameter Store...${NC}"
aws ssm put-parameter `
    --name "/nats/tls/ca-cert" `
    --type "SecureString" `
    --value $caCert `
    --overwrite `
    --description "NATS CA certificate for mTLS" | Out-Null

# Process each instance
$failed = @()
foreach ($instanceId in $instances) {
    try {
        Write-Host ""
        Write-Host "${GREEN}Processing instance: $instanceId${NC}"
        
        # Get instance private IP
        $privateIp = aws ec2 describe-instances `
            --instance-ids $instanceId `
            --query 'Reservations[0].Instances[0].PrivateIpAddress' `
            --output text
        
        Write-Host "Private IP: $privateIp"
        
        # Generate certificate for this instance
        Write-Host "Generating certificate..."
        
        # Create certificate configuration
        $certConfig = @"
[req]
default_bits = 4096
prompt = no
default_md = sha512
distinguished_name = dn
req_extensions = v3_req

[dn]
CN = nats-$instanceId
O = Gaming System
OU = NATS Cluster
C = US

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = nats-$instanceId
DNS.2 = nats-$instanceId.internal
DNS.3 = localhost
IP.1 = $privateIp
IP.2 = 127.0.0.1
"@
        
        # Generate key and CSR
        $keyPath = Join-Path $tempDir "$instanceId-key.pem"
        $csrPath = Join-Path $tempDir "$instanceId.csr"
        $certConfigPath = Join-Path $tempDir "$instanceId-config.txt"
        
        Set-Content -Path $certConfigPath -Value $certConfig
        
        # Generate private key
        & openssl genrsa -out $keyPath 4096 2>$null
        if ($LASTEXITCODE -ne 0) { throw "Failed to generate private key" }
        
        # Generate CSR
        & openssl req -new -key $keyPath -out $csrPath -config $certConfigPath 2>$null
        if ($LASTEXITCODE -ne 0) { throw "Failed to generate CSR" }
        
        # Issue certificate
        $certResponse = aws acm-pca issue-certificate `
            --certificate-authority-arn $caArn `
            --csr "fileb://$csrPath" `
            --signing-algorithm SHA512WITHRSA `
            --validity Value=365,Type=DAYS `
            --idempotency-token "nats-$instanceId-$(Get-Date -Format 'yyyyMMddHHmmss')" `
            --output json | ConvertFrom-Json
        
        $certArn = $certResponse.CertificateArn
        Write-Host "Certificate issued: $certArn"
        
        # Wait and get certificate
        Start-Sleep -Seconds 3
        $cert = aws acm-pca get-certificate `
            --certificate-authority-arn $caArn `
            --certificate-arn $certArn `
            --output json | ConvertFrom-Json
        
        # Store certificates in SSM Parameter Store
        Write-Host "Storing certificates in SSM Parameter Store..."
        
        $privateKey = Get-Content -Path $keyPath -Raw
        
        aws ssm put-parameter `
            --name "/nats/tls/$instanceId/server-cert" `
            --type "SecureString" `
            --value $cert.Certificate `
            --overwrite `
            --description "NATS server certificate for $instanceId" | Out-Null
        
        aws ssm put-parameter `
            --name "/nats/tls/$instanceId/server-key" `
            --type "SecureString" `
            --value $privateKey `
            --overwrite `
            --description "NATS server private key for $instanceId" | Out-Null
        
        # Deploy TLS configuration script
        Write-Host "Deploying TLS configuration to instance..."
        
        $command = aws ssm send-command `
            --instance-ids $instanceId `
            --document-name "AWS-RunShellScript" `
            --parameters "commands=['export INSTANCE_ID=$instanceId',$($tlsSetupScript -replace "'", "'\''")]" `
            --output json | ConvertFrom-Json
        
        $commandId = $command.Command.CommandId
        Write-Host "Command sent: $commandId"
        
        # Wait for completion
        Write-Host "Waiting for deployment..."
        $maxWait = 60
        $waited = 0
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 5
            $waited += 5
            
            $status = aws ssm get-command-invocation `
                --command-id $commandId `
                --instance-id $instanceId `
                --query 'Status' `
                --output text 2>$null
            
            if ($status -eq "Success") {
                Write-Host "${GREEN}✓ Instance $instanceId configured successfully${NC}"
                break
            }
            elseif ($status -eq "Failed" -or $status -eq "TimedOut") {
                $output = aws ssm get-command-invocation `
                    --command-id $commandId `
                    --instance-id $instanceId `
                    --query 'StandardErrorContent' `
                    --output text
                throw "Deployment failed: $output"
            }
        }
        
        if ($waited -ge $maxWait) {
            throw "Deployment timeout"
        }
        
    }
    catch {
        Write-Host "${RED}✗ Failed to configure instance $instanceId : $_${NC}"
        $failed += $instanceId
    }
}

# Cleanup temporary directory
Remove-Item -Path $tempDir -Recurse -Force

Write-Host ""
Write-Host "${GREEN}=== TLS Configuration Summary ===${NC}"
Write-Host "Total instances: $($instances.Count)"
Write-Host "Successful: $($instances.Count - $failed.Count)"
Write-Host "Failed: $($failed.Count)"

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "${RED}Failed instances:${NC}"
    foreach ($id in $failed) {
        Write-Host "  - $id"
    }
    exit 1
}

Write-Host ""
Write-Host "${GREEN}✓ All NATS instances configured with TLS successfully!${NC}"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Update ECS services with TLS connection strings"
Write-Host "2. Test TLS connectivity"
Write-Host "3. Update security groups if needed"
