# AWS SES Email Integration
**Production Email System Setup and Troubleshooting**

## Overview

Amazon SES (Simple Email Service) is a reliable, scalable email platform for sending transactional and marketing emails. This guide documents the setup, configuration, and lessons learned from integrating AWS SES into production applications, specifically addressing common pitfalls and environment variable conflicts.

**Created:** October 19, 2025  
**Project:** Innovation Forge Website  
**Purpose:** Production email delivery for contact forms and notifications

---

## Lessons Learned

### Critical Discoveries

1. **Sandbox Mode vs Production**
   - AWS SES starts in sandbox mode
   - Can only send to verified email addresses
   - Must request production access to send to any address

2. **Global Environment Variable Conflicts**
   - Global `/etc/environment` variables override project `.env` files
   - Multiple projects on same server need unique SMTP variable names
   - Use project-specific prefixes (e.g., `AWS_SES_SMTP_*` vs generic `SMTP_*`)

3. **PM2 Environment Variable Loading**
   - Simple `pm2 restart` doesn't reload environment variables
   - Use `pm2 reload <id> --update-env` or `pm2 delete` + `pm2 start`
   - Must explicitly source environment files

4. **Email Client Rendering**
   - Gmail strips `<style>` tags from email HTML
   - Must use inline styles or table-based layouts
   - Test across multiple email clients

5. **TLS/SSL Certificate Verification**
   - Some servers may have CA certificate issues with AWS
   - May need `rejectUnauthorized: false` workaround
   - Better solution: Update system CA certificates

---

## Prerequisites

- AWS Account with SES access
- Domain ownership verification
- Email addresses verified in SES console
- SMTP credentials generated

---

## AWS SES Setup

### 1. Request Production Access

**AWS Console → Amazon SES → Account dashboard → Request production access**

**Required Information:**
- Mail type: Transactional
- Website URL
- Use case description
- Compliance with AWS policies
- How you handle bounces/complaints

**Processing Time:** 1-2 business days

### 2. Verify Domain

**Method 1: Email Verification**
```
AWS Console → Verified identities → Create identity
→ Email address → Enter email → Create identity
→ Check email and click verification link
```

**Method 2: Domain Verification (Recommended)**
```
AWS Console → Verified identities → Create identity
→ Domain → Enter domain name → Create identity
→ Add DNS records (DKIM, SPF, DMARC)
```

**DNS Records to Add:**
```dns
; SPF Record
example.com. IN TXT "v=spf1 include:amazonses.com ~all"

; DKIM Records (3 provided by AWS)
xyz1._domainkey.example.com. IN CNAME xyz1.dkim.amazonses.com.
xyz2._domainkey.example.com. IN CNAME xyz2.dkim.amazonses.com.
xyz3._domainkey.example.com. IN CNAME xyz3.dkim.amazonses.com.

; DMARC Record
_dmarc.example.com. IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
```

### 3. Generate SMTP Credentials

```
AWS Console → Amazon SES → SMTP settings
→ Create SMTP credentials
→ Create user
→ Download credentials (CRITICAL: only shown once!)
```

**Credentials Format:**
- SMTP Username: `AKIA...` (20 characters)
- SMTP Password: Long base64 string

**SMTP Server Details:**
- **Host:** `email-smtp.us-east-1.amazonaws.com` (or your region)
- **Port:** 587 (TLS), 465 (SSL), or 25
- **Protocol:** STARTTLS recommended

---

## Application Integration

### Environment Configuration

**Per-Project .env File** (Recommended)
```env
# AWS SES SMTP Configuration
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587
AWS_SES_SMTP_USER=AKIA2DZSOUO2K5EI4QWR
AWS_SES_SMTP_PASSWORD=BAE4+dj49K3PB1fM7LaErGGSxGIsjD3Z/7c0uBDZsemm

# Email Addresses
EMAIL_FROM=noreply@tenant2.ai
EMAIL_TO=info@tenant2.ai

# Force production email mode
EMAIL_MODE=production
NODE_ENV=production
```

**Global Environment (Multi-Tenant Servers)**
```bash
# /etc/environment
# Use project-specific prefixes!
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587

# Each project should set their own credentials in .env
```

### Nodemailer Setup

**lib/email.ts**
```typescript
import nodemailer from 'nodemailer';

// Determine if we should use production email
const useProductionEmail = 
  process.env.EMAIL_MODE === 'production' || 
  process.env.NODE_ENV === 'production';

// Production SMTP configuration
const productionHost = 
  process.env.AWS_SES_SMTP_HOST || 
  process.env.SMTP_HOST || 
  'email-smtp.us-east-1.amazonaws.com';

const productionPort = 
  process.env.AWS_SES_SMTP_PORT || 
  process.env.SMTP_PORT || 
  '587';

const productionUser = 
  process.env.AWS_SES_SMTP_USER || 
  process.env.SMTP_USER;

const productionPass = 
  process.env.AWS_SES_SMTP_PASSWORD || 
  process.env.SMTP_PASS;

// Debug logging
console.log('[EMAIL CONFIG] EMAIL_MODE:', process.env.EMAIL_MODE);
console.log('[EMAIL CONFIG] useProductionEmail:', useProductionEmail);
console.log('[EMAIL CONFIG] SMTP_HOST:', useProductionEmail ? productionHost : 'localhost');

// Create transporter
const transporter = nodemailer.createTransport({
  host: useProductionEmail ? productionHost : 'localhost',
  port: useProductionEmail ? parseInt(productionPort) : 1025,
  secure: false, // Use STARTTLS on port 587
  auth: useProductionEmail
    ? {
        user: productionUser,
        pass: productionPass,
      }
    : undefined,
  tls: useProductionEmail
    ? {
        // Workaround for CA certificate issues
        rejectUnauthorized: false,
        minVersion: 'TLSv1.2',
      }
    : undefined,
  debug: true,
  logger: true,
});

// Verify connection
transporter.verify((error, success) => {
  if (error) {
    console.error('[EMAIL] Connection failed:', error);
  } else {
    console.log('[EMAIL] Server ready to send emails');
  }
});

export default transporter;
```

### Sending Emails

**Example: Contact Form Email**
```typescript
import transporter from './email';

export async function sendContactEmail(data: {
  name: string;
  email: string;
  message: string;
}) {
  const emailHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
      </head>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
        <table width="600" cellpadding="0" cellspacing="0" style="background: #fff;">
          <tr>
            <td style="background: #0A2540; padding: 40px; text-align: center;">
              <h1 style="color: #00FF9D; margin: 0;">New Contact Message</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 30px;">
              <p><strong>From:</strong> ${data.name} (${data.email})</p>
              <p><strong>Message:</strong></p>
              <p>${data.message}</p>
            </td>
          </tr>
        </table>
      </body>
    </html>
  `;

  await transporter.sendMail({
    from: process.env.EMAIL_FROM || 'noreply@example.com',
    to: process.env.EMAIL_TO || 'info@example.com',
    subject: 'New Contact Form Submission',
    html: emailHtml,
    text: `From: ${data.name} (${data.email})\n\nMessage: ${data.message}`,
  });
}
```

---

## Troubleshooting

### 1. Email Not Sending

**Error:** `ECONNREFUSED 127.0.0.1:1025`

**Cause:** Application trying to use local MailHog instead of AWS SES

**Solution:**
```env
# Force production mode
EMAIL_MODE=production
NODE_ENV=production
```

Restart application:
```bash
pm2 reload app-name --update-env
```

### 2. 554 Message Rejected: Email Address Not Verified

**Cause:** AWS SES still in sandbox mode

**Solution:**
1. Verify both sender and recipient addresses in AWS console
2. Request production access
3. Wait for approval (1-2 business days)

### 3. 401 Unauthorized / Invalid Credentials

**Cause:** Incorrect SMTP credentials

**Solution:**
1. Verify credentials in AWS SES → SMTP settings
2. Generate new SMTP credentials if lost
3. Update .env file
4. Restart with `pm2 reload app --update-env`

### 4. TLS/SSL Certificate Error

**Error:** `Error: self-signed certificate`

**Temporary Workaround:**
```typescript
tls: {
  rejectUnauthorized: false,
  minVersion: 'TLSv1.2',
}
```

**Proper Fix:**
```bash
# Update CA certificates
sudo apt-get update
sudo apt-get install ca-certificates
sudo update-ca-certificates
```

### 5. PM2 Not Loading Environment Variables

**Problem:** Changed .env but emails still failing

**Solution:**
```bash
# Option 1: Reload with env update
pm2 reload app-id --update-env

# Option 2: Delete and restart
pm2 delete app-id
pm2 start ecosystem.config.js

# Option 3: Explicit env file
pm2 start app.js --env-file .env
```

### 6. Global SMTP Variables Overriding Project Settings

**Problem:** Multiple projects on same server, email config conflicts

**Solution:**
```bash
# In /etc/environment - Keep generic AWS vars
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_PORT=587

# REMOVE these from /etc/environment:
# SMTP_HOST (causes conflict)
# SMTP_PORT (causes conflict)
```

**In each project's .env:**
```env
# Project A
AWS_SES_SMTP_USER=project_a_user
AWS_SES_SMTP_PASSWORD=project_a_password
EMAIL_FROM=noreply@projecta.com

# Project B
AWS_SES_SMTP_USER=project_b_user
AWS_SES_SMTP_PASSWORD=project_b_password
EMAIL_FROM=noreply@projectb.com
```

---

## Email Template Best Practices

### Use Table-Based Layouts

**❌ Bad: Div-based (Gmail will break)**
```html
<div style="background: blue;">
  <h1>Header</h1>
</div>
```

**✅ Good: Table-based**
```html
<table width="600" cellpadding="0" cellspacing="0">
  <tr>
    <td style="background-color: blue; padding: 20px;">
      <h1 style="color: white; margin: 0;">Header</h1>
    </td>
  </tr>
</table>
```

### Always Use Inline Styles

**❌ Bad:**
```html
<style>
  .header { color: red; }
</style>
<h1 class="header">Title</h1>
```

**✅ Good:**
```html
<h1 style="color: red; font-size: 24px; margin: 0;">Title</h1>
```

### Test Across Email Clients

- Gmail (web, mobile)
- Outlook (desktop, web)
- Apple Mail
- Mobile clients (iOS, Android)

**Testing Tools:**
- [Litmus](https://litmus.com/)
- [Email on Acid](https://www.emailonacid.com/)
- Manual testing with real accounts

---

## Monitoring & Metrics

### AWS SES Console Metrics

**Monitor:**
- Delivery rate
- Bounce rate
- Complaint rate
- Reputation status

**Alert Thresholds:**
- Bounce rate > 5%: Warning
- Complaint rate > 0.1%: Critical
- Low reputation score: Review immediately

### Application Logging

```typescript
async function sendEmailWithLogging(options: any) {
  console.log(`[EMAIL] Attempting to send to: ${options.to}`);
  console.log(`[EMAIL] From: ${options.from}`);
  console.log(`[EMAIL] Subject: ${options.subject}`);

  try {
    const info = await transporter.sendMail(options);
    console.log(`[EMAIL] ✓ Sent successfully`);
    console.log(`[EMAIL] Message ID: ${info.messageId}`);
    return info;
  } catch (error) {
    console.error(`[EMAIL] ✗ Failed:`, error);
    throw error;
  }
}
```

### Database Logging

```sql
CREATE TABLE email_log (
    id SERIAL PRIMARY KEY,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    status VARCHAR(50),
    error_message TEXT,
    message_id VARCHAR(255),
    sent_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_recipient (recipient),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at DESC)
);
```

---

## Security Best Practices

### 1. Secure Credentials

```bash
# .env file permissions
chmod 600 .env

# Never commit to git
echo ".env" >> .gitignore
```

### 2. Rotate Credentials Regularly

- Generate new SMTP credentials every 90 days
- Update all applications
- Delete old credentials

### 3. Use IAM Roles (EC2)

**Instead of SMTP credentials:**
```typescript
// Use AWS SDK with IAM role
import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses";

const sesClient = new SESClient({ 
  region: "us-east-1",
  // Credentials automatically from IAM role
});

const command = new SendEmailCommand({
  Source: "noreply@example.com",
  Destination: { ToAddresses: ["user@example.com"] },
  Message: {
    Subject: { Data: "Subject" },
    Body: { Html: { Data: "<html>...</html>" } },
  },
});

await sesClient.send(command);
```

### 4. Rate Limiting

```typescript
import pLimit from 'p-limit';

// Limit concurrent email sends
const emailLimit = pLimit(10);

async function sendBulkEmails(recipients: string[]) {
  return Promise.all(
    recipients.map(recipient => 
      emailLimit(() => sendEmail(recipient))
    )
  );
}
```

### 5. Handle Bounces and Complaints

**Setup SNS Notifications:**
```
AWS Console → Amazon SES → Configuration sets
→ Create configuration set
→ Add SNS topic for bounces
→ Add SNS topic for complaints
```

**Process Notifications:**
```typescript
// Lambda function or webhook endpoint
export async function handleSNSNotification(event: any) {
  const message = JSON.parse(event.Records[0].Sns.Message);
  
  if (message.notificationType === 'Bounce') {
    await handleBounce(message.bounce);
  } else if (message.notificationType === 'Complaint') {
    await handleComplaint(message.complaint);
  }
}

async function handleBounce(bounce: any) {
  for (const recipient of bounce.bouncedRecipients) {
    // Mark email as invalid in database
    await db.query(
      'UPDATE users SET email_bounced = true WHERE email = $1',
      [recipient.emailAddress]
    );
  }
}
```

---

## Cost Optimization

### Pricing (as of 2025)

- **First 62,000 emails/month:** FREE (if sent from EC2)
- **Additional emails:** $0.10 per 1,000 emails

### Optimization Strategies

1. **Batch Similar Emails**
   - Use templates
   - Send during off-peak hours

2. **Avoid Unnecessary Sends**
   - Deduplicate recipients
   - Implement send preferences

3. **Use Configuration Sets**
   - Track metrics
   - Identify costly patterns

4. **Monitor Bounce Rates**
   - High bounces waste money
   - Clean email lists regularly

---

## Testing

### Local Testing with MailHog

**Development .env:**
```env
EMAIL_MODE=development
SMTP_HOST=localhost
SMTP_PORT=1025
```

**Start MailHog:**
```bash
# Windows
.\mailhog.exe

# Linux/Mac
mailhog
```

**View emails:** http://localhost:8025

### Production Testing

```typescript
// Test script
async function testSES() {
  try {
    await sendEmail({
      to: 'your-verified-email@example.com',
      subject: 'SES Test',
      html: '<h1>Test successful!</h1>',
    });
    console.log('✓ Email sent successfully');
  } catch (error) {
    console.error('✗ Email failed:', error);
  }
}
```

---

## Related Documentation

- [AI-COLLABORATIVE-AUTHORING-SYSTEM.md](./AI-COLLABORATIVE-AUTHORING-SYSTEM.md) - System that uses email notifications
- [MULTI-TENANT-DEPLOYMENT.md](./MULTI-TENANT-DEPLOYMENT.md) - Managing multiple projects on one server

---

**Last Updated:** October 19, 2025  
**Maintained By:** AI Development Team

