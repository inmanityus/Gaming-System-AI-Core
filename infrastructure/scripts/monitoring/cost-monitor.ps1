# Multi-Tier Cost Monitoring Script
# Monitors costs for Gold, Silver, and Bronze tiers

param(
    [string]$Region = "us-east-1",
    [int]$Days = 7
)

Write-Host "=== Multi-Tier Cost Monitoring ===" -ForegroundColor Cyan
Write-Host "Period: Last $Days days" -ForegroundColor White
Write-Host ""

$totalCost = 0
$errors = @()

# Gold Tier Cost (EKS + EC2 instances)
Write-Host "[Gold Tier] Calculating EKS and EC2 costs..." -ForegroundColor Yellow
try {
    $startDate = (Get-Date).AddDays(-$Days).ToString("yyyy-MM-dd")
    $endDate = (Get-Date).ToString("yyyy-MM-dd")
    
    # Get EKS cluster costs
    $eksCosts = aws ce get-cost-and-usage `
        --time-period Start=$startDate,End=$endDate `
        --granularity DAILY `
        --metrics "UnblendedCost" `
        --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Kubernetes Service"]}}') `
        --region $Region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $eksData = $eksCosts | ConvertFrom-Json
        $eksTotal = ($eksData.ResultsByTime | ForEach-Object { [double]$_.Total.UnblendedCost.Amount } | Measure-Object -Sum).Sum
        Write-Host "  EKS Cluster: `$$([Math]::Round($eksTotal, 2))" -ForegroundColor White
        $totalCost += $eksTotal
    }
    
    # Get EC2 instance costs (g6.xlarge, g5.xlarge for Gold tier)
    $ec2Costs = aws ce get-cost-and-usage `
        --time-period Start=$startDate,End=$endDate `
        --granularity DAILY `
        --metrics "UnblendedCost" `
        --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]},"Tags":{"Key":"Tier","Values":["Gold"]}}') `
        --region $Region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $ec2Data = $ec2Costs | ConvertFrom-Json
        $ec2Total = ($ec2Data.ResultsByTime | ForEach-Object { [double]$_.Total.UnblendedCost.Amount } | Measure-Object -Sum).Sum
        Write-Host "  EC2 Instances (Gold): `$$([Math]::Round($ec2Total, 2))" -ForegroundColor White
        $totalCost += $ec2Total
    }
} catch {
    $errors += "Gold tier cost calculation failed: $($_.Exception.Message)"
}

Write-Host ""

# Silver Tier Cost (EKS + EC2 instances)
Write-Host "[Silver Tier] Calculating EKS and EC2 costs..." -ForegroundColor Yellow
try {
    # Get EC2 instance costs (g6.12xlarge, g5.12xlarge for Silver tier)
    $ec2Costs = aws ce get-cost-and-usage `
        --time-period Start=$startDate,End=$endDate `
        --granularity DAILY `
        --metrics "UnblendedCost" `
        --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]},"Tags":{"Key":"Tier","Values":["Silver"]}}') `
        --region $Region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $ec2Data = $ec2Costs | ConvertFrom-Json
        $ec2Total = ($ec2Data.ResultsByTime | ForEach-Object { [double]$_.Total.UnblendedCost.Amount } | Measure-Object -Sum).Sum
        Write-Host "  EC2 Instances (Silver): `$$([Math]::Round($ec2Total, 2))" -ForegroundColor White
        $totalCost += $ec2Total
    }
} catch {
    $errors += "Silver tier cost calculation failed: $($_.Exception.Message)"
}

Write-Host ""

# Bronze Tier Cost (SageMaker)
Write-Host "[Bronze Tier] Calculating SageMaker costs..." -ForegroundColor Yellow
try {
    $sagemakerCosts = aws ce get-cost-and-usage `
        --time-period Start=$startDate,End=$endDate `
        --granularity DAILY `
        --metrics "UnblendedCost" `
        --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["Amazon SageMaker"]}}') `
        --region $Region 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $smData = $sagemakerCosts | ConvertFrom-Json
        $smTotal = ($smData.ResultsByTime | ForEach-Object { [double]$_.Total.UnblendedCost.Amount } | Measure-Object -Sum).Sum
        Write-Host "  SageMaker: `$$([Math]::Round($smTotal, 2))" -ForegroundColor White
        $totalCost += $smTotal
    }
} catch {
    $errors += "Bronze tier cost calculation failed: $($_.Exception.Message)"
}

# Summary
Write-Host ""
Write-Host "=== Cost Summary ===" -ForegroundColor Cyan
Write-Host "Total Cost (Last $Days days): `$$([Math]::Round($totalCost, 2))" -ForegroundColor White
Write-Host "Daily Average: `$$([Math]::Round($totalCost / $Days, 2))" -ForegroundColor White
Write-Host "Monthly Projection: `$$([Math]::Round(($totalCost / $Days) * 30, 2))" -ForegroundColor White

if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Host "Errors:" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "Note: Cost data may have 24-48 hour delay" -ForegroundColor Gray





