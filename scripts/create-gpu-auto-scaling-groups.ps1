# Create GPU Auto Scaling Groups for AI Model Tiers
# Implements auto-scaling design from 4-model consensus (GPT-5 Pro, Claude 4.5, Gemini 2.5 Pro, Perplexity)

param(
    [string]$Region = "us-east-1",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Creating GPU Auto Scaling Groups for AI Gaming System" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Configuration
$VpcId = "vpc-045c9e283c23ae01e"
$SubnetIds = @("subnet-0f353054b8e31561d", "subnet-036ef66c03b45b1da")
$SecurityGroupId = "sg-00419f4094a7d2101"
$KeyName = "gaming-system-ai-core-admin"

# ============================================================================
# GOLD TIER AUTO SCALING GROUP (Real-time, <16ms)
# ============================================================================
Write-Host "📦 GOLD TIER: g5.xlarge (NVIDIA A10G, 24GB VRAM)" -ForegroundColor Yellow
Write-Host "  Model: Qwen2.5-3B-AWQ (currently operational at 54.234.135.254)" -ForegroundColor Gray
Write-Host "  Scaling: Min 1 → Max 50 instances" -ForegroundColor Gray
Write-Host "  Cost: ~$730/mo per instance" -ForegroundColor Gray
Write-Host ""

# Create Launch Template for Gold Tier
$GoldLaunchTemplate = @"
{
  "LaunchTemplateName": "AI-Gaming-Gold-Tier-Template",
  "VersionDescription": "Gold tier GPU instances for real-time AI inference",
  "LaunchTemplateData": {
    "ImageId": "ami-0c7217cdde317cfec",
    "InstanceType": "g5.xlarge",
    "KeyName": "$KeyName",
    "SecurityGroupIds": ["$SecurityGroupId"],
    "IamInstanceProfile": {
      "Name": "AI-Gaming-GPU-Instance-Profile"
    },
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 100,
        "VolumeType": "gp3",
        "DeleteOnTermination": true
      }
    }],
    "UserData": "$(
        $userData = @"
#!/bin/bash
set -e

# Install NVIDIA drivers and Docker
yum update -y
yum install -y docker git

# Install NVIDIA container toolkit
distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/\$distribution/libnvidia-container.repo | tee /etc/yum.repos.d/nvidia-container-toolkit.repo
yum install -y nvidia-container-toolkit

# Start Docker
systemctl enable docker
systemctl start docker

# Configure Docker for NVIDIA
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Pull vLLM image
docker pull vllm/vllm-openai:latest

# Start vLLM server for Qwen2.5-3B-AWQ
docker run -d --gpus all --restart unless-stopped \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env HF_TOKEN=\$HF_TOKEN \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-3B-Instruct-AWQ \
  --quantization awq \
  --dtype half \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9

echo '✅ Gold tier vLLM server started'
"@
        [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($userData))
    )",
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [
        {"Key": "Name", "Value": "AI-Gaming-Gold-GPU"},
        {"Key": "Tier", "Value": "Gold"},
        {"Key": "Model", "Value": "Qwen2.5-3B-AWQ"},
        {"Key": "ManagedBy", "Value": "AutoScaling"}
      ]
    }]
  }
}
"@

if (-not $DryRun) {
    Write-Host "  Creating Gold Tier Launch Template..." -ForegroundColor Cyan
    aws ec2 create-launch-template --cli-input-json $GoldLaunchTemplate --region $Region
    Write-Host "  ✅ Gold Launch Template created" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would create Gold Launch Template" -ForegroundColor Yellow
}

# Create Gold Tier Auto Scaling Group
$GoldASGConfig = @{
    AutoScalingGroupName = "AI-Gaming-Gold-Tier-ASG"
    LaunchTemplate = @{
        LaunchTemplateName = "AI-Gaming-Gold-Tier-Template"
        Version = '$$Latest'
    }
    MinSize = 1
    MaxSize = 50
    DesiredCapacity = 1
    VPCZoneIdentifier = ($SubnetIds -join ",")
    Tags = @(
        @{Key="Name"; Value="AI-Gaming-Gold-ASG"; PropagateAtLaunch=$true},
        @{Key="Tier"; Value="Gold"; PropagateAtLaunch=$true}
    )
}

if (-not $DryRun) {
    Write-Host "  Creating Gold Tier Auto Scaling Group..." -ForegroundColor Cyan
    aws autoscaling create-auto-scaling-group `
        --auto-scaling-group-name $GoldASGConfig.AutoScalingGroupName `
        --launch-template LaunchTemplateName=$($GoldASGConfig.LaunchTemplate.LaunchTemplateName),Version=$($GoldASGConfig.LaunchTemplate.Version) `
        --min-size $GoldASGConfig.MinSize `
        --max-size $GoldASGConfig.MaxSize `
        --desired-capacity $GoldASGConfig.DesiredCapacity `
        --vpc-zone-identifier $GoldASGConfig.VPCZoneIdentifier `
        --region $Region
    
    Write-Host "  ✅ Gold Tier ASG created (Min: 1, Max: 50)" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would create Gold ASG" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# SILVER TIER AUTO SCALING GROUP (Interactive, <250ms)
# ============================================================================
Write-Host "📦 SILVER TIER: g5.2xlarge (NVIDIA A10G, 24GB VRAM)" -ForegroundColor Yellow
Write-Host "  Model: Qwen2.5-7B-Instruct (currently operational at 18.208.225.146)" -ForegroundColor Gray
Write-Host "  Scaling: Min 1 → Max 30 instances" -ForegroundColor Gray
Write-Host "  Cost: ~$870/mo per instance" -ForegroundColor Gray
Write-Host ""

# Create Launch Template for Silver Tier
$SilverLaunchTemplate = @"
{
  "LaunchTemplateName": "AI-Gaming-Silver-Tier-Template",
  "VersionDescription": "Silver tier GPU instances for interactive AI",
  "LaunchTemplateData": {
    "ImageId": "ami-0c7217cdde317cfec",
    "InstanceType": "g5.2xlarge",
    "KeyName": "$KeyName",
    "SecurityGroupIds": ["$SecurityGroupId"],
    "IamInstanceProfile": {
      "Name": "AI-Gaming-GPU-Instance-Profile"
    },
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeSize": 150,
        "VolumeType": "gp3",
        "DeleteOnTermination": true
      }
    }],
    "UserData": "$(
        $userData = @"
#!/bin/bash
set -e

# Install NVIDIA drivers and Docker
yum update -y
yum install -y docker git

# Install NVIDIA container toolkit
distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/\$distribution/libnvidia-container.repo | tee /etc/yum.repos.d/nvidia-container-toolkit.repo
yum install -y nvidia-container-toolkit

# Start Docker
systemctl enable docker
systemctl start docker

# Configure Docker for NVIDIA
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Pull vLLM image
docker pull vllm/vllm-openai:latest

# Start vLLM server for Qwen2.5-7B-Instruct
docker run -d --gpus all --restart unless-stopped \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env HF_TOKEN=\$HF_TOKEN \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-7B-Instruct \
  --dtype half \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.85

echo '✅ Silver tier vLLM server started'
"@
        [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($userData))
    )",
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [
        {"Key": "Name", "Value": "AI-Gaming-Silver-GPU"},
        {"Key": "Tier", "Value": "Silver"},
        {"Key": "Model", "Value": "Qwen2.5-7B-Instruct"},
        {"Key": "ManagedBy", "Value": "AutoScaling"}
      ]
    }]
  }
}
"@

if (-not $DryRun) {
    Write-Host "  Creating Silver Tier Launch Template..." -ForegroundColor Cyan
    aws ec2 create-launch-template --cli-input-json $SilverLaunchTemplate --region $Region
    Write-Host "  ✅ Silver Launch Template created" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would create Silver Launch Template" -ForegroundColor Yellow
}

# Create Silver Tier Auto Scaling Group  
if (-not $DryRun) {
    Write-Host "  Creating Silver Tier Auto Scaling Group..." -ForegroundColor Cyan
    aws autoscaling create-auto-scaling-group `
        --auto-scaling-group-name "AI-Gaming-Silver-Tier-ASG" `
        --launch-template LaunchTemplateName="AI-Gaming-Silver-Tier-Template",Version='$$Latest' `
        --min-size 1 `
        --max-size 30 `
        --desired-capacity 1 `
        --vpc-zone-identifier ($SubnetIds -join ",") `
        --region $Region
    
    Write-Host "  ✅ Silver Tier ASG created (Min: 1, Max: 30)" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would create Silver ASG" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "="*70 -ForegroundColor Green
Write-Host "✅ GPU AUTO SCALING GROUPS CREATED" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Create ECS Capacity Providers" -ForegroundColor White
Write-Host "  2. Build GPU metrics publisher" -ForegroundColor White
Write-Host "  3. Configure scaling policies" -ForegroundColor White
Write-Host "  4. Load testing" -ForegroundColor White
Write-Host ""

