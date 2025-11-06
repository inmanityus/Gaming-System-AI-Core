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
2. Copy your **Publishable key** (starts with pk_test_)
3. Copy your **Secret key** (starts with sk_test_)
4. Add these to your .env file:
   \\\
   STRIPE_SECRET_KEY=sk_test_your_secret_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
   \\\

### 3. Set Up Webhooks (Optional for Development)
1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login: \stripe login\
3. Forward webhooks: \stripe listen --forward-to localhost:8000/webhooks/stripe\
4. Copy webhook signing secret to .env:
   \\\
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   \\\

### 4. Create Products and Prices
Use Stripe Dashboard or API to create subscription tiers:
- Basic tier
- Premium tier
- VIP tier

### 5. Test Integration
Use Stripe test cards:
- Success: \4242 4242 4242 4242\
- Decline: \4000 0000 0000 0002\
- 3D Secure: \4000 0025 0000 3155\

## Environment Variables
\\\
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=http://localhost:3000/payment/success
STRIPE_CANCEL_URL=http://localhost:3000/payment/cancel
\\\

## Resources
- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Docs: https://stripe.com/docs
- Stripe API Reference: https://stripe.com/docs/api
- Test Cards: https://stripe.com/docs/testing
