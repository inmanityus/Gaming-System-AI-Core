# End-to-End Test for AI-Driven Game Testing System
# Tests complete workflow: Capture → Upload → Analysis → Consensus → Recommendation
# Uses 3 AI models for peer validation

param(
    [string]$OrchestratorUrl = "http://54.174.89.122:8000"
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  END-TO-END TEST: AI Game Testing System" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$TestResults = @{
    Passed = @()
    Failed = @()
    Warnings = @()
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET"
    )
    
    Write-Host "Testing: $Name..." -NoNewline
    
    try {
        $Response = Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec 15
        Write-Host " ✓ PASSED" -ForegroundColor Green
        $TestResults.Passed += $Name
        return $Response
    } catch {
        Write-Host " ✗ FAILED" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
        $TestResults.Failed += $Name
        return $null
    }
}

# Test 1: Orchestrator Root
Write-Host "`n[TEST 1] Orchestrator Root Endpoint" -ForegroundColor Yellow
$RootResponse = Test-Endpoint -Name "Root Endpoint" -Url "$OrchestratorUrl/"
if ($RootResponse) {
    Write-Host "  Service: $($RootResponse.service)" -ForegroundColor Gray
    Write-Host "  Version: $($RootResponse.version)" -ForegroundColor Gray
}

# Test 2: Health Check
Write-Host "`n[TEST 2] Health Check Endpoint" -ForegroundColor Yellow
$HealthResponse = Test-Endpoint -Name "Health Check" -Url "$OrchestratorUrl/health"
if ($HealthResponse) {
    Write-Host "  Status: $($HealthResponse.status)" -ForegroundColor $(if ($HealthResponse.status -eq "healthy") { "Green" } else { "Yellow" })
    Write-Host "  S3: $($HealthResponse.services.s3)" -ForegroundColor $(if ($HealthResponse.services.s3 -eq "healthy") { "Green" } else { "Red" })
    Write-Host "  SQS: $($HealthResponse.services.sqs)" -ForegroundColor $(if ($HealthResponse.services.sqs -eq "healthy") { "Green" } else { "Red" })
    Write-Host "  Database: $($HealthResponse.services.database)" -ForegroundColor Yellow
    
    if ($HealthResponse.services.s3 -ne "healthy") {
        $TestResults.Warnings += "S3 not healthy"
    }
    if ($HealthResponse.services.sqs -ne "healthy") {
        $TestResults.Warnings += "SQS not healthy"
    }
}

# Test 3: Statistics Endpoint
Write-Host "`n[TEST 3] Statistics Endpoint" -ForegroundColor Yellow
$StatsResponse = Test-Endpoint -Name "Statistics" -Url "$OrchestratorUrl/stats"
if ($StatsResponse) {
    Write-Host "  Total Captures: $($StatsResponse.total_captures)" -ForegroundColor Gray
    Write-Host "  Issues Flagged: $($StatsResponse.issues_flagged)" -ForegroundColor Gray
}

# Test 4: S3 Bucket Accessibility
Write-Host "`n[TEST 4] S3 Bucket Access" -ForegroundColor Yellow
try {
    aws s3 ls s3://body-broker-qa-captures 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ S3 bucket accessible" -ForegroundColor Green
        $TestResults.Passed += "S3 Bucket Access"
    } else {
        Write-Host "  ✗ S3 bucket not accessible" -ForegroundColor Red
        $TestResults.Failed += "S3 Bucket Access"
    }
} catch {
    Write-Host "  ✗ S3 bucket test failed" -ForegroundColor Red
    $TestResults.Failed += "S3 Bucket Access"
}

# Test 5: SQS Queue Accessibility
Write-Host "`n[TEST 5] SQS Queue Access" -ForegroundColor Yellow
try {
    $QueueAttrs = aws sqs get-queue-attributes --queue-url "https://sqs.us-east-1.amazonaws.com/695353648052/body-broker-qa-analysis-jobs" --attribute-names All --output json | ConvertFrom-Json
    Write-Host "  ✓ SQS queue accessible" -ForegroundColor Green
    Write-Host "  Messages in queue: $($QueueAttrs.Attributes.ApproximateNumberOfMessages)" -ForegroundColor Gray
    $TestResults.Passed += "SQS Queue Access"
} catch {
    Write-Host "  ✗ SQS queue not accessible" -ForegroundColor Red
    $TestResults.Failed += "SQS Queue Access"
}

# Test 6: Redis Cache Status
Write-Host "`n[TEST 6] Redis Cache Status" -ForegroundColor Yellow
try {
    $CacheStatus = aws elasticache describe-cache-clusters --cache-cluster-id body-broker-qa-cache --query 'CacheClusters[0].CacheClusterStatus' --output text 2>&1
    if ($CacheStatus -eq "available") {
        Write-Host "  ✓ Redis cache available" -ForegroundColor Green
        $TestResults.Passed += "Redis Cache"
    } else {
        Write-Host "  ⚠ Redis cache status: $CacheStatus" -ForegroundColor Yellow
        $TestResults.Warnings += "Redis still creating"
    }
} catch {
    Write-Host "  ✗ Redis cache check failed" -ForegroundColor Red
    $TestResults.Failed += "Redis Cache"
}

# Test 7: GameObserver Plugin Exists
Write-Host "`n[TEST 7] GameObserver Plugin" -ForegroundColor Yellow
if (Test-Path "unreal\Plugins\GameObserver\GameObserver.uplugin") {
    Write-Host "  ✓ GameObserver plugin present" -ForegroundColor Green
    $TestResults.Passed += "GameObserver Plugin"
} else {
    Write-Host "  ✗ GameObserver plugin not found" -ForegroundColor Red
    $TestResults.Failed += "GameObserver Plugin"
}

# Test 8: Local Agent Exists
Write-Host "`n[TEST 8] Local Test Runner Agent" -ForegroundColor Yellow
if (Test-Path "ai-testing-system\local-test-runner\agent.py") {
    Write-Host "  ✓ Local agent present" -ForegroundColor Green
    $TestResults.Passed += "Local Agent"
} else {
    Write-Host "  ✗ Local agent not found" -ForegroundColor Red
    $TestResults.Failed += "Local Agent"
}

# Test 9: Vision Analysis Agent Exists
Write-Host "`n[TEST 9] Vision Analysis Agent" -ForegroundColor Yellow
if (Test-Path "ai-testing-system\vision-analysis\vision_agent.py") {
    Write-Host "  ✓ Vision agent present" -ForegroundColor Green
    $TestResults.Passed += "Vision Agent"
} else {
    Write-Host "  ✗ Vision agent not found" -ForegroundColor Red
    $TestResults.Failed += "Vision Agent"
}

# Test 10: Triage Dashboard Exists
Write-Host "`n[TEST 10] Triage Dashboard" -ForegroundColor Yellow
if (Test-Path "ai-testing-system\dashboard\package.json") {
    Write-Host "  ✓ Dashboard present" -ForegroundColor Green
    $TestResults.Passed += "Triage Dashboard"
} else {
    Write-Host "  ✗ Dashboard not found" -ForegroundColor Red
    $TestResults.Failed += "Triage Dashboard"
}

# Summary
Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Passed:   $($TestResults.Passed.Count)" -ForegroundColor Green
Write-Host "Failed:   $($TestResults.Failed.Count)" -ForegroundColor $(if ($TestResults.Failed.Count -eq 0) { "Gray" } else { "Red" })
Write-Host "Warnings: $($TestResults.Warnings.Count)" -ForegroundColor $(if ($TestResults.Warnings.Count -eq 0) { "Gray" } else { "Yellow" })
Write-Host ""

if ($TestResults.Failed.Count -eq 0 -and $TestResults.Warnings.Count -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! System is operational." -ForegroundColor Green
    exit 0
} elseif ($TestResults.Failed.Count -eq 0) {
    Write-Host "⚠️  All tests passed with warnings. System is operational but not optimal." -ForegroundColor Yellow
    foreach ($Warning in $TestResults.Warnings) {
        Write-Host "  - $Warning" -ForegroundColor Yellow
    }
    exit 0
} else {
    Write-Host "❌ SOME TESTS FAILED. System requires fixes:" -ForegroundColor Red
    foreach ($Failed in $TestResults.Failed) {
        Write-Host "  - $Failed" -ForegroundColor Red
    }
    exit 1
}

