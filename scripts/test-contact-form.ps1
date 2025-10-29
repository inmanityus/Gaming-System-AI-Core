# Test Contact Form Submission and Email Verification
Write-Host "`n📧 PHASE 2: TESTING CONTACT FORM`n" -ForegroundColor Cyan

$apiUrl = "http://localhost:4000"
$mailhogUrl = "http://localhost:8025"

# Generate unique test data
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$testEmail = "test.contact.$timestamp@example.com"

# Step 1: Clear MailHog
Write-Host "Clearing MailHog..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$mailhogUrl/api/v1/messages" -Method Delete | Out-Null
    Write-Host "  ✓ MailHog cleared" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Could not clear MailHog" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# Step 2: Submit contact form
Write-Host "`nSubmitting contact form..." -ForegroundColor Yellow
$contactData = @{
    firstName = "Jessica"
    lastName = "Martinez"
    email = $testEmail
    phone = "(555) 123-4567"
    subject = "Interested in functional fitness training"
    message = "I would like to learn more about your AI-powered fitness programs and how they can help me improve my movement patterns."
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$apiUrl/api/forms/contact" -Method Post -Body $contactData -ContentType "application/json"
    Write-Host "  ✓ Contact form submitted successfully" -ForegroundColor Green
    Write-Host "    Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Contact form submission failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Wait for emails to be sent
Write-Host "`nWaiting for emails to be processed..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 4: Check MailHog for emails
Write-Host "`nVerifying emails in MailHog..." -ForegroundColor Yellow
try {
    $emails = Invoke-RestMethod -Uri "$mailhogUrl/api/v2/messages"
    $emailCount = $emails.total
    
    Write-Host "  Total emails found: $emailCount" -ForegroundColor Cyan
    
    if ($emailCount -eq 0) {
        Write-Host "  ✗ No emails found!" -ForegroundColor Red
        exit 1
    }
    
    # Check for user confirmation email
    $userEmail = $emails.items | Where-Object {
        $_.To[0].Mailbox -like "*test.contact.*" -and
        $_.To[0].Domain -eq "example.com"
    }
    
    if ($userEmail) {
        Write-Host "  ✓ User confirmation email found" -ForegroundColor Green
        Write-Host "    To: $($userEmail.To[0].Mailbox)@$($userEmail.To[0].Domain)" -ForegroundColor Gray
        Write-Host "    Subject: $($userEmail.Subject)" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  User confirmation email not found" -ForegroundColor Yellow
    }
    
    # Check for sales notification email
    $salesEmail = $emails.items | Where-Object {
        $_.To[0].Mailbox -eq "Sales" -and
        $_.To[0].Domain -eq "BeFreeFitness.ai"
    }
    
    if ($salesEmail) {
        Write-Host "  ✓ Sales notification email found" -ForegroundColor Green
        Write-Host "    To: Sales@BeFreeFitness.ai" -ForegroundColor Gray
        Write-Host "    Subject: $($salesEmail.Subject)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Sales notification email NOT found - CHECK EMAIL SYSTEM!" -ForegroundColor Red
        exit 1
    }
    
    # Step 5: Verify email content
    Write-Host "`nChecking email content..." -ForegroundColor Yellow
    
    if ($salesEmail) {
        # Get the HTML content
        $htmlContent = $salesEmail.Content.Body
        
        if ($htmlContent -like "*Jessica*" -and $htmlContent -like "*Martinez*") {
            Write-Host "  ✓ Sales email contains customer name" -ForegroundColor Green
        }
        
        if ($htmlContent -like "*$testEmail*") {
            Write-Host "  ✓ Sales email contains customer email" -ForegroundColor Green
        }
        
        if ($htmlContent -like "*(555) 123-4567*") {
            Write-Host "  ✓ Sales email contains customer phone" -ForegroundColor Green
        }
        
        if ($htmlContent -like "*Interested in functional fitness training*") {
            Write-Host "  ✓ Sales email contains subject" -ForegroundColor Green
        }
        
        if ($htmlContent -like "*AI-powered fitness programs*") {
            Write-Host "  ✓ Sales email contains message content" -ForegroundColor Green
        }
    }
    
    Write-Host "`n✅ PHASE 2 COMPLETE - Contact form working, emails sent to Sales@BeFreeFitness.ai`n" -ForegroundColor Green
    exit 0
    
} catch {
    Write-Host "  ✗ Error checking MailHog: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

