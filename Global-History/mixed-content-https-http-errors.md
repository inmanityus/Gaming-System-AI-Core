# Solution: Mixed Content Errors (HTTPS/HTTP)

**Issue ID**: mixed-content-https-http  
**Date Solved**: 2025-10-29  
**Project**: Production deployment  
**Severity**: High  
**Category**: security, deployment, browser-errors

---

## Problem Statement

HTTPS pages trying to fetch from HTTP endpoints cause "Mixed Content" errors. Browser blocks HTTP resources when page is loaded over HTTPS.

**Error Messages:**
- `Mixed Content: The page was loaded over HTTPS, but requested an insecure resource`
- `Failed to fetch` (browser blocked request)
- `net::ERR_FAILED` (network error)
- Services page showing "Loading..." indefinitely

---

## Root Cause

**Problem**: HTTPS website (`https://befreefitness.ai`) trying to fetch from HTTP API (`http://34.239.119.192:4000`)

**Why Browsers Block This:**
- Security policy: HTTPS pages cannot load HTTP resources
- Prevents man-in-the-middle attacks
- Browser blocks mixed content by default

**Common Causes:**
1. `NEXT_PUBLIC_API_URL` not set in production
2. Falls back to `localhost:4000` or `http://...`
3. Production site is HTTPS but API URL is HTTP
4. Hardcoded HTTP URLs in code

---

## Solution

### Fix 1: Use HTTPS API URL

```typescript
// ❌ WRONG: HTTP URL from HTTPS page
const API_URL = 'http://34.239.119.192:4000';

// ✅ CORRECT: HTTPS URL
const API_URL = 'https://api.befreefitness.ai';
// OR
const API_URL = 'https://befreefitness.ai';
```

### Fix 2: Set Environment Variable Correctly

```bash
# Production environment
export NEXT_PUBLIC_API_URL=https://befreefitness.ai

# Or in .env.production
NEXT_PUBLIC_API_URL=https://befreefitness.ai
```

```typescript
// In code
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

// Production should use HTTPS
// Development can use HTTP (localhost)
```

### Fix 3: Use Same-Origin or Relative URLs

```typescript
// If API is on same domain
const API_URL = '/api';  // Relative URL, uses same protocol

// OR use protocol-relative (deprecated but works)
const API_URL = '//api.befreefitness.ai';  // Uses current page protocol
```

### Fix 4: Proxy API Through Nginx

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name befreefitness.ai;
    
    # Proxy API requests to backend (keeps HTTPS)
    location /api {
        proxy_pass http://localhost:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```typescript
// Frontend code - use relative URL
const API_URL = '/api';  // Always uses current page protocol (HTTPS)
```

---

## Implementation

### Production Environment Setup
```bash
# Set in production server .env
NEXT_PUBLIC_API_URL=https://befreefitness.ai

# Or in PM2 ecosystem.config.js
env: {
  NEXT_PUBLIC_API_URL: 'https://befreefitness.ai'
}

# Restart after setting
pm2 restart web-app
```

### Code Implementation
```typescript
// utils/api.ts
const getApiUrl = () => {
  // Use environment variable if set
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Development fallback (HTTP OK for localhost)
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:4000';
  }
  
  // Production should always be HTTPS
  // If no env var, assume same origin
  return '';
};

export const API_URL = getApiUrl();
```

### Frontend Fetch
```typescript
// Always use API_URL from config
const response = await fetch(`${API_URL}/api/services/packages`, {
  cache: 'no-store'
});

// Or if using relative URLs
const response = await fetch('/api/services/packages', {
  cache: 'no-store'
});
```

---

## Detection

### Browser Console
```javascript
// Look for:
Mixed Content: The page at 'https://...' was loaded over HTTPS,
but requested an insecure resource 'http://...'. This request
has been blocked.

// Network tab shows:
Status: (blocked:mixed-content)
```

### Code Check
```typescript
// If page is HTTPS but API is HTTP:
if (window.location.protocol === 'https:' && API_URL.startsWith('http:')) {
  console.error('Mixed content detected!');
  // Fix API_URL
}
```

---

## Prevention

### 1. Always Use Environment Variables
```typescript
// Never hardcode API URLs
// ✅ Good
const API_URL = process.env.NEXT_PUBLIC_API_URL;

// ❌ Bad
const API_URL = 'http://34.239.119.192:4000';
```

### 2. Protocol-Aware Configuration
```typescript
function getApiUrl() {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  
  // If no env var, use same origin (safest)
  if (!envUrl) {
    return '';  // Relative URL
  }
  
  // Ensure HTTPS in production
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    return envUrl.replace('http://', 'https://');
  }
  
  return envUrl;
}
```

### 3. Nginx Proxy (Recommended)
```nginx
# Proxy keeps everything HTTPS
location /api {
    proxy_pass http://localhost:4000;
}
```

Then use relative URLs:
```typescript
fetch('/api/endpoint')  # Always uses current protocol
```

---

## Testing

### Check for Mixed Content
```bash
# Browser DevTools → Console
# Look for mixed content warnings

# Network tab
# Check if requests are blocked (status: blocked)
```

### Verify API URL
```javascript
// In browser console on production
console.log(process.env.NEXT_PUBLIC_API_URL);
// Should show HTTPS URL or be undefined (using relative)
```

### Test API Accessibility
```bash
# Test HTTPS API
curl https://befreefitness.ai/api/healthz

# Test HTTP (should fail in production browser)
curl http://34.239.119.192:4000/api/healthz
```

---

## Lessons Learned

1. **HTTPS Requires HTTPS Resources**: All resources on HTTPS page must be HTTPS
2. **Environment Variables Critical**: Never hardcode URLs
3. **Relative URLs Safe**: Use relative URLs when API is on same domain
4. **Nginx Proxy**: Simplest solution - proxy keeps everything HTTPS
5. **Browser Blocks Mixed Content**: Security feature, cannot be bypassed client-side

---

## Related Issues

- **NEXT_PUBLIC_API_URL Not Set**: Falls back to localhost
- **Nginx Configuration**: Proxy setup for API routes
- **Production Environment Variables**: Missing or incorrect configuration

---

## Quick Fix Checklist

When seeing mixed content errors:

- [ ] Check if page is HTTPS
- [ ] Verify API URL is HTTPS (not HTTP)
- [ ] Check `NEXT_PUBLIC_API_URL` environment variable
- [ ] Use relative URLs if API is on same domain
- [ ] Set up Nginx proxy for API routes
- [ ] Test with browser DevTools Network tab
- [ ] Verify no hardcoded HTTP URLs in code

---

**Last Updated**: 2025-10-29  
**Status**: Verified Solution

