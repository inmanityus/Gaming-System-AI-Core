# PowerShell Script: Check EKS Cluster Kubernetes Version
# Purpose: Verify current Kubernetes version of EKS clusters
# Usage: .\scripts\aws-check-eks-version.ps1

param(
    [string]$Region = "us-east-1",
    [string[]]$ClusterNames = @("gaming-ai-gold-tier", "gaming-ai-silver-tier")
)

Write-Host "`n=== EKS Cluster Version Check ===" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor White
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

Write-Host ""

foreach ($clusterName in $ClusterNames) {
    Write-Host "[CLUSTER] Checking: $clusterName" -ForegroundColor Cyan
    
    try {
        $cluster = aws eks describe-cluster --name $clusterName --region $Region 2>&1 | ConvertFrom-Json
        
        if ($cluster) {
            $version = $cluster.cluster.version
            $status = $cluster.cluster.status
            $created = $cluster.cluster.createdAt
            $endpoint = $cluster.cluster.endpoint
            
            # Determine version status
            $versionStatus = "OK"
            $versionColor = "Green"
            
            if ($version -eq "1.29") {
                $versionStatus = "⚠️  NEEDS UPGRADE (Support ends March 23, 2026)"
                $versionColor = "Red"
            } elseif ($version -match "1\.(30|31)") {
                $versionStatus = "⚠️  CONSIDER UPGRADE (Use 1.32+ to avoid frequent upgrades)"
                $versionColor = "Yellow"
            } elseif ($version -match "1\.(32|33)") {
                $versionStatus = "✓ Current (Recommended)"
                $versionColor = "Green"
            }
            
            Write-Host "  Version: $version" -ForegroundColor White
            Write-Host "  Status: $status" -ForegroundColor $(if ($status -eq "ACTIVE") { "Green" } else { "Yellow" })
            Write-Host "  Version Status: $versionStatus" -ForegroundColor $versionColor
            Write-Host "  Created: $created" -ForegroundColor Gray
            Write-Host "  Endpoint: $endpoint" -ForegroundColor Gray
            
            # Check addons
            $addons = aws eks list-addons --cluster-name $clusterName --region $Region 2>&1 | ConvertFrom-Json
            if ($addons.addons) {
                Write-Host "  Addons: $($addons.addons -join ', ')" -ForegroundColor Gray
            }
            
            # Check node groups
            $nodegroups = aws eks list-nodegroups --cluster-name $clusterName --region $Region 2>&1 | ConvertFrom-Json
            if ($nodegroups.nodegroups) {
                Write-Host "  Node Groups: $($nodegroups.nodegroups.Count)" -ForegroundColor Gray
                foreach ($ng in $nodegroups.nodegroups) {
                    $ngInfo = aws eks describe-nodegroup --cluster-name $clusterName --nodegroup-name $ng --region $Region 2>&1 | ConvertFrom-Json
                    if ($ngInfo.nodegroup) {
                        $ngVersion = $ngInfo.nodegroup.version
                        $ngStatus = $ngInfo.nodegroup.status
                        Write-Host "    - $ng : $ngVersion ($ngStatus)" -ForegroundColor Gray
                    }
                }
            }
            
        } else {
            Write-Host "  [ERROR] Could not retrieve cluster information" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "  [ERROR] Cluster not found or access denied: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=== Version Check Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  - If version is 1.29, upgrade to 1.32+ before March 23, 2026" -ForegroundColor White
Write-Host "  - Review: infrastructure/terraform/eks-gold-tier/UPGRADE-K8S-1.32.md" -ForegroundColor White
Write-Host "  - Run upgrade: .\scripts\aws-upgrade-eks-k8s.ps1" -ForegroundColor White




