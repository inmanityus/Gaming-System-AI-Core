# Deploy GPU Metrics Publisher to Gold and Silver GPU instances
# Deploys NVIDIA DCGM metrics publisher for CloudWatch auto-scaling

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying GPU Metrics Publisher" -ForegroundColor Cyan
Write-Host "=" * 60

# Configuration
$goldIP = "54.234.135.254"
$silverIP = "18.208.225.146"
$keyPath = "~\.ssh\ai-gaming-gpu-key.pem"
$sshUser = "ubuntu"

# Files to deploy
$publisherScript = "E:\Vibe Code\Gaming System\AI Core\services\gpu_metrics_publisher\publisher.py"
$requirements = "E:\Vibe Code\Gaming System\AI Core\services\gpu_metrics_publisher\requirements.txt"

# Systemd service content
$systemdService = @'
[Unit]
Description=GPU Metrics Publisher for CloudWatch
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/gpu_metrics
Environment="GPU_TIER=%TIER%"
Environment="AWS_DEFAULT_REGION=us-east-1"
ExecStart=/usr/bin/python3 /home/ubuntu/gpu_metrics/publisher.py
Restart=always
RestartSec=10

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
        # Create remote directory
        Write-Host "  → Creating remote directory..."
        ssh -i $keyPath -o StrictHostKeyChecking=no "$sshUser@$IP" "mkdir -p /home/ubuntu/gpu_metrics"
        
        # Upload files
        Write-Host "  → Uploading publisher.py..."
        scp -i $keyPath -o StrictHostKeyChecking=no $publisherScript "$sshUser@${IP}:/home/ubuntu/gpu_metrics/"
        
        Write-Host "  → Uploading requirements.txt..."
        scp -i $keyPath -o StrictHostKeyChecking=no $requirements "$sshUser@${IP}:/home/ubuntu/gpu_metrics/"
        
        # Install dependencies
        Write-Host "  → Installing Python dependencies..."
        ssh -i $keyPath "$sshUser@$IP" @"
sudo apt-get update -qq
sudo apt-get install -y python3-pip
cd /home/ubuntu/gpu_metrics
pip3 install -r requirements.txt --quiet
"@
        
        # Create systemd service
        Write-Host "  → Creating systemd service..."
        $serviceContent = $systemdService -replace '%TIER%', $Tier
        ssh -i $keyPath "$sshUser@$IP" "echo '$serviceContent' | sudo tee /etc/systemd/system/gpu-metrics.service > /dev/null"
        
        # Enable and start service
        Write-Host "  → Enabling and starting service..."
        ssh -i $keyPath "$sshUser@$IP" @"
sudo systemctl daemon-reload
sudo systemctl enable gpu-metrics.service
sudo systemctl restart gpu-metrics.service
"@
        
        # Check status
        Write-Host "  → Checking service status..."
        $status = ssh -i $keyPath "$sshUser@$IP" "sudo systemctl is-active gpu-metrics.service"
        
        if ($status -eq "active") {
            Write-Host "  ✅ $Tier GPU metrics publisher deployed and running" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Service deployed but not active (status: $status)" -ForegroundColor Yellow
            Write-Host "    Checking logs..."
            ssh -i $keyPath "$sshUser@$IP" "sudo journalctl -u gpu-metrics.service -n 20 --no-pager"
        }
        
    } catch {
        Write-Host "  ❌ Failed to deploy to $Tier GPU: $_" -ForegroundColor Red
        throw
    }
}

try {
    # Check SSH key exists
    if (-not (Test-Path (Resolve-Path $keyPath -ErrorAction SilentlyContinue))) {
        throw "SSH key not found at: $keyPath"
    }
    
    # Deploy to Gold GPU
    Deploy-To-Instance -IP $goldIP -Tier "gold"
    
    # Deploy to Silver GPU
    Deploy-To-Instance -IP $silverIP -Tier "silver"
    
    Write-Host "`n" + ("=" * 60)
    Write-Host "✅ GPU METRICS PUBLISHERS DEPLOYED" -ForegroundColor Green
    Write-Host ("=" * 60)
    Write-Host "Monitoring:"
    Write-Host "  - Gold GPU:   $goldIP (tier: gold)"
    Write-Host "  - Silver GPU: $silverIP (tier: silver)"
    Write-Host "`nMetrics published to CloudWatch:"
    Write-Host "  - Namespace: AI-Gaming/GPU"
    Write-Host "  - Interval: 60 seconds"
    Write-Host "  - Metrics: GPU utilization, memory, temperature, power"
    Write-Host "`nCheck logs:"
    Write-Host "  ssh -i $keyPath $sshUser@$goldIP 'sudo journalctl -u gpu-metrics.service -f'"
    Write-Host ""
    
} catch {
    Write-Host "`n❌ ERROR: $_" -ForegroundColor Red
    exit 1
}

