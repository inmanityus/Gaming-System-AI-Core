# Deploy GPU Metrics Publisher to Gold and Silver GPU instances
# Production-ready deployment with proper service management and security

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying GPU Metrics Publisher (Production-Ready)" -ForegroundColor Cyan
Write-Host "=" * 60

# Configuration
$goldIP = "54.234.135.254"
$silverIP = "18.208.225.146"
$keyPath = "~\.ssh\ai-gaming-gpu-key.pem"
$sshUser = "ubuntu"

# Files to deploy
$publisherScript = "E:\Vibe Code\Gaming System\AI Core\services\gpu_metrics_publisher\publisher.py"
$requirements = "E:\Vibe Code\Gaming System\AI Core\services\gpu_metrics_publisher\requirements.txt"

# PRODUCTION-READY systemd service with hardening
$systemdService = @'
[Unit]
Description=GPU Metrics Publisher for CloudWatch Auto-Scaling
Documentation=https://github.com/your-org/gaming-system-ai-core
After=network-online.target cloud-init.service
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=video
WorkingDirectory=/opt/gpu-metrics
EnvironmentFile=/etc/default/gpu-metrics
ExecStart=/opt/gpu-metrics/venv/bin/python3 /opt/gpu-metrics/publisher.py

# Restart policy (on-failure with rate limiting)
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=10

# Logging
StandardOutput=journal
StandardError=journal

# Basic security hardening
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
'@

function Deploy-To-Instance {
    param(
        [string]$IP,
        [string]$Tier
    )
    
    Write-Host "`n📡 Deploying to $Tier GPU ($IP)..." -ForegroundColor Yellow
    
    try {
        # Pre-flight checks
        Write-Host "  → Running pre-flight checks..."
        $gpuCheck = ssh -i $keyPath -o StrictHostKeyChecking=accept-new "$sshUser@$IP" "nvidia-smi -L 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    ⚠️ Warning: nvidia-smi check failed: $gpuCheck" -ForegroundColor Yellow
        } else {
            Write-Host "    ✅ NVIDIA GPU detected" -ForegroundColor Green
        }
        
        # Create deployment directory structure
        Write-Host "  → Creating deployment structure..."
        ssh -i $keyPath "$sshUser@$IP" @"
sudo mkdir -p /opt/gpu-metrics
sudo chown ubuntu:ubuntu /opt/gpu-metrics
mkdir -p /opt/gpu-metrics/releases/\$(date +%Y%m%d-%H%M%S)
"@
        
        # Get latest release directory
        $releaseDir = ssh -i $keyPath "$sshUser@$IP" "ls -t /opt/gpu-metrics/releases/ | head -1"
        $fullReleasePath = "/opt/gpu-metrics/releases/$releaseDir"
        
        # Upload files to release directory
        Write-Host "  → Uploading files to $fullReleasePath..."
        ssh -i $keyPath "$sshUser@$IP" "mkdir -p $fullReleasePath"
        scp -i $keyPath -o StrictHostKeyChecking=accept-new $publisherScript "$sshUser@${IP}:$fullReleasePath/"
        scp -i $keyPath $requirements "$sshUser@${IP}:$fullReleasePath/"
        
        # Create virtual environment and install dependencies
        Write-Host "  → Creating Python virtual environment..."
        ssh -i $keyPath "$sshUser@$IP" @"
cd $fullReleasePath
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
deactivate
"@
        
        # Create symlink to current release
        Write-Host "  → Activating new release..."
        ssh -i $keyPath "$sshUser@$IP" @"
rm -f /opt/gpu-metrics/current
ln -sf $fullReleasePath /opt/gpu-metrics/current
"@
        
        # Create main symlinks for convenience
        ssh -i $keyPath "$sshUser@$IP" @"
sudo rm -f /opt/gpu-metrics/publisher.py /opt/gpu-metrics/venv
sudo ln -sf /opt/gpu-metrics/current/publisher.py /opt/gpu-metrics/publisher.py
sudo ln -sf /opt/gpu-metrics/current/venv /opt/gpu-metrics/venv
"@
        
        # Create environment file
        Write-Host "  → Creating environment configuration..."
        ssh -i $keyPath "$sshUser@$IP" @"
echo 'GPU_TIER=$Tier' | sudo tee /etc/default/gpu-metrics > /dev/null
echo 'AWS_DEFAULT_REGION=us-east-1' | sudo tee -a /etc/default/gpu-metrics > /dev/null
sudo chmod 644 /etc/default/gpu-metrics
"@
        
        # Install systemd service
        Write-Host "  → Installing systemd service..."
        ssh -i $keyPath "$sshUser@$IP" "echo '$systemdService' | sudo tee /etc/systemd/system/gpu-metrics.service > /dev/null"
        
        # Reload systemd and enable service
        Write-Host "  → Enabling service..."
        ssh -i $keyPath "$sshUser@$IP" @"
sudo systemctl daemon-reload
sudo systemctl enable gpu-metrics.service
"@
        
        # Restart service
        Write-Host "  → Starting service..."
        ssh -i $keyPath "$sshUser@$IP" "sudo systemctl restart gpu-metrics.service"
        
        # Wait for service to start
        Start-Sleep -Seconds 3
        
        # Check status
        Write-Host "  → Verifying deployment..."
        $status = ssh -i $keyPath "$sshUser@$IP" "sudo systemctl is-active gpu-metrics.service"
        $isEnabled = ssh -i $keyPath "$sshUser@$IP" "sudo systemctl is-enabled gpu-metrics.service"
        
        if ($status -eq "active" -and $isEnabled -eq "enabled") {
            Write-Host "  ✅ $Tier GPU metrics publisher deployed successfully" -ForegroundColor Green
            
            # Show recent logs
            Write-Host "    Recent logs:"
            ssh -i $keyPath "$sshUser@$IP" "sudo journalctl -u gpu-metrics.service -n 5 --no-pager" | ForEach-Object {
                Write-Host "      $_" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ⚠️ Service deployed but status unexpected" -ForegroundColor Yellow
            Write-Host "    Status: $status, Enabled: $isEnabled"
            Write-Host "    Full logs:"
            ssh -i $keyPath "$sshUser@$IP" "sudo journalctl -u gpu-metrics.service -n 30 --no-pager"
            throw "Service not active after deployment"
        }
        
        # Keep last 5 releases only
        Write-Host "  → Cleaning up old releases..."
        ssh -i $keyPath "$sshUser@$IP" @"
cd /opt/gpu-metrics/releases
ls -t | tail -n +6 | xargs -r rm -rf
"@
        
    } catch {
        Write-Host "  ❌ Failed to deploy to $Tier GPU: $_" -ForegroundColor Red
        throw
    }
}

try {
    # Check SSH key exists
    $resolvedKeyPath = Resolve-Path $keyPath -ErrorAction Stop
    Write-Host "Using SSH key: $resolvedKeyPath"
    
    # Deploy to Gold GPU
    Deploy-To-Instance -IP $goldIP -Tier "gold"
    
    # Deploy to Silver GPU
    Deploy-To-Instance -IP $silverIP -Tier "silver"
    
    Write-Host "`n" + ("=" * 60)
    Write-Host "✅ GPU METRICS PUBLISHERS DEPLOYED" -ForegroundColor Green
    Write-Host ("=" * 60)
    Write-Host "Configuration:"
    Write-Host "  - Gold GPU:   $goldIP (tier: gold)"
    Write-Host "  - Silver GPU: $silverIP (tier: silver)"
    Write-Host "  - Install path: /opt/gpu-metrics"
    Write-Host "  - Virtual env: /opt/gpu-metrics/venv"
    Write-Host "  - Config: /etc/default/gpu-metrics"
    Write-Host "`nCloudWatch Metrics:"
    Write-Host "  - Namespace: AI-Gaming/GPU"
    Write-Host "  - Interval: 60 seconds"
    Write-Host "  - Dimensions: InstanceId, Tier, DeviceIndex"
    Write-Host "`nMonitoring Commands:"
    Write-Host "  # Check service status"
    Write-Host "  ssh -i $keyPath $sshUser@$goldIP 'sudo systemctl status gpu-metrics.service'"
    Write-Host ""
    Write-Host "  # View real-time logs"
    Write-Host "  ssh -i $keyPath $sshUser@$goldIP 'sudo journalctl -u gpu-metrics.service -f'"
    Write-Host ""
    Write-Host "  # Check CloudWatch metrics"
    Write-Host "  aws cloudwatch get-metric-statistics --namespace AI-Gaming/GPU --metric-name GPUUtilization --dimensions Name=Tier,Value=gold --statistics Average --start-time (Get-Date).AddMinutes(-10).ToUniversalTime().ToString('o') --end-time (Get-Date).ToUniversalTime().ToString('o') --period 60"
    Write-Host ""
    
} catch {
    Write-Host "`n❌ ERROR: $_" -ForegroundColor Red
    Write-Host "Deployment failed. Check logs above for details." -ForegroundColor Red
    exit 1
}

