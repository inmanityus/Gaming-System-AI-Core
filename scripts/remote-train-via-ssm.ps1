# Remote training via AWS Systems Manager (no SSH key needed)

param(
    [string]$InstanceId = "i-089e3ab2b8830e3d2"
)

Write-Host "Starting remote training via SSM..." -ForegroundColor Cyan

# Send setup commands
$commands = @"
#!/bin/bash
set -e

# Update and install dependencies
sudo apt-get update -y
sudo apt-get install -y python3-pip redis-server

# Install vLLM and training deps
pip3 install torch transformers peft bitsandbytes datasets accelerate vllm --break-system-packages

# Start Redis
sudo systemctl start redis-server

# Note: Code needs to be transferred separately or pulled from git

echo 'Environment ready for training'
"@

Write-Host "Sending setup commands..."
$commandId = aws ssm send-command `
    --instance-ids $InstanceId `
    --document-name "AWS-RunShellScript" `
    --parameters "commands=$commands" `
    --query "Command.CommandId" `
    --output text

Write-Host "Command ID: $commandId"
Write-Host "Check status: aws ssm list-command-invocations --command-id $commandId --details"

