# Test Admin API Endpoints
# Comprehensive testing script for all admin APIs

param(
    [string]$BaseUrl = "http://localhost:3001/admin/v1"
)

$ErrorActionPreference = "Continue"

Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Admin API Test Suite" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$TestResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [string]$Token = $null
    )

    $Uri = "$BaseUrl$Endpoint"
    $Headers = @{
        "Content-Type" = "application/json"
    }
    
    if ($Token) {
        $Headers["Authorization"] = "Bearer $Token"
    }

    try {
        $Params = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
        }

        if ($Body) {
            $Params["Body"] = ($Body | ConvertTo-Json)
        }

        $Response = Invoke-RestMethod @Params
        
        Write-Host "✅ $Name" -ForegroundColor Green
        $Script:TestResults += [PSCustomObject]@{
            Test = $Name
            Status = "PASS"
            StatusCode = 200
        }
        
        return $Response
    }
    catch {
        $StatusCode = $_.Exception.Response.StatusCode.value__
        
        if ($StatusCode -eq 401 -or $StatusCode -eq 403) {
            Write-Host "⚠️  $Name (Auth required)" -ForegroundColor Yellow
            $Script:TestResults += [PSCustomObject]@{
                Test = $Name
                Status = "AUTH_REQUIRED"
                StatusCode = $StatusCode
            }
        }
        else {
            Write-Host "❌ $Name - Error: $StatusCode" -ForegroundColor Red
            $Script:TestResults += [PSCustomObject]@{
                Test = $Name
                Status = "FAIL"
                StatusCode = $StatusCode
            }
        }
        
        return $null
    }
}

# Test public endpoints
Write-Host "Testing Public Endpoints..." -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Name "Health Check" -Method "GET" -Endpoint "/health"

# Test authentication (would need real credentials)
Write-Host ""
Write-Host "Testing Auth Endpoints..." -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Name "Login Endpoint" -Method "POST" -Endpoint "/auth/login" -Body @{
    email = "test@example.com"
    password = "testpassword"
}

# Test protected endpoints (expect 401)
Write-Host ""
Write-Host "Testing Protected Endpoints (should require auth)..." -ForegroundColor Yellow
Write-Host ""

Test-Endpoint -Name "Dashboard Data" -Method "GET" -Endpoint "/dashboard"
Test-Endpoint -Name "User List" -Method "GET" -Endpoint "/users"
Test-Endpoint -Name "Trainer List" -Method "GET" -Endpoint "/trainers"
Test-Endpoint -Name "Messaging Inbox" -Method "GET" -Endpoint "/messaging/inbox"
Test-Endpoint -Name "Moderation Queue" -Method "GET" -Endpoint "/moderation/queue"
Test-Endpoint -Name "Email Templates" -Method "GET" -Endpoint "/email-templates"
Test-Endpoint -Name "Services List" -Method "GET" -Endpoint "/services"
Test-Endpoint -Name "Finance Dashboard" -Method "GET" -Endpoint "/finance/dashboard"
Test-Endpoint -Name "Analytics Data" -Method "GET" -Endpoint "/analytics/overview"
Test-Endpoint -Name "AI Sources" -Method "GET" -Endpoint "/ai/sources"
Test-Endpoint -Name "Settings" -Method "GET" -Endpoint "/settings/system"
Test-Endpoint -Name "Audit Logs" -Method "GET" -Endpoint "/audit-logs"

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$Passed = ($TestResults | Where-Object { $_.Status -eq "PASS" }).Count
$AuthRequired = ($TestResults | Where-Object { $_.Status -eq "AUTH_REQUIRED" }).Count
$Failed = ($TestResults | Where-Object { $_.Status -eq "FAIL" }).Count
$Total = $TestResults.Count

Write-Host "Total Tests: $Total" -ForegroundColor Cyan
Write-Host "✅ Passed: $Passed" -ForegroundColor Green
Write-Host "⚠️  Auth Required: $AuthRequired" -ForegroundColor Yellow
Write-Host "❌ Failed: $Failed" -ForegroundColor Red
Write-Host ""

if ($Failed -gt 0) {
    Write-Host "Failed Tests:" -ForegroundColor Red
    $TestResults | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  - $($_.Test) (Status: $($_.StatusCode))" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Note: Auth-required endpoints are expected to return 401/403" -ForegroundColor Gray
Write-Host "Run with valid JWT token for full testing" -ForegroundColor Gray






