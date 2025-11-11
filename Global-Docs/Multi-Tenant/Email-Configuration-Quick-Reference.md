# Multi-Tenant Email Configuration - Quick Reference

## Overview

Quick reference for setting up email services (Resend, AWS SES, SMTP) across multiple applications on shared server infrastructure.

**Based on**: Innovation Forge Website deployment (October 2025)

---

## Email Service Options

### Option 1: Resend (Recommended for New Projects)
- **Best for**: Transactional emails, contact forms, notifications
- **Pros**: Simple setup, good deliverability, modern API, free tier
- **Cons**: Requires domain verification

### Option 2: AWS SES
- **Best for**: High-volume email, existing AWS infrastructure
- **Pros**: Scalable, cost-effective at scale
- **Cons**: More complex setup, sandbox mode restrictions

### Option 3: MailHog (Development Only)
- **Best for**: Local development, testing
- **Pros**: No external dependencies, catches all emails
- **Cons**: Not for production

---

## Quick Setup Checklist

### For New Project with Resend

- [ ] **1. Verify Domain in Resend**
  - Go to https://resend.com/domains
  - Add domain (e.g., `example.com`)
  - Add DNS records (TXT, MX, DMARC, DKIM)
  - Wait for verification (5-10 minutes)

- [ ] **2. Create API Key**
  - Go to https://resend.com/api-keys
  - Create key with "Sending access"
  - Save key (format: `re_xxxxxxxxxxxx`)

- [ ] **3. Configure Application**
  - Update `.env`:
    ```bash
    USE_RESEND=true
    RESEND_API_KEY=re_your_key
    EMAIL_FROM=noreply@example.com
    EMAIL_TO=info@example.com
    EMAIL_MODE=production
    ```
  - Update `ecosystem.config.js`:
    ```javascript
    env: {
      USE_RESEND: 'true',
      RESEND_API_KEY: 're_your_key',
      EMAIL_FROM: 'noreply@example.com',
      EMAIL_TO: 'info@example.com',
      EMAIL_MODE: 'production'
    }
    ```

- [ ] **4. Implement Runtime Pattern**
  - Use `getTransporter()` function (not module-level init)
  - Access env vars inside functions
  - See: `Global-Docs/Resend/Complete-Setup-Guide.md`

- [ ] **5. Deploy and Test**
  - Build: `npm run build`
  - Upload `.next` to server
  - Restart PM2: `pm2 delete app && pm2 start ecosystem.config.js`
  - Test API endpoint
  - Verify in Resend dashboard

---

## Critical Configuration Rules

### 1. Domain Must Match Exactly
```
✅ CORRECT:
Verified domain: example.com
EMAIL_FROM: noreply@example.com
EMAIL_TO: info@example.com

❌ WRONG:
Verified domain: example.com
EMAIL_FROM: noreply@example.co.uk  ← Different domain
```

### 2. Keep Files in Sync
```
✅ CORRECT: Both files use same domain
- .env: EMAIL_FROM=noreply@example.com
- ecosystem.config.js: EMAIL_FROM: 'noreply@example.com'

❌ WRONG: Files have different domains
- .env: EMAIL_FROM=noreply@example.com
- ecosystem.config.js: EMAIL_FROM: 'noreply@example.org'
```

### 3. Update ALL Fallback Values
```typescript
// ✅ CORRECT: Fallback matches verified domain
const from = process.env.EMAIL_FROM || 'noreply@example.com';

// ❌ WRONG: Fallback uses different domain
const from = process.env.EMAIL_FROM || 'noreply@wrong-domain.com';
```

### 4. Use Runtime Pattern
```typescript
// ✅ CORRECT: Runtime access
function sendEmail() {
  const transporter = getTransporter(); // Creates fresh transporter
  const from = process.env.EMAIL_FROM; // Reads at runtime
}

// ❌ WRONG: Module-level initialization
const transporter = createTransporter(); // Created at build time
const from = process.env.EMAIL_FROM; // Read at build time
```

### 5. Restart PM2 Properly
```bash
# ✅ CORRECT: Full restart loads fresh config
pm2 delete app-name
pm2 start ecosystem.config.js
pm2 save

# ❌ WRONG: Doesn't reload ecosystem.config.js
pm2 restart app-name --update-env
```

---

## Per-Project Configuration

### Standard Directory Structure
```
/var/www/
  ├── project-1/
  │   ├── .env                      # Project-specific config
  │   ├── ecosystem.config.js       # PM2 config with env vars
  │   ├── .next/                    # Built application
  │   └── lib/email.ts              # Email implementation
  ├── project-2/
  │   ├── .env
  │   ├── ecosystem.config.js
  │   └── ...
```

### Environment Variable Priority
1. System env (`/etc/environment`) - Lowest
2. Project `.env` file - Middle
3. `ecosystem.config.js` env section - **Highest** ⭐

---

## Common Multi-Tenant Scenarios

### Scenario 1: Multiple Projects, One Domain
```
Project 1: info@company.com
Project 2: support@company.com
Project 3: sales@company.com

✅ Solution: One verified domain, different email addresses
```

### Scenario 2: Multiple Projects, Different Domains
```
Project 1: info@company1.com (Resend account 1)
Project 2: info@company2.com (Resend account 2)

✅ Solution: Separate Resend accounts, different API keys
```

### Scenario 3: Staging + Production
```
Staging: staging@example.com (Resend test domain)
Production: info@example.com (Resend production domain)

✅ Solution: Different API keys in ecosystem.config.js
```

---

## Server-Level Configuration

### Global Email Settings (Optional)

For shared SMTP settings across projects:

```bash
# /etc/environment (system-wide)
SMTP_HOST=smtp.resend.com
SMTP_PORT=465
```

Projects can override in their `ecosystem.config.js`.

### Nginx Configuration

No special email configuration needed in Nginx. Emails send directly from Node.js application via SMTP.

### Firewall Rules

Ensure outbound SMTP ports are open:
```bash
# Check if port 465 is accessible
telnet smtp.resend.com 465

# Check if port 587 is accessible
telnet smtp.resend.com 587
```

If blocked, contact hosting provider.

---

## Debugging Checklist

When emails don't send:

1. **Check Domain Verification**
   - Visit Resend dashboard
   - Verify domain shows green checkmark
   - Check DNS records: `dig TXT example.com`

2. **Verify API Key**
   - Check format: starts with `re_`
   - Verify not expired/deleted in Resend
   - Test with direct SMTP connection

3. **Check Environment Variables**
   - Add file logging to verify runtime values
   - Check PM2 environment: `pm2 show app-name`
   - Verify `.env` and `ecosystem.config.js` match

4. **Check Application Logs**
   - PM2 logs: `pm2 logs app-name --lines 100`
   - Application logs: `tail -f /var/www/app-name/*.log`
   - Check for SMTP errors

5. **Test Direct SMTP**
   - Create test script with nodemailer
   - Test with same credentials
   - Isolate application vs SMTP issue

6. **Verify Resend Dashboard**
   - Check https://resend.com/emails
   - Look for error messages
   - Verify delivery status

---

## Quick Commands Reference

```bash
# Add domain to Resend (via dashboard)
https://resend.com/domains → Add Domain

# Update project configuration
nano /var/www/project-name/.env
nano /var/www/project-name/ecosystem.config.js

# Deploy changes
pm2 delete project-name
pm2 start /var/www/project-name/ecosystem.config.js
pm2 save

# Test email
curl -X POST http://localhost:PORT/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","message":"Test"}'

# Check logs
pm2 logs project-name --lines 50
tail -f /var/www/project-name/*.log

# Verify Resend
https://resend.com/emails
```

---

## Template Files

### `.env` Template
```bash
# Resend Email Configuration
USE_RESEND=true
RESEND_API_KEY=re_your_api_key_here
EMAIL_FROM=noreply@example.com
EMAIL_TO=info@example.com
SMTP_FROM=noreply@example.com
EMAIL_MODE=production
NODE_ENV=production
```

### `ecosystem.config.js` Template
```javascript
module.exports = {
  apps: [{
    name: 'project-name',
    script: 'npm',
    args: 'start',
    cwd: '/var/www/project-name',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      
      // Resend Email
      USE_RESEND: 'true',
      RESEND_API_KEY: 're_your_api_key',
      EMAIL_FROM: 'noreply@example.com',
      EMAIL_TO: 'info@example.com',
      SMTP_FROM: 'noreply@example.com',
      EMAIL_MODE: 'production'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
}
```

### `lib/email.ts` Template
```typescript
import nodemailer from 'nodemailer';

function getTransporter(): nodemailer.Transporter {
  const USE_RESEND = process.env.USE_RESEND === 'true';
  const RESEND_API_KEY = process.env.RESEND_API_KEY;
  
  if (USE_RESEND && RESEND_API_KEY) {
    return nodemailer.createTransport({
      host: 'smtp.resend.com',
      port: 465,
      secure: true,
      auth: {
        user: 'resend',
        pass: RESEND_API_KEY
      }
    });
  }
  
  throw new Error('Email not configured');
}

export async function sendEmail(to: string, subject: string, html: string) {
  const transporter = getTransporter();
  const from = process.env.EMAIL_FROM || 'noreply@example.com';
  
  await transporter.sendMail({ from, to, subject, html });
}
```

---

## Best Practices

1. ✅ **One Resend account per domain** (or use subdomains)
2. ✅ **Separate API keys for staging/production**
3. ✅ **Keep configuration files in sync**
4. ✅ **Use runtime pattern for environment variables**
5. ✅ **Test after every deployment**
6. ✅ **Monitor Resend dashboard regularly**
7. ✅ **Keep PM2 configs in version control** (exclude API keys)
8. ✅ **Document domain verification for each project**
9. ✅ **Use file-based logging for debugging**
10. ✅ **Full PM2 restart after config changes**

---

## Related Documentation

- [Complete Resend Setup Guide](../Resend/Complete-Setup-Guide.md)
- [Next.js Environment Variables Guide](../Next.js/Environment-Variables-Critical-Guide.md)
- [Multi-Tenant Server Setup](./Server-Setup-Guide.md)

---

**Last Updated**: 2025-10-29  
**Verified**: Innovation Forge Website production deployment

