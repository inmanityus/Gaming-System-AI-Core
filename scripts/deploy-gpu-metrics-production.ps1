# Production-Ready GPU Metrics Publisher Deployment
# Implements ALL GPT-5 Pro recommendations for 100% production readiness
# - Dedicated user with least privilege
# - Full systemd hardening
# - Automated rollback on failure
# - IAM policy validation
# - Health checks and monitoring

$ErrorActionPreference = "Stop"

Write-Host "🚀 GPU Metrics Publisher - Production Deployment" -ForegroundColor Cyan
Write-Host "=" * 70

# Configuration
$goldIP = "54.234.135.254"
$silverIP = "18.208.225.146"
$keyPath = "~\.ssh\ai-gaming-gpu-key.pem"
$sshUser = "ubuntu"
$deployUser = "gpu-metrics"
$installPath = "/opt/gpu-metrics"

# Files to deploy
$publisherScript = "E:\Vibe Code\Gaming System\AI Core\services\gpu_metrics_publisher\publisher.py"
$requirements = "E:\Vibe Code\Gaming System\AI Core\services\gpu_metrics_publisher\requirements.txt"

# PRODUCTION systemd service with FULL hardening
$systemdService = @'
[Unit]
Description=GPU Metrics Publisher for CloudWatch Auto-Scaling
Documentation=https://github.com/your-org/gaming-system-ai-core
After=network-online.target cloud-init.service nvidia-persistenced.service time-sync.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=notify
User=gpu-metrics
Group=gpu-metrics
SupplementaryGroups=video render
WorkingDirectory=/opt/gpu-metrics/current
EnvironmentFile=/etc/default/gpu-metrics
Environment="PYTHONDONTWRITEBYTECODE=1"
Environment="PYTHONUNBUFFERED=1"

# Pre-flight check (tolerant of missing GPU, with 5s timeout to prevent hangs)
ExecStartPre=/usr/bin/timeout 5s /bin/sh -c '[ -c /dev/nvidiactl ] && /usr/bin/nvidia-smi -L || echo "No GPU detected - starting heartbeat-only mode"'

# Main execution
ExecStart=/opt/gpu-metrics/current/venv/bin/python3 -u /opt/gpu-metrics/current/publisher.py

# Restart policy with rate limiting (production-tuned)
Restart=on-failure
RestartSec=5
WatchdogSec=45
TimeoutStartSec=30
TimeoutStopSec=15
KillSignal=SIGTERM
OOMPolicy=kill

# Logging
StandardOutput=journal
StandardError=journal

# Resource limits (prevent runaway)
MemoryMax=256M
CPUQuota=5%

# Security hardening (full production)
# NOTE: PrivateDevices NOT set (defaults to no) - required for GPU access
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=true
PrivateTmp=yes
ProtectControlGroups=yes
ProtectKernelTunables=yes
ProtectKernelLogs=yes
ProtectClock=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictRealtime=yes
RestrictNamespaces=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
CapabilityBoundingSet=
AmbientCapabilities=
SystemCallArchitectures=native
ProtectProc=invisible
ProcSubset=pid
UMask=0027
TasksMax=512

[Install]
WantedBy=multi-user.target
'@

# IAM Policy for validation
$iamPolicyJSON = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchMetricsPublish",
      "Effect": "Allow",
      "Action": "cloudwatch:PutMetricData",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "AI-Gaming/GPU"
        }
      }
    }
  ]
}
'@

function Test-IAMPolicy {
    param([string]$InstanceIP)
    
    Write-Host "  → Validating IAM policy (PutMetricData test)..." -ForegroundColor Yellow
    
    # Test actual PutMetricData permission with allowed namespace
    $testResult = ssh -i $keyPath -o StrictHostKeyChecking=accept-new "$sshUser@$InstanceIP" @"
python3 << 'PYEOF'
import boto3
import json
from datetime import datetime

try:
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    cloudwatch.put_metric_data(
        Namespace='AI-Gaming/GPU',
        MetricData=[{
            'MetricName': 'DeploymentCheck',
            'Value': 1.0,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [{'Name': 'Test', 'Value': 'PreFlight'}]
        }]
    )
    print('SUCCESS')
except Exception as e:
    print(f'FAILED: {e}')
PYEOF
"@
    
    if ($testResult -like "*SUCCESS*") {
        Write-Host "    ✅ IAM policy validated (PutMetricData works)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "    ⚠️ WARNING: PutMetricData test failed" -ForegroundColor Yellow
        Write-Host "    Result: $testResult" -ForegroundColor Gray
        Write-Host "    Ensure instance has cloudwatch:PutMetricData for AI-Gaming/GPU namespace"
        return $false
    }
}

function Deploy-To-Instance {
    param(
        [string]$IP,
        [string]$Tier
    )
    
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "📡 Deploying to $Tier GPU ($IP)" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    
    try {
        # Step 1: Pre-flight checks
        Write-Host "`n[1/12] Pre-flight checks..." -ForegroundColor Yellow
        
        # Check NVIDIA driver
        $gpuCheck = ssh -i $keyPath -o StrictHostKeyChecking=accept-new "$sshUser@$IP" "nvidia-smi -L 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ NVIDIA GPU detected: $($gpuCheck.Split("`n")[0])" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ WARNING: nvidia-smi check failed" -ForegroundColor Yellow
        }
        
        # Check IMDSv2
        $imdsCheck = ssh -i $keyPath "$sshUser@$IP" @"
TOKEN=\$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)
if [ -n "\$TOKEN" ]; then echo "IMDSv2"; else echo "IMDSv1"; fi
"@
        Write-Host "  ✅ Metadata service: $imdsCheck" -ForegroundColor Green
        
        # Check IAM policy
        Test-IAMPolicy -InstanceIP $IP | Out-Null
        
        # Step 2: Create dedicated user
        Write-Host "`n[2/12] Creating dedicated user ($deployUser)..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
if ! id $deployUser > /dev/null 2>&1; then
    sudo useradd --system --no-create-home --shell /usr/sbin/nologin $deployUser
    sudo usermod -aG video,render $deployUser
    echo '  ✅ Created user: $deployUser (groups: video, render)'
else
    echo '  ℹ️ User $deployUser already exists'
fi
"@
        
        # Step 3: Create directory structure
        Write-Host "`n[3/12] Creating deployment structure..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
sudo mkdir -p $installPath/releases
sudo chown root:root $installPath
sudo chmod 0755 $installPath
"@
        
        # Create timestamped release directory
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $releaseDir = "$installPath/releases/$timestamp"
        
        ssh -i $keyPath "$sshUser@$IP" "sudo mkdir -p $releaseDir"
        Write-Host "  ✅ Created release: $releaseDir" -ForegroundColor Green
        
        # Step 4: Upload files
        Write-Host "`n[4/12] Uploading files..." -ForegroundColor Yellow
        
        # Upload to temp location first (ubuntu can write here)
        $tempDir = "/tmp/gpu-metrics-deploy-$timestamp"
        ssh -i $keyPath "$sshUser@$IP" "mkdir -p $tempDir"
        
        scp -i $keyPath -o StrictHostKeyChecking=accept-new $publisherScript "$sshUser@${IP}:$tempDir/"
        scp -i $keyPath $requirements "$sshUser@${IP}:$tempDir/"
        
        # Move to release directory with proper ownership
        ssh -i $keyPath "$sshUser@$IP" @"
sudo mv $tempDir/* $releaseDir/
sudo chown -R root:root $releaseDir
sudo chmod -R 0755 $releaseDir
rm -rf $tempDir
"@
        Write-Host "  ✅ Files uploaded and secured" -ForegroundColor Green
        
        # Step 5: Create virtual environment
        Write-Host "`n[5/12] Creating Python virtual environment..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
cd $releaseDir
sudo python3 -m venv venv
sudo chown -R root:root venv
"@
        
        # Step 6: Install OS packages and Python dependencies
        Write-Host "`n[6/12] Installing system packages and Python dependencies..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
# Install OS systemd package (more reliable than pip)
sudo apt-get update -qq
sudo apt-get install -y python3-systemd > /dev/null 2>&1 || echo "python3-systemd not available (will use native fallback)"

# Install Python dependencies
cd $releaseDir
sudo venv/bin/pip install --upgrade pip --quiet
sudo PIP_NO_CACHE_DIR=1 venv/bin/pip install -r requirements.txt --quiet

# Try to make python3-systemd available in venv (if OS package exists)
if [ -d /usr/lib/python3/dist-packages/systemd ]; then
    sudo ln -sf /usr/lib/python3/dist-packages/systemd venv/lib/python*/site-packages/ 2>/dev/null || true
fi
"@
        Write-Host "  ✅ Dependencies installed (with OS systemd package if available)" -ForegroundColor Green
        
        # Step 7: Store previous release for rollback
        Write-Host "`n[7/12] Preparing rollback capability..." -ForegroundColor Yellow
        $previousRelease = ssh -i $keyPath "$sshUser@$IP" @"
if [ -L $installPath/current ]; then
    readlink $installPath/current
else
    echo "none"
fi
"@
        Write-Host "  Previous release: $previousRelease" -ForegroundColor Gray
        
        # Step 8: Atomic symlink swap
        Write-Host "`n[8/12] Activating new release..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
sudo ln -sfn $releaseDir $installPath/current
"@
        Write-Host "  ✅ Activated: $installPath/current → $releaseDir" -ForegroundColor Green
        
        # Step 9: Create environment file
        Write-Host "`n[9/12] Creating environment configuration..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
echo 'GPU_TIER=$Tier' | sudo tee /etc/default/gpu-metrics > /dev/null
echo 'AWS_DEFAULT_REGION=us-east-1' | sudo tee -a /etc/default/gpu-metrics > /dev/null
sudo chown root:root /etc/default/gpu-metrics
sudo chmod 0644 /etc/default/gpu-metrics
"@
        Write-Host "  ✅ Environment configured" -ForegroundColor Green
        
        # Step 10: Install systemd service
        Write-Host "`n[10/12] Installing systemd service..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" "echo '$systemdService' | sudo tee /etc/systemd/system/gpu-metrics.service > /dev/null"
        ssh -i $keyPath "$sshUser@$IP" @"
sudo systemctl daemon-reload
sudo systemctl enable gpu-metrics.service
"@
        
        # Step 11: Start service and validate
        Write-Host "`n[11/12] Starting service..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" "sudo systemctl restart gpu-metrics.service"
        
        # Wait for service to start
        Start-Sleep -Seconds 5
        
        # Check status
        $status = ssh -i $keyPath "$sshUser@$IP" "sudo systemctl is-active gpu-metrics.service"
        $isEnabled = ssh -i $keyPath "$sshUser@$IP" "sudo systemctl is-enabled gpu-metrics.service"
        
        if ($status -eq "active" -and $isEnabled -eq "enabled") {
            Write-Host "  ✅ Service started successfully" -ForegroundColor Green
            
            # Show recent logs
            Write-Host "`n  Recent logs:" -ForegroundColor Gray
            ssh -i $keyPath "$sshUser@$IP" "sudo journalctl -u gpu-metrics.service -n 10 --no-pager" | ForEach-Object {
                Write-Host "    $_" -ForegroundColor DarkGray
            }
            
            # Verify heartbeat metric will be published
            Write-Host "`n  Heartbeat metric will publish in <60 seconds" -ForegroundColor Gray
            
        } else {
            Write-Host "  ❌ Service failed to start (status: $status)" -ForegroundColor Red
            
            # Show detailed logs
            Write-Host "`n  Service logs:" -ForegroundColor Red
            ssh -i $keyPath "$sshUser@$IP" "sudo journalctl -u gpu-metrics.service -n 50 --no-pager"
            
            # Rollback if previous release exists
            if ($previousRelease -ne "none" -and (Test-Path $previousRelease)) {
                Write-Host "`n  🔄 Rolling back to previous release..." -ForegroundColor Yellow
                ssh -i $keyPath "$sshUser@$IP" @"
sudo ln -sfn $previousRelease $installPath/current
sudo systemctl restart gpu-metrics.service
"@
                Start-Sleep -Seconds 3
                $rollbackStatus = ssh -i $keyPath "$sshUser@$IP" "sudo systemctl is-active gpu-metrics.service"
                
                if ($rollbackStatus -eq "active") {
                    Write-Host "  ✅ Rollback successful" -ForegroundColor Green
                } else {
                    Write-Host "  ❌ Rollback failed - manual intervention required" -ForegroundColor Red
                }
            }
            
            throw "Service deployment failed"
        }
        
        # Step 12: Cleanup old releases
        Write-Host "`n[12/12] Cleaning up old releases..." -ForegroundColor Yellow
        ssh -i $keyPath "$sshUser@$IP" @"
cd $installPath/releases
ls -t | tail -n +6 | xargs -r sudo rm -rf
"@
        $remainingReleases = ssh -i $keyPath "$sshUser@$IP" "ls -1 $installPath/releases | wc -l"
        Write-Host "  ✅ Keeping last 5 releases ($remainingReleases total)" -ForegroundColor Green
        
        Write-Host "`n✅ $Tier GPU deployment complete!" -ForegroundColor Green
        
    } catch {
        Write-Host "`n❌ Deployment failed: $_" -ForegroundColor Red
        throw
    }
}

try {
    # Check SSH key exists
    $resolvedKeyPath = Resolve-Path $keyPath -ErrorAction Stop
    Write-Host "SSH key: $resolvedKeyPath`n"
    
    # Deploy to both instances
    Deploy-To-Instance -IP $goldIP -Tier "gold"
    Deploy-To-Instance -IP $silverIP -Tier "silver"
    
    # Final summary
    Write-Host "`n" + ("=" * 70) -ForegroundColor Green
    Write-Host "✅ PRODUCTION DEPLOYMENT COMPLETE" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green
    
    Write-Host "`nConfiguration:"
    Write-Host "  • Gold GPU:   $goldIP (tier: gold)"
    Write-Host "  • Silver GPU: $silverIP (tier: silver)"
    Write-Host "  • Install path: $installPath"
    Write-Host "  • Service user: $deployUser (systemd, no login)"
    Write-Host "  • Config: /etc/default/gpu-metrics"
    
    Write-Host "`nSecurity:"
    Write-Host "  • Full systemd hardening enabled"
    Write-Host "  • No new privileges, protected system/home"
    Write-Host "  • Network restrictions (AF_UNIX, AF_INET, AF_INET6 only)"
    Write-Host "  • Memory protection (DEP, no exec)"
    Write-Host "  • Watchdog: 45s (auto-restart on hang)"
    
    Write-Host "`nCloudWatch Metrics:"
    Write-Host "  • Namespace: AI-Gaming/GPU"
    Write-Host "  • Interval: 60 seconds"
    Write-Host "  • Dimensions: InstanceId, Tier, InstanceType, AZ"
    Write-Host "  • Heartbeat: Enabled (liveness monitoring)"
    
    Write-Host "`nMonitoring Commands:"
    Write-Host "  # Check service status"
    Write-Host "  ssh -i $keyPath $sshUser@$goldIP 'sudo systemctl status gpu-metrics.service'"
    Write-Host ""
    Write-Host "  # View real-time logs"
    Write-Host "  ssh -i $keyPath $sshUser@$goldIP 'sudo journalctl -u gpu-metrics.service -f'"
    Write-Host ""
    Write-Host "  # Check heartbeat metric (wait 2-3 minutes after deployment)"
    Write-Host "  aws cloudwatch get-metric-statistics --namespace AI-Gaming/GPU \\"
    Write-Host "    --metric-name Heartbeat --dimensions Name=Tier,Value=gold \\"
    Write-Host "    --statistics Sum --start-time (Get-Date).AddMinutes(-5) \\"
    Write-Host "    --end-time (Get-Date) --period 60 --region us-east-1"
    Write-Host ""
    
    Write-Host "🎉 Production-ready deployment with full hardening complete!" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "`n❌ DEPLOYMENT FAILED: $_" -ForegroundColor Red
    Write-Host "Check logs above for details." -ForegroundColor Red
    exit 1
}

