# Twilio SMS Setup Script for Be Free Fitness
# This script helps you configure Twilio SMS functionality

Write-Host "📱 Twilio SMS Setup for Be Free Fitness" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "To enable SMS functionality, you need to:" -ForegroundColor Yellow
Write-Host "1. Create a Twilio account at https://www.twilio.com/try-twilio" -ForegroundColor White
Write-Host "2. Get your Account SID and Auth Token from the Twilio Console" -ForegroundColor White
Write-Host "3. Purchase a Twilio phone number" -ForegroundColor White
Write-Host "4. Add the credentials to your .env file" -ForegroundColor White
Write-Host ""

Write-Host "Required Environment Variables:" -ForegroundColor Green
Write-Host "TWILIO_ACCOUNT_SID=your_account_sid_here" -ForegroundColor Gray
Write-Host "TWILIO_AUTH_TOKEN=your_auth_token_here" -ForegroundColor Gray
Write-Host "TWILIO_PHONE_NUMBER=+1234567890" -ForegroundColor Gray
Write-Host ""

Write-Host "Steps to get Twilio credentials:" -ForegroundColor Yellow
Write-Host "1. Sign up at https://www.twilio.com/try-twilio" -ForegroundColor White
Write-Host "2. Verify your phone number" -ForegroundColor White
Write-Host "3. Go to Console Dashboard" -ForegroundColor White
Write-Host "4. Copy Account SID and Auth Token" -ForegroundColor White
Write-Host "5. Buy a phone number (free trial gets one free)" -ForegroundColor White
Write-Host ""

Write-Host "After getting credentials, run:" -ForegroundColor Cyan
Write-Host "Set-EnvironmentVariable -Name 'TWILIO_ACCOUNT_SID' -Value 'your_sid'" -ForegroundColor Gray
Write-Host "Set-EnvironmentVariable -Name 'TWILIO_AUTH_TOKEN' -Value 'your_token'" -ForegroundColor Gray
Write-Host "Set-EnvironmentVariable -Name 'TWILIO_PHONE_NUMBER' -Value '+1234567890'" -ForegroundColor Gray
Write-Host ""

Write-Host "Or add them to your .env file:" -ForegroundColor Cyan
Write-Host "TWILIO_ACCOUNT_SID=your_account_sid_here" -ForegroundColor Gray
Write-Host "TWILIO_AUTH_TOKEN=your_auth_token_here" -ForegroundColor Gray
Write-Host "TWILIO_PHONE_NUMBER=+1234567890" -ForegroundColor Gray
Write-Host ""

Write-Host "💰 Twilio Pricing:" -ForegroundColor Yellow
Write-Host "- Free trial: $15 credit" -ForegroundColor White
Write-Host "- SMS cost: ~$0.0075 per message" -ForegroundColor White
Write-Host "- Phone number: ~$1/month" -ForegroundColor White
Write-Host ""

Write-Host "🔧 Testing SMS:" -ForegroundColor Green
Write-Host "Once configured, SMS will be sent to:" -ForegroundColor White
Write-Host "- Signup verification codes" -ForegroundColor White
Write-Host "- Login verification codes" -ForegroundColor White
Write-Host "- Password reset codes" -ForegroundColor White
Write-Host ""

Write-Host "Press any key to continue..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")







