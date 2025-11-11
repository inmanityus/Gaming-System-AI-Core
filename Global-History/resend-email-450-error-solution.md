# Solution: Resend Email "450 Not Authorized" Error

**Issue ID**: resend-450-not-authorized  
**Date Solved**: October 29, 2025  
**Project**: Innovation Forge Website  
**Severity**: Critical - Email delivery failure

---

## Problem Statement

Email sending fails with error:
```
450 Not authorized to send emails from domain.com
```

Application returns success but emails never arrive. Resend dashboard shows no activity.

---

## Root Cause

**Domain mismatch** between:
- Email address in application: `noreply@innovationforge.com`
- Verified domain in Resend: `innovationforge.ai`

Resend **requires exact domain match** between verified domain and email sender address.

---

## Solution

1. **Identify verified domain** in Resend dashboard (https://resend.com/domains)
2. **Update ALL email addresses** to match verified domain:
   - Configuration files (`.env`, `ecosystem.config.js`)
   - Code fallback values (`lib/email.ts`)
   - Any hardcoded addresses
3. **Rebuild application** (`npm run build`)
4. **Full PM2 restart**: `pm2 delete app && pm2 start ecosystem.config.js`
5. **Test and verify** in Resend dashboard

---

## Critical Details

### Email Domain Must Match Exactly
```
✅ CORRECT:
Verified Domain: example.com
Email Address: noreply@example.com

❌ WRONG:
Verified Domain: example.com  
Email Address: noreply@example.org  ← Different domain!
```

### Update Locations
1. `.env` file
2. `ecosystem.config.js` (PM2 config)
3. Code fallback values
4. Any hardcoded strings

### Deployment Procedure
```bash
# Build
npm run build

# Deploy
tar -czf build.tar.gz .next
scp build.tar.gz server:~/

# On server
tar -xzf build.tar.gz
pm2 delete app-name
pm2 start ecosystem.config.js
pm2 save
```

---

## Verification

1. Test with curl/API call
2. Check Resend dashboard for emails
3. Verify "Delivered" status
4. Confirm correct sender domain

---

## Related Issues

- Environment variables not loading → See Global-History/pm2-env-vars-not-loading.md
- Module-level initialization → See Global-History/nextjs-build-time-freeze.md

---

**Status**: ✅ Resolved  
**Applicable To**: Any Resend email integration  
**Prevention**: Always verify domain matches before deployment

