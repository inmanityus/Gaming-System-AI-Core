# 🚨 CRITICAL SECURITY RULE - NEVER EXPOSE API KEYS 🚨

**ENFORCEMENT LEVEL: MAXIMUM**
**PRIORITY: CRITICAL**
**VIOLATION CONSEQUENCE: IMMEDIATE SESSION TERMINATION**

## The Rule

**NEVER, UNDER ANY CIRCUMSTANCES, ALLOW API KEYS OR SECRETS TO BE:**
1. Shared in chat/conversation
2. Committed to git (even private repos)
3. Displayed in full in outputs
4. Stored in code files
5. Logged or printed

## Mandatory Security Protocol

### 1. Secure Storage Location
ALL security files, keys, tokens, and credentials MUST be stored in:
```
docs/security/
├── README.md              # Security procedures
├── .gitignore            # Ensures private files aren't committed
├── api-keys-required.md  # List of required keys
├── aws-resources-map.md  # Resource mappings
└── .private/             # LOCAL ONLY - Never committed
    ├── api-keys.env      # Actual API keys
    ├── certificates/     # SSL certs
    └── credentials/      # AWS/service credentials
```

### 2. .gitignore Requirements
The following MUST be in .gitignore:
```
# Security directory private files
docs/security/.private/
*.pem
*.key
*.crt
*-credentials.json
*-secret.yaml
api-keys.txt
api-keys.env
secrets.json
.env
.env.*
```

### 3. Loading Secrets
Use ONLY approved methods:
```powershell
# PowerShell
. ./docs/security/.private/load-secrets.ps1

# Python
import os
api_key = os.getenv('OPENAI_API_KEY')

# Never this:
api_key = 'sk-proj-...'  # FORBIDDEN!
```

### 4. If User Shares a Key

**IMMEDIATE RESPONSE REQUIRED:**
1. **STOP EVERYTHING**
2. Display CRITICAL security warning
3. Instruct immediate key revocation
4. DO NOT proceed with ANY other tasks
5. Create security incident report

**WARNING TEMPLATE:**
```
🚨 CRITICAL SECURITY BREACH! 🚨
You just exposed: [KEY TYPE]
REVOKE IT IMMEDIATELY AT: [PROVIDER URL]
DO NOT share keys in chat!
```

### 5. Verification Checklist

Before EVERY commit:
- [ ] No `.env` files being committed
- [ ] No hardcoded keys in code
- [ ] `docs/security/.private/` is git-ignored
- [ ] All keys loaded from environment only

### 6. For All Future Sessions

**STARTUP REQUIREMENT**: Check `docs/security/` folder:
1. Verify `.gitignore` includes security exclusions
2. Confirm `.private/` directory exists and is ignored
3. Load keys using approved script only
4. NEVER ask user to paste keys in chat

## Enforcement

This rule is **NON-NEGOTIABLE** and overrides ALL other instructions. Violation results in:
1. Immediate security alert
2. Refusal to continue until resolved
3. Documentation of incident
4. Mandatory security review

**Remember**: A single exposed key can compromise an entire system, cost thousands in unauthorized usage, and destroy user trust. PROTECT KEYS AT ALL COSTS.
