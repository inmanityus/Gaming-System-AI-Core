# PowerShell Script: Upgrade EKS Cluster Kubernetes Version
# Purpose: Upgrade gaming-ai-gold-tier cluster from K8s 1.29 to 1.32
# AWS Notification: K8s 1.29 support ends March 23, 2026

param(
    [string]$ClusterName = "gaming-ai-gold-tier",
    [string]$Region = "us-east-1",
    [string]$TargetVersion = "1.32",
    [switch]$DryRun = $false
)

Write-Host "`n=== EKS Kubernetes Upgrade Script ===" -ForegroundColor Cyan
Write-Host "Cluster: $ClusterName" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Target Version: $TargetVersion" -ForegroundColor White
Write-Host "Dry Run: $DryRun" -ForegroundColor $(if ($DryRun) { "Yellow" } else { "Red" })
Write-Host ""

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] AWS CLI not found. Install: winget install Amazon.AWSCLI" -ForegroundColor Red
    exit 1
}

# Verify AWS credentials
Write-Host "[CHECK] Verifying AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Host "[CHECK] ✓ AWS credentials valid (Account: $($identity.Account))" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}

# Check cluster exists
Write-Host "[CHECK] Verifying cluster exists..." -ForegroundColor Yellow
try {
    $cluster = aws eks describe-cluster --name $ClusterName --region $Region 2>&1 | ConvertFrom-Json
    $currentVersion = $cluster.cluster.version
    Write-Host "[CHECK] ✓ Cluster found (Current Version: $currentVersion)" -ForegroundColor Green
    
    if ($currentVersion -eq $TargetVersion) {
        Write-Host "[INFO] Cluster is already on version $TargetVersion. No upgrade needed." -ForegroundColor Green
        exit 0
    }
    
    if ($currentVersion -gt $TargetVersion) {
        Write-Host "[WARNING] Cluster version ($currentVersion) is newer than target ($TargetVersion). Downgrade not supported." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Cluster '$ClusterName' not found or access denied." -ForegroundColor Red
    exit 1
}

# Check cluster status
Write-Host "[CHECK] Checking cluster status..." -ForegroundColor Yellow
$status = $cluster.cluster.status
if ($status -ne "ACTIVE") {
    Write-Host "[ERROR] Cluster is not in ACTIVE state (Current: $status). Cannot upgrade." -ForegroundColor Red
    exit 1
}
Write-Host "[CHECK] ✓ Cluster is ACTIVE" -ForegroundColor Green

# Pre-upgrade checks
Write-Host "`n[PRE-UPGRADE] Running pre-upgrade checks..." -ForegroundColor Cyan

# Check kubectl
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] kubectl not found. Some checks will be skipped." -ForegroundColor Yellow
} else {
    # Update kubeconfig
    Write-Host "[PRE-UPGRADE] Updating kubeconfig..." -ForegroundColor Yellow
    aws eks update-kubeconfig --name $ClusterName --region $Region 2>&1 | Out-Null
    
    # Check node versions
    Write-Host "[PRE-UPGRADE] Checking node versions..." -ForegroundColor Yellow
    $nodes = kubectl get nodes -o json 2>&1 | ConvertFrom-Json
    if ($nodes) {
        Write-Host "[PRE-UPGRADE] Current node versions:" -ForegroundColor White
        $nodes.items | ForEach-Object {
            $nodeVersion = $_.status.nodeInfo.kubeletVersion
            Write-Host "  - $($_.metadata.name): $nodeVersion" -ForegroundColor Gray
        }
    }
    
    # Check pod status
    Write-Host "[PRE-UPGRADE] Checking pod status..." -ForegroundColor Yellow
    $pods = kubectl get pods --all-namespaces --field-selector=status.phase!=Running 2>&1
    if ($pods -match "No resources") {
        Write-Host "[PRE-UPGRADE] ✓ All pods are running" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Some pods are not in Running state. Review before upgrade." -ForegroundColor Yellow
        Write-Host $pods -ForegroundColor Gray
    }
}

# Check addon compatibility
Write-Host "[PRE-UPGRADE] Checking addon compatibility..." -ForegroundColor Yellow
$addons = aws eks list-addons --cluster-name $ClusterName --region $Region 2>&1 | ConvertFrom-Json
if ($addons.addons) {
    Write-Host "[PRE-UPGRADE] Installed addons:" -ForegroundColor White
    $addons.addons | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Gray
    }
}

# Confirm upgrade
if (-not $DryRun) {
    Write-Host "`n[CONFIRM] Ready to upgrade cluster from $currentVersion to $TargetVersion" -ForegroundColor Yellow
    Write-Host "[CONFIRM] This will take approximately 30-60 minutes." -ForegroundColor Yellow
    Write-Host "[CONFIRM] Control plane will be temporarily unavailable during upgrade." -ForegroundColor Yellow
    Write-Host "[CONFIRM] Running workloads will continue, but new deployments may be delayed." -ForegroundColor Yellow
    
    $confirm = Read-Host "`nContinue with upgrade? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "[CANCELLED] Upgrade cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

# Perform upgrade
if ($DryRun) {
    Write-Host "`n[DRY-RUN] Would upgrade cluster using Terraform:" -ForegroundColor Cyan
    Write-Host "  cd infrastructure/terraform/eks-gold-tier" -ForegroundColor White
    Write-Host "  terraform init" -ForegroundColor White
    Write-Host "  terraform plan" -ForegroundColor White
    Write-Host "  terraform apply" -ForegroundColor White
    Write-Host "`n[DRY-RUN] Or using AWS CLI:" -ForegroundColor Cyan
    Write-Host "  aws eks update-cluster-version --name $ClusterName --version $TargetVersion --region $Region" -ForegroundColor White
} else {
    Write-Host "`n[UPGRADE] Starting cluster upgrade..." -ForegroundColor Cyan
    
    # Option 1: Use Terraform (recommended)
    Write-Host "[UPGRADE] Using Terraform for upgrade..." -ForegroundColor Yellow
    $terraformDir = Join-Path $PSScriptRoot "..\terraform\eks-gold-tier"
    
    if (Test-Path $terraformDir) {
        Push-Location $terraformDir
        
        try {
            Write-Host "[UPGRADE] Running terraform init..." -ForegroundColor Yellow
            terraform init 2>&1 | Out-Null
            
            Write-Host "[UPGRADE] Running terraform plan..." -ForegroundColor Yellow
            terraform plan -out=upgrade.tfplan 2>&1 | Out-Null
            
            Write-Host "[UPGRADE] Applying upgrade..." -ForegroundColor Yellow
            terraform apply upgrade.tfplan
            
            Write-Host "[UPGRADE] ✓ Terraform apply completed" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] Terraform upgrade failed: $_" -ForegroundColor Red
            Pop-Location
            exit 1
        } finally {
            Pop-Location
        }
    } else {
        # Option 2: Use AWS CLI directly
        Write-Host "[UPGRADE] Terraform not found, using AWS CLI..." -ForegroundColor Yellow
        Write-Host "[UPGRADE] Starting cluster version update..." -ForegroundColor Yellow
        
        aws eks update-cluster-version `
            --name $ClusterName `
            --version $TargetVersion `
            --region $Region
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Cluster upgrade failed." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "[UPGRADE] ✓ Upgrade initiated. Waiting for completion..." -ForegroundColor Green
        
        # Wait for upgrade to complete
        $maxWait = 3600  # 60 minutes
        $elapsed = 0
        $interval = 30   # Check every 30 seconds
        
        while ($elapsed -lt $maxWait) {
            Start-Sleep -Seconds $interval
            $elapsed += $interval
            
            $clusterStatus = (aws eks describe-cluster --name $ClusterName --region $Region 2>&1 | ConvertFrom-Json).cluster.status
            $clusterVersion = (aws eks describe-cluster --name $ClusterName --region $Region 2>&1 | ConvertFrom-Json).cluster.version
            
            Write-Host "[WAIT] Status: $clusterStatus, Version: $clusterVersion (Elapsed: $elapsed seconds)" -ForegroundColor Gray
            
            if ($clusterStatus -eq "ACTIVE" -and $clusterVersion -eq $TargetVersion) {
                Write-Host "[UPGRADE] ✓ Upgrade completed successfully!" -ForegroundColor Green
                break
            }
            
            if ($clusterStatus -eq "FAILED") {
                Write-Host "[ERROR] Upgrade failed. Check AWS Console for details." -ForegroundColor Red
                exit 1
            }
        }
        
        if ($elapsed -ge $maxWait) {
            Write-Host "[WARNING] Upgrade is taking longer than expected. Check AWS Console for status." -ForegroundColor Yellow
        }
    }
    
    # Post-upgrade verification
    Write-Host "`n[VERIFY] Verifying upgrade..." -ForegroundColor Cyan
    
    $finalCluster = aws eks describe-cluster --name $ClusterName --region $Region 2>&1 | ConvertFrom-Json
    $finalVersion = $finalCluster.cluster.version
    $finalStatus = $finalCluster.cluster.status
    
    Write-Host "[VERIFY] Final Version: $finalVersion" -ForegroundColor $(if ($finalVersion -eq $TargetVersion) { "Green" } else { "Yellow" })
    Write-Host "[VERIFY] Final Status: $finalStatus" -ForegroundColor $(if ($finalStatus -eq "ACTIVE") { "Green" } else { "Yellow" })
    
    if ($finalVersion -eq $TargetVersion -and $finalStatus -eq "ACTIVE") {
        Write-Host "`n[SUCCESS] Cluster upgrade completed successfully!" -ForegroundColor Green
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "  1. Update kubectl context: aws eks update-kubeconfig --name $ClusterName --region $Region" -ForegroundColor White
        Write-Host "  2. Verify nodes: kubectl get nodes" -ForegroundColor White
        Write-Host "  3. Check pods: kubectl get pods --all-namespaces" -ForegroundColor White
        Write-Host "  4. Update node groups (if needed): See upgrade guide" -ForegroundColor White
    } else {
        Write-Host "[WARNING] Upgrade may not be complete. Please verify manually." -ForegroundColor Yellow
    }
}

Write-Host "`n=== Upgrade Script Complete ===" -ForegroundColor Cyan









