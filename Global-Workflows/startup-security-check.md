# Startup Security Check - MANDATORY

**CRITICAL**: This security check MUST be performed at the start of EVERY session.

## Automatic Security Verification

At session startup, ALWAYS run:
```powershell
& "Global-Scripts\check-security-setup.ps1"
```

## What This Checks

1. **Security Folder Structure**
   - `docs/security/` exists
   - `docs/security/.private/` exists and is git-ignored
   - Required documentation files present

2. **Git Ignore Patterns**
   - `.env` files excluded
   - `*.key`, `*.pem` files excluded
   - `docs/security/.private/` excluded
   - All sensitive patterns covered

3. **Exposed Secrets Scan**
   - No `.env` files in root (except .env.example)
   - No `*.pem` or `*.key` files outside secure location
   - No files with "secret" or "credential" in name
   - No API keys in tracked files

4. **Documentation**
   - Security README exists
   - API keys documentation exists
   - Proper templates available

## If Issues Found

1. **STOP** all other work
2. Run `/clean-project` to fix security setup
3. Move any exposed files to `docs/security/.private/`
4. Update `.gitignore` with missing patterns
5. Re-run security check to verify

## Loading Secrets

Once security is verified, load secrets with:
```powershell
. ./docs/security/.private/load-secrets.ps1
```

## Critical Rules

- **NEVER** proceed with exposed secrets
- **NEVER** skip security verification
- **NEVER** store keys outside `docs/security/.private/`
- **ALWAYS** use environment variables for secrets
- **ALWAYS** check security BEFORE any other work

This is not optional. Security comes first, always.
