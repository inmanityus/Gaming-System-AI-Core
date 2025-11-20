#!/usr/bin/env pwsh
# Configure NATS TLS Certificates
# Generates and distributes TLS certificates to all NATS instances

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

Write-Host "${GREEN}=== NATS TLS Certificate Configuration ===${NC}"
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
if ($LASTEXITCODE -ne 0) {
    Write-Host "${RED}ERROR: Failed to get CA certificate from Secrets Manager${NC}"
    exit 1
}

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
Write-Host "Found $($instances.Count) NATS instances:"
foreach ($id in $instances) {
    Write-Host "  - $id"
}

# Function to generate certificate for a NATS node
function Generate-NATSCertificate {
    param(
        [string]$InstanceId,
        [string]$PrivateIp,
        [string]$CAArn
    )
    
    Write-Host "${YELLOW}Generating certificate for instance $InstanceId (IP: $PrivateIp)...${NC}"
    
    # Create certificate signing request
    $csrConfig = @"
[req]
default_bits = 4096
prompt = no
default_md = sha512
distinguished_name = dn
req_extensions = v3_req

[dn]
CN = nats-$InstanceId
O = Gaming System
OU = NATS Cluster
C = US

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = nats-$InstanceId
DNS.2 = nats-$InstanceId.internal
DNS.3 = *.nats-cluster.internal
IP.1 = $PrivateIp
"@
    
    # Save CSR config temporarily
    $csrConfigFile = New-TemporaryFile
    Set-Content -Path $csrConfigFile -Value $csrConfig
    
    try {
        # Generate private key and CSR
        $keyFile = New-TemporaryFile
        $csrFile = New-TemporaryFile
        
        # Generate key
        openssl genrsa -out $keyFile 4096 2>$null
        
        # Generate CSR
        openssl req -new -key $keyFile -out $csrFile -config $csrConfigFile 2>$null
        
        # Issue certificate from Private CA
        $csrContent = Get-Content -Path $csrFile -Raw
        $certResponse = aws acm-pca issue-certificate `
            --certificate-authority-arn $CAArn `
            --csr "fileb://$csrFile" `
            --signing-algorithm SHA512WITHRSA `
            --validity Value=365,Type=DAYS `
            --idempotency-token "nats-$InstanceId" `
            --output json | ConvertFrom-Json
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to issue certificate"
        }
        
        $certArn = $certResponse.CertificateArn
        Write-Host "Certificate issued: $certArn"
        
        # Wait for certificate to be issued
        Start-Sleep -Seconds 2
        
        # Get the certificate
        $cert = aws acm-pca get-certificate `
            --certificate-authority-arn $CAArn `
            --certificate-arn $certArn `
            --output json | ConvertFrom-Json
        
        # Return certificate data
        return @{
            PrivateKey = Get-Content -Path $keyFile -Raw
            Certificate = $cert.Certificate
            CertificateChain = $cert.CertificateChain
        }
    }
    finally {
        # Clean up temporary files
        Remove-Item -Path $csrConfigFile -ErrorAction SilentlyContinue
        Remove-Item -Path $keyFile -ErrorAction SilentlyContinue
        Remove-Item -Path $csrFile -ErrorAction SilentlyContinue
    }
}

# Function to deploy certificate to instance
function Deploy-CertificateToInstance {
    param(
        [string]$InstanceId,
        [hashtable]$CertData,
        [string]$CACert
    )
    
    Write-Host "${YELLOW}Deploying certificate to instance $InstanceId...${NC}"
    
    # Escape certificate content for bash script
    $cert = $CertData.Certificate -replace "'", "'\''"
    $key = $CertData.PrivateKey -replace "'", "'\''"
    $ca = $CACert -replace "'", "'\''"
    
    # Create certificate installation script
    $installScript = @"
#!/bin/bash
set -e

# Create TLS directory
mkdir -p /etc/nats/tls
chmod 700 /etc/nats/tls

# Write certificate files
cat > /etc/nats/tls/server-cert.pem << 'EOF'
$cert
EOF

cat > /etc/nats/tls/server-key.pem << 'EOF'
$key
EOF

cat > /etc/nats/tls/ca-cert.pem << 'EOF'
$ca
EOF

# Set permissions
chmod 600 /etc/nats/tls/server-key.pem
chmod 644 /etc/nats/tls/server-cert.pem
chmod 644 /etc/nats/tls/ca-cert.pem
chown -R nats:nats /etc/nats/tls

# Update NATS configuration for TLS
cat > /etc/nats/nats-server.conf << 'EOF'
# NATS Server Configuration with TLS

# Server name
server_name: "nats-$InstanceId"

# Client port with TLS
port: 4222
tls {
  cert_file: "/etc/nats/tls/server-cert.pem"
  key_file: "/etc/nats/tls/server-key.pem"
  ca_file: "/etc/nats/tls/ca-cert.pem"
  verify: true
}

# Cluster port with TLS
cluster {
  port: 6222
  tls {
    cert_file: "/etc/nats/tls/server-cert.pem"
    key_file: "/etc/nats/tls/server-key.pem"
    ca_file: "/etc/nats/tls/ca-cert.pem"
    verify: true
  }
  
  # Discover other nodes via AWS API
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
log_file: "/var/log/nats-server.log"

# Limits
max_connections: 65536
max_payload: 64MB

# Authorization
authorization {
  timeout: 2
}
EOF

# Restart NATS with new configuration
systemctl restart nats-server || nats-server -c /etc/nats/nats-server.conf &

echo "TLS configuration deployed successfully"
"@
    
    # Deploy via SSM
    $result = aws ssm send-command `
        --instance-ids $InstanceId `
        --document-name "AWS-RunShellScript" `
        --parameters "commands=[$($installScript | ConvertTo-Json)]" `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to send command to instance"
    }
    
    $commandId = $result.Command.CommandId
    Write-Host "Command sent: $commandId"
    
    # Wait for command to complete
    Write-Host "Waiting for certificate deployment..."
    $maxWait = 60
    $waited = 0
    
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 5
        $waited += 5
        
        $status = aws ssm get-command-invocation `
            --command-id $commandId `
            --instance-id $InstanceId `
            --query 'Status' `
            --output text 2>$null
        
        if ($status -eq "Success") {
            Write-Host "${GREEN}Certificate deployed successfully${NC}"
            return
        }
        elseif ($status -eq "Failed") {
            $output = aws ssm get-command-invocation `
                --command-id $commandId `
                --instance-id $InstanceId `
                --query 'StandardErrorContent' `
                --output text
            Write-Host "${RED}Certificate deployment failed: $output${NC}"
            throw "Deployment failed"
        }
    }
    
    throw "Deployment timeout"
}

# Main deployment loop
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
        
        if (-not $privateIp) {
            throw "Failed to get private IP for instance"
        }
        
        Write-Host "Private IP: $privateIp"
        
        # Generate certificate
        $certData = Generate-NATSCertificate -InstanceId $instanceId -PrivateIp $privateIp -CAArn $caArn
        
        # Deploy certificate
        Deploy-CertificateToInstance -InstanceId $instanceId -CertData $certData -CACert $caCert
        
        Write-Host "${GREEN}✓ Instance $instanceId configured successfully${NC}"
    }
    catch {
        Write-Host "${RED}✗ Failed to configure instance $instanceId : $_${NC}"
        $failed += $instanceId
    }
}

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
Write-Host "1. Update ECS services to use TLS connection strings"
Write-Host "2. Update security groups to restrict non-TLS ports"
Write-Host "3. Test TLS connectivity with: nats-cli --tlscert cert.pem --tlskey key.pem --tlsca ca.pem"
