# Solution: PM2 Environment Variables Not Loading After Update

**Issue ID**: pm2-env-reload-failure  
**Date Solved**: October 29, 2025  
**Project**: Innovation Forge Website  
**Severity**: High - Configuration not applying

---

## Problem Statement

After updating `ecosystem.config.js` with new environment variables and running `pm2 restart app-name --update-env`, the application still uses **old/cached values**.

Configuration appears correct in files but runtime values remain unchanged.

---

## Root Cause

`pm2 restart --update-env` only reloads **system environment variables**, NOT the `env` section in `ecosystem.config.js`.

PM2 caches the configuration from the initial `pm2 start` command and keeps using it despite the `--update-env` flag.

---

## Solution

Use **full restart sequence** instead of `pm2 restart`:

```bash
# ❌ WRONG - Doesn't reload ecosystem.config.js
pm2 restart app-name --update-env

# ✅ CORRECT - Full restart with fresh config
pm2 delete app-name
pm2 start ecosystem.config.js
pm2 save
```

---

## Step-by-Step Procedure

### 1. Update Configuration
```bash
nano .env
nano ecosystem.config.js
# Ensure both files have matching values
```

### 2. Full PM2 Restart
```bash
pm2 delete app-name
pm2 start ecosystem.config.js
pm2 save
pm2 list  # Verify running
```

### 3. Verify Variables Loaded
```bash
# Check PM2 environment
pm2 show app-name

# Test application
curl -X POST http://localhost:PORT/api/test

# Check application logs
pm2 logs app-name --lines 50
```

---

## When to Use Each Command

### Use `pm2 restart`
- Application code changes only
- No configuration changes
- Quick restart needed

### Use `pm2 delete + pm2 start`
- Environment variable changes
- Configuration file updates
- Switching modes (dev/prod)
- After updating ecosystem.config.js

---

## Why This Matters

PM2 loads configuration in this order:
1. System environment (`/etc/environment`)
2. `.env` file (if loaded by app)
3. `ecosystem.config.js` env section ⭐ **HIGHEST PRIORITY**

The `ecosystem.config.js` env values are loaded **once** at `pm2 start` and cached. They don't reload with `pm2 restart`.

---

## Verification Checklist

- [ ] Updated `.env` file
- [ ] Updated `ecosystem.config.js`
- [ ] Values match in both files
- [ ] Ran `pm2 delete app-name`
- [ ] Ran `pm2 start ecosystem.config.js`
- [ ] Ran `pm2 save`
- [ ] Verified with `pm2 show app-name`
- [ ] Tested application functionality

---

## Related Issues

- Resend domain errors → See Global-History/resend-email-450-error-solution.md
- Next.js env vars → See Global-History/nextjs-build-time-freeze.md

---

**Status**: ✅ Resolved  
**Applicable To**: All PM2-managed applications  
**Prevention**: Always use full restart for config changes

