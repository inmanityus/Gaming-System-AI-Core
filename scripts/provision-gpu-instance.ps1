# Provision g5.2xlarge GPU Instance for Body Broker Training

param(
    [string]$InstanceType = "g5.2xlarge",
    [string]$Region = "us-east-1",
    [string]$KeyName = "gaming-ai-key"
)

Write-Host "Provisioning GPU instance for Body Broker..." -ForegroundColor Cyan

# Find latest Deep Learning AMI (Ubuntu with CUDA)
Write-Host "`nFinding latest Deep Learning AMI..."
$ami = aws ec2 describe-images `
    --region $Region `
    --owners amazon `
    --filters "Name=name,Values=Deep Learning AMI GPU PyTorch * (Ubuntu 22.04)*" `
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' `
    --output text

Write-Host "  AMI: $ami"

# Launch instance
Write-Host "`nLaunching $InstanceType instance..."
$instanceId = aws ec2 run-instances `
    --region $Region `
    --image-id $ami `
    --instance-type $InstanceType `
    --key-name $KeyName `
    --security-group-ids sg-default `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=body-broker-gpu-training},{Key=Project,Value=BodyBroker},{Key=Purpose,Value=LoRATraining}]" `
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=200,VolumeType=gp3}" `
    --query 'Instances[0].InstanceId' `
    --output text

Write-Host "  Instance ID: $instanceId"

# Wait for running
Write-Host "`nWaiting for instance to start..."
aws ec2 wait instance-running --region $Region --instance-ids $instanceId

# Get public IP
$publicIp = aws ec2 describe-instances `
    --region $Region `
    --instance-ids $instanceId `
    --query 'Reservations[0].Instances[0].PublicIpAddress' `
    --output text

Write-Host "`n" + ("="*60)
Write-Host "✅ GPU INSTANCE PROVISIONED" -ForegroundColor Green
Write-Host ("="*60)
Write-Host "Instance ID: $instanceId"
Write-Host "Instance Type: $InstanceType"
Write-Host "Public IP: $publicIp"
Write-Host "`nNext: SSH and setup environment"
Write-Host "  ssh -i ~/.ssh/$KeyName.pem ubuntu@$publicIp"

