# Email System Setup Script for Be Free Fitness (PowerShell)
# This script sets up and tests the email system

Write-Host "Setting up Be Free Fitness Email System..." -ForegroundColor Green

# Function to test SMTP connection
function Test-SMTPConnection {
    param(
        [string]$SMTPHost,
        [int]$Port,
        [string]$Name
    )
    
    Write-Host "Testing $Name connection ($SMTPHost`:$Port)..." -ForegroundColor Yellow
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($SMTPHost, $Port)
        $tcpClient.Close()
        Write-Host "SUCCESS: $Name is accessible" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "ERROR: $Name is not accessible" -ForegroundColor Red
        return $false
    }
}

# Function to send test email via API
function Send-TestEmail {
    param(
        [string]$TemplateName = "video_submission_thank_you",
        [string]$RecipientEmail = "test@befreefitness.local"
    )
    
    Write-Host "Testing email template: $TemplateName" -ForegroundColor Cyan
    Write-Host "Sending to: $RecipientEmail" -ForegroundColor Cyan
    
    $testData = @{
        first_name = "John"
        last_name = "Doe"
        email = $RecipientEmail
        intake_form_url = "http://localhost:3000/intake"
        access_token = "test-token-12345"
    } | ConvertTo-Json
    
    $body = @{
        to = $RecipientEmail
        templateName = $TemplateName
        data = $testData
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4000/api/email/test" -Method POST -Body $body -ContentType "application/json"
        Write-Host "SUCCESS: Test email sent successfully!" -ForegroundColor Green
        Write-Host "Check MailHog at: http://localhost:8025" -ForegroundColor Blue
    }
    catch {
        Write-Host "ERROR: Failed to send test email: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test MailHog (Development)
Write-Host ""
Write-Host "Testing MailHog (Development SMTP)..." -ForegroundColor Yellow
if (Test-SMTPConnection -SMTPHost "localhost" -Port 1025 -Name "MailHog SMTP") {
    Write-Host "MailHog is running and accessible" -ForegroundColor Green
    Write-Host "You can view emails at: http://localhost:8025" -ForegroundColor Blue
} else {
    Write-Host "MailHog is not running. Start it with: docker-compose up mailhog" -ForegroundColor Red
}

# Test Postfix (Alternative Development)
Write-Host ""
Write-Host "Testing Postfix (Alternative Development SMTP)..." -ForegroundColor Yellow
if (Test-SMTPConnection -SMTPHost "localhost" -Port 25 -Name "Postfix SMTP") {
    Write-Host "Postfix is running and accessible" -ForegroundColor Green
} else {
    Write-Host "Postfix is not running. Start it with: docker-compose up postfix" -ForegroundColor Red
}

# Test API Email Service
Write-Host ""
Write-Host "Testing API Email Service..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4000/api/email/test" -Method GET
    Write-Host "SUCCESS: Email API endpoint is accessible" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Email API endpoint is not accessible" -ForegroundColor Red
}

# Create email testing script
Write-Host ""
Write-Host "Creating email testing script..." -ForegroundColor Yellow

$testScript = @'
# Email Testing Script for Be Free Fitness (PowerShell)
# Usage: .\test-email.ps1 [template_name] [recipient_email]

param(
    [string]$TemplateName = "video_submission_thank_you",
    [string]$RecipientEmail = "test@befreefitness.local"
)

Write-Host "Testing email template: $TemplateName" -ForegroundColor Cyan
Write-Host "Sending to: $RecipientEmail" -ForegroundColor Cyan

$testData = @{
    first_name = "John"
    last_name = "Doe"
    email = $RecipientEmail
    intake_form_url = "http://localhost:3000/intake"
    access_token = "test-token-12345"
} | ConvertTo-Json

$body = @{
    to = $RecipientEmail
    templateName = $TemplateName
    data = $testData
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:4000/api/email/test" -Method POST -Body $body -ContentType "application/json"
    Write-Host "SUCCESS: Test email sent successfully!" -ForegroundColor Green
    Write-Host "Check MailHog at: http://localhost:8025" -ForegroundColor Blue
} catch {
    Write-Host "ERROR: Failed to send test email: $($_.Exception.Message)" -ForegroundColor Red
}
'@

$testScript | Out-File -FilePath "test-email.ps1" -Encoding UTF8

Write-Host ""
Write-Host "Email system setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Available SMTP servers:" -ForegroundColor Cyan
Write-Host "  - MailHog (Development): localhost:1025" -ForegroundColor White
Write-Host "  - Postfix (Alternative): localhost:25" -ForegroundColor White
Write-Host ""
Write-Host "Configuration files:" -ForegroundColor Cyan
Write-Host "  - Email config: Docker-Template/email-config.env" -ForegroundColor White
Write-Host "  - Postfix config: Docker-Template/postfix/config/" -ForegroundColor White
Write-Host ""
Write-Host "Testing:" -ForegroundColor Cyan
Write-Host "  - Run: .\test-email.ps1 [template] [email]" -ForegroundColor White
Write-Host "  - View emails: http://localhost:8025 (MailHog)" -ForegroundColor White
Write-Host "  - API test: http://localhost:4000/api/email/test" -ForegroundColor White
Write-Host ""
Write-Host "Available email templates:" -ForegroundColor Cyan
Write-Host "  - video_submission_thank_you" -ForegroundColor White
Write-Host "  - video_submission_alert" -ForegroundColor White
Write-Host "  - intake_form_thank_you" -ForegroundColor White
Write-Host "  - intake_form_alert" -ForegroundColor White
Write-Host "  - contact_form_alert" -ForegroundColor White
Write-Host "  - ai_analysis_complete" -ForegroundColor White