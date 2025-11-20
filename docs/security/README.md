# Security and Secrets Management

⚠️ **CRITICAL**: NEVER commit actual secrets, API keys, or credentials to Git!

## Directory Structure

```
docs/security/
├── README.md                    # This file
├── .gitignore                  # Ensures private files aren't committed
├── secrets-template.md         # Template for documenting secrets
├── aws-resources.md            # AWS resource mappings
├── api-keys-required.md        # List of required API keys
└── .private/                   # LOCAL ONLY - Never committed to git
    ├── api-keys.env           # Actual API keys (create locally)
    ├── aws-credentials.json    # AWS credentials (create locally)
    └── certificates/          # SSL certificates (create locally)
```

## Required Secrets

### 1. OpenAI API Key
- **Purpose**: Direct OpenAI API access (not OpenRouter)
- **Format**: `sk-proj-...`
- **Storage**: Environment variable `OPENAI_API_KEY`
- **NEVER**: Share in chat, commit to git, or expose in logs

### 2. AWS Credentials
- **Purpose**: AWS service access
- **Components**:
  - AWS Account ID: 695353648052
  - Region: us-east-1
  - Access Key ID: (stored securely)
  - Secret Access Key: (stored securely)
- **Preferred**: Use IAM roles with OIDC, not long-lived keys

### 3. Database Credentials
- **PostgreSQL**: Amazon RDS Aurora
- **Redis**: Amazon ElastiCache
- **Storage**: AWS Secrets Manager or environment variables

### 4. Service API Keys
- **Perplexity API**: For AI search
- **OpenRouter**: For model routing
- **MCP Services**: Various service credentials

## Best Practices

1. **Use Environment Variables**
   ```bash
   # .env.local (never commit this)
   OPENAI_API_KEY=your-key-here
   AWS_SECRET_ACCESS_KEY=your-secret-here
   ```

2. **Use AWS Secrets Manager**
   ```bash
   aws secretsmanager create-secret \
     --name gaming-system/openai-api-key \
     --secret-string "your-key-here"
   ```

3. **Use GitHub Secrets**
   - For CI/CD workflows
   - Set via repository settings, not code

4. **Rotate Regularly**
   - API keys: Every 90 days
   - AWS credentials: Every 30 days
   - Certificates: Before expiration

## Emergency Procedures

### If a Secret is Exposed:

1. **Immediately Revoke** the exposed credential
2. **Generate New** credential
3. **Update All Services** using the credential
4. **Audit Logs** for unauthorized usage
5. **Document Incident** for future reference

### Secure Key Generation:

```powershell
# Generate secure random key
[System.Web.Security.Membership]::GeneratePassword(32, 8)

# Generate certificate
New-SelfSignedCertificate -DnsName "api.bodybrokergame.com" -CertStoreLocation "cert:\LocalMachine\My"
```

## Local Development Setup

1. Copy templates to `.private/` directory
2. Fill in actual values (never commit these)
3. Source environment variables:
   ```bash
   # PowerShell
   . ./docs/security/.private/load-secrets.ps1
   
   # Bash
   source ./docs/security/.private/load-secrets.sh
   ```

## CI/CD Secret Management

GitHub Actions secrets are configured separately:
- Go to: Settings → Secrets and variables → Actions
- Required secrets:
  - `AWS_ACCOUNT_ID`
  - `AWS_REGION`
  - `OPENAI_API_KEY` (if needed for tests)

## Security Contacts

For security incidents or questions:
- Primary: [Your Email]
- Security Team: [Team Email]
- AWS Support: Via AWS Console

---

**Remember**: Security is everyone's responsibility. When in doubt, ask before exposing any credential.
