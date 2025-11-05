# Cybersecurity Review Protocol

## Overview

When the user requests a **"cybersecurity review"**, **"security audit"**, **"security assessment"**, or similar, follow this comprehensive protocol to analyze threats, research attack vectors, and implement protections for both development and production environments.

---

## 🎯 When to Execute This Protocol

### **Execute Full Review When:**
- User explicitly requests cybersecurity review
- `Development-Security-Implementation.md` doesn't exist
- `Production-Security-Implementation.md` doesn't exist
- Either file is > 30 days old (monthly security updates)
- Major architecture change occurred
- New deployment target added
- Significant new features added (admin panel, payment system, etc.)

### **Use Existing Documentation When:**
- Security implementation files exist
- Files are < 30 days old
- No major changes since last review
- Just following existing security guidelines

---

## 🔄 The Cybersecurity Review Workflow

### **Stage 1: Project Analysis**

**1.1 Analyze Project Characteristics**

```typescript
const projectProfile = {
  type: "Web Application", // or Mobile App, API, Desktop, etc.
  
  technology_stack: {
    frontend: ["Next.js", "React", "TypeScript"],
    backend: ["Fastify", "Node.js", "TypeScript"],
    database: ["PostgreSQL"],
    caching: ["Redis"],
    email: ["SMTP", "MailHog (dev)"],
    payments: ["Stripe"],
    file_storage: ["Local (dev)", "S3 (prod)"],
    authentication: ["JWT", "Passwordless"],
  },
  
  deployment: {
    development: "Windows/Linux local",
    production: "AWS Linux Ubuntu",
    containerization: "Docker",
    orchestration: "Docker Compose / ECS (planned)",
  },
  
  network: {
    domain: "https://befreefitness.ai",
    protocols: ["HTTPS", "WSS"],
    ports: {
      web: 3000,
      api: 4000,
      db: 5432,
      redis: 6379,
      mailhog: 1025
    }
  },
  
  services: {
    external: ["Stripe", "AWS S3", "SendGrid", "Twilio"],
    internal: ["User Management", "AI Analysis", "BFF Network", "Admin Portal"]
  },
  
  data_sensitivity: {
    pii: ["email", "name", "birthdate", "address", "phone"],
    phi: ["medical conditions", "injuries", "biometric data"],
    financial: ["payment information", "Stripe tokens"],
    proprietary: ["AI analysis algorithms", "workout programs"],
  },
  
  compliance_requirements: ["GDPR", "CCPA", "HIPAA (partial)", "PCI-DSS (via Stripe)"]
}
```

**1.2 Identify Attack Surface**

Map all entry points:
- Web application endpoints
- API endpoints (REST)
- WebSocket connections
- Admin portal
- Database connections
- File upload endpoints
- Email system
- Third-party integrations
- Docker containers
- AWS infrastructure

---

### **Stage 2: Threat Research (Collaborate with AI Models)**

**2.1 Use MCP Servers for Research**

**Exa MCP:**
```typescript
// Research latest attack vectors
mcp_exa_web_search_exa({
  query: "Latest web application vulnerabilities 2025 Next.js Fastify",
  numResults: 20
})

mcp_exa_web_search_exa({
  query: "AWS Ubuntu server security hardening best practices",
  numResults: 15
})

mcp_exa_get_code_context_exa({
  query: "JWT authentication vulnerabilities and mitigations",
  tokensNum: "dynamic"
})
```

**Perplexity Ask MCP:**
```typescript
mcp_perplexity-ask_perplexity_ask({
  messages: [{
    role: "user",
    content: "What are the most common attack vectors for Next.js applications in 2025? How do attackers exploit JWT authentication?"
  }]
})

mcp_perplexity-ask_perplexity_ask({
  messages: [{
    role: "user",
    content: "What are the latest AWS Linux Ubuntu server hardening techniques? How do attackers compromise cloud infrastructure?"
  }]
})
```

**Ref MCP:**
```typescript
mcp_Ref_ref_search_documentation({
  query: "OWASP Top 10 2025 security guidelines"
})

mcp_Ref_ref_search_documentation({
  query: "Docker security best practices container hardening"
})
```

**2.2 Research Attack Categories**

**Direct Hacking Attempts:**
- SQL Injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- XXE (XML External Entity)
- Server-Side Request Forgery (SSRF)
- Remote Code Execution (RCE)
- Authentication bypass
- Authorization flaws
- Session hijacking
- Token theft/manipulation

**Network Attacks:**
- DDoS (Distributed Denial of Service)
- Man-in-the-Middle (MITM)
- DNS spoofing
- SSL/TLS downgrade attacks
- Port scanning
- Network sniffing
- ARP spoofing

**Indirect Attacks:**
- Social engineering (phishing, pretexting)
- Supply chain attacks (compromised dependencies)
- Dependency confusion
- Typosquatting
- Subdomain takeover
- Email spoofing

**Insider Threats:**
- Malicious admins
- Credential theft
- Data exfiltration
- Privilege escalation
- Audit log tampering
- Backdoor creation

**Infrastructure Attacks:**
- Container escape
- Misconfigured S3 buckets
- Exposed secrets in environment variables
- Weak IAM policies
- Unpatched systems
- Open ports
- Default credentials

**Application-Specific:**
- File upload exploits (malicious videos)
- AI model poisoning
- Prompt injection
- Payment system fraud
- Coupon abuse
- Rate limit bypass
- API key theft

---

### **Stage 3: AI Model Collaboration**

**3.1 Director Model Analysis**

Select Director (GPT-5-Pro, Claude Sonnet 4.5, or best reasoning model)

**Director Tasks:**
1. Review project profile
2. Review threat research
3. Categorize threats by:
   - Severity (Critical, High, Medium, Low)
   - Likelihood (High, Medium, Low)
   - Impact (Severe, Moderate, Minor)
4. Prioritize threats (Severity × Likelihood)
5. Draft initial countermeasures

**3.2 Peer Review by Security-Focused Models**

Pass Director's threat assessment to 3-5 models:
- Security specialist models
- Infrastructure experts
- Code security reviewers

**Each Model Reviews:**
- Completeness of threat list
- Accuracy of countermeasures
- Implementation feasibility
- Performance impact
- Cost considerations
- Missing attack vectors

**3.3 Consolidation**

Director consolidates feedback:
- Updates threat list with new findings
- Refines countermeasures
- Resolves conflicting recommendations
- Creates implementation priority

---

### **Stage 4: Separate Development vs Production**

**4.1 Development Environment**

**Characteristics:**
- Local Windows/Linux
- localhost domains
- Development databases
- MailHog (not real email)
- Fake Stripe keys (test mode)
- No HTTPS (HTTP only)
- Permissive CORS
- Debug logging enabled

**Security Focus:**
- Prevent accidental secret commits
- Secure local database
- Protect against malicious dependencies
- Local firewall rules
- Development-only feature flags

**What NOT to Apply:**
- Production SSL certificates
- Domain-specific CORS
- Production API keys
- Strict CSP (too restrictive for dev)
- Production rate limits (too strict for testing)

---

**4.2 Production Environment**

**Characteristics:**
- AWS Linux Ubuntu
- Domain: https://befreefitness.ai
- Production PostgreSQL (possibly RDS)
- Real email (SendGrid/SES)
- Real Stripe keys (live mode)
- HTTPS enforced
- Strict CORS
- Minimal logging (PII redaction)

**Security Focus:**
- Full OWASP Top 10 compliance
- Infrastructure hardening
- Network security
- DDoS protection
- Intrusion detection
- Secrets management (AWS Secrets Manager)
- Automated patching
- Incident response

**Production-Specific Elements:**
```
Domain-based:
  - CSP with 'self' and befreefitness.ai
  - CORS: https://befreefitness.ai only
  - Cookies: domain=.befreefitness.ai, secure=true
  - SSL certificate for befreefitness.ai

AWS-specific:
  - WAF (Web Application Firewall)
  - Shield (DDoS protection)
  - CloudFront CDN
  - S3 bucket policies
  - RDS encryption
  - VPC security groups
  - IAM roles and policies
```

---

### **Stage 5: Implementation Planning**

**5.1 Git Versioning Requirement**

**CRITICAL:** Before implementing ANY security changes:

```bash
# 1. Commit all current work and push to GitHub
git add -A
git commit -m "chore(cursor): pre-security-implementation checkpoint [chat:security-review]"
# Push to GitHub (creates private repo if needed)
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\git-push-to-github.ps1"

# 2. Create security branch
git checkout -b security-implementation-$(date +%Y%m%d)

# 3. Tag current state
git tag "pre-security-$(date +%Y%m%d)"

# 4. Implement changes on branch

# 5. Test thoroughly

# 6. If successful: merge to main
git checkout main
git merge security-implementation-$(date +%Y%m%d)

# 7. If failed: rollback
git checkout main
git branch -D security-implementation-$(date +%Y%m%d)
# Project unchanged
```

**Why This Approach?**
- Easy rollback if something breaks
- Clear checkpoint before security changes
- Can review changes before merging
- Safety net for production deployment

---

**5.2 Implementation Priority**

**Phase 1: Critical (Implement Immediately)**
- Authentication vulnerabilities
- SQL injection prevention
- XSS prevention
- Exposed secrets
- Missing access controls
- Insecure direct object references

**Phase 2: High (Implement Soon)**
- CSRF protection
- Security headers
- Rate limiting
- Input validation
- Error handling
- Audit logging

**Phase 3: Medium (Implement Before Production)**
- DDoS protection
- Intrusion detection
- Network hardening
- Container security
- Dependency scanning

**Phase 4: Nice to Have**
- Advanced monitoring
- Penetration testing
- Bug bounty program
- Security training

---

### **Stage 6: Generate Implementation Documents**

**6.1 Development-Security-Implementation.md**

**Structure:**
```markdown
# Development Security Implementation
**Generated:** {timestamp}
**Valid Until:** {timestamp + 30 days}
**Project:** Be Free Fitness
**Environment:** Development (Local)

## Overview
Security measures for local development environment.

## Threats Specific to Development
1. Accidental secret commits
2. Malicious dependencies
3. Local database exposure
...

## Countermeasures
### 1. Secret Management
**Threat:** Accidental commit of API keys
**Solution:** 
- Use .env files (gitignored)
- Pre-commit hooks to scan for secrets
- Environment-specific configs
**Implementation:**
[Step-by-step commands]

### 2. Dependency Security
**Threat:** Malicious npm packages
**Solution:**
- npm audit before install
- Lock file verification
- Dependabot alerts
**Implementation:**
[Commands and configs]

...

## Pre-Implementation Checklist
- [ ] Git commit current state
- [ ] Create security branch
- [ ] Tag current state
- [ ] Backup database
...

## Rollback Procedure
If implementation causes issues:
```bash
git checkout main
git reset --hard pre-security-{date}
```

## Validation
After implementation, verify:
- [ ] Tests still pass
- [ ] Application still runs
- [ ] No secrets in git
...
```

---

**6.2 Production-Security-Implementation.md**

**Structure:**
```markdown
# Production Security Implementation
**Generated:** {timestamp}
**Valid Until:** {timestamp + 30 days}
**Project:** Be Free Fitness
**Environment:** Production (AWS Ubuntu)
**Domain:** https://befreefitness.ai

## Overview
Comprehensive security hardening for production deployment.

## AWS Infrastructure Security
### 1. VPC Configuration
**Threat:** Network exposure
**Solution:**
- Private subnets for database
- Public subnets for load balancers only
- Security groups (whitelist approach)
**Implementation:**
[AWS CLI commands / CloudFormation]

### 2. IAM Security
**Threat:** Privilege escalation
**Solution:**
- Least privilege policies
- MFA for all admin access
- Service roles for ECS/EC2
**Implementation:**
[IAM policy JSON]

...

## Application Security
### 1. HTTPS Enforcement
**Threat:** Man-in-the-middle attacks
**Solution:**
- SSL certificate (Let's Encrypt / AWS Certificate Manager)
- HSTS headers
- Redirect HTTP → HTTPS
**Implementation:**
[Nginx config / ALB config]

### 2. CSP Headers
**Threat:** XSS attacks
**Solution:**
```
Content-Security-Policy: 
  default-src 'self' https://befreefitness.ai;
  script-src 'self' 'unsafe-inline' https://js.stripe.com;
  img-src 'self' data: https:;
  ...
```
**Implementation:**
[Fastify middleware config]

...

## Docker Security
### 1. Container Hardening
**Threat:** Container escape
**Solution:**
- Non-root user
- Read-only root filesystem
- Drop capabilities
- Scan images for vulnerabilities
**Implementation:**
[Dockerfile changes]

...

## Network Security
### 1. DDoS Protection
**Threat:** Denial of service
**Solution:**
- AWS Shield
- CloudFront CDN
- Rate limiting (WAF rules)
**Implementation:**
[AWS console steps / Terraform]

...

## Database Security
### 1. Encryption
**Threat:** Data breach
**Solution:**
- RDS encryption at rest
- SSL connections
- Encrypted backups
**Implementation:**
[RDS configuration]

...

## Monitoring & Response
### 1. Intrusion Detection
**Threat:** Undetected breaches
**Solution:**
- CloudWatch alarms
- GuardDuty
- Log aggregation
**Implementation:**
[Monitoring setup]

...

## Pre-Deployment Checklist
- [ ] All secrets in AWS Secrets Manager
- [ ] SSL certificate configured
- [ ] Firewall rules tested
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Incident response plan ready
...

## Rollback Procedure
[Production-specific rollback steps]

## Validation
- [ ] SSL Labs A+ rating
- [ ] Security headers verified
- [ ] Penetration test passed
- [ ] Compliance audit completed
```

---

## 📋 Threat Research Categories

### **1. Direct Hacking Attempts**

Research using Exa + Perplexity:
- SQL Injection (parameterized queries, ORMs)
- XSS (input sanitization, CSP headers)
- CSRF (tokens, SameSite cookies)
- Authentication bypass (session management, JWT security)
- Path traversal (input validation)
- Remote code execution (dependency security)
- Privilege escalation (RBAC enforcement)
- Insecure deserialization (JSON parsing)

**Example Research Query:**
```
Exa: "SQL injection prevention PostgreSQL Node.js 2025"
Perplexity: "What are the latest techniques for preventing XSS in React applications?"
Ref: "OWASP SQL Injection Prevention Cheat Sheet"
```

---

### **2. Network Attacks**

Research:
- DDoS mitigation (CloudFlare, AWS Shield)
- MITM prevention (HTTPS, HSTS, certificate pinning)
- DNS attacks (DNSSEC, CloudFlare)
- Port scanning (firewall rules, fail2ban)
- Network sniffing (encryption in transit)
- SSL/TLS vulnerabilities (TLS 1.3, strong ciphers)

**Example Research:**
```
Exa: "AWS Shield DDoS protection setup"
Perplexity: "How to prevent man-in-the-middle attacks on web applications?"
Ref: "Nginx SSL/TLS configuration best practices"
```

---

### **3. Social Engineering**

Research:
- Phishing prevention (DMARC, SPF, DKIM)
- Pretexting (admin training, verification procedures)
- Baiting (security awareness)
- Quid pro quo (policy enforcement)
- Email spoofing (sender verification)
- Domain spoofing (brand monitoring)

**Example Research:**
```
Perplexity: "How to prevent email phishing attacks on SaaS platforms?"
Exa: "DMARC SPF DKIM email security setup"
```

---

### **4. Insider Threats**

Research:
- Access control (principle of least privilege)
- Audit logging (all admin actions)
- Separation of duties (no single point of power)
- Code review requirements (peer review)
- Database access monitoring (query logging)
- Anomaly detection (unusual patterns)

**Example Research:**
```
Perplexity: "How to detect and prevent insider threats in web applications?"
Exa: "Database audit logging PostgreSQL security"
```

---

### **5. Infrastructure Attacks**

**AWS-Specific:**
- EC2 compromise (security groups, patching)
- S3 bucket exposure (bucket policies, encryption)
- RDS attacks (network isolation, encryption)
- IAM exploitation (MFA, least privilege)
- Secrets exposure (AWS Secrets Manager)
- Container vulnerabilities (image scanning)

**Docker-Specific:**
- Container escape (capabilities, seccomp)
- Image vulnerabilities (Trivy, Snyk scanning)
- Registry poisoning (signed images)
- Resource exhaustion (limits, quotas)

**Example Research:**
```
Exa: "AWS S3 bucket security misconfiguration prevention"
Perplexity: "How do attackers exploit Docker containers in production?"
Ref: "AWS IAM security best practices documentation"
```

---

### **6. Application-Specific Attacks**

**For This Project:**
- File upload exploits (malicious video files)
- AI model poisoning (adversarial inputs)
- Payment fraud (coupon abuse, Stripe manipulation)
- Video analysis manipulation
- Trainer impersonation
- Data scraping (rate limiting, bot detection)
- API abuse (authentication, rate limits)

**Example Research:**
```
Exa: "File upload security video files malicious content detection"
Perplexity: "How to prevent payment fraud in Stripe integrations?"
```

---

## 🤝 AI Model Collaboration

**Director Model (e.g., GPT-5-Pro):**
1. Analyzes all threat research
2. Creates comprehensive threat matrix
3. Proposes countermeasures for each threat
4. Separates dev vs production implementations

**Review Models (3-5 different models):**
1. Security-specialized model reviews threat completeness
2. Infrastructure expert reviews AWS hardening
3. Code security expert reviews application protections
4. Compliance expert reviews regulatory requirements
5. General architecture expert reviews overall approach

**Iteration:**
- Repeat until no new significant threats found
- Consolidate countermeasures
- Resolve conflicts between different approaches
- Finalize implementation plans

---

## 🚫 Critical Boundaries

### **NEVER Modify:**
- ❌ Development computer system settings
- ❌ Cursor configuration (outside project)
- ❌ Windows/Linux OS configuration
- ❌ User's personal files
- ❌ MCP server configurations
- ❌ Global npm/node settings

### **ONLY Modify:**
- ✅ Project code files
- ✅ Project configuration files
- ✅ Docker files
- ✅ Database (project-specific)
- ✅ .env files (project)
- ✅ package.json (project dependencies)
- ✅ nginx.conf (project web server)

---

## 🏗️ Development vs Production Separation

### **Development-Only Protections:**

```javascript
// Example: Relaxed CSP for dev
if (process.env.NODE_ENV === 'development') {
  csp: "default-src * 'unsafe-inline' 'unsafe-eval'"
} else {
  csp: "default-src 'self' https://befreefitness.ai"
}
```

**Apply in Development:**
- Secret scanning in git
- Dependency vulnerability scanning
- Local firewall rules
- Code linting for security issues
- Pre-commit hooks

**DO NOT Apply in Development:**
- Production domain restrictions
- Real SSL certificates
- Strict CORS (blocks local testing)
- CloudFront configurations
- AWS WAF rules
- Production secrets

---

### **Production-Only Protections:**

**Domain-Dependent:**
```nginx
# HTTPS enforcement (production only)
if ($host = befreefitness.ai) {
  return 301 https://$host$request_uri;
}

# HSTS (production only)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";

# CSP (production domain)
add_header Content-Security-Policy "default-src 'self' https://befreefitness.ai";
```

**AWS-Specific:**
- Security groups (EC2, RDS)
- IAM policies
- S3 bucket policies
- CloudFront distributions
- Route53 DNS security
- Secrets Manager
- GuardDuty
- CloudWatch alarms

---

## 📊 Implementation Tracking

### **Security Implementation Log:**

```
.logs/security-implementation/
  ├── 2025-10-10-threat-research.md
  ├── 2025-10-10-dev-implementation.log
  ├── 2025-10-10-prod-planning.md
  └── security-checklist-{date}.md
```

### **Validation:**

After implementation, run security tests:
```bash
# Dependency vulnerabilities
npm audit

# Code security scanning
npm run lint:security

# Container scanning (if Docker)
trivy image be-free-fitness:latest

# SSL test (production only)
curl https://www.ssllabs.com/ssltest/analyze.html?d=befreefitness.ai

# Security headers test
curl -I https://befreefitness.ai | grep -i "security\|x-frame\|x-content"
```

---

## 🔄 Monthly Review Cycle

**Every 30 Days:**

1. **Check File Timestamps:**
   ```bash
   # Check if security docs are > 30 days old
   find . -name "*Security-Implementation.md" -mtime +30
   ```

2. **If Outdated:**
   - Run full cybersecurity review protocol
   - Research new threats (2025 updates)
   - Update implementation documents
   - Apply new protections

3. **If Current:**
   - Use existing implementation guides
   - Skip full review
   - Save time and resources

**Automated Reminder:**
```bash
# Add to cron (Linux) or Task Scheduler (Windows)
# Check monthly: "Is security review needed?"
```

---

## 🐧 Setup for Windows Cursor

```powershell
# 1. Copy documentation
Copy-Item docs/Cybersecurity-Review-Protocol.md \\path\to\windows\

# 2. Create logging directory
New-Item -ItemType Directory -Path .logs\security-implementation -Force

# 3. Install security tools
npm install -D eslint-plugin-security
npm install -D snyk

# 4. Configure git hooks
# Pre-commit: Scan for secrets
# Pre-push: Run security tests

# 5. Add to startup script
# Check if security review needed (> 30 days)
```

---

## 📚 Related Documentation

- [Security Baseline](./Security-Baseline.md)
- [Security Checklist](./Security-Checklist.md)
- [OWASP Top 10](https://owasp.org/Top10/)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)

---

## 🔄 Version History

- **v1.0** - Initial cybersecurity review protocol
- Created: 2025-10-10
- Last Updated: 2025-10-10

---

**Regular cybersecurity reviews ensure the application stays protected against evolving threats and maintains security best practices.**





