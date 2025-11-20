# Backend Security Tests Runner
# Collects and runs all security-related tests from various locations

Write-Host "=== Running Backend Security Tests ===" -ForegroundColor Cyan

$rootPath = Get-Location
$testsPath = Join-Path $rootPath "tests"

# List of security test files
$securityTestFiles = @(
    "test_security_fixes.py",
    "test_all_security_fixes.py", 
    "test_security_integration.py",
    "test_session_authentication.py",
    "smoke/test_api_smoke.py::TestAPISecurity::test_security_headers"
)

# Check Python and pytest
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } 
              elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
              else { $null }

if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $pythonCmd" -ForegroundColor Gray

# Check/Install pytest
$pytestCheck = & $pythonCmd -m pytest --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pytest..." -ForegroundColor Yellow
    & $pythonCmd -m pip install pytest pytest-cov
}

# Set Python path
$env:PYTHONPATH = $rootPath

# Run tests
$totalPassed = 0
$totalFailed = 0
$results = @()

Push-Location $testsPath

foreach ($testFile in $securityTestFiles) {
    if (Test-Path $testFile) {
        Write-Host "`nRunning: $testFile" -ForegroundColor Yellow
        
        $output = & $pythonCmd -m pytest $testFile -v --tb=short 2>&1
        $exitCode = $LASTEXITCODE
        
        # Parse results
        $summaryLine = $output | Select-String -Pattern "(\d+) passed|(\d+) failed" | Select-Object -Last 1
        
        if ($summaryLine) {
            $passed = 0
            $failed = 0
            
            if ($summaryLine -match "(\d+) passed") {
                $passed = [int]$Matches[1]
            }
            if ($summaryLine -match "(\d+) failed") {
                $failed = [int]$Matches[1]
            }
            
            $totalPassed += $passed
            $totalFailed += $failed
            
            $results += @{
                File = $testFile
                Passed = $passed
                Failed = $failed
                Status = if ($failed -eq 0) { "✅ PASSED" } else { "❌ FAILED" }
            }
            
            Write-Host "  Result: $passed passed, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
        } else {
            Write-Host "  [WARNING] Could not parse test results" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n[SKIP] Not found: $testFile" -ForegroundColor Gray
    }
}

Pop-Location

# Summary
Write-Host "`n=== SECURITY TEST SUMMARY ===" -ForegroundColor Cyan

$table = @()
foreach ($result in $results) {
    $table += [PSCustomObject]@{
        TestFile = $result.File
        Passed = $result.Passed
        Failed = $result.Failed
        Status = $result.Status
    }
}

$table | Format-Table -AutoSize

Write-Host "`nTotal Passed: $totalPassed" -ForegroundColor Green
Write-Host "Total Failed: $totalFailed" -ForegroundColor $(if ($totalFailed -gt 0) { "Red" } else { "Gray" })

$totalTests = $totalPassed + $totalFailed
$passRate = if ($totalTests -gt 0) { [math]::Round(($totalPassed / $totalTests) * 100, 1) } else { 0 }
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -eq 100) { "Green" } else { "Yellow" })

# Save results
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportPath = "Project-Management\security-test-results-$timestamp.json"

$report = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TotalTests = $totalTests
    PassedTests = $totalPassed
    FailedTests = $totalFailed
    PassRate = $passRate
    Results = $results
} | ConvertTo-Json -Depth 3

$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "`nReport saved to: $reportPath" -ForegroundColor Gray

exit $(if ($totalFailed -eq 0) { 0 } else { 1 })
