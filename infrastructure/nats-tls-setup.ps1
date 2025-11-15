# Setup TLS for NATS Cluster (PowerShell)
# Generates certificates and uploads to S3

$ErrorActionPreference = "Continue"

Write-Host "=== Setting Up TLS for NATS Cluster ===" -ForegroundColor Cyan

# Check if certificates already generated
$certsExist = Test-Path "infrastructure/nats-ca-cert.pem"

if ($certsExist) {
    Write-Host "Certificates already generated, uploading to S3..." -ForegroundColor Yellow
} else {
    Write-Host "Certificates need to be generated first" -ForegroundColor Yellow
    Write-Host "Please run: bash infrastructure/nats-tls-setup.sh (up to Step 4)" -ForegroundColor Yellow
    Write-Host "Then run this script again for S3 upload and deployment" -ForegroundColor Yellow
    exit 1
}

# Step 5: Upload to S3
Write-Host "`nStep 5: Uploading certificates to S3..." -ForegroundColor Yellow
$bucket = "gaming-system-nats-certs"
$region = "us-east-1"

# Create bucket
aws s3 mb "s3://$bucket" --region $region 2>&1 | Out-Null

# Upload CA and client certs
aws s3 cp infrastructure/nats-ca-cert.pem "s3://$bucket/ca-cert.pem"
aws s3 cp infrastructure/nats-client-cert.pem "s3://$bucket/client-cert.pem"
aws s3 cp infrastructure/nats-client-key.pem "s3://$bucket/client-key.pem"

# Upload server certs
for ($i=1; $i -le 5; $i++) {
    aws s3 cp "infrastructure/nats-server-$i-cert.pem" "s3://$bucket/server-$i-cert.pem"
    aws s3 cp "infrastructure/nats-server-$i-key.pem" "s3://$bucket/server-$i-key.pem"
}

# Upload config
aws s3 cp infrastructure/nats-tls.conf "s3://$bucket/nats-tls.conf"

Write-Host "✅ Certificates uploaded to S3: $bucket" -ForegroundColor Green

Write-Host "`n=== TLS Setup Complete ===" -ForegroundColor Cyan
Write-Host "Certificates are now in S3 bucket: $bucket"
Write-Host ""
Write-Host "To deploy to NATS nodes, you would need to:"
Write-Host "1. SSH or use SSM to connect to each NATS EC2 instance"
Write-Host "2. Download certs from S3"
Write-Host "3. Update NATS config to use TLS"
Write-Host "4. Restart NATS server"
Write-Host ""
Write-Host "Then update all service connection strings to:"
Write-Host "  tls://nats-production-*.elb.us-east-1.amazonaws.com:4222"
Write-Host ""
Write-Host "For development/staging, TLS is optional."
Write-Host "For production, TLS is MANDATORY per peer review."

