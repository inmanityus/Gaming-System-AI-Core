# Deploy Body Broker to existing GPU instance

param(
    [string]$InstanceIp = "18.208.225.146",
    [string]$KeyPath = "~/.ssh/gaming-ai-key.pem"
)

Write-Host "Deploying Body Broker to GPU instance: $InstanceIp" -ForegroundColor Cyan

# Create deployment package
Write-Host "`nCreating deployment package..."
$tempDir = New-Item -ItemType Directory -Force -Path ".deploy-temp"

# Copy necessary files
Copy-Item -Recurse services $tempDir
Copy-Item -Recurse training $tempDir
Copy-Item -Recurse tests $tempDir
Copy-Item -Recurse examples $tempDir
Copy-Item requirements-complete.txt $tempDir
Copy-Item config/body-broker-config.yaml $tempDir
Copy-Item scripts/setup-gpu-environment.sh $tempDir
Copy-Item scripts/train-all-adapters.sh $tempDir

# Create tarball
Write-Host "Creating tarball..."
tar -czf body-broker-deploy.tar.gz -C $tempDir .

# SCP to instance
Write-Host "`nTransferring to GPU instance..."
scp -i $KeyPath body-broker-deploy.tar.gz ubuntu@${InstanceIp}:~/

# SSH and setup
Write-Host "`nSetting up environment..."
$setupCommands = @"
cd ~
tar -xzf body-broker-deploy.tar.gz
chmod +x setup-gpu-environment.sh train-all-adapters.sh
bash setup-gpu-environment.sh
"@

ssh -i $KeyPath ubuntu@$InstanceIp $setupCommands

Write-Host "`n✅ Deployment complete"
Write-Host "vLLM server starting on $InstanceIp:8000"

# Cleanup
Remove-Item -Recurse -Force $tempDir
Remove-Item body-broker-deploy.tar.gz

Write-Host "`nTo train adapters, run:"
Write-Host "  ssh -i $KeyPath ubuntu@$InstanceIp"
Write-Host "  bash train-all-adapters.sh"

