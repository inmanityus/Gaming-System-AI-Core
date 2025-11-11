# Next.js Environment Variables - Critical Guide

## 🚨 Critical Lessons Learned

This guide documents critical lessons learned from debugging a production email system that appeared to have correct environment variables but was using cached/wrong values at runtime.

---

## The Problem: Build-Time vs Runtime Environment Variables

### What Happened
- `.env` and `ecosystem.config.js` were updated with correct values
- PM2 was restarted with `pm2 restart --update-env`
- Application still used OLD cached values
- **Root Cause**: Next.js bundles environment variables at BUILD TIME, and PM2 caches configuration

### The Solution
```bash
# ❌ WRONG - This doesn't reload PM2 environment variables
pm2 restart app-name --update-env

# ✅ CORRECT - Full restart loads fresh configuration
pm2 delete app-name
pm2 start ecosystem.config.js
```

---

## Critical Next.js Environment Variable Rules

### 1. **Module-Level Initialization is DANGEROUS**

#### ❌ BAD - Reads env vars at build/module load time:
```typescript
// lib/email.ts
const EMAIL_FROM = process.env.EMAIL_FROM || 'fallback@example.com';
const transporter = nodemailer.createTransport({ /* ... */ });

export function sendEmail() {
  // EMAIL_FROM is frozen with BUILD-TIME or MODULE-LOAD-TIME value
  await transporter.sendMail({ from: EMAIL_FROM });
}
```

**Why this fails:**
- `EMAIL_FROM` is evaluated when the module loads
- PM2 environment variables may not be available yet
- Changing PM2 config and restarting doesn't update the cached value
- The value is "frozen" in the built bundle

#### ✅ GOOD - Reads env vars at runtime:
```typescript
// lib/email.ts
function getTransporter() {
  // ✅ Evaluated EVERY TIME function is called
  const EMAIL_FROM = process.env.EMAIL_FROM || 'fallback@example.com';
  
  return nodemailer.createTransport({
    // config using runtime env vars
  });
}

export function sendEmail() {
  const transporter = getTransporter(); // Fresh env vars every time
  await transporter.sendMail({ from: process.env.EMAIL_FROM });
}
```

**Why this works:**
- Environment variables are read when the function executes
- PM2 environment variables are available at runtime
- Restarting PM2 loads new values
- No caching issues

---

### 2. **Hardcoded Fallbacks are DANGEROUS**

#### ❌ BAD - Wrong domain persists even after config changes:
```typescript
const EMAIL_FROM = process.env.EMAIL_FROM || 'noreply@wrongdomain.com';
```

**The problem:**
- If `process.env.EMAIL_FROM` is undefined (even temporarily), fallback is used
- Fallback domain might not be verified in email service
- Very difficult to debug because it "looks correct" in config files

#### ✅ GOOD - Use the CORRECT domain in fallbacks:
```typescript
const EMAIL_FROM = process.env.EMAIL_FROM || 'noreply@correctdomain.com';
```

#### ✅ BETTER - Fail fast if missing:
```typescript
const EMAIL_FROM = process.env.EMAIL_FROM;
if (!EMAIL_FROM) {
  throw new Error('EMAIL_FROM environment variable is required');
}
```

---

### 3. **PM2 Environment Variable Priority**

PM2 loads environment variables in this order (last wins):
1. System environment variables (`/etc/environment`, shell)
2. `.env` file in project directory
3. `ecosystem.config.js` `env` section ⭐ **HIGHEST PRIORITY**

#### Example:
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'my-app',
    script: 'npm',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      EMAIL_FROM: 'noreply@example.com',  // ⭐ This overrides .env
      EMAIL_TO: 'info@example.com'
    }
  }]
}
```

**Critical Rules:**
- Always keep `ecosystem.config.js` and `.env` in sync
- When changing email domains, update BOTH files
- After updating, use `pm2 delete` + `pm2 start` (not just restart)

---

## Debugging Environment Variables

### Add Runtime Logging

Always add logging to verify environment variables at runtime:

```typescript
function getEmailConfig() {
  const config = {
    from: process.env.EMAIL_FROM || 'fallback@example.com',
    to: process.env.EMAIL_TO || 'admin@example.com'
  };
  
  // ✅ Log at runtime to verify actual values
  console.log('[EMAIL CONFIG - RUNTIME]', {
    from: config.from,
    to: config.to,
    EMAIL_FROM_env: process.env.EMAIL_FROM || 'undefined',
    EMAIL_TO_env: process.env.EMAIL_TO || 'undefined'
  });
  
  return config;
}
```

### File-Based Logging in Production

`console.log()` is often suppressed in Next.js production. Use file logging:

```typescript
import * as fs from 'fs';
import * as path from 'path';

const LOG_FILE = path.join(process.cwd(), 'runtime-debug.log');

function fileLog(message: string) {
  try {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(LOG_FILE, `[${timestamp}] ${message}\n`);
  } catch (error) {
    // Silently fail if logging fails
  }
}

function sendEmail() {
  fileLog('EMAIL_FROM: ' + process.env.EMAIL_FROM);
  fileLog('EMAIL_TO: ' + process.env.EMAIL_TO);
  // ... send email
}
```

---

## Next.js Build Process and Environment Variables

### Build-Time Variables
These are **frozen** into the bundle at build time:
- Any `process.env.NEXT_PUBLIC_*` variables
- Any environment variable accessed at the module level
- Fallback values in `||` expressions at module level

### Runtime Variables
These are evaluated when code runs:
- Environment variables inside functions
- Variables accessed in API routes
- Variables in server components (when called)

### Example:
```typescript
// ❌ BUILD-TIME - Frozen at build
const API_KEY = process.env.API_KEY;

// ✅ RUNTIME - Evaluated when function runs
function getApiKey() {
  return process.env.API_KEY;
}

// ❌ BUILD-TIME - Frozen at build
export default function Component() {
  const url = process.env.NEXT_PUBLIC_URL; // Bundled into client code
}

// ✅ RUNTIME - Evaluated on server
export default async function Page() {
  const data = await fetch(process.env.API_URL); // Server-side only
}
```

---

## Complete PM2 Deployment Checklist

When deploying Next.js apps with PM2:

### 1. **Update Configuration Files**
```bash
# Update .env
nano .env

# Update ecosystem.config.js
nano ecosystem.config.js

# ✅ Ensure domains/emails match in BOTH files
```

### 2. **Build Application**
```bash
npm run build
```

### 3. **Deploy Build**
```bash
scp -r .next/ server:/path/to/app/
```

### 4. **Restart PM2 Properly**
```bash
# ❌ WRONG - Doesn't reload config from ecosystem.config.js
pm2 restart app-name --update-env

# ✅ CORRECT - Full restart with fresh config
pm2 delete app-name
pm2 start ecosystem.config.js

# Verify it's running
pm2 list
```

### 5. **Verify Environment Variables**
```bash
# Check PM2 process environment
pm2 show app-name

# Test with curl and check logs
curl -X POST http://localhost:PORT/api/endpoint

# Check application logs
tail -f /path/to/app/debug.log
```

---

## Common Pitfalls

### Pitfall 1: "pm2 restart --update-env" Doesn't Work
**Problem**: Only reloads system environment, not `ecosystem.config.js`  
**Solution**: Use `pm2 delete` + `pm2 start`

### Pitfall 2: Old Values Persist After Config Update
**Problem**: Module-level initialization caches values  
**Solution**: Move env var access into functions

### Pitfall 3: Works Locally, Fails in Production
**Problem**: Different environment variable loading in dev vs production  
**Solution**: Use runtime access pattern for consistency

### Pitfall 4: Hardcoded Fallbacks with Wrong Domain
**Problem**: Fallback domain doesn't match verified domain in email service  
**Solution**: Update ALL fallbacks when changing domains

### Pitfall 5: Can't Debug Without Logs
**Problem**: `console.log()` suppressed in production  
**Solution**: Use file-based logging for debugging

---

## Best Practices Summary

1. ✅ **Read environment variables inside functions**, not at module level
2. ✅ **Use `pm2 delete` + `pm2 start`** for configuration changes
3. ✅ **Keep `.env` and `ecosystem.config.js` in sync**
4. ✅ **Use file-based logging** for production debugging
5. ✅ **Verify fallback domains** match your email service
6. ✅ **Add runtime logging** to verify env vars are loaded
7. ✅ **Test after deployment** with curl/API calls
8. ✅ **Check actual values at runtime**, not just config files

---

## Quick Reference Commands

```bash
# ✅ Proper PM2 restart sequence
pm2 delete app-name
pm2 start ecosystem.config.js
pm2 save

# Check process details
pm2 show app-name

# View logs
pm2 logs app-name --lines 50

# Test API endpoint
curl -X POST http://localhost:PORT/api/test \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'

# Check application log files
tail -f /path/to/app/*.log
```

---

## Related Issues to Watch For

- Email service domain verification
- SMTP authentication failures
- DNS/MX record configuration
- Rate limiting on email services
- Timezone issues with timestamps
- Character encoding in email content

---

**Last Updated**: 2025-10-29  
**Verified With**: Next.js 14.x, PM2 5.x, Node.js 20.x

