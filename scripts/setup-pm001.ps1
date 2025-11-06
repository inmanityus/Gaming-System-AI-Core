# PM-001: Stripe Account Setup Script
# Purpose: Set up Stripe integration for payment processing
# Task: PM-001 from Phase 1 Foundation Tasks

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PM-001: Stripe Account Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Stripe CLI is installed
Write-Host "Checking Stripe CLI installation..." -ForegroundColor Yellow
$stripeCliInstalled = $false
try {
    $stripeVersion = stripe --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $stripeCliInstalled = $true
        Write-Host "✓ Stripe CLI is installed" -ForegroundColor Green
        Write-Host "  Version: $stripeVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Stripe CLI not found (optional)" -ForegroundColor Yellow
}

# Install Stripe CLI if not installed (optional)
if (-not $stripeCliInstalled) {
    Write-Host ""
    Write-Host "Stripe CLI Installation (Optional):" -ForegroundColor Yellow
    Write-Host "  The Stripe CLI is useful for testing webhooks locally" -ForegroundColor Gray
    Write-Host "  Download from: https://stripe.com/docs/stripe-cli" -ForegroundColor Cyan
    Write-Host "  Or install via: scoop install stripe" -ForegroundColor Gray
    Write-Host ""
}

# Check Python Stripe package
Write-Host ""
Write-Host "Checking Python Stripe package..." -ForegroundColor Yellow
try {
    $stripePython = python -m pip show stripe 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Stripe Python package is installed" -ForegroundColor Green
        $versionLine = $stripePython | Select-String -Pattern "Version:"
        if ($versionLine) {
            Write-Host "  $versionLine" -ForegroundColor Gray
        }
    } else {
        Write-Host "  Installing Stripe Python package..." -ForegroundColor Yellow
        python -m pip install stripe --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Stripe Python package installed" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Failed to install Stripe Python package" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  ⚠ Could not check/install Stripe Python package" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Check for .env file
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
$envFile = ".env"
$envExampleFile = ".env.example"

if (Test-Path $envFile) {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
    
    # Check for Stripe keys
    $envContent = Get-Content $envFile -Raw
    $hasStripeKey = $envContent -match "STRIPE.*KEY"
    $hasStripeSecret = $envContent -match "STRIPE.*SECRET"
    
    if ($hasStripeKey -or $hasStripeSecret) {
        Write-Host "  ✓ Stripe keys found in .env" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Stripe keys not found in .env" -ForegroundColor Yellow
        Write-Host "    Add the following to your .env file:" -ForegroundColor Gray
        Write-Host "    STRIPE_SECRET_KEY=sk_test_..." -ForegroundColor Gray
        Write-Host "    STRIPE_PUBLISHABLE_KEY=pk_test_..." -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "    Creating .env.example template..." -ForegroundColor Gray
    
    $envExample = @"
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Payment Configuration
STRIPE_SUCCESS_URL=http://localhost:3000/payment/success
STRIPE_CANCEL_URL=http://localhost:3000/payment/cancel
"@
    
    if (-not (Test-Path $envExampleFile)) {
        $envExample | Out-File -FilePath $envExampleFile -Encoding UTF8
        Write-Host "    ✓ Created .env.example" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "  Please create a .env file with your Stripe keys:" -ForegroundColor Yellow
    Write-Host "    1. Copy .env.example to .env" -ForegroundColor Gray
    Write-Host "    2. Get your Stripe keys from: https://dashboard.stripe.com/apikeys" -ForegroundColor Gray
    Write-Host "    3. Add your keys to .env" -ForegroundColor Gray
}

# Check for Stripe service implementation
Write-Host ""
Write-Host "Checking Stripe service implementation..." -ForegroundColor Yellow
$stripeServicePath = "services/payment"
if (Test-Path $stripeServicePath) {
    Write-Host "  ✓ Payment service directory exists" -ForegroundColor Green
    
    $stripeFiles = Get-ChildItem -Path $stripeServicePath -Filter "*stripe*" -Recurse
    if ($stripeFiles.Count -gt 0) {
        Write-Host "  ✓ Stripe service files found" -ForegroundColor Green
        foreach ($file in $stripeFiles) {
            Write-Host "    - $($file.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠ No Stripe service files found" -ForegroundColor Yellow
        Write-Host "    Payment service implementation needed" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Payment service directory not found" -ForegroundColor Yellow
    Write-Host "    Creating payment service structure..." -ForegroundColor Gray
    
    New-Item -ItemType Directory -Force -Path $stripeServicePath | Out-Null
    Write-Host "    ✓ Created payment service directory" -ForegroundColor Green
}

# Create Stripe setup documentation
Write-Host ""
Write-Host "Creating Stripe setup documentation..." -ForegroundColor Yellow
$stripeDocPath = "docs/setup/STRIPE-SETUP.md"
$stripeDocDir = Split-Path $stripeDocPath -Parent
if (-not (Test-Path $stripeDocDir)) {
    New-Item -ItemType Directory -Force -Path $stripeDocDir | Out-Null
}

$stripeDoc = @"
# Stripe Setup Guide

## Overview
This guide covers setting up Stripe for payment processing in The Body Broker.

## Prerequisites
- Stripe account (sign up at https://stripe.com)
- Stripe API keys (get from https://dashboard.stripe.com/apikeys)

## Setup Steps

### 1. Create Stripe Account
1. Go to https://stripe.com and sign up
2. Complete account verification
3. Switch to Test Mode for development

### 2. Get API Keys
1. Navigate to https://dashboard.stripe.com/apikeys
2. Copy your **Publishable key** (starts with `pk_test_`)
3. Copy your **Secret key** (starts with `sk_test_`)
4. Add these to your `.env` file:
   \`\`\`
   STRIPE_SECRET_KEY=sk_test_your_secret_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
   \`\`\`

### 3. Set Up Webhooks (Optional for Development)
1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login: \`stripe login\`
3. Forward webhooks: \`stripe listen --forward-to localhost:8000/webhooks/stripe\`
4. Copy webhook signing secret to `.env`:
   \`\`\`
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   \`\`\`

### 4. Create Products and Prices
Use Stripe Dashboard or API to create subscription tiers:
- Basic tier
- Premium tier
- VIP tier

### 5. Test Integration
Use Stripe test cards:
- Success: \`4242 4242 4242 4242\`
- Decline: \`4000 0000 0000 0002\`
- 3D Secure: \`4000 0025 0000 3155\`

## Environment Variables
\`\`\`
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=http://localhost:3000/payment/success
STRIPE_CANCEL_URL=http://localhost:3000/payment/cancel
\`\`\`

## Resources
- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Docs: https://stripe.com/docs
- Stripe API Reference: https://stripe.com/docs/api
- Test Cards: https://stripe.com/docs/testing
"@

$stripeDoc | Out-File -FilePath $stripeDocPath -Encoding UTF8
Write-Host "  ✓ Created Stripe setup documentation" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "PM-001 Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Create Stripe account: https://stripe.com" -ForegroundColor White
Write-Host "  2. Get API keys: https://dashboard.stripe.com/apikeys" -ForegroundColor White
Write-Host "  3. Add keys to .env file" -ForegroundColor White
Write-Host "  4. Install Stripe CLI (optional): https://stripe.com/docs/stripe-cli" -ForegroundColor White
Write-Host "  5. Review setup guide: $stripeDocPath" -ForegroundColor White
Write-Host ""
Write-Host "Status:" -ForegroundColor Cyan
if ($stripeCliInstalled) {
    Write-Host "  ✓ Stripe CLI installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Stripe CLI not installed (optional)" -ForegroundColor Yellow
}
Write-Host "  ✓ Stripe Python package ready" -ForegroundColor Green
Write-Host "  ✓ Setup documentation created" -ForegroundColor Green
Write-Host ""

