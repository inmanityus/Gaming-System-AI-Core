# Create new g5.2xlarge with SSM enabled and auto-setup

$instanceProfile = "gaming-system-ssm-role"
$bucketName = "body-broker-training-9728"

# Create IAM role if doesn't exist
Write-Host "Setting up IAM role for SSM..."
aws iam create-role --role-name gaming-system-ssm-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}' 2>$null

aws iam attach-role-policy --role-name gaming-system-ssm-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore 2>$null
aws iam attach-role-policy --role-name gaming-system-ssm-role --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess 2>$null

aws iam create-instance-profile --instance-profile-name $instanceProfile 2>$null
aws iam add-role-to-instance-profile --instance-profile-name $instanceProfile --role-name gaming-system-ssm-role 2>$null

Start-Sleep -Seconds 10

# User data script
$userData = @"
#!/bin/bash
cd /home/ubuntu
aws s3 cp s3://$bucketName/body-broker-code.tar.gz .
tar -xzf body-broker-code.tar.gz
pip3 install -r requirements-complete.txt --break-system-packages
pip3 install vllm --break-system-packages
echo 'Auto-setup complete' > /home/ubuntu/setup-status.txt
"@

$userDataB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($userData))

# Launch instance
Write-Host "Launching g5.2xlarge with auto-setup..."
$ami = "ami-0c7217cdde317cfec"  # Deep Learning Base GPU AMI (Ubuntu 22.04)

$instanceId = aws ec2 run-instances `
    --image-id $ami `
    --instance-type g5.2xlarge `
    --iam-instance-profile Name=$instanceProfile `
    --user-data $userDataB64 `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=body-broker-training-auto},{Key=Project,Value=BodyBroker}]" `
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=200}" `
    --query 'Instances[0].InstanceId' `
    --output text

Write-Host "Instance ID: $instanceId"
Write-Host "Waiting for running state..."
aws ec2 wait instance-running --instance-ids $instanceId

$ip = aws ec2 describe-instances --instance-ids $instanceId --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

Write-Host "`n✅ Instance ready: $instanceId @ $ip"
Write-Host "Code auto-deploying from S3"
Write-Host "Check setup: aws ssm send-command --instance-ids $instanceId --document-name AWS-RunShellScript --parameters 'commands=[cat /home/ubuntu/setup-status.txt]'"

