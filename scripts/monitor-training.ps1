# Monitor Model Training Script
# Purpose: Monitor automatic model training progress across all tiers

param(
    [Parameter(Mandatory=$false)]
    [string]$Tier = "all"  # all, gold, silver, bronze
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== Model Training Monitor ===" -ForegroundColor Green
Write-Host "Tier: $Tier" -ForegroundColor Cyan
Write-Host ""

# Check Gold Tier (EKS)
if ($Tier -eq "all" -or $Tier -eq "gold") {
    Write-Host "=== Gold Tier Training Status ===" -ForegroundColor Green
    try {
        $goldCluster = aws eks describe-cluster --name gaming-ai-gold-tier --region us-east-1 --query 'cluster.status' --output text 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Cluster Status: $goldCluster" -ForegroundColor $(if ($goldCluster -eq "ACTIVE") { "Green" } else { "Yellow" })
            
            # Check node group status
            $nodeGroups = aws eks list-nodegroups --cluster-name gaming-ai-gold-tier --region us-east-1 --query 'nodegroups' --output json 2>&1 | ConvertFrom-Json
            if ($nodeGroups) {
                foreach ($ng in $nodeGroups) {
                    $ngStatus = aws eks describe-nodegroup --cluster-name gaming-ai-gold-tier --nodegroup-name $ng --region us-east-1 --query 'nodegroup.status' --output text 2>&1
                    Write-Host "  Node Group ($ng): $ngStatus" -ForegroundColor $(if ($ngStatus -eq "ACTIVE") { "Green" } else { "Yellow" })
                }
            }
        } else {
            Write-Host "  ⚠ Gold tier cluster not accessible" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Error checking Gold tier: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Check Silver Tier (EKS)
if ($Tier -eq "all" -or $Tier -eq "silver") {
    Write-Host "=== Silver Tier Training Status ===" -ForegroundColor Green
    try {
        $silverCluster = aws eks describe-cluster --name gaming-ai-silver-tier --region us-east-1 --query 'cluster.status' --output text 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Cluster Status: $silverCluster" -ForegroundColor $(if ($silverCluster -eq "ACTIVE") { "Green" } else { "Yellow" })
        } else {
            Write-Host "  ⚠ Silver tier cluster not accessible or not deployed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Error checking Silver tier: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Check Bronze Tier (SageMaker)
if ($Tier -eq "all" -or $Tier -eq "bronze") {
    Write-Host "=== Bronze Tier Training Status ===" -ForegroundColor Green
    try {
        $endpoints = aws sagemaker list-endpoints --region us-east-1 --query 'Endpoints[?contains(EndpointName, `bronze`) || contains(EndpointName, `async`)].{Name:EndpointName,Status:EndpointStatus}' --output json 2>&1 | ConvertFrom-Json
        if ($endpoints) {
            foreach ($ep in $endpoints) {
                Write-Host "  Endpoint ($($ep.Name)): $($ep.Status)" -ForegroundColor $(if ($ep.Status -eq "InService") { "Green" } else { "Yellow" })
            }
        } else {
            Write-Host "  ⚠ No Bronze tier endpoints found" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Error checking Bronze tier: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=== Monitoring Complete ===" -ForegroundColor Green




