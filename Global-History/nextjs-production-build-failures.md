# Solution: Next.js Production Build Failures

**Issue ID**: nextjs-production-build-failures  
**Date Solved**: 2025-10-29  
**Project**: Next.js production deployment  
**Severity**: Critical  
**Category**: deployment, nextjs, build-errors

---

## Problem Statement

Next.js production mode fails to start with crashes or build errors. Common causes include missing BUILD_ID file, missing 'use client' directives, and Suspense boundary issues.

**Symptoms:**
- PM2 shows process crashed (183+ restarts)
- Production app won't start
- Build process fails
- Error: "Cannot find module" or "Missing BUILD_ID"

---

## Root Causes

### Issue 1: Missing BUILD_ID File
**Error**: `.next/BUILD_ID` file not found  
**Impact**: Production mode cannot start  
**Cause**: Build incomplete or .next directory missing/incomplete

### Issue 2: Missing 'use client' Directive
**Error**: Build fails with "use" instead of "'use client';"  
**Impact**: Cannot build production version  
**Cause**: Client component missing directive

### Issue 3: Suspense Boundary Issues
**Error**: useSearchParams() requires Suspense boundary  
**Impact**: Pages crash or fail to render  
**Cause**: Client components using useSearchParams() without Suspense wrapper

---

## Solutions

### Solution 1: Fix Missing BUILD_ID

```bash
# Ensure .next directory exists and is complete
cd /path/to/nextjs/app

# Clean and rebuild
rm -rf .next
npm run build

# Verify BUILD_ID exists
ls -la .next/BUILD_ID
# Should show file exists

# Start production server
npm start
```

**Prevention:**
```bash
# Add to CI/CD pipeline
npm run build
test -f .next/BUILD_ID || (echo "Build failed - missing BUILD_ID" && exit 1)
```

### Solution 2: Fix Missing 'use client' Directive

```typescript
// ❌ WRONG
'use'  // Typo

// ✅ CORRECT
'use client'

// Check all client components
// Files that need 'use client':
// - Components using hooks (useState, useEffect, etc.)
// - Components using browser APIs
// - Interactive components
```

**Find Missing Directives:**
```bash
# Find files using client features without directive
grep -r "useState\|useEffect\|useSearchParams" apps/web/src/app --include="*.tsx" | \
  grep -v "'use client'"

# Add 'use client' to top of those files
```

### Solution 3: Fix Suspense Boundary Issues

```typescript
// ❌ WRONG: useSearchParams without Suspense
import { useSearchParams } from 'next/navigation';

export default function Page() {
  const searchParams = useSearchParams();  // Error!
  // ...
}

// ✅ CORRECT: Wrap in Suspense
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function PageContent() {
  const searchParams = useSearchParams();
  // ...
}

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PageContent />
    </Suspense>
  );
}
```

**Pattern for All Pages Using useSearchParams:**
```typescript
'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function Content() {
  const searchParams = useSearchParams();
  // Your page content
}

export default function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <Content />
    </Suspense>
  );
}
```

---

## Investigation Steps

### Step 1: Check Build Process
```bash
cd /path/to/nextjs/app
npm run build

# Watch for errors:
# - Missing 'use client' directives
# - TypeScript errors
# - Module resolution errors
```

### Step 2: Check BUILD_ID
```bash
ls -la .next/BUILD_ID
cat .next/BUILD_ID
# Should show a hash string
```

### Step 3: Check PM2 Logs
```bash
pm2 logs nextjs-app --lines 100
# Look for:
# - "Cannot find module"
# - "Missing BUILD_ID"
# - React errors
```

### Step 4: Verify Production Mode
```bash
# Check NODE_ENV
echo $NODE_ENV
# Should be "production"

# Check package.json scripts
cat package.json | grep '"start"'
# Should use: next start
```

---

## Prevention Checklist

- [ ] Always run `npm run build` before deploying
- [ ] Verify `.next/BUILD_ID` exists after build
- [ ] Check all client components have `'use client'` directive
- [ ] Wrap useSearchParams() in Suspense boundaries
- [ ] Test production build locally: `npm run build && npm start`
- [ ] Use TypeScript to catch missing directives
- [ ] Add build verification to CI/CD
- [ ] Monitor PM2 restart count (high = problem)

---

## Common Errors and Fixes

### Error: "Cannot find module .next/static/..."
**Fix**: Rebuild the application
```bash
rm -rf .next node_modules/.cache
npm run build
```

### Error: "Module not found: Can't resolve '...'"
**Fix**: Check imports and dependencies
```bash
npm install
npm run build
```

### Error: "React Error: useSearchParams() should be wrapped"
**Fix**: Add Suspense boundary (see Solution 3 above)

### Error: PM2 crashing repeatedly
**Fix**: Check logs for specific error
```bash
pm2 logs --err
# Fix the root cause, then restart
pm2 restart app
```

---

## Testing Production Build

```bash
# 1. Build
npm run build

# 2. Start production server
npm start

# 3. Test locally
curl http://localhost:3000

# 4. Test all routes
# - Homepage
# - API routes
# - Dynamic routes
# - Pages with searchParams
```

---

## Lessons Learned

1. **Always Build Before Deploy**: Never deploy without successful build
2. **Check BUILD_ID**: File must exist for production mode
3. **Client Directives**: All interactive components need 'use client'
4. **Suspense Boundaries**: Required for useSearchParams() and async components
5. **PM2 Monitoring**: High restart count indicates issues

---

## Related Issues

- **Nginx 502 Bad Gateway**: Production app not running
- **Missing Environment Variables**: Causes startup failures
- **TypeScript Build Errors**: Must fix before production build

---

**Last Updated**: 2025-10-29  
**Status**: Verified Solution

