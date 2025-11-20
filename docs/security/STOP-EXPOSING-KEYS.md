# 🛑 STOP EXPOSING API KEYS - Security Guide

## You've Exposed These Keys (REVOKE IMMEDIATELY!)

1. **OpenAI Key**: `sk-proj-SFjVTj3bah3k...`
   - Revoke at: https://platform.openai.com/api-keys
   
2. **Anthropic/Claude Key**: `sk-ant-api03-NfIP56j9...`
   - Revoke at: https://console.anthropic.com/settings/keys
   
3. **OpenRouter Key**: `sk-or-v1-96ed70c18702...`
   - Revoke at: https://openrouter.ai/keys

## Why This Is Critical

When you share API keys in chat or commit them to git:
- **Anyone** who sees them can use them
- **You** get charged for their usage
- **Your account** could be suspended for abuse
- **Your data** could be compromised

## The RIGHT Way to Handle API Keys

### 1. Create Local Secrets File
```bash
# Navigate to security directory
cd docs/security/.private/

# Copy the template
cp api-keys.env.example api-keys.env

# Edit with your actual keys
notepad api-keys.env  # or your preferred editor
```

### 2. Load Secrets Securely
```powershell
# Load environment variables
. ./docs/security/.private/load-secrets.ps1

# Verify loaded (shows partial key only)
echo $env:OPENAI_API_KEY.Substring(0,10)
```

### 3. Use in Your Code
```python
import os

# GOOD - Read from environment
openai_key = os.getenv('OPENAI_API_KEY')

# BAD - Never hardcode!
openai_key = 'sk-proj-abc123...'  # NEVER DO THIS!
```

## For CI/CD (GitHub Actions)

### Add Secrets to GitHub:
1. Go to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret:
   - Name: `OPENAI_API_KEY`
   - Value: Your actual key
4. Use in workflows:
   ```yaml
   env:
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   ```

## For AWS Deployment

### Use AWS Secrets Manager:
```bash
# Create secret
aws secretsmanager create-secret \
  --name gaming-system/openai-api-key \
  --secret-string "sk-proj-YOUR-ACTUAL-KEY"

# Reference in ECS task
{
  "secrets": [{
    "name": "OPENAI_API_KEY",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:695353648052:secret:gaming-system/openai-api-key"
  }]
}
```

## Security Checklist

- [ ] **Revoked** all exposed keys
- [ ] **Generated** new keys
- [ ] **Created** local api-keys.env file
- [ ] **Added** .private/ to .gitignore
- [ ] **Tested** load-secrets.ps1 script
- [ ] **Updated** code to use environment variables
- [ ] **Configured** GitHub Secrets for CI/CD
- [ ] **Set up** AWS Secrets Manager for production

## Emergency Contacts

If keys are compromised:
1. **Revoke immediately** at provider's website
2. **Check usage** for unauthorized access
3. **Generate new keys**
4. **Update all services** using the keys
5. **Enable 2FA** on all accounts

## Remember

- **NEVER** share keys in chat/email/slack
- **NEVER** commit keys to git
- **NEVER** log keys in your application
- **ALWAYS** use environment variables
- **ALWAYS** rotate keys every 90 days
- **ALWAYS** use separate keys per environment

---

**Your security is only as strong as your weakest key management!**
