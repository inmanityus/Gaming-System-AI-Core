# Resend Email Service - Complete Setup Guide

## 🎯 Overview

Resend is a modern email API that provides reliable transactional email delivery. This guide covers complete setup from domain verification to production deployment.

**Project Experience**: Innovation Forge Website (October 2025)  
**Verified Working Configuration**: Next.js 14 + PM2 + Resend SMTP

---

## 🚨 Critical Lessons Learned

### The #1 Mistake: Domain Mismatch

**What Happened:**
- Verified domain: `innovationforge.ai`
- Configured email: `noreply@innovationforge.com` ❌
- Result: `450 Not authorized to send emails from innovationforge.com`

**The Fix:**
- Email domain MUST exactly match verified domain
- Check fallback values in code
- Verify runtime environment variables

---

## Step 1: Domain Verification in Resend

### 1.1 Add Domain to Resend Dashboard

1. Go to https://resend.com/domains
2. Click "Add Domain"
3. Enter your domain: `example.com`
4. Resend provides DNS records to add

### 1.2 Add DNS Records

Add these records to your DNS provider (e.g., Cloudflare, GoDaddy):

```
Type: TXT
Name: @
Value: resend-verification=<verification-code>
TTL: Auto or 3600

Type: MX
Name: @
Priority: 10
Value: feedback-smtp.us-east-1.amazonses.com
TTL: Auto or 3600

Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@example.com
TTL: Auto or 3600

Type: TXT
Name: resend._domainkey
Value: <DKIM-public-key>
TTL: Auto or 3600
```

### 1.3 Verify Domain

1. Wait 5-10 minutes for DNS propagation
2. Click "Verify" in Resend dashboard
3. Status should change to "Verified" ✅

**Common Issues:**
- DNS propagation can take up to 24 hours (usually 5-10 minutes)
- Check DNS with: `dig TXT example.com`
- Verify MX records: `dig MX example.com`

---

## Step 2: Get API Key

### 2.1 Create API Key

1. Go to https://resend.com/api-keys
2. Click "Create API Key"
3. Name: `Production - [Project Name]`
4. Permission: "Sending access"
5. Copy key: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **Save this immediately** - you can't retrieve it later!

### 2.2 API Key Format

```
re_7NYi67Me_NCfVivGmqKGouMr4UcE5bpBY
^^ Starts with "re_"
```

---

## Step 3: Configure Application

### 3.1 Environment Variables

Create/update `.env` file:

```bash
# Resend Email Configuration
USE_RESEND=true
RESEND_API_KEY=re_your_actual_api_key_here

# Email Addresses - MUST use verified domain
EMAIL_FROM=noreply@example.com
EMAIL_TO=info@example.com

# Optional: SMTP fallback
SMTP_FROM=noreply@example.com

# Environment
EMAIL_MODE=production
NODE_ENV=production
```

⚠️ **Critical**: `EMAIL_FROM` domain MUST match verified domain in Resend!

### 3.2 PM2 Configuration

Update `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'my-app',
    script: 'npm',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      
      // Resend Configuration
      USE_RESEND: 'true',
      RESEND_API_KEY: 're_your_actual_api_key_here',
      
      // Email Addresses - MUST match verified domain
      EMAIL_FROM: 'noreply@example.com',
      EMAIL_TO: 'info@example.com',
      SMTP_FROM: 'noreply@example.com',
      
      EMAIL_MODE: 'production',
      
      // Other config...
    }
  }]
}
```

⚠️ **Critical**: Keep `.env` and `ecosystem.config.js` in sync!

---

## Step 4: Implementation Code

### 4.1 Email Library (Runtime Pattern)

Create `lib/email.ts`:

```typescript
import nodemailer from 'nodemailer';

/**
 * ✅ CORRECT: Create transporter at RUNTIME
 * This ensures PM2 environment variables are loaded
 */
function getTransporter(): nodemailer.Transporter {
  const USE_RESEND = process.env.USE_RESEND === 'true';
  const RESEND_API_KEY = process.env.RESEND_API_KEY;
  
  // Debug logging (remove in production)
  console.log('[EMAIL CONFIG - RUNTIME]', {
    USE_RESEND,
    hasApiKey: !!RESEND_API_KEY,
    EMAIL_FROM: process.env.EMAIL_FROM,
    EMAIL_MODE: process.env.EMAIL_MODE
  });
  
  if (USE_RESEND && RESEND_API_KEY) {
    // Resend SMTP Configuration
    return nodemailer.createTransport({
      host: 'smtp.resend.com',
      port: 465,
      secure: true, // SSL
      auth: {
        user: 'resend',
        pass: RESEND_API_KEY
      }
    });
  }
  
  // Fallback configuration
  throw new Error('Resend not configured');
}

/**
 * Send notification email
 */
export async function sendNotificationEmail(data: {
  name: string;
  email: string;
  message: string;
}) {
  // ✅ Get transporter at runtime
  const transporter = getTransporter();
  
  // ✅ Read env vars at runtime
  const useProductionEmail = 
    process.env.EMAIL_MODE === 'production' || 
    process.env.NODE_ENV === 'production';
  
  const fromEmail = useProductionEmail
    ? process.env.EMAIL_FROM || 'noreply@example.com'
    : 'noreply@example.com';
    
  const toEmail = useProductionEmail
    ? process.env.EMAIL_TO || 'info@example.com'
    : 'info@example.com';
  
  await transporter.sendMail({
    from: fromEmail,
    to: toEmail,
    subject: `New Contact from ${data.name}`,
    html: `<p>Name: ${data.name}</p>
           <p>Email: ${data.email}</p>
           <p>Message: ${data.message}</p>`
  });
}

/**
 * Send confirmation email to user
 */
export async function sendConfirmationEmail(data: {
  name: string;
  email: string;
}) {
  const transporter = getTransporter();
  
  const fromEmail = process.env.EMAIL_FROM || 'noreply@example.com';
  
  await transporter.sendMail({
    from: fromEmail,
    to: data.email,
    subject: 'Thank you for contacting us',
    html: `<p>Hi ${data.name},</p>
           <p>We received your message and will get back to you soon!</p>`
  });
}
```

### 4.2 API Route Implementation

```typescript
// app/api/contact/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { sendNotificationEmail, sendConfirmationEmail } from '@/lib/email';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, email, message } = body;
    
    // Validate input
    if (!name || !email || !message) {
      return NextResponse.json(
        { error: 'All fields required' },
        { status: 400 }
      );
    }
    
    // Send emails
    try {
      await sendNotificationEmail({ name, email, message });
      await sendConfirmationEmail({ name, email });
    } catch (emailError) {
      console.error('Email error:', emailError);
      // Continue - don't fail request if email fails
    }
    
    return NextResponse.json({ 
      success: true,
      message: 'Form submitted successfully'
    });
    
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

---

## Step 5: Testing

### 5.1 Local Testing (Development)

```bash
# Set environment variables
export USE_RESEND=true
export RESEND_API_KEY=re_your_key
export EMAIL_FROM=noreply@example.com
export EMAIL_TO=info@example.com

# Run dev server
npm run dev

# Test API
curl -X POST http://localhost:3000/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "Test message"
  }'
```

### 5.2 Direct SMTP Test

Create `test-resend.js`:

```javascript
const nodemailer = require('nodemailer');

async function testResend() {
  const transporter = nodemailer.createTransport({
    host: 'smtp.resend.com',
    port: 465,
    secure: true,
    auth: {
      user: 'resend',
      pass: 're_your_api_key'
    },
    debug: true // Show detailed logs
  });

  try {
    const info = await transporter.sendMail({
      from: 'noreply@example.com',
      to: 'test@example.com',
      subject: 'Test Email',
      text: 'This is a test email from Resend'
    });
    
    console.log('✅ Email sent successfully!');
    console.log('Message ID:', info.messageId);
    console.log('Response:', info.response);
  } catch (error) {
    console.error('❌ Email failed:', error);
  }
}

testResend();
```

Run test:
```bash
node test-resend.js
```

### 5.3 Production Testing

```bash
# SSH to server
ssh user@server

# Test API
curl -X POST http://localhost:8888/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Test",
    "email": "test@example.com",
    "message": "Testing production email"
  }'

# Check logs
pm2 logs my-app --lines 50

# Check application debug logs
tail -f /path/to/app/email-debug.log
```

---

## Step 6: Production Deployment

### 6.1 Deployment Checklist

- [ ] Domain verified in Resend (green checkmark)
- [ ] API key created and saved
- [ ] `.env` updated with correct domain
- [ ] `ecosystem.config.js` updated with correct domain
- [ ] Email addresses match verified domain
- [ ] Code uses runtime pattern (not module-level init)
- [ ] Build completed: `npm run build`
- [ ] Files uploaded to server
- [ ] PM2 fully restarted: `pm2 delete` + `pm2 start`

### 6.2 Deployment Commands

```bash
# Local: Build application
npm run build

# Local: Create tarball
tar -czf next-build.tar.gz .next

# Local: Upload to server
scp -i key.pem next-build.tar.gz user@server:~/

# Server: Deploy
ssh -i key.pem user@server
cd /var/www/my-app
rm -rf .next
tar -xzf ~/next-build.tar.gz
chown -R user:user .next

# Server: Restart PM2 (FULL RESTART)
pm2 delete my-app
pm2 start ecosystem.config.js
pm2 save

# Verify
pm2 list
pm2 logs my-app --lines 20
```

### 6.3 Post-Deployment Verification

1. **Check PM2 Status**:
   ```bash
   pm2 list
   # Should show "online" status
   ```

2. **Test API Endpoint**:
   ```bash
   curl -X POST http://localhost:PORT/api/contact \
     -H "Content-Type: application/json" \
     -d '{"name":"Test","email":"test@example.com","message":"Test"}'
   ```

3. **Check Resend Dashboard**:
   - Go to https://resend.com/emails
   - Verify emails appear with "Delivered" status
   - Check delivery timestamps

4. **Check Application Logs**:
   ```bash
   pm2 logs my-app --lines 50
   tail -f /path/to/app/*.log
   ```

---

## Troubleshooting

### Error: "450 Not authorized to send emails from domain.com"

**Cause**: Email domain doesn't match verified domain

**Solutions**:
1. Check verified domain in Resend dashboard
2. Update `EMAIL_FROM` to match: `noreply@verified-domain.com`
3. Update ALL fallback values in code
4. Update `.env` and `ecosystem.config.js`
5. Rebuild and redeploy
6. Use `pm2 delete` + `pm2 start` (not just restart)

### Error: "Missing credentials for PLAIN"

**Cause**: `RESEND_API_KEY` not available at runtime

**Solutions**:
1. Verify API key in `ecosystem.config.js`
2. Check key format: starts with `re_`
3. Use runtime pattern (getTransporter function)
4. Restart PM2 fully: `pm2 delete` + `pm2 start`
5. Add logging to verify env vars at runtime

### Error: "Connection timeout"

**Cause**: Network/firewall issues

**Solutions**:
1. Check server outbound port 465/587
2. Verify no firewall blocking SMTP
3. Test with: `telnet smtp.resend.com 465`
4. Check Resend service status

### Emails Not Appearing in Resend Dashboard

**Causes**:
1. Wrong API key
2. Wrong domain in `from` address
3. Email sending silently failing
4. Transporter created at module load (not runtime)

**Solutions**:
1. Add comprehensive logging
2. Verify API key is correct
3. Test with direct SMTP script
4. Check application error logs
5. Verify runtime pattern usage

### Old Email Addresses Still Being Used

**Cause**: PM2 cached configuration

**Solution**:
```bash
# ❌ WRONG
pm2 restart my-app --update-env

# ✅ CORRECT
pm2 delete my-app
pm2 start ecosystem.config.js
pm2 save
```

---

## Best Practices

### 1. **Runtime Environment Variable Access**
```typescript
// ✅ CORRECT
function sendEmail() {
  const apiKey = process.env.RESEND_API_KEY;
}

// ❌ WRONG
const apiKey = process.env.RESEND_API_KEY;
function sendEmail() { /* uses cached apiKey */ }
```

### 2. **Error Handling**
```typescript
try {
  await sendNotificationEmail(data);
} catch (emailError) {
  console.error('Email failed:', emailError);
  // Log but don't fail the request
  // User submission was saved, email is secondary
}
```

### 3. **Domain Consistency**
- Use single verified domain for all emails
- Keep configuration files in sync
- Update ALL fallback values when changing domains

### 4. **Security**
- Never commit API keys to git
- Use environment variables
- Rotate keys periodically
- Use separate keys for dev/staging/production

### 5. **Monitoring**
- Check Resend dashboard regularly
- Monitor delivery rates
- Set up webhooks for failures
- Keep logs for debugging

---

## Configuration Templates

### Minimal `.env`
```bash
USE_RESEND=true
RESEND_API_KEY=re_your_key
EMAIL_FROM=noreply@example.com
EMAIL_TO=info@example.com
EMAIL_MODE=production
NODE_ENV=production
```

### Complete `ecosystem.config.js`
```javascript
module.exports = {
  apps: [{
    name: 'my-app',
    script: 'npm',
    args: 'start',
    cwd: '/var/www/my-app',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      
      // Resend Email
      USE_RESEND: 'true',
      RESEND_API_KEY: 're_your_api_key',
      EMAIL_FROM: 'noreply@example.com',
      EMAIL_TO: 'info@example.com',
      SMTP_FROM: 'noreply@example.com',
      EMAIL_MODE: 'production',
      
      // Database
      DATABASE_URL: 'postgresql://user:pass@localhost:5432/db'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
}
```

---

## Quick Reference

### Resend SMTP Settings
```
Host: smtp.resend.com
Port: 465 (SSL) or 587 (TLS)
Username: resend
Password: <your-api-key>
```

### Common Commands
```bash
# Full PM2 restart
pm2 delete app && pm2 start ecosystem.config.js && pm2 save

# Check Resend emails via CLI
curl https://api.resend.com/emails \
  -H "Authorization: Bearer re_your_key"

# Test DNS records
dig TXT example.com
dig MX example.com

# Test SMTP connection
telnet smtp.resend.com 465
```

---

## Related Resources

- Resend Documentation: https://resend.com/docs
- Resend Dashboard: https://resend.com/overview
- Resend Status: https://status.resend.com
- Nodemailer Documentation: https://nodemailer.com

---

**Last Updated**: 2025-10-29  
**Verified Configuration**: Next.js 14 + PM2 5.x + Resend API  
**Production Tested**: ✅ Innovation Forge Website

