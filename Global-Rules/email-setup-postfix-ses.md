# Email Setup: Postfix + AWS SES

**Purpose**: Configure reliable email sending for web applications using local Postfix SMTP and AWS SES for external delivery.

**Use Case**: Contact forms, login codes, password resets, notifications

**Validated**: Functional Fitness USA Website (October 2025)

---

## Overview

This guide sets up a two-tier email system:
1. **Local Postfix** (port 25) - Simple, secure localhost SMTP
2. **AWS SES** (port 587) - Production email delivery with high deliverability

### Why Two Options?

| Feature | Local Postfix | AWS SES |
|---------|---------------|---------|
| Setup Complexity | Simple | Moderate |
| Deliverability | Low (often spam) | High (trusted sender) |
| Cost | Free | $0.10 per 1,000 emails |
| Rate Limits | None | 14 emails/second |
| Bounce Handling | Manual | Automatic (SNS) |
| Best For | Development/Testing | Production |

---

## Option 1: Local Postfix (Simple)

### Installation
```bash
sudo apt-get install -y postfix

# Select "Internet Site" when prompted
# Or configure manually:
```

### Configuration
Edit `/etc/postfix/main.cf`:
```conf
# Listen only on localhost (secure)
inet_interfaces = loopback-only

# Only deliver to localhost
mydestination = localhost

# Only trust localhost
mynetworks = 127.0.0.0/8

# Hostname
myhostname = localhost
```

### Reload Postfix
```bash
sudo systemctl restart postfix
```

### Application Configuration
```javascript
// In your email service (Node.js)
const transporter = nodemailer.createTransport({
  host: 'localhost',
  port: 25,
  secure: false,  // No encryption needed for localhost
  auth: false     // No authentication for localhost
});
```

### Security Note
✅ **This is secure because:**
- Port 25 only accepts connections from localhost
- Not exposed to internet (firewall blocks it)
- Cannot be used as an open relay
- Simple and no password management

⚠️ **Limitations:**
- Emails may go to spam (no reputation)
- No bounce handling
- No deliverability tracking

---

## Option 2: AWS SES (Production)

### Prerequisites
1. AWS account with SES access
2. Verified sender email address or domain

### Step 1: Verify Email Address (Sandbox Mode)
```bash
# Verify sender email
aws ses verify-email-identity \
  --email-address noreply@yourdomain.com \
  --region us-east-1

# Verify recipient email (for testing)
aws ses verify-email-identity \
  --email-address test@example.com \
  --region us-east-1

# Check verification status
aws ses list-verified-email-addresses --region us-east-1
```

### Step 2: Create SMTP Credentials
```bash
# Go to AWS Console → SES → SMTP Settings → Create SMTP Credentials
# Or use IAM:

# Create IAM user for SMTP
aws iam create-user --user-name ses-smtp-user

# Attach SES sending policy
aws iam attach-user-policy \
  --user-name ses-smtp-user \
  --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess

# Create access key
aws iam create-access-key --user-name ses-smtp-user
```

**Save the output:**
- Access Key ID: `AKIA...`
- Secret Access Key: `wJalrXUtn...`

### Step 3: Convert Secret to SMTP Password
```javascript
// convert-ses-password.js
const crypto = require('crypto');

const key = 'YOUR_SECRET_ACCESS_KEY';
const message = 'SendRawEmail';
const version = Buffer.from([0x02]);
const signatureInBytes = crypto.createHmac('sha256', key).update(message).digest();
const signatureAndVersion = Buffer.concat([version, signatureInBytes]);
const smtpPassword = signatureAndVersion.toString('base64');

console.log('SMTP Password:', smtpPassword);
```

```bash
node convert-ses-password.js
```

### Step 4: Configure Application
```javascript
// Email service with AWS SES
const transporter = nodemailer.createTransport({
  host: 'email-smtp.us-east-1.amazonaws.com',
  port: 587,
  secure: false,  // IMPORTANT: false for STARTTLS
  requireTLS: true,  // IMPORTANT: upgrade to TLS
  auth: {
    user: 'AKIA...', // Access Key ID
    pass: 'BASE64_SMTP_PASSWORD'  // Converted password
  }
});
```

### Step 5: Test Email Sending
```javascript
const mailOptions = {
  from: 'noreply@yourdomain.com',
  to: 'test@example.com',
  subject: 'Test Email',
  text: 'This is a test email from AWS SES'
};

transporter.sendMail(mailOptions, (error, info) => {
  if (error) {
    console.log('Error:', error);
  } else {
    console.log('Email sent:', info.messageId);
  }
});
```

### Step 6: Request Production Access
When ready to send to any email address (not just verified ones):

1. Go to AWS Console → SES → Account Dashboard
2. Click "Request production access"
3. Fill out form:
   - **Use Case**: Transactional (login codes, contact forms)
   - **Website**: your-domain.com
   - **Description**: "Sending login verification codes and contact form responses"
   - **Bounce/Complaint Handling**: "Configured via SNS" or "Will monitor bounce rate"

4. AWS typically approves in 24 hours

---

## Multi-Site Configuration

### Global Variables (Shared)
In `/etc/environment`:
```bash
# Shared AWS SES credentials (all sites)
AWS_SES_SMTP_USER=AKIA...
AWS_SES_SMTP_PASSWORD=BASE64...
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
```

### Site-Specific Variables
In each site's `.env.local`:
```bash
# Site 1
SMTP_FROM_EMAIL=noreply@site1.com
SMTP_FROM_NAME="Site 1"
DEFAULT_EMAIL=info@site1.com

# Site 2
SMTP_FROM_EMAIL=noreply@site2.com
SMTP_FROM_NAME="Site 2"
DEFAULT_EMAIL=contact@site2.com
```

### Benefit
- ✅ One AWS SES account for all sites
- ✅ Each site has own sender identity
- ✅ Easy to manage credentials
- ✅ No credential duplication

---

## DNS Configuration (Production)

### Why DNS Records Matter
Without SPF, DKIM, and DMARC:
- 70-90% of emails go to spam
- Low sender reputation
- May be blocked by email providers

### SPF Record
Proves your server is authorized to send email for your domain.

```
Type: TXT
Name: @
Value: v=spf1 ip4:YOUR_SERVER_IP include:amazonses.com ~all
```

### DKIM Record
Signs emails to prevent tampering.

AWS SES generates these for you:
1. Go to SES → Verified Identities → Your Domain
2. Copy the three DKIM records
3. Add to your DNS:

```
Type: CNAME
Name: abc._domainkey.yourdomain.com
Value: abc.dkim.amazonses.com
```

(Repeat for all three DKIM records)

### DMARC Record
Tells receivers what to do with unauthenticated emails.

```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:postmaster@yourdomain.com
```

### Verification
After adding DNS records:
```bash
# Check SPF
dig TXT yourdomain.com

# Check DKIM
dig TXT abc._domainkey.yourdomain.com

# Check DMARC
dig TXT _dmarc.yourdomain.com
```

**Wait 24-48 hours for DNS propagation before testing**

---

## Email Templates

### Transactional Email Template
```javascript
async function sendLoginCode(email, code) {
  const mailOptions = {
    from: `"${process.env.SMTP_FROM_NAME}" <${process.env.SMTP_FROM_EMAIL}>`,
    to: email,
    subject: 'Your Login Code',
    text: `Your login code is: ${code}\n\nThis code expires in 10 minutes.`,
    html: `
      <h2>Your Login Code</h2>
      <p>Enter this code to complete your login:</p>
      <h1 style="font-size: 32px; letter-spacing: 5px;">${code}</h1>
      <p>This code expires in 10 minutes.</p>
    `
  };

  return transporter.sendMail(mailOptions);
}
```

### Contact Form Email Template
```javascript
async function sendContactForm(formData) {
  // Email to admin
  await transporter.sendMail({
    from: process.env.SMTP_FROM_EMAIL,
    to: process.env.DEFAULT_EMAIL,
    subject: `Contact Form: ${formData.subject}`,
    html: `
      <h2>New Contact Form Submission</h2>
      <p><strong>Name:</strong> ${formData.name}</p>
      <p><strong>Email:</strong> ${formData.email}</p>
      <p><strong>Phone:</strong> ${formData.phone}</p>
      <p><strong>Message:</strong></p>
      <p>${formData.message}</p>
    `
  });

  // Confirmation to user
  await transporter.sendMail({
    from: `"${process.env.SMTP_FROM_NAME}" <${process.env.SMTP_FROM_EMAIL}>`,
    to: formData.email,
    subject: 'Thank you for contacting us',
    html: `
      <h2>Thank you for your message</h2>
      <p>We received your message and will respond within 24 hours.</p>
    `
  });
}
```

---

## Troubleshooting

### Email Not Sending (Postfix)
```bash
# Check if Postfix is running
sudo systemctl status postfix

# Check mail queue
sudo postqueue -p

# View Postfix logs
sudo tail -f /var/log/mail.log

# Flush queue
sudo postqueue -f
```

### Email Not Sending (AWS SES)
```bash
# Common issues:

# 1. Wrong port (should be 587, not 465 or 25)
port: 587

# 2. Wrong secure setting (should be false for STARTTLS)
secure: false
requireTLS: true

# 3. Sandbox mode (verify recipient email)
aws ses list-verified-email-addresses

# 4. Wrong SMTP password (must convert Secret Key)
# Use convert-ses-password.js script

# 5. Self-signed SSL certificate
tls: {
  rejectUnauthorized: false  // For testing only
}
```

### Emails Going to Spam
```bash
# Check sender reputation
# Visit: mail-tester.com

# Common fixes:
# 1. Add SPF record
# 2. Add DKIM records (AWS SES provides these)
# 3. Add DMARC record
# 4. Use verified domain (not gmail.com)
# 5. Proper from/reply-to headers
```

### Testing Email Deliverability
```bash
# Send test email
curl -X POST http://localhost:3000/api/test-email

# Check AWS SES sending statistics
aws ses get-send-statistics --region us-east-1

# Check bounces and complaints
aws ses get-send-quota --region us-east-1
```

---

## Cost Analysis

### AWS SES Pricing
- **First 62,000 emails/month**: FREE (if sent from EC2)
- **Additional emails**: $0.10 per 1,000
- **Attachments**: $0.12 per GB

### Example Costs
| Volume | Monthly Cost |
|--------|--------------|
| 10,000 emails | $0 |
| 100,000 emails | $3.80 |
| 1,000,000 emails | $94.00 |

**Conclusion**: Very cost-effective for most applications

---

## Security Best Practices

### 1. Use Environment Variables
```javascript
// NEVER hardcode credentials
const config = {
  host: process.env.SMTP_HOST,
  user: process.env.SMTP_USER,
  pass: process.env.SMTP_PASSWORD
};
```

### 2. Restrict SMTP Access
```javascript
// Only allow localhost Postfix
if (process.env.SMTP_HOST === 'localhost') {
  // No authentication needed
} else {
  // Require authentication for external SMTP
  config.auth = {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASSWORD
  };
}
```

### 3. Rate Limiting
```javascript
// Prevent email abuse
const rateLimit = require('express-rate-limit');

const emailLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 emails per 15 minutes
  message: 'Too many emails sent, please try again later'
});

app.post('/api/contact', emailLimiter, async (req, res) => {
  // Send email
});
```

### 4. Validate Email Addresses
```javascript
function isValidEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// Prevent sending to invalid addresses
if (!isValidEmail(recipientEmail)) {
  throw new Error('Invalid email address');
}
```

---

## Monitoring & Logging

### Track Email Sending
```javascript
async function sendEmailWithLogging(mailOptions) {
  try {
    const info = await transporter.sendMail(mailOptions);
    
    // Log success
    console.log({
      timestamp: new Date().toISOString(),
      messageId: info.messageId,
      recipient: mailOptions.to,
      subject: mailOptions.subject,
      status: 'sent'
    });
    
    return info;
  } catch (error) {
    // Log failure
    console.error({
      timestamp: new Date().toISOString(),
      recipient: mailOptions.to,
      subject: mailOptions.subject,
      status: 'failed',
      error: error.message
    });
    
    throw error;
  }
}
```

### AWS SES Metrics
```bash
# View sending statistics
aws ses get-send-statistics --region us-east-1

# View daily sending quota
aws ses get-send-quota --region us-east-1
```

---

## Quick Start Checklist

### Development (Local Postfix)
- [ ] Install Postfix: `sudo apt-get install postfix`
- [ ] Configure localhost-only: `inet_interfaces = loopback-only`
- [ ] Test: Send email to localhost
- [ ] Configure app: `host: 'localhost', port: 25`

### Production (AWS SES)
- [ ] Create AWS SES account
- [ ] Verify sender email/domain
- [ ] Create SMTP credentials
- [ ] Convert secret to SMTP password
- [ ] Configure app with credentials
- [ ] Test email sending
- [ ] Request production access
- [ ] Add DNS records (SPF, DKIM, DMARC)
- [ ] Wait 24-48 hours for DNS propagation
- [ ] Test deliverability with mail-tester.com

---

## Related Documentation

- **Multi-Tenant Deployment**: See Global-Workflows/deploy-multi-tenant-web-server.md
- **AWS Deployment Lessons**: See Global-History/resolutions/aws-deployment-lessons.md
- **AWS CLI Usage**: See Global-Rules/AWS-Direct-CLI-Usage.md

---

**Last Updated**: 2025-10-18  
**Validated**: Production use in Functional Fitness USA  
**Status**: Battle-tested and reliable

