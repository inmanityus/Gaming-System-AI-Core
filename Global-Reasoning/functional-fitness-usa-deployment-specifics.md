---
type: reasoning
category: deployment
project: functional-fitness-usa
component: production-deployment
created: 2025-10-15
updated: 2025-10-20
status: active
confidence: high
related: [deployment-patterns-multi-tenant, command-execution-patterns]
tags: [aws-ec2, nextjs, postgresql, email-integration, production]
source: local-project-memory
---

# Functional Fitness USA Deployment - Project-Specific Reasoning

**Source**: Merged from local `.project-memory/reasoning/production-deployment-learnings.md` on 2025-10-20  
**Purpose**: Complement global deployment patterns with Functional Fitness USA specific details

> **Important**: The global repository contains more recent and comprehensive deployment patterns (October 18-19, 2025). This document captures project-specific learnings from an earlier deployment (October 15, 2025) that provide additional context and details.

---

## Key Learnings Summary

This deployment to AWS EC2 Ubuntu 22.04 provided valuable insights that informed the more comprehensive global deployment patterns. Many learnings here were generalized and incorporated into:
- `deployment-patterns-multi-tenant.md` (architectural patterns)
- `command-execution-patterns.md` (command safety)
- Global-Docs deployment guides

---

## PostgreSQL Authentication - Critical Learning

### The Discovery
Initial deployment struggled with PostgreSQL password authentication. After testing multiple methods (peer, md5, scram-sha-256), discovered that **trust authentication for localhost** is the most reliable approach.

### Why This Matters
- **Secure**: Only localhost processes can connect
- **Simple**: No password complexity issues
- **Reliable**: No hash mismatch errors
- **Fast**: No encryption overhead

### Configuration
```conf
# /etc/postgresql/14/main/pg_hba.conf
host    all    all    127.0.0.1/32    trust
```

**Reasoning**: On a properly secured server where PostgreSQL port 5432 is NOT exposed externally, trust authentication for localhost connections provides the optimal balance of security, simplicity, and reliability.

---

## Email System Journey - From Postfix to AWS SES

### Stage 1: Local Postfix (Failed)
**Attempt**: Use Postfix on localhost:25
**Result**: AWS blocks outbound port 25
**Learning**: Never rely on port 25 for production email on AWS

### Stage 2: AWS SES via SMTP (Success)
**Configuration**:
- Host: `email-smtp.us-east-1.amazonaws.com`
- Port: 587 (STARTTLS)
- Auth: AWS Access Key + converted SMTP password

**Critical Detail**: Port 587 requires:
```javascript
{
  port: 587,
  secure: false,  // FALSE for STARTTLS
  requireTLS: true // REQUIRED for STARTTLS
}
```

### Why This Architecture?
AWS blocks port 25 at the infrastructure level. Port 587 with STARTTLS is the only reliable option for email delivery from EC2 instances.

---

## Environment Variable Architecture

### The Three-Tier Strategy

#### Tier 1: Global Infrastructure (`/etc/environment`)
**For**: Credentials shared across all sites on server
```bash
export PGPASSWORD=Inn0vat1on!
AWS_SES_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
AWS_SES_SMTP_USER=AKIA...
TWILIO_ACCOUNT_SID=AC...
```

#### Tier 2: Project-Specific (`.env.local`)
**For**: Site-unique configurations
```bash
DB_NAME=funfitusa
TWILIO_PHONE_NUMBER=+17208189223
SMTP_FROM=noreply@functionalfitnessusa.com
NEXT_PUBLIC_BASE_URL=https://98.89.40.81
```

#### Tier 3: PM2 Explicit (`ecosystem.config.js`)
**For**: Ensuring variables are loaded (belt and suspenders)
```javascript
env: {
  NODE_ENV: "production",
  PORT: 5000,
  DB_PASSWORD: process.env.PGPASSWORD,
  SMTP_HOST: process.env.AWS_SES_SMTP_HOST,
  // ... explicit setting of all critical vars
}
```

### Reasoning Behind Three Tiers
1. **Global**: Share infrastructure credentials across sites
2. **Local**: Customize per project
3. **Explicit**: Ensure PM2 has everything (doesn't always inherit `/etc/environment`)

---

## Next.js Production Insights

### NEXT_PUBLIC_ Variables Must Be Set Before Build
**Discovery**: Variables prefixed with `NEXT_PUBLIC_` are baked into the build at compile time.

**Wrong Sequence**:
```bash
npm run build  # Build without variable
export NEXT_PUBLIC_VAR=value  # Too late!
pm2 start
```

**Correct Sequence**:
```bash
export NEXT_PUBLIC_VAR=value  # Set first
npm run build  # Bakes variable into build
pm2 start  # Uses built code with variable
```

### Why?
Next.js replaces `process.env.NEXT_PUBLIC_*` references with literal values at build time for client-side code. This is a static replacement, not runtime lookup.

---

## Database Schema - Array Type Compatibility

### The Issue
Query using `ARRAY[]::varchar[]` failed in COALESCE with ARRAY_AGG context.

### The Fix
```sql
-- WRONG
COALESCE(ARRAY_AGG(column), ARRAY[]::varchar[])

-- RIGHT
COALESCE(ARRAY_AGG(column), ARRAY[]::text[])
```

### Reasoning
`text[]` is PostgreSQL's canonical array type. `varchar[]` works in some contexts but not universally. Always use `text[]` for maximum compatibility.

---

## PM2 Environment Reload

### The Problem
Changing `.env.local` and running `pm2 restart app` didn't pick up new values.

### The Solution
```bash
# Option 1: Force environment reload
pm2 restart app --update-env

# Option 2: Full reset (most reliable)
pm2 delete app
pm2 start ecosystem.config.js
```

### Why?
PM2 caches environment variables at process start. Simple restart reuses cached values. Must explicitly tell PM2 to reload environment.

---

## AWS Infrastructure Constraints

### Port 25 Blocking
**Reality**: AWS blocks outbound port 25 on ALL EC2 instances
**Why**: Anti-spam measure
**Cannot be changed**: Requests are rarely approved
**Solution**: Use port 587 (SMTP with STARTTLS)

### Security Group Best Practices
**Inbound**:
- Port 22 (SSH): Your IP only
- Port 80/443 (HTTP/HTTPS): 0.0.0.0/0
- Port 5432 (PostgreSQL): NOT in security group (localhost only)

**Outbound**:
- Port 25: Blocked by AWS (infrastructure level)
- Port 587: Open (use for SMTP)
- Port 443: Open (HTTPS)

---

## Email Deliverability - DNS is Critical

### Without DNS Records
- 70-90% of emails go to spam
- Recipients see "unverified sender" warnings
- Domain reputation suffers

### With Complete DNS Configuration
- 90-95% inbox delivery
- Professional appearance
- Better engagement

### Required Records (Priority Order)
1. **SPF** (Most Important): Authorizes AWS SES
2. **DKIM** (Very Important): Cryptographic signing
3. **Domain Verification** (Required): Proves ownership
4. **DMARC** (Important): Policy for failed auth

---

## Case Sensitivity - Linux vs Windows

### The Problem
Code developed on Windows, deployed to Linux.

**Example**:
- Code: `<img src="/images/Logo.png" />`
- File: `/images/logo.png`
- Windows: Works (case-insensitive)
- Linux: 404 (case-sensitive)

### The Fix
```bash
# Create case-preserving symlink
ln -sf logo.png Logo.png
```

### Best Practice
Use lowercase for all filenames to avoid cross-platform issues.

---

## Debugging Techniques That Worked

### Email Failures
1. Check PM2 logs: `pm2 logs app --err`
2. Look for specific errors:
   - "self-signed certificate" → Add `tls: { rejectUnauthorized: false }`
   - "wrong version number" → Wrong port or secure setting
   - "Email not verified" → AWS SES sandbox mode
   - "Connection timeout" → Port 25 blocked

### Database Failures
1. Check auth method: `cat /etc/postgresql/14/main/pg_hba.conf`
2. Test connection: `psql -h 127.0.0.1 -U postgres -d dbname`
3. Verify password hash: `SELECT rolpassword FROM pg_authid WHERE rolname='postgres'`

### Environment Variable Issues
1. Check if loaded: `pm2 env 0 | grep VAR_NAME`
2. Restart properly: `pm2 delete app && pm2 start ecosystem.config.js`
3. For NEXT_PUBLIC: Must rebuild

---

## Architectural Decisions - Rationale

### Decision 1: Trust Auth for PostgreSQL Localhost
**Rationale**: 
- Server properly secured (port 5432 not exposed)
- Trust auth is simple, fast, reliable
- No password maintenance overhead
- Secure because localhost-only

### Decision 2: AWS SES Over Postfix
**Rationale**:
- AWS blocks port 25 (no choice)
- SES has better deliverability
- Free tier sufficient (62k emails/month)
- Professional DNS records

### Decision 3: Three-Tier Environment Variables
**Rationale**:
- Share infrastructure creds globally
- Customize per project as needed
- Explicit in PM2 for reliability
- Clear separation of concerns

### Decision 4: Disable reCAPTCHA for IP Testing
**Rationale**:
- reCAPTCHA requires domain
- IP address testing comes first
- Can enable later after domain configured
- Allows form testing immediately

---

## Performance & Cost Optimization

### EC2 Instance Sizing
- **t3.small**: $30/month, sufficient for single site
- **t3.medium**: $60/month, multiple sites or high traffic
- **Strategy**: Start small, upgrade as needed (no downtime)

### Email Costs
- **AWS SES**: $0.10 per 1,000 emails (after free 62k/month)
- **Extremely cost-effective** for transactional email
- No monthly fee

### Storage Management
- **30GB EBS**: Sufficient for most sites
- **Monitor**: `df -h` regularly
- **Cleanup**: Old logs, temp files, old builds

---

## Security Best Practices Applied

1. **Never Expose Database Port**: 5432 not in security group
2. **Use Environment Variables**: No hardcoded secrets
3. **Role-Based Access**: Admin vs member roles
4. **HTTPS Always**: Even with self-signed for testing
5. **Log Monitoring**: Check logs after every deployment

---

## Lessons Learned (What NOT to Do)

❌ Don't set PostgreSQL password with wrong pg_hba.conf method  
❌ Don't use port 25 for production on AWS  
❌ Don't forget to rebuild after NEXT_PUBLIC_ changes  
❌ Don't use `secure: true` for port 587 (it's STARTTLS)  
❌ Don't assume `/etc/environment` loads in PM2  
❌ Don't skip DNS records (emails will go to spam)  

---

## Critical Success Factors

**What Made This Work**:
1. Trust authentication for PostgreSQL
2. AWS SES instead of Postfix
3. Explicit environment variables in PM2
4. STARTTLS configuration (not direct SSL)
5. Disabling reCAPTCHA for IP testing
6. Iterative debugging with logs
7. Global variable architecture

**What Would Have Failed**:
- Password auth with hash mismatches
- Relying on port 25 (AWS blocks it)
- Not converting Secret Key to SMTP password
- Using `secure: true` for port 587
- Not checking SES sandbox mode
- Hardcoding configurations

---

## Comparison with Global Patterns

This deployment occurred on **October 15, 2025**. The learnings here informed more comprehensive global documentation created **October 18-19, 2025**:

- **Global**: `deployment-patterns-multi-tenant.md` - Generalized architectural patterns
- **This**: Project-specific implementation details

**Key Contributions to Global Knowledge**:
1. Trust authentication pattern for PostgreSQL
2. Three-tier environment variable strategy
3. STARTTLS configuration specifics
4. PM2 environment reload techniques

---

## Cross-References

**Superseded By** (More Recent Global Docs):
- `Global-Reasoning/deployment-patterns-multi-tenant.md` (Oct 19, 2025)
- `Global-Reasoning/command-execution-patterns.md` (Oct 18, 2025)
- `Global-History/2025-10-19-innovation-forge-deployment.md`

**Related Local Memory**:
- `.project-memory/reasoning/startup-script-design.md`
- `.project-memory/history/2025-10-12-startup-cleanup.md`

---

**Note**: This document preserves project-specific deployment details from an earlier deployment. For the most current and comprehensive deployment patterns, refer to the global reasoning documents dated October 18-19, 2025, which incorporate and expand upon these learnings.

**Status**: Historical reference with valuable project-specific details  
**Confidence**: High (production-tested)  
**Reusability**: Medium (specific to this project, but patterns generalized in global docs)

