#!/usr/bin/env pwsh
# Run all project tests

param(
    [switch]$Quick,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Gaming System AI Core - Test Suite ===${NC}"
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Test categories
$testCategories = @(
    @{Name = "Unit Tests"; Pattern = "tests/test_*.py"; ExcludePattern = "integration|e2e"},
    @{Name = "Integration Tests"; Pattern = "tests/integration/*.py"},
    @{Name = "NATS Tests"; Pattern = "tests/nats/*.py"},
    @{Name = "Security Tests"; Pattern = "tests/test_security*.py"},
    @{Name = "Performance Tests"; Pattern = "tests/performance/*.py"},
    @{Name = "E2E Tests"; Pattern = "tests/e2e*.py"}
)

$results = @{}
$totalPassed = 0
$totalFailed = 0

foreach ($category in $testCategories) {
    Write-Host "${YELLOW}Running $($category.Name)...${NC}"
    
    # Find test files
    $testFiles = Get-ChildItem -Path . -Filter $category.Pattern -Recurse | 
                 Where-Object { $_.Name -match "test_.*\.py$" }
    
    if ($category.ExcludePattern) {
        $testFiles = $testFiles | Where-Object { $_.FullName -notmatch $category.ExcludePattern }
    }
    
    if ($testFiles.Count -eq 0) {
        Write-Host "  No tests found"
        continue
    }
    
    Write-Host "  Found $($testFiles.Count) test file(s)"
    
    # Run pytest
    $args = @(
        "-m", "pytest",
        "--tb=short",
        "--maxfail=10",
        "-q"
    )
    
    if ($Verbose) {
        $args += "-v"
    }
    
    $args += $testFiles.FullName
    
    $result = python $args 2>&1
    $exitCode = $LASTEXITCODE
    
    # Parse results
    if ($exitCode -eq 0) {
        Write-Host "${GREEN}  [PASS] All tests passed${NC}"
        $results[$category.Name] = "PASS"
        $totalPassed++
    }
    elseif ($exitCode -eq 1) {
        Write-Host "${RED}  [FAIL] Some tests failed${NC}"
        $results[$category.Name] = "FAIL"
        $totalFailed++
    }
    else {
        Write-Host "${RED}  [ERROR] Test execution error (code: $exitCode)${NC}"
        $results[$category.Name] = "ERROR"
        $totalFailed++
    }
    
    Write-Host ""
}

Write-Host "${GREEN}=== Test Summary ===${NC}"
foreach ($item in $results.GetEnumerator()) {
    $color = if ($item.Value -eq "PASS") { $GREEN } else { $RED }
    $symbol = if ($item.Value -eq "PASS") { "[OK]" } else { "[FAIL]" }
    Write-Host "$color  $symbol $($item.Key): $($item.Value)${NC}"
}

Write-Host ""
Write-Host "Total Categories: $($results.Count)"
Write-Host "Passed: $totalPassed"
Write-Host "Failed: $totalFailed"

$passRate = if ($results.Count -gt 0) { 
    [math]::Round(($totalPassed / $results.Count) * 100, 1) 
} else { 
    0 
}

Write-Host ""
if ($passRate -ge 70) {
    Write-Host "${GREEN}Overall: ACCEPTABLE ($passRate% pass rate)${NC}"
    exit 0
}
else {
    Write-Host "${RED}Overall: NEEDS WORK ($passRate% pass rate)${NC}"
    exit 1
}
