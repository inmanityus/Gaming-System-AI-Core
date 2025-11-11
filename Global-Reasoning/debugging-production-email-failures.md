# Reasoning Framework: Debugging Production Email Failures

**Framework ID**: email-failure-diagnosis  
**Category**: Systematic Debugging  
**Applicable To**: Email systems, API integrations, External services  
**Complexity**: Medium

---

## Problem Recognition

Email system reports success but emails don't arrive. Symptoms:
- API returns 200/success
- Database shows entries
- Application logs show "success"
- Emails never delivered
- External service dashboard shows no activity

---

## Reasoning Approach

### Phase 1: Establish Visibility

**Problem**: Can't debug what you can't see.

**Actions**:
1. Add comprehensive logging at EVERY step
2. Use file-based logging (console.log often suppressed in production)
3. Log inputs, outputs, and intermediate states
4. Include timestamps and request IDs

**Why**: Production environments often suppress console output. File logs persist and can be reviewed.

```typescript
// Add file logging
const LOG_FILE = path.join(process.cwd(), 'debug.log');
function fileLog(msg: string) {
  fs.appendFileSync(LOG_FILE, `[${new Date().toISOString()}] ${msg}\n`);
}

// Log EVERYTHING
fileLog('Step 1: Received request');
fileLog('Step 2: Validated input');
fileLog('Step 3: Calling email service...');
fileLog('Step 4: Email service response: ' + JSON.stringify(response));
```

---

### Phase 2: Verify Configuration Chain

**Problem**: Configuration loaded from multiple sources with precedence rules.

**Actions**:
1. **Trace configuration loading**
   - Where are values defined? (.env, ecosystem.config.js, system env)
   - What's the precedence? (ecosystem.config.js > .env > system)
   - Are values what you expect?

2. **Log runtime values**
   ```typescript
   fileLog('EMAIL_FROM: ' + process.env.EMAIL_FROM);
   fileLog('RESEND_API_KEY: ' + (process.env.RESEND_API_KEY ? 'SET' : 'MISSING'));
   ```

3. **Check for cached values**
   - Is config read at build time? (module level)
   - Is config read at runtime? (inside functions)
   - Does restart load new values?

**Why**: Configuration errors are often invisible. Values appear correct in files but wrong at runtime.

---

### Phase 3: Isolate the Failure Point

**Problem**: Email flow has many steps - which one fails?

**Actions**:
1. **Test each layer separately**
   ```
   Application → Library → SMTP → Service → Delivery
   ```

2. **Create isolation tests**
   - Direct SMTP test (bypass application)
   - Direct API test (bypass UI)
   - Mock service test (bypass network)

3. **Binary search through stack**
   - If direct SMTP works → Problem in application layer
   - If direct SMTP fails → Problem in SMTP/service layer

**Example**: Direct SMTP test script
```javascript
const nodemailer = require('nodemailer');
const transporter = nodemailer.createTransporter({
  host: 'smtp.resend.com',
  port: 465,
  secure: true,
  auth: { user: 'resend', pass: process.env.RESEND_API_KEY },
  debug: true  // ← Show full SMTP conversation
});

transporter.sendMail({
  from: 'noreply@example.com',
  to: 'test@example.com',
  subject: 'Direct Test',
  text: 'Testing SMTP directly'
}).then(info => console.log('✅', info))
  .catch(err => console.error('❌', err));
```

**Why**: Isolating layers reveals whether problem is in code, configuration, network, or service.

---

### Phase 4: Verify External Service State

**Problem**: Service may have restrictions or validation we're not aware of.

**Actions**:
1. **Check service dashboard**
   - Are requests reaching the service?
   - What errors does service report?
   - Are there rate limits or quotas?

2. **Verify service configuration**
   - Domain verification status
   - API key validity
   - Account status/billing

3. **Check service requirements**
   - Domain matching rules (Resend)
   - DNS records (SPF, DKIM, DMARC)
   - Sender reputation

**Why**: Services have their own validation that may silently fail.

---

### Phase 5: Check Environment-Specific Behavior

**Problem**: Behavior differs between environments.

**Actions**:
1. **Compare environments**
   - Development works but production fails?
   - Local works but server fails?
   - One project works but another fails?

2. **Check environment variables**
   ```bash
   # Development
   echo $EMAIL_FROM  # → noreply@example.ai

   # Production
   pm2 show app | grep EMAIL_FROM  # → noreply@example.com (wrong!)
   ```

3. **Verify process manager state**
   - PM2: Are env vars loaded from correct config?
   - Docker: Are env vars passed to container?
   - Systemd: Are env vars in service file?

**Why**: Environment-specific configuration is common failure point.

---

## Decision Tree

```
Email not arriving?
├─ Are requests reaching API?
│  ├─ NO → Check client-side, network, CORS
│  └─ YES → Continue
│
├─ Does API log show success?
│  ├─ NO → Fix API errors first
│  └─ YES → Continue
│
├─ Are logs visible for email sending?
│  ├─ NO → Add file-based logging
│  └─ YES → Continue
│
├─ Does direct SMTP test work?
│  ├─ NO → Problem with SMTP/service (check credentials, domain)
│  └─ YES → Problem with application (check code, runtime values)
│
├─ Does service dashboard show requests?
│  ├─ NO → Requests not reaching service (check connection, auth)
│  └─ YES → Check service error messages
│
└─ Service error present?
   ├─ "450 Not authorized" → Domain mismatch
   ├─ "Missing credentials" → Env vars not loaded
   ├─ "Rate limit" → Too many requests
   └─ Other → Check service docs
```

---

## Common Patterns

### Pattern 1: Domain Mismatch
- **Symptom**: 450/451 error, "not authorized"
- **Cause**: Email domain ≠ verified domain
- **Fix**: Update ALL email addresses to match verified domain

### Pattern 2: Cached Configuration
- **Symptom**: Config looks right but uses old values
- **Cause**: Module-level initialization or PM2 cache
- **Fix**: Runtime pattern + full PM2 restart

### Pattern 3: Silent Failure
- **Symptom**: No errors, no emails
- **Cause**: Try-catch swallowing errors
- **Fix**: Log errors before swallowing, check external service

### Pattern 4: Environment Variable Undefined
- **Symptom**: Using fallback values unexpectedly
- **Cause**: PM2 not loading ecosystem.config.js
- **Fix**: Full PM2 restart (delete + start)

---

## Debugging Toolkit

### Essential Commands
```bash
# Check PM2 environment
pm2 show app-name

# View application logs
pm2 logs app-name --lines 100
tail -f /path/to/app/debug.log

# Test email directly
node test-smtp-direct.js

# Check DNS records
dig TXT example.com
dig MX example.com

# Test SMTP connection
telnet smtp.resend.com 465
```

### Essential Code
```typescript
// File logging
const LOG_FILE = path.join(process.cwd(), 'email-debug.log');
function fileLog(msg: string) {
  fs.appendFileSync(LOG_FILE, `[${new Date().toISOString()}] ${msg}\n`);
}

// Runtime env check
fileLog('EMAIL_FROM: ' + process.env.EMAIL_FROM);
fileLog('API_KEY: ' + (process.env.API_KEY ? 'SET' : 'MISSING'));

// Detailed error logging
try {
  await sendEmail();
} catch (error) {
  fileLog('ERROR: ' + error.message);
  fileLog('STACK: ' + error.stack);
  fileLog('FULL: ' + JSON.stringify(error, null, 2));
  throw error;
}
```

---

## Meta-Reasoning

### When to Stop Investigating
- ✅ Root cause identified and documented
- ✅ Fix implemented and tested
- ✅ Prevention measures in place
- ✅ Learning captured for future

### When to Escalate
- Service is down (check status page)
- Account issue (contact support)
- Network/firewall issue (contact ops)

### When to Pivot Approach
- After 30 min with no progress → Try isolation test
- After isolation works → Problem is in integration
- After multiple failed attempts → Check assumptions

---

## Success Criteria

Debugging is complete when:
1. ✅ Emails arrive successfully
2. ✅ Service dashboard shows delivered status
3. ✅ Logs show complete flow
4. ✅ Test cases pass
5. ✅ Root cause documented
6. ✅ Prevention measures documented

---

## Related Frameworks

- Configuration debugging → See Global-Reasoning/config-troubleshooting.md
- Production monitoring → See Global-Reasoning/production-observability.md

---

**Application**: Email, SMS, Push notifications, External APIs  
**Outcome**: Systematic isolation and resolution  
**Time**: Typically 1-2 hours with this framework vs 4+ hours ad-hoc

