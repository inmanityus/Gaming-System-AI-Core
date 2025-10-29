# Test SMS Functionality Script
# Run this after configuring Twilio credentials

Write-Host "📱 Testing SMS Functionality" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

# Check if Twilio credentials are set
$accountSid = $env:TWILIO_ACCOUNT_SID
$authToken = $env:TWILIO_AUTH_TOKEN
$phoneNumber = $env:TWILIO_PHONE_NUMBER

if (-not $accountSid -or -not $authToken -or -not $phoneNumber) {
    Write-Host "❌ Twilio credentials not found!" -ForegroundColor Red
    Write-Host "Please set the following environment variables:" -ForegroundColor Yellow
    Write-Host "TWILIO_ACCOUNT_SID" -ForegroundColor Gray
    Write-Host "TWILIO_AUTH_TOKEN" -ForegroundColor Gray
    Write-Host "TWILIO_PHONE_NUMBER" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Run: scripts/setup-twilio-sms.ps1 for setup instructions" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Twilio credentials found!" -ForegroundColor Green
Write-Host "Account SID: $($accountSid.Substring(0,8))..." -ForegroundColor Gray
Write-Host "Phone Number: $phoneNumber" -ForegroundColor Gray
Write-Host ""

# Test SMS service
Write-Host "🧪 Testing SMS Service..." -ForegroundColor Yellow

try {
    # Test the SMS endpoint
    $testPhone = Read-Host "Enter your phone number to test SMS (e.g., +1234567890)"
    
    if (-not $testPhone) {
        Write-Host "❌ No phone number provided" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Sending test SMS to $testPhone..." -ForegroundColor Yellow
    
    # Call the test SMS endpoint
    $response = Invoke-RestMethod -Uri "http://localhost:4000/api/forms/test-sms" -Method POST -ContentType "application/json" -Body (@{
        phone = $testPhone
        message = "Test SMS from Be Free Fitness! SMS system is working correctly."
    } | ConvertTo-Json)
    
    Write-Host "✅ SMS sent successfully!" -ForegroundColor Green
    Write-Host "Response: $($response.message)" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ SMS test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure the API server is running on port 4000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Check your phone for the test SMS" -ForegroundColor White
Write-Host "2. Test signup/login flows to verify SMS codes" -ForegroundColor White
Write-Host "3. Monitor Twilio console for usage and billing" -ForegroundColor White
Write-Host ""







