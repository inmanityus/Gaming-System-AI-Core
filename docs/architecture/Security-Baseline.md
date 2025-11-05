# Be Free Fitness - Security Baseline
**Version:** 1.0  
**Last Updated:** 2025-01-09  
**Scope:** Entire Platform (Admin, Extranet, API, Database)  
**Compliance:** OWASP Top 10 2021, GDPR, CCPA, HIPAA (if applicable)

---

## CRITICAL: Next.js CVE-2025-29927 Mitigation

**IMMEDIATE ACTION REQUIRED:**
- Upgrade Next.js to: ≥12.3.5, ≥13.5.9, ≥14.2.25, or ≥15.2.3
- Delete `x-middleware-subrequest` header at CDN/WAF and API entry points
- Never trust this header for authorization

---

## 1. Authentication Standards

### 1.1 Admin Authentication
```typescript
// 4-hour sessions, MFA required, max 2 concurrent
const ADMIN_AUTH_CONFIG = {
  sessionDuration: 4 * 60 * 60 * 1000, // 4 hours
  maxConcurrentSessions: 2,
  failedLoginLockout: 5,
  lockoutDuration: 30 * 60 * 1000, // 30 minutes
  requireMFA: true, // TOTP mandatory
  requireReauthForCriticalActions: true,
};
```

### 1.2 User Authentication
```typescript
// 30-day sessions, optional MFA
const USER_AUTH_CONFIG = {
  sessionDuration: 30 * 24 * 60 * 60 * 1000,
  maxConcurrentSessions: 5,
  failedLoginLockout: 10,
  lockoutDuration: 15 * 60 * 1000,
  requireMFA: false, // Optional for users
};
```

### 1.3 Password Requirements
- **Minimum:** 12 characters
- **Algorithm:** Argon2id (memoryCost: 19456, timeCost: 3, parallelism: 1)
- **Rotation:** Every 90 days
- **History:** Prevent reuse of last 5 passwords
- **Breach Check:** Validate against Have I Been Pwned API

```typescript
import argon2 from 'argon2';

async function hashPassword(plain: string): Promise<string> {
  return argon2.hash(plain, {
    type: argon2.argon2id,
    memoryCost: 19456,
    timeCost: 3,
    parallelism: 1,
  });
}
```

### 1.4 JWT Token Standards
```typescript
// Access Token (short-lived)
{
  sub: userId,
  tenant_id: tenantId,
  roles: ['admin'],
  scopes: ['users:write', 'broadcasts:create'],
  mfa: true,
  aud: 'api.befreefitness.com',
  iss: 'auth.befreefitness.com',
  iat: 1234567890,
  exp: 1234567890 + 600, // 10 minutes
  jti: 'unique-token-id'
}

// Algorithm: RS256 or ES256 (never HS256 with shared secret)
// Rotation: Signing keys rotated every 90 days
```

---

## 2. Authorization Patterns

### 2.1 RBAC Roles
- `super_admin` - Full system access
- `admin` - Admin portal access
- `moderator` - Content moderation only
- `email_manager` - Email template management
- `support_agent` - User support, read-only
- `trainer_manager` - Trainer operations
- `finance_admin` - Financial operations
- `content_manager` - Exercise/content management

### 2.2 ABAC Attributes
```typescript
interface AccessPolicy {
  role: string;
  dataClassification: 'public' | 'internal' | 'confidential' | 'restricted';
  geographicScope?: string[]; // ['US', 'EU']
  purposeLimitation: string[]; // ['support', 'billing', 'moderation']
  maxRecords?: number; // Bulk operation limits
}
```

### 2.3 Row-Level Security (PostgreSQL)
```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Set session variables per request
CREATE OR REPLACE FUNCTION app.current_admin_id() RETURNS UUID AS $$
  SELECT nullif(current_setting('app.admin_id', true), '')::UUID
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION app.current_admin_regions() RETURNS TEXT[] AS $$
  SELECT string_to_array(current_setting('app.admin_regions', true), ',')
$$ LANGUAGE SQL STABLE;

-- Policy: Regional access control
CREATE POLICY admin_regional_access ON users
  FOR ALL TO admin_app_user
  USING (
    region = ANY(app.current_admin_regions()) OR
    'all' = ANY(app.current_admin_regions())
  );
```

---

## 3. Input Validation

### 3.1 Fastify Schema Validation (AJV)
```typescript
import S from 'fluent-json-schema';

const createUserSchema = {
  body: S.object()
    .additionalProperties(false) // Reject unknown properties
    .prop('email', S.string().format('email').maxLength(255).required())
    .prop('firstName', S.string().minLength(1).maxLength(100).required())
    .prop('lastName', S.string().minLength(1).maxLength(100).required())
    .prop('phone', S.string().pattern(/^\+?[1-9]\d{1,14}$/))
};

fastify.post('/api/v1/users', { schema: createUserSchema }, handler);
```

### 3.2 HTML Sanitization
```typescript
import DOMPurify from 'isomorphic-dompurify';

// NEVER use dangerouslySetInnerHTML without sanitization
const sanitizeHTML = (dirty: string): string => {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'br'],
    ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onclick', 'onerror', 'onload'],
  });
};
```

### 3.3 SQL Injection Prevention
```typescript
// ALWAYS use parameterized queries
// ✅ CORRECT
await pool.query(
  'SELECT * FROM users WHERE email = $1 AND deleted_at IS NULL',
  [email]
);

// ❌ NEVER DO THIS
await pool.query(`SELECT * FROM users WHERE email = '${email}'`); // VULNERABLE!
```

---

## 4. Security Headers

### 4.1 Next.js Configuration
```javascript
// next.config.js
const securityHeaders = [
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'geolocation=(), microphone=(), camera=(), payment=()' },
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
  { key: 'Cross-Origin-Resource-Policy', value: 'same-origin' },
  { 
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'nonce-{NONCE}'",
      "style-src 'self' 'nonce-{NONCE}'",
      "img-src 'self' data: https://cdn.befreefitness.com",
      "connect-src 'self' https://api.befreefitness.com",
      "font-src 'self'",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests"
    ].join('; ')
  }
];

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },
};
```

### 4.2 Fastify Helmet Configuration
```typescript
import helmet from '@fastify/helmet';

fastify.register(helmet, {
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  frameguard: { action: 'deny' },
  noSniff: true,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
});

// Remove server identification
fastify.addHook('onSend', (req, reply, payload, done) => {
  reply.removeHeader('X-Powered-By');
  reply.removeHeader('Server');
  done();
});
```

---

## 5. Database Security (PostgreSQL)

### 5.1 SSL/TLS Configuration
```sql
-- postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
ssl_ca_file = '/path/to/ca.crt'
ssl_ciphers = 'HIGH:!aNULL:!MD5'
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'
```

```typescript
// Node.js client connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: true,
    ca: process.env.PG_CA_CERT,
  },
});
```

### 5.2 User & Role Security
```sql
-- Create limited privilege roles (NO superuser for apps)
CREATE ROLE admin_app_user WITH LOGIN PASSWORD '<from-secrets-manager>';
GRANT CONNECT ON DATABASE befreefitness TO admin_app_user;
GRANT USAGE ON SCHEMA public, app TO admin_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO admin_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO admin_app_user;

-- Revoke dangerous permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON pg_catalog.pg_authid FROM PUBLIC;
```

### 5.3 Connection Security (pg_hba.conf)
```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
hostssl befreefitness   admin_app_user  10.0.0.0/8             scram-sha-256
hostssl befreefitness   migrator        10.0.0.0/8             scram-sha-256
hostssl befreefitness   readonly        10.0.0.0/8             scram-sha-256

# Reject all others
hostnossl all           all             all                     reject
```

### 5.4 Audit Logging (pgAudit)
```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Configure in postgresql.conf
shared_preload_libraries = 'pgaudit,pg_stat_statements'
pgaudit.log = 'write, ddl, role, function'
pgaudit.log_parameter = on
log_connections = on
log_disconnections = on
log_duration = on
log_statement = 'ddl'
```

---

## 6. Secret Management

### 6.1 AWS Secrets Manager Integration
```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

class SecretsService {
  private client: SecretsManagerClient;
  private cache = new Map<string, { value: any; expires: number }>();
  
  async getSecret(secretName: string): Promise<any> {
    // Cache for 5 minutes
    const cached = this.cache.get(secretName);
    if (cached && cached.expires > Date.now()) {
      return cached.value;
    }
    
    const command = new GetSecretValueCommand({ SecretId: secretName });
    const response = await this.client.send(command);
    const value = JSON.parse(response.SecretString!);
    
    this.cache.set(secretName, {
      value,
      expires: Date.now() + 300000, // 5 min
    });
    
    return value;
  }
}

// Usage
const secrets = await secretsService.getSecret('prod/bff/api');
const dbUrl = secrets.DATABASE_URL;
const jwtPrivateKey = secrets.JWT_PRIVATE_KEY;
```

### 6.2 Secret Rotation
- **Frequency:** Every 90 days
- **Immediate:** On suspected compromise
- **Automated:** Lambda function triggered by Secrets Manager rotation

---

## 7. Rate Limiting

### 7.1 Global Limits
```typescript
import rateLimit from '@fastify/rate-limit';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

// Global rate limit
fastify.register(rateLimit, {
  max: 100, // requests
  timeWindow: '1 minute',
  cache: 10000,
  redis: redis,
  keyGenerator: (req) => req.user?.id || req.ip,
  errorResponseBuilder: (req, context) => ({
    error: 'Too Many Requests',
    limit: context.max,
    remaining: context.remaining,
    retryAfter: context.after,
  }),
});
```

### 7.2 Endpoint-Specific Limits
```typescript
const RATE_LIMITS = {
  '/admin/v1/auth/login': { max: 5, window: '1 minute' },
  '/admin/v1/users/search': { max: 30, window: '1 minute' },
  '/admin/v1/users/bulk-export': { max: 5, window: '1 hour', maxRecords: 100000 },
  '/admin/v1/broadcasts': { max: 10, window: '1 hour' },
  '/admin/v1/impersonation': { max: 5, window: '1 hour' },
};
```

---

## 8. Security Logging

### 8.1 Structured Logging (Pino)
```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  redact: {
    paths: [
      'req.headers.authorization',
      'req.headers.cookie',
      'res.headers["set-cookie"]',
      'req.body.password',
      '*.secret',
      '*.token',
    ],
    censor: '[REDACTED]',
  },
});

// Security event logging
logger.info({
  event: 'login_success',
  userId: user.id,
  ip: req.ip,
  userAgent: req.headers['user-agent'],
  mfa: true,
});
```

### 8.2 Audit Events (Must Log)
- login_success / login_failure
- mfa_challenge / mfa_failure
- token_refresh / token_revoked
- password_change / password_reset
- role_change / permission_change
- data_export / bulk_operation
- admin_action (any admin operation)
- impersonation_start / impersonation_end
- rate_limit_exceeded
- authorization_denied

---

## 9. OWASP Top 10 Mitigations

### A01: Broken Access Control
- ✅ RBAC + ABAC at API layer
- ✅ Row-Level Security in PostgreSQL
- ✅ Never trust client-provided roles
- ✅ Deny-by-default authorization
- ✅ Test for IDOR vulnerabilities

### A02: Cryptographic Failures
- ✅ HTTPS-only (TLS 1.3 preferred, 1.2 minimum)
- ✅ HSTS with preload
- ✅ Argon2id for passwords
- ✅ RS256/ES256 for JWTs
- ✅ Encrypted cookies (HttpOnly, Secure, SameSite=Strict)
- ✅ Secrets in Secrets Manager, never in code

### A03: Injection
- ✅ Parameterized SQL queries (never string concatenation)
- ✅ AJV schema validation for all inputs
- ✅ HTML sanitization (DOMPurify)
- ✅ CSP to block inline scripts
- ✅ No eval(), Function(), or dynamic code execution

### A04: Insecure Design
- ✅ Threat modeling per feature
- ✅ Secure defaults (deny-by-default)
- ✅ Rate limiting to prevent abuse
- ✅ Separation of admin and user contexts

### A05: Security Misconfiguration
- ✅ Hardened pg_hba.conf
- ✅ Security headers (CSP, HSTS, etc.)
- ✅ Remove X-Powered-By, Server headers
- ✅ Minimal container images, non-root user
- ✅ Production NODE_ENV=production

### A06: Vulnerable Components
- ✅ Automated dependency scanning (npm audit, Snyk)
- ✅ Lockfiles committed
- ✅ Regular updates (Next.js CVE-2025-29927 patched)
- ✅ Only maintained packages

### A07: Authentication Failures
- ✅ MFA for admins
- ✅ Account lockout (5 failures, 30 min)
- ✅ Refresh token rotation with reuse detection
- ✅ Short-lived access tokens (10 min)
- ✅ Secure session cookies
- ✅ CSRF tokens for state-changing operations

### A08: Data Integrity Failures
- ✅ Signed JWTs with jti
- ✅ Database constraints and foreign keys
- ✅ Checksums for backups
- ✅ Immutable audit logs

### A09: Logging/Monitoring Failures
- ✅ Centralized structured logging
- ✅ pgAudit for database
- ✅ Security event logging
- ✅ Alerting on anomalies
- ✅ Log retention per compliance

### A10: SSRF
- ✅ Whitelist allowed external URLs
- ✅ Block metadata IPs (169.254.169.254)
- ✅ Network egress restrictions
- ✅ Validate user-supplied URLs before fetching

---

## 10. Security Testing Checklist

### Pre-Deployment (Every Feature)
- [ ] Dependency scan passed (npm audit, Snyk)
- [ ] Next.js version patched for CVE-2025-29927
- [ ] ESLint security rules passed
- [ ] No hardcoded secrets (TruffleHog scan)
- [ ] Security headers present and correct
- [ ] CORS configured (no wildcards with credentials)
- [ ] Cookies: HttpOnly, Secure, SameSite=Strict
- [ ] Password requirements enforced
- [ ] MFA works correctly
- [ ] JWT validation robust (signature, issuer, audience, expiration)
- [ ] RBAC/ABAC tests passed
- [ ] RLS policies tested (cross-tenant access blocked)
- [ ] CSRF protection verified
- [ ] Rate limits enforced
- [ ] Input validation comprehensive
- [ ] XSS tests passed (no injection possible)
- [ ] SQL injection tests passed
- [ ] SSRF mitigated
- [ ] Audit logging complete
- [ ] Error messages don't leak sensitive info

### Production Readiness
- [ ] OWASP ZAP scan completed
- [ ] Penetration test completed
- [ ] Load test passed (50+ concurrent admins)
- [ ] Disaster recovery tested
- [ ] Secrets rotated within 90 days
- [ ] Security playbooks documented
- [ ] Incident response plan ready

---

## 11. Quick Reference

### CSRF Protection
```typescript
import csrf from '@fastify/csrf-protection';

fastify.register(csrf, {
  cookieOpts: { signed: true, secure: true, sameSite: 'strict', httpOnly: true },
});

// Validate on state-changing endpoints
fastify.post('/api/v1/resource', {
  preValidation: fastify.csrfProtection,
}, handler);
```

### CORS Configuration
```typescript
import cors from '@fastify/cors';

fastify.register(cors, {
  origin: (origin, cb) => {
    const allowed = ['https://app.befreefitness.com', 'https://admin.befreefitness.com'];
    if (!origin || allowed.includes(origin)) {
      cb(null, true);
    } else {
      cb(new Error('CORS not allowed'), false);
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
});
```

### Impersonation Audit
```typescript
// Every action during impersonation must log
logger.warn({
  event: 'impersonation_action',
  adminId: req.admin.id,
  targetUserId: req.impersonation.targetUserId,
  action: 'user.update',
  changes: diff,
  reason: req.impersonation.reason,
});
```

---

**Status:** ✅ Security Baseline Established  
**Next:** Implement these standards in all tasks





