# Test Security Deployment
# Validates all security fixes are working in deployed services

$ErrorActionPreference = "Stop"

Write-Host "=== TESTING SECURITY DEPLOYMENT ===" -ForegroundColor Cyan

# Test 1: Authentication service
Write-Host "`n[TEST 1] Authentication Service" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8100/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Host "✅ Auth service healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Auth service not responding: $_" -ForegroundColor Red
}

# Test 2: Protected endpoint without auth (should fail)
Write-Host "`n[TEST 2] Protected Endpoint Without Auth" -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:8100/auth/sessions" -Method Get -ErrorAction Stop
    Write-Host "❌ Should have returned 401" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 401) {
        Write-Host "✅ Correctly returned 401 Unauthorized" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Unexpected error: $_" -ForegroundColor Yellow
    }
}

# Test 3: Login creates session
Write-Host "`n[TEST 3] Login Creates Session" -ForegroundColor Yellow
try {
    $userId = [guid]::NewGuid().ToString()
    $body = @{ user_id = $userId; metadata = @{} } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8100/auth/login" -Method Post -Body $body -ContentType "application/json"
    
    if ($response.session_id) {
        Write-Host "✅ Session created: $($response.session_id.Substring(0,16))..." -ForegroundColor Green
        
        # Test 4: Use session to access protected endpoint
        Write-Host "`n[TEST 4] Session Authentication" -ForegroundColor Yellow
        $headers = @{ Authorization = "Bearer $($response.session_id)" }
        $sessionInfo = Invoke-RestMethod -Uri "http://localhost:8100/auth/session" -Method Get -Headers $headers
        
        if ($sessionInfo.user_id -eq $userId) {
            Write-Host "✅ Session authentication working" -ForegroundColor Green
        } else {
            Write-Host "❌ User ID mismatch" -ForegroundColor Red
        }
        
        # Test 5: Logout
        Write-Host "`n[TEST 5] Logout" -ForegroundColor Yellow
        $logoutResponse = Invoke-RestMethod -Uri "http://localhost:8100/auth/logout" -Method Post -Headers $headers
        
        if ($logoutResponse.success) {
            Write-Host "✅ Logout successful" -ForegroundColor Green
            
            # Test 6: Session invalid after logout
            Write-Host "`n[TEST 6] Session Invalid After Logout" -ForegroundColor Yellow
            try {
                Invoke-RestMethod -Uri "http://localhost:8100/auth/session" -Method Get -Headers $headers -ErrorAction Stop
                Write-Host "❌ Session should be invalid after logout" -ForegroundColor Red
            } catch {
                if ($_.Exception.Response.StatusCode.value__ -eq 401) {
                    Write-Host "✅ Session correctly invalidated" -ForegroundColor Green
                }
            }
        }
    }
} catch {
    Write-Host "❌ Login test failed: $_" -ForegroundColor Red
}

Write-Host "`n=== SECURITY TESTS COMPLETE ===" -ForegroundColor Cyan

