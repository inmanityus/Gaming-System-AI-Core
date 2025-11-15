# Create EC2 Bastion for NATS Load Testing

$region = "us-east-1"
$accountId = "695353648052"

Write-Host "=== Creating Load Testing Bastion ===" -ForegroundColor Cyan

# Get VPC and subnet info from existing NATS infrastructure
Write-Host "`nGetting VPC configuration from NATS instances..."
$natsInstance = aws ec2 describe-instances --filters "Name=tag:Name,Values=nats-node-*" --query 'Reservations[0].Instances[0].[VpcId,SubnetId,SecurityGroups[0].GroupId]' --output json --region $region | ConvertFrom-Json

if (-not $natsInstance) {
    Write-Host "❌ Could not find NATS instances" -ForegroundColor Red
    Write-Host "Using default VPC configuration..." -ForegroundColor Yellow
    $vpcId = "vpc-045c9e283c23ae01e"
    $subnetId = "subnet-0f353054b8e31561d"
    $securityGroupId = "sg-00419f4094a7d2101"
} else {
    $vpcId = $natsInstance[0]
    $subnetId = $natsInstance[1]
    $securityGroupId = $natsInstance[2]
}

Write-Host "VPC: $vpcId"
Write-Host "Subnet: $subnetId"
Write-Host "Security Group: $securityGroupId"

# Create bastion instance
Write-Host "`nCreating t3.micro bastion instance..."

$userData = @"
#!/bin/bash
set -e

# Update system
yum update -y

# Install NATS CLI tools
cd /tmp
curl -L https://github.com/nats-io/natscli/releases/download/v0.1.5/nats-0.1.5-linux-amd64.tar.gz | tar -xz
mv nats /usr/local/bin/
chmod +x /usr/local/bin/nats

# Install nats-bench
curl -L https://github.com/nats-io/nats.go/releases/download/v1.35.0/nats-bench-linux-amd64.tar.gz | tar -xz
mv nats-bench /usr/local/bin/
chmod +x /usr/local/bin/nats-bench

# Install Python and testing tools
yum install -y python3 python3-pip
pip3 install nats-py asyncio-nats

# Install monitoring tools
yum install -y htop netcat telnet

# Create test scripts directory
mkdir -p /home/ec2-user/load-tests
chown ec2-user:ec2-user /home/ec2-user/load-tests

# Create simple connectivity test script
cat > /home/ec2-user/test-nats-connection.sh << 'SCRIPT'
#!/bin/bash
NATS_URL="nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
echo "Testing NATS connectivity to: \$NATS_URL"
nats --server \$NATS_URL pub test.connectivity "Hello from bastion"
if [ \$? -eq 0 ]; then
    echo "✅ NATS connectivity successful"
else
    echo "❌ NATS connectivity failed"
fi
SCRIPT

chmod +x /home/ec2-user/test-nats-connection.sh
chown ec2-user:ec2-user /home/ec2-user/test-nats-connection.sh

echo "Bastion setup complete" > /tmp/bastion-setup-complete
"@

$userDataBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($userData))

$instanceConfig = @"
{
  "ImageId": "ami-0c55b159cbfafe1f0",
  "InstanceType": "t3.micro",
  "KeyName": "gaming-system-ai-core-admin",
  "SecurityGroupIds": ["$securityGroupId"],
  "SubnetId": "$subnetId",
  "UserData": "$userDataBase64",
  "TagSpecifications": [{
    "ResourceType": "instance",
    "Tags": [
      {"Key": "Name", "Value": "nats-load-testing-bastion"},
      {"Key": "Purpose", "Value": "NATS load testing and monitoring"},
      {"Key": "Project", "Value": "gaming-system-nats"},
      {"Key": "Environment", "Value": "testing"}
    ]
  }],
  "IamInstanceProfile": {
    "Name": "ecsInstanceRole"
  },
  "Monitoring": {
    "Enabled": true
  }
}
"@

$configFile = New-TemporaryFile
$instanceConfig | Set-Content $configFile.FullName

Write-Host "`nLaunching instance..."
$result = aws ec2 run-instances --cli-input-json file://$($configFile.FullName) --region $region --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    $instanceId = $result.Instances[0].InstanceId
    Write-Host "✅ Instance created: $instanceId" -ForegroundColor Green
    
    # Wait for instance to be running
    Write-Host "`nWaiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids $instanceId --region $region
    
    # Get instance details
    $instance = aws ec2 describe-instances --instance-ids $instanceId --query 'Reservations[0].Instances[0].[PublicIpAddress,PrivateIpAddress]' --output json --region $region | ConvertFrom-Json
    $publicIp = $instance[0]
    $privateIp = $instance[1]
    
    Write-Host "`n=== Bastion Instance Created ===" -ForegroundColor Green
    Write-Host "Instance ID: $instanceId"
    Write-Host "Public IP: $publicIp"
    Write-Host "Private IP: $privateIp"
    Write-Host "SSH Key: C:\Users\kento\.ssh\gaming-system-ai-core-admin.pem"
    Write-Host ""
    Write-Host "To connect:"
    Write-Host "  ssh -i C:\Users\kento\.ssh\gaming-system-ai-core-admin.pem ec2-user@$publicIp"
    Write-Host ""
    Write-Host "Wait 2-3 minutes for user data script to complete, then test:"
    Write-Host "  ./test-nats-connection.sh"
    Write-Host ""
    Write-Host "Run load tests:"
    Write-Host "  nats-bench svc.ai.llm.v1.infer --pub 1000 --size 1024 --msgs 10000"
    
    # Save instance info
    @{
        InstanceId = $instanceId
        PublicIP = $publicIp
        PrivateIP = $privateIp
        Purpose = "NATS Load Testing Bastion"
        Created = (Get-Date).ToString()
    } | ConvertTo-Json | Set-Content "infrastructure/bastion-instance-info.json"
    
    Write-Host "`n✅ Bastion instance info saved to infrastructure/bastion-instance-info.json"
    
} else {
    Write-Host "❌ Failed to create instance" -ForegroundColor Red
}

Remove-Item $configFile.FullName -ErrorAction SilentlyContinue

