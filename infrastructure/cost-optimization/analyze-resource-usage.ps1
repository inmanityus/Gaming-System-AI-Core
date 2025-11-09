# Analyze ECS Service Resource Usage for Cost Optimization
# Collects 7 days of metrics to identify over-provisioned services

$ErrorActionPreference = "Stop"

Write-Host "📊 Analyzing Resource Usage for Cost Optimization" -ForegroundColor Cyan
Write-Host "=" * 70

$region = "us-east-1"
$cluster = "gaming-system-cluster"
$analysisStart = (Get-Date).AddDays(-7)
$analysisEnd = Get-Date

# Get all services
Write-Host "`nFetching services from cluster: $cluster..."
$services = aws ecs list-services --cluster $cluster --region $region --query "serviceArns[]" --output json | 
    ConvertFrom-Json | 
    ForEach-Object { $_.Split('/')[-1] }

Write-Host "Found $($services.Count) services`n"

# Analysis results
$results = @()

foreach ($service in $services) {
    Write-Host "Analyzing: $service" -ForegroundColor Yellow
    
    try {
        # Get task definition to see current allocation
        $serviceDetails = aws ecs describe-services `
            --cluster $cluster `
            --services $service `
            --region $region `
            --output json | ConvertFrom-Json
        
        $taskDef = $serviceDetails.services[0].taskDefinition
        $runningCount = $serviceDetails.services[0].runningCount
        
        # Get task definition details
        $taskDefDetails = aws ecs describe-task-definition `
            --task-definition $taskDef `
            --region $region `
            --output json | ConvertFrom-Json
        
        $cpu = $taskDefDetails.taskDefinition.cpu
        $memory = $taskDefDetails.taskDefinition.memory
        
        # Get actual usage metrics (7-day average)
        $cpuStats = aws cloudwatch get-metric-statistics `
            --namespace "AWS/ECS" `
            --metric-name "CPUUtilization" `
            --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
            --start-time $analysisStart.ToUniversalTime().ToString("o") `
            --end-time $analysisEnd.ToUniversalTime().ToString("o") `
            --period 3600 `
            --statistics Average `
            --statistics Maximum `
            --region $region `
            --output json | ConvertFrom-Json
        
        $memStats = aws cloudwatch get-metric-statistics `
            --namespace "AWS/ECS" `
            --metric-name "MemoryUtilization" `
            --dimensions Name=ServiceName,Value=$service Name=ClusterName,Value=$cluster `
            --start-time $analysisStart.ToUniversalTime().ToString("o") `
            --end-time $analysisEnd.ToUniversalTime().ToString("o") `
            --period 3600 `
            --statistics Average `
            --statistics Maximum `
            --region $region `
            --output json | ConvertFrom-Json
        
        # Calculate averages
        $avgCPU = if ($cpuStats.Datapoints.Count -gt 0) {
            ($cpuStats.Datapoints | Measure-Object -Property Average -Average).Average
        } else { 0 }
        
        $maxCPU = if ($cpuStats.Datapoints.Count -gt 0) {
            ($cpuStats.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
        } else { 0 }
        
        $avgMemory = if ($memStats.Datapoints.Count -gt 0) {
            ($memStats.Datapoints | Measure-Object -Property Average -Average).Average
        } else { 0 }
        
        $maxMemory = if ($memStats.Datapoints.Count -gt 0) {
            ($memStats.Datapoints | Measure-Object -Property Maximum -Maximum).Maximum
        } else { 0 }
        
        # Determine recommendations
        $cpuRecommendation = "OK"
        $memRecommendation = "OK"
        $actionNeeded = "None"
        
        if ($avgCPU -lt 30 -and $maxCPU -lt 50) {
            $cpuRecommendation = "REDUCE"
            $actionNeeded = "Right-size"
        }
        
        if ($avgMemory -lt 30 -and $maxMemory -lt 50) {
            $memRecommendation = "REDUCE"
            if ($actionNeeded -eq "None") {
                $actionNeeded = "Right-size"
            }
        }
        
        if ($avgCPU -gt 70 -or $maxCPU -gt 85) {
            $cpuRecommendation = "INCREASE"
            $actionNeeded = "Scale Up"
        }
        
        if ($avgMemory -gt 70 -or $maxMemory -gt 85) {
            $memRecommendation = "INCREASE"
            if ($actionNeeded -eq "None" -or $actionNeeded -eq "Right-size") {
                $actionNeeded = "Scale Up"
            }
        }
        
        $results += [PSCustomObject]@{
            Service = $service
            RunningTasks = $runningCount
            AllocatedCPU = $cpu
            AllocatedMemory = $memory
            AvgCPU = [math]::Round($avgCPU, 1)
            MaxCPU = [math]::Round($maxCPU, 1)
            AvgMemory = [math]::Round($avgMemory, 1)
            MaxMemory = [math]::Round($maxMemory, 1)
            CPURecommendation = $cpuRecommendation
            MemoryRecommendation = $memRecommendation
            Action = $actionNeeded
        }
        
        Write-Host "  CPU: $([math]::Round($avgCPU,1))% avg, $([math]::Round($maxCPU,1))% max | Memory: $([math]::Round($avgMemory,1))% avg, $([math]::Round($maxMemory,1))% max | Action: $actionNeeded"
        
    } catch {
        Write-Host "  ⚠️ Error analyzing $service : $_" -ForegroundColor Red
    }
}

# Generate report
Write-Host "`n" + ("=" * 70)
Write-Host "📋 COST OPTIMIZATION ANALYSIS REPORT" -ForegroundColor Green
Write-Host ("=" * 70)

# Summary statistics
$overProvisioned = $results | Where-Object { $_.Action -eq "Right-size" }
$underProvisioned = $results | Where-Object { $_.Action -eq "Scale Up" }
$optimal = $results | Where-Object { $_.Action -eq "None" }

Write-Host "`nSummary:"
Write-Host "  Over-provisioned: $($overProvisioned.Count) services (can reduce resources)"
Write-Host "  Under-provisioned: $($underProvisioned.Count) services (need more resources)"
Write-Host "  Optimal: $($optimal.Count) services (no changes needed)"

if ($overProvisioned.Count -gt 0) {
    Write-Host "`nOver-Provisioned Services (Right-Sizing Opportunities):"
    $overProvisioned | Format-Table Service, AllocatedCPU, AvgCPU, MaxCPU, AllocatedMemory, AvgMemory, MaxMemory -AutoSize
    
    # Estimate savings
    $estimatedSavings = $overProvisioned.Count * 2  # ~$2/service/month if reduced
    Write-Host "Estimated Monthly Savings: ~$$estimatedSavings (conservative)" -ForegroundColor Green
}

if ($underProvisioned.Count -gt 0) {
    Write-Host "`nUnder-Provisioned Services (Need Scale Up):"
    $underProvisioned | Format-Table Service, AllocatedCPU, AvgCPU, MaxCPU, AllocatedMemory, AvgMemory, MaxMemory -AutoSize
    Write-Host "⚠️ These services may experience performance issues" -ForegroundColor Yellow
}

# Export full report to CSV
$reportPath = "E:\Vibe Code\Gaming System\AI Core\infrastructure\cost-optimization\resource-usage-analysis.csv"
$results | Export-Csv -Path $reportPath -NoTypeInformation
Write-Host "`n✅ Full report saved to: $reportPath" -ForegroundColor Green

# Generate recommendations file
$recommendations = @"
# Cost Optimization Recommendations
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Analysis Period: 7 days
Start: $($analysisStart.ToString("yyyy-MM-dd"))
End: $($analysisEnd.ToString("yyyy-MM-dd"))

## Services Analyzed: $($results.Count)

## Over-Provisioned Services: $($overProvisioned.Count)
$(if ($overProvisioned.Count -gt 0) {
    $overProvisioned | ForEach-Object {
        "- $($_.Service): CPU $($_.AvgCPU)% avg (allocated: $($_.AllocatedCPU)), Memory $($_.AvgMemory)% avg (allocated: $($_.AllocatedMemory))"
    } | Out-String
} else {
    "None found"
})

## Under-Provisioned Services: $($underProvisioned.Count)
$(if ($underProvisioned.Count -gt 0) {
    $underProvisioned | ForEach-Object {
        "- $($_.Service): CPU $($_.AvgCPU)% avg, $($_.MaxCPU)% max | Memory $($_.AvgMemory)% avg, $($_.MaxMemory)% max"
    } | Out-String
} else {
    "None found"
})

## Estimated Savings:
- Right-sizing services: ~$$($overProvisioned.Count * 2)/mo
- Additional optimization opportunities to investigate:
  - Database right-sizing
  - VPC endpoints (eliminate data transfer costs)
  - Reserved capacity for baseline
  - Service consolidation for low-traffic services

## Action Items:
1. Review over-provisioned services
2. Test with reduced CPU/memory allocations in dev
3. Monitor for 48 hours after changes
4. Roll out to production if stable
"@

$recPath = "E:\Vibe Code\Gaming System\AI Core\infrastructure\cost-optimization\recommendations.md"
$recommendations | Set-Content -Path $recPath
Write-Host "✅ Recommendations saved to: $recPath" -ForegroundColor Green

Write-Host "`n🎯 Next Steps:"
Write-Host "  1. Review recommendations.md"
Write-Host "  2. Test right-sizing changes in dev environment"
Write-Host "  3. Implement VPC endpoints for S3/ECR/CloudWatch"
Write-Host "  4. Analyze database usage"
Write-Host ""

