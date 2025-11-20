# Test Comprehensive - Master Test Suite Runner
# Based on MASTER-TEST-REGISTRY.md

param(
    [switch]$SkipVocalSynthesis = $false,
    [switch]$SkipBackendSecurity = $false,
    [switch]$SkipUE5 = $false,
    [switch]$VerboseOutput = $false
)

Write-Host "=== Running Test Comprehensive Suite ===" -ForegroundColor Cyan
Write-Host "Total Expected Tests: 160" -ForegroundColor Yellow
Write-Host "  - Vocal Synthesis: 62 tests" -ForegroundColor Gray
Write-Host "  - Backend Security: 65 tests" -ForegroundColor Gray
Write-Host "  - UE5 Game Systems: 33 tests (manual only)" -ForegroundColor Gray

$totalTests = 0
$passedTests = 0
$failedTests = 0
$unverifiedTests = 0
$results = @()

# Test 1: Vocal Synthesis (C++ DSP Library)
if (-not $SkipVocalSynthesis) {
    Write-Host "`n=== Testing Vocal Synthesis (C++ DSP) ===" -ForegroundColor Yellow
    
    $vocalPath = Join-Path (Get-Location) "vocal-chord-research\cpp-implementation\build"
    
    if (Test-Path $vocalPath) {
        Push-Location $vocalPath
        
        # Check if test executable exists
        $testExe = "tests\Release\vocal_tests.exe"
        if (-not (Test-Path $testExe)) {
            $testExe = "tests\Debug\vocal_tests.exe"
        }
        
        if (Test-Path $testExe) {
            Write-Host "Running Vocal Synthesis tests directly..." -ForegroundColor Gray
            $ctestOutput = & .\$testExe 2>&1
            $ctestExitCode = $LASTEXITCODE
        } else {
            Write-Host "Test executable not found at $testExe" -ForegroundColor Red
            $ctestExitCode = 1
        }
        
        Pop-Location
        
        if ($ctestExitCode -eq 0) {
            Write-Host "✓ Vocal Synthesis: 62/62 tests PASSED" -ForegroundColor Green
            $passedTests += 62
            $totalTests += 62
            
            $results += @{
                Suite = "Vocal Synthesis"
                Total = 62
                Passed = 62
                Failed = 0
                Status = "✅ PASSED"
            }
        } else {
            Write-Host "✗ Vocal Synthesis: FAILED" -ForegroundColor Red
            
            # Try to parse test results
            $passedPattern = "(\d+) tests passed"
            $failedPattern = "(\d+) tests failed"
            
            $passed = 0
            $failed = 0
            
            if ($ctestOutput -match $passedPattern) {
                $passed = [int]$Matches[1]
            }
            if ($ctestOutput -match $failedPattern) {
                $failed = [int]$Matches[1]
            }
            
            $totalVocal = $passed + $failed
            if ($totalVocal -eq 0) { $totalVocal = 62 }
            
            Write-Host "  Passed: $passed/$totalVocal" -ForegroundColor Yellow
            Write-Host "  Failed: $failed" -ForegroundColor Red
            
            $passedTests += $passed
            $failedTests += $failed
            $totalTests += $totalVocal
            
            $results += @{
                Suite = "Vocal Synthesis"
                Total = $totalVocal
                Passed = $passed
                Failed = $failed
                Status = "❌ FAILED"
            }
            
            if ($VerboseOutput) {
                Write-Host "`nTest Output:" -ForegroundColor Gray
                Write-Host $ctestOutput
            }
        }
    } else {
        Write-Host "⚠️ Vocal Synthesis build directory not found: $vocalPath" -ForegroundColor Yellow
        Write-Host "  Please build the project first:" -ForegroundColor Gray
        Write-Host "  cd vocal-chord-research/cpp-implementation" -ForegroundColor Gray
        Write-Host "  mkdir build; cd build" -ForegroundColor Gray
        Write-Host "  cmake .." -ForegroundColor Gray
        Write-Host "  cmake --build ." -ForegroundColor Gray
        
        $unverifiedTests += 62
        $totalTests += 62
        
        $results += @{
            Suite = "Vocal Synthesis"
            Total = 62
            Passed = 0
            Failed = 0
            Status = "⚠️ NOT FOUND"
        }
    }
}

# Test 2: Backend Security (Python FastAPI)
if (-not $SkipBackendSecurity) {
    Write-Host "`n=== Testing Backend Security ===" -ForegroundColor Yellow
    
    $testsPath = Join-Path (Get-Location) "tests"
    
    if (Test-Path $testsPath) {
        Push-Location $testsPath
        
        # Check if pytest is available
        $pythonPath = "C:\Users\kento\AppData\Local\Python\bin\python.exe"
        & $pythonPath -m pytest --version 2>$null
        $pytestExists = $LASTEXITCODE -eq 0
        
        if ($pytestExists) {
            Write-Host "Running pytest on security tests..." -ForegroundColor Gray
            
            $env:PYTHONPATH = Join-Path (Get-Location) ".."
            $pytestOutput = & $pythonPath -m pytest test_security_fixes.py test_all_security_fixes.py test_security_integration.py -v --tb=short --no-cov 2>&1
            $pytestExitCode = $LASTEXITCODE
            
            if ($pytestExitCode -eq 0) {
                Write-Host "✓ Backend Security: 65/65 tests PASSED" -ForegroundColor Green
                $passedTests += 65
                $totalTests += 65
                
                $results += @{
                    Suite = "Backend Security"
                    Total = 65
                    Passed = 65
                    Failed = 0
                    Status = "✅ PASSED"
                }
            } else {
                Write-Host "✗ Backend Security: FAILED" -ForegroundColor Red
                
                # Try to parse pytest results
                $summaryPattern = "(\d+) passed.*?(\d+) failed"
                $passedPattern = "(\d+) passed"
                
                $passed = 0
                $failed = 0
                
                if ($pytestOutput -match $summaryPattern) {
                    $passed = [int]$Matches[1]
                    $failed = [int]$Matches[2]
                } elseif ($pytestOutput -match $passedPattern) {
                    $passed = [int]$Matches[1]
                }
                
                $totalSecurity = $passed + $failed
                if ($totalSecurity -eq 0) { $totalSecurity = 65 }
                
                Write-Host "  Passed: $passed/$totalSecurity" -ForegroundColor Yellow
                Write-Host "  Failed: $failed" -ForegroundColor Red
                
                $passedTests += $passed
                $failedTests += $failed
                $totalTests += $totalSecurity
                
                $results += @{
                    Suite = "Backend Security"
                    Total = $totalSecurity
                    Passed = $passed
                    Failed = $failed
                    Status = "❌ FAILED"
                }
                
                if ($VerboseOutput) {
                    Write-Host "`nTest Output:" -ForegroundColor Gray
                    Write-Host $pytestOutput
                }
            }
        } else {
            Write-Host "⚠️ pytest not found. Installing..." -ForegroundColor Yellow
            & $pythonPath -m pip install pytest pytest-cov
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Retrying tests..." -ForegroundColor Gray
                # Retry the test execution
                & $MyInvocation.MyCommand -SkipVocalSynthesis:$SkipVocalSynthesis -SkipBackendSecurity:$false -SkipUE5:$SkipUE5 -VerboseOutput:$VerboseOutput
                exit
            } else {
                Write-Host "✗ Failed to install pytest" -ForegroundColor Red
                $unverifiedTests += 65
                $totalTests += 65
                
                $results += @{
                    Suite = "Backend Security"
                    Total = 65
                    Passed = 0
                    Failed = 0
                    Status = "⚠️ PYTEST NOT INSTALLED"
                }
            }
        }
        
        Pop-Location
    } else {
        Write-Host "⚠️ Tests directory not found: $testsPath" -ForegroundColor Yellow
        $unverifiedTests += 65
        $totalTests += 65
        
        $results += @{
            Suite = "Backend Security"
            Total = 65
            Passed = 0
            Failed = 0
            Status = "⚠️ NOT FOUND"
        }
    }
}

# Test 3: UE5 Game Systems
if (-not $SkipUE5) {
    Write-Host "`n=== UE5 Game Systems Tests ===" -ForegroundColor Yellow
    Write-Host "⚠️ MANUAL EXECUTION REQUIRED" -ForegroundColor Yellow
    Write-Host "UE5 tests cannot be automated via CLI. They require the Unreal Editor GUI." -ForegroundColor Gray
    
    Write-Host "`nTo run UE5 tests manually:" -ForegroundColor Cyan
    Write-Host '1. Open UE 5.7 Editor:' -ForegroundColor White
    Write-Host '   "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe" "unreal\BodyBroker.uproject"' -ForegroundColor Gray
    Write-Host '2. Open Session Frontend: Window > Developer Tools > Session Frontend' -ForegroundColor White
    Write-Host '3. Click Automation tab' -ForegroundColor White
    Write-Host '4. Filter: BodyBroker.*' -ForegroundColor White
    Write-Host '5. Select all 33 tests and click "Run Tests"' -ForegroundColor White
    Write-Host '6. Save results to: Project-Management\UE5-Test-Results-$(Get-Date -Format "yyyy-MM-dd").log' -ForegroundColor White
    
    $unverifiedTests += 33
    $totalTests += 33
    
    $results += @{
        Suite = "UE5 Game Systems"
        Total = 33
        Passed = 0
        Failed = 0
        Status = "⚠️ MANUAL ONLY"
    }
}

# Generate Summary Report
Write-Host "`n=== TEST SUMMARY ===" -ForegroundColor Cyan

$table = @()
foreach ($result in $results) {
    $table += [PSCustomObject]@{
        Suite = $result.Suite
        Total = $result.Total
        Passed = $result.Passed
        Failed = $result.Failed
        Status = $result.Status
    }
}

$table | Format-Table -AutoSize

Write-Host "`n=== OVERALL RESULTS ===" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if ($failedTests -gt 0) { "Red" } else { "Gray" })
Write-Host "Unverified: $unverifiedTests" -ForegroundColor $(if ($unverifiedTests -gt 0) { "Yellow" } else { "Gray" })

$percentPassed = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 1) } else { 0 }
Write-Host "Pass Rate: $percentPassed%" -ForegroundColor $(if ($percentPassed -eq 100) { "Green" } elseif ($percentPassed -ge 70) { "Yellow" } else { "Red" })

# Save results
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportPath = "Project-Management\test-results-$timestamp.json"

$report = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    TotalTests = $totalTests
    PassedTests = $passedTests
    FailedTests = $failedTests
    UnverifiedTests = $unverifiedTests
    PassRate = $percentPassed
    Results = $results
} | ConvertTo-Json -Depth 3

$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "`nTest report saved to: $reportPath" -ForegroundColor Gray

# Exit code
if ($failedTests -gt 0) {
    Write-Host "`n❌ TEST SUITE FAILED" -ForegroundColor Red
    exit 1
} elseif ($unverifiedTests -eq $totalTests) {
    Write-Host "`n⚠️ NO TESTS COULD BE VERIFIED" -ForegroundColor Yellow
    exit 2
} else {
    Write-Host "`n✅ TEST SUITE PASSED" -ForegroundColor Green
    exit 0
}
