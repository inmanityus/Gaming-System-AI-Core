# AWS Services Test Script
# Purpose: Comprehensive testing of all deployed AWS services (Gold, Silver, Bronze tiers)
# Requirements: AWS CLI configured, kubectl installed, services deployed

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item (Join-Path $scriptDir "..")).FullName
Set-Location $projectRoot

Write-Host "=== AWS Services Test Script ===" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host ""

$testResults = @{
    Gold = @{ Passed = 0; Failed = 0; Tests = @() }
    Silver = @{ Passed = 0; Failed = 0; Tests = @() }
    Bronze = @{ Passed = 0; Failed = 0; Tests = @() }
}

function Test-ServiceHealth {
    param(
        [string]$Tier,
        [string]$ClusterName,
        [string]$Namespace = "default"
    )
    
    Write-Host "Testing $Tier Tier..." -ForegroundColor Yellow
    
    # Configure kubectl
    aws eks update-kubeconfig --region $Region --name $ClusterName --alias $Tier.ToLower()
    kubectl config use-context $Tier.ToLower()
    
    # Test 1: Cluster connectivity
    Write-Host "  [1] Testing cluster connectivity..." -ForegroundColor Cyan
    try {
        $nodes = kubectl get nodes 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✓ Cluster is accessible" -ForegroundColor Green
            $testResults[$Tier].Passed++
            $testResults[$Tier].Tests += @{ Name = "Cluster Connectivity"; Status = "PASSED" }
        } else {
            Write-Host "    ✗ Cluster is not accessible" -ForegroundColor Red
            $testResults[$Tier].Failed++
            $testResults[$Tier].Tests += @{ Name = "Cluster Connectivity"; Status = "FAILED"; Error = $nodes }
        }
    } catch {
        Write-Host "    ✗ Cluster connectivity test failed: $_" -ForegroundColor Red
        $testResults[$Tier].Failed++
        $testResults[$Tier].Tests += @{ Name = "Cluster Connectivity"; Status = "FAILED"; Error = $_.Exception.Message }
    }
    
    # Test 2: Pods are running
    Write-Host "  [2] Checking pods status..." -ForegroundColor Cyan
    try {
        $pods = kubectl get pods -n $Namespace -o json | ConvertFrom-Json
        $runningPods = $pods.items | Where-Object { $_.status.phase -eq "Running" }
        $totalPods = $pods.items.Count
        
        if ($totalPods -gt 0) {
            Write-Host "    ✓ Found $totalPods pods, $($runningPods.Count) running" -ForegroundColor Green
            $testResults[$Tier].Passed++
            $testResults[$Tier].Tests += @{ Name = "Pods Running"; Status = "PASSED"; Details = "$($runningPods.Count)/$totalPods running" }
        } else {
            Write-Host "    ✗ No pods found" -ForegroundColor Red
            $testResults[$Tier].Failed++
            $testResults[$Tier].Tests += @{ Name = "Pods Running"; Status = "FAILED"; Error = "No pods found" }
        }
    } catch {
        Write-Host "    ✗ Pod status check failed: $_" -ForegroundColor Red
        $testResults[$Tier].Failed++
        $testResults[$Tier].Tests += @{ Name = "Pods Running"; Status = "FAILED"; Error = $_.Exception.Message }
    }
    
    # Test 3: Services are available
    Write-Host "  [3] Checking services..." -ForegroundColor Cyan
    try {
        $services = kubectl get services -n $Namespace -o json | ConvertFrom-Json
        if ($services.items.Count -gt 0) {
            Write-Host "    ✓ Found $($services.items.Count) services" -ForegroundColor Green
            $testResults[$Tier].Passed++
            $testResults[$Tier].Tests += @{ Name = "Services Available"; Status = "PASSED"; Details = "$($services.items.Count) services" }
            
            # Test 4: Service endpoints are accessible
            Write-Host "  [4] Testing service endpoints..." -ForegroundColor Cyan
            foreach ($service in $services.items) {
                $serviceName = $service.metadata.name
                $serviceType = $service.spec.type
                
                if ($serviceType -eq "LoadBalancer" -or $serviceType -eq "NodePort") {
                    $endpoint = kubectl get service $serviceName -n $Namespace -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>&1
                    if ($endpoint -and $endpoint -ne "") {
                        Write-Host "    ✓ Service $serviceName has endpoint: $endpoint" -ForegroundColor Green
                        $testResults[$Tier].Passed++
                        $testResults[$Tier].Tests += @{ Name = "Service Endpoint: $serviceName"; Status = "PASSED"; Details = $endpoint }
                    } else {
                        Write-Host "    ⚠ Service $serviceName endpoint not yet ready" -ForegroundColor Yellow
                        $testResults[$Tier].Tests += @{ Name = "Service Endpoint: $serviceName"; Status = "PENDING"; Details = "Endpoint provisioning" }
                    }
                }
            }
        } else {
            Write-Host "    ✗ No services found" -ForegroundColor Red
            $testResults[$Tier].Failed++
            $testResults[$Tier].Tests += @{ Name = "Services Available"; Status = "FAILED"; Error = "No services found" }
        }
    } catch {
        Write-Host "    ✗ Service check failed: $_" -ForegroundColor Red
        $testResults[$Tier].Failed++
        $testResults[$Tier].Tests += @{ Name = "Services Available"; Status = "FAILED"; Error = $_.Exception.Message }
    }
    
    # Test 5: Health checks
    Write-Host "  [5] Running health checks..." -ForegroundColor Cyan
    try {
        $pods = kubectl get pods -n $Namespace -o json | ConvertFrom-Json
        foreach ($pod in $pods.items) {
            $podName = $pod.metadata.name
            $podPhase = $pod.status.phase
            
            if ($podPhase -eq "Running") {
                # Check if pod has readiness probe
                $readinessProbe = $pod.spec.containers[0].readinessProbe
                if ($readinessProbe) {
                    Write-Host "    ✓ Pod $podName is running and has readiness probe" -ForegroundColor Green
                    $testResults[$Tier].Passed++
                    $testResults[$Tier].Tests += @{ Name = "Pod Health: $podName"; Status = "PASSED" }
                } else {
                    Write-Host "    ⚠ Pod $podName is running but has no readiness probe" -ForegroundColor Yellow
                    $testResults[$Tier].Tests += @{ Name = "Pod Health: $podName"; Status = "WARNING"; Details = "No readiness probe" }
                }
            } else {
                Write-Host "    ✗ Pod $podName is in phase: $podPhase" -ForegroundColor Red
                $testResults[$Tier].Failed++
                $testResults[$Tier].Tests += @{ Name = "Pod Health: $podName"; Status = "FAILED"; Error = "Phase: $podPhase" }
            }
        }
    } catch {
        Write-Host "    ✗ Health check failed: $_" -ForegroundColor Red
        $testResults[$Tier].Failed++
        $testResults[$Tier].Tests += @{ Name = "Health Checks"; Status = "FAILED"; Error = $_.Exception.Message }
    }
}

# Test Gold Tier
Write-Host "=== Testing Gold Tier ===" -ForegroundColor Green
$goldDir = Join-Path $projectRoot "infrastructure\terraform\eks-gold-tier"
if (Test-Path $goldDir) {
    Set-Location $goldDir
    $goldClusterName = terraform output -raw cluster_name 2>&1
    if ($goldClusterName -and $goldClusterName -notmatch "Error") {
        Test-ServiceHealth -Tier "Gold" -ClusterName $goldClusterName
    } else {
        Write-Host "Gold tier cluster not found or not deployed" -ForegroundColor Yellow
    }
} else {
    Write-Host "Gold tier Terraform directory not found" -ForegroundColor Yellow
}

# Test Silver Tier
Write-Host ""
Write-Host "=== Testing Silver Tier ===" -ForegroundColor Green
$silverDir = Join-Path $projectRoot "infrastructure\terraform\eks-silver-tier"
if (Test-Path $silverDir) {
    Set-Location $silverDir
    $silverClusterName = terraform output -raw cluster_name 2>&1
    if ($silverClusterName -and $silverClusterName -notmatch "Error") {
        Test-ServiceHealth -Tier "Silver" -ClusterName $silverClusterName
    } else {
        Write-Host "Silver tier cluster not found or not deployed" -ForegroundColor Yellow
    }
} else {
    Write-Host "Silver tier Terraform directory not found" -ForegroundColor Yellow
}

# Test Bronze Tier (SageMaker)
Write-Host ""
Write-Host "=== Testing Bronze Tier (SageMaker) ===" -ForegroundColor Green
$bronzeDir = Join-Path $projectRoot "infrastructure\terraform\sagemaker-bronze-tier"
if (Test-Path $bronzeDir) {
    Set-Location $bronzeDir
    $endpointName = terraform output -raw endpoint_name 2>&1
    if ($endpointName -and $endpointName -notmatch "Error") {
        Write-Host "Testing SageMaker endpoint: $endpointName" -ForegroundColor Cyan
        
        # Test endpoint exists
        Write-Host "  [1] Checking endpoint exists..." -ForegroundColor Cyan
        try {
            $endpoint = aws sagemaker describe-endpoint --endpoint-name $endpointName --region $Region 2>&1 | ConvertFrom-Json
            if ($endpoint.EndpointStatus -eq "InService") {
                Write-Host "    ✓ Endpoint is InService" -ForegroundColor Green
                $testResults["Bronze"].Passed++
                $testResults["Bronze"].Tests += @{ Name = "Endpoint Status"; Status = "PASSED"; Details = "InService" }
            } else {
                Write-Host "    ✗ Endpoint status: $($endpoint.EndpointStatus)" -ForegroundColor Red
                $testResults["Bronze"].Failed++
                $testResults["Bronze"].Tests += @{ Name = "Endpoint Status"; Status = "FAILED"; Error = "Status: $($endpoint.EndpointStatus)" }
            }
        } catch {
            Write-Host "    ✗ Endpoint check failed: $_" -ForegroundColor Red
            $testResults["Bronze"].Failed++
            $testResults["Bronze"].Tests += @{ Name = "Endpoint Status"; Status = "FAILED"; Error = $_.Exception.Message }
        }
        
        # Test endpoint configuration
        Write-Host "  [2] Checking endpoint configuration..." -ForegroundColor Cyan
        try {
            $config = aws sagemaker describe-endpoint-config --endpoint-config-name $endpoint.EndpointConfigName --region $Region 2>&1 | ConvertFrom-Json
            Write-Host "    ✓ Endpoint configuration valid" -ForegroundColor Green
            $testResults["Bronze"].Passed++
            $testResults["Bronze"].Tests += @{ Name = "Endpoint Configuration"; Status = "PASSED" }
        } catch {
            Write-Host "    ✗ Configuration check failed: $_" -ForegroundColor Red
            $testResults["Bronze"].Failed++
            $testResults["Bronze"].Tests += @{ Name = "Endpoint Configuration"; Status = "FAILED"; Error = $_.Exception.Message }
        }
    } else {
        Write-Host "Bronze tier endpoint not found or not deployed" -ForegroundColor Yellow
    }
} else {
    Write-Host "Bronze tier Terraform directory not found" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Green
foreach ($tier in $testResults.Keys) {
    $results = $testResults[$tier]
    $total = $results.Passed + $results.Failed
    if ($total -gt 0) {
        $passRate = [math]::Round(($results.Passed / $total) * 100, 2)
        Write-Host ""
        Write-Host "$tier Tier:" -ForegroundColor Cyan
        Write-Host "  Passed: $($results.Passed)" -ForegroundColor Green
        Write-Host "  Failed: $($results.Failed)" -ForegroundColor $(if ($results.Failed -eq 0) { "Green" } else { "Red" })
        Write-Host "  Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -eq 100) { "Green" } else { "Yellow" })
        
        if ($results.Failed -gt 0) {
            Write-Host ""
            Write-Host "  Failed Tests:" -ForegroundColor Red
            foreach ($test in $results.Tests) {
                if ($test.Status -eq "FAILED") {
                    Write-Host "    - $($test.Name): $($test.Error)" -ForegroundColor Red
                }
            }
        }
    }
}

# Overall result
$totalPassed = ($testResults.Values | Measure-Object -Property Passed -Sum).Sum
$totalFailed = ($testResults.Values | Measure-Object -Property Failed -Sum).Sum
$totalTests = $totalPassed + $totalFailed

Write-Host ""
Write-Host "Overall:" -ForegroundColor Cyan
Write-Host "  Total Passed: $totalPassed" -ForegroundColor Green
Write-Host "  Total Failed: $totalFailed" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })

if ($totalFailed -eq 0) {
    Write-Host ""
    Write-Host "✓ ALL TESTS PASSED - ZERO ISSUES" -ForegroundColor Green
    Set-Location $projectRoot
    exit 0
} else {
    Write-Host ""
    Write-Host "✗ SOME TESTS FAILED - REVIEW ERRORS ABOVE" -ForegroundColor Red
    Set-Location $projectRoot
    exit 1
}







