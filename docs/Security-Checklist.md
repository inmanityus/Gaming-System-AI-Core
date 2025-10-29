# Security Checklist - Per Task Validation
**Must be verified for EVERY task that touches authentication, authorization, data access, or user input**

## ✅ Authentication & Authorization
- [ ] Server-side auth validation only (never trust client)
- [ ] JWT signature verified (RS256/ES256)
- [ ] Token expiration checked
- [ ] User roles/scopes validated
- [ ] RBAC permissions enforced
- [ ] RLS policies active for database queries
- [ ] No trust of `x-middleware-subrequest` header (CVE-2025-29927)

## ✅ Input Validation
- [ ] AJV schema defined for all inputs
- [ ] Unknown properties rejected (`additionalProperties: false`)
- [ ] String lengths limited
- [ ] Numeric ranges validated
- [ ] Enums validated
- [ ] SQL parameters used (never string concatenation)
- [ ] HTML sanitized if rendered (DOMPurify)

## ✅ Security Headers
- [ ] CSP configured
- [ ] HSTS enabled (max-age 31536000)
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy configured
- [ ] X-Powered-By removed

## ✅ Rate Limiting
- [ ] Global rate limit applied (100 req/min)
- [ ] Endpoint-specific limit if applicable
- [ ] Redis-backed (cluster-safe)
- [ ] Proper error responses (429 with retry-after)

## ✅ Logging & Audit
- [ ] All actions logged with user context
- [ ] PII redacted from logs
- [ ] Security events flagged
- [ ] Request ID generated and propagated
- [ ] Errors logged with stack traces (server-side only)

## ✅ Database Security
- [ ] SSL/TLS connection enforced
- [ ] Parameterized queries only
- [ ] RLS policies enabled
- [ ] Session variables set per request
- [ ] No superuser privileges for app

## ✅ OWASP Top 10
- [ ] Access control verified (no IDOR)
- [ ] Cryptography: HTTPS only, secure cookies
- [ ] Injection prevented (parameterized, sanitized)
- [ ] Security misconfiguration checked
- [ ] Dependencies scanned (npm audit)
- [ ] Authentication tested (MFA, lockout, tokens)
- [ ] Data integrity (constraints, validations)
- [ ] Logging comprehensive
- [ ] SSRF prevented (URL whitelist)

## ✅ Testing
- [ ] Unit tests written (80% coverage min)
- [ ] Integration tests for auth flow
- [ ] Security-specific tests (SQL injection, XSS, CSRF)
- [ ] All tests passing before task complete

## ✅ Code Review
- [ ] Peer reviewed by different AI model
- [ ] Security concerns addressed
- [ ] No hardcoded secrets
- [ ] No sensitive data in logs





