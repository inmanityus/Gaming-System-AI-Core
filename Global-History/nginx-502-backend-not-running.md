# Solution: Nginx 502 Bad Gateway - Backend Not Running

**Issue ID**: nginx-502-backend-not-running  
**Date Solved**: 2025-10-29  
**Project**: Production deployment diagnostics  
**Severity**: Critical  
**Category**: deployment, production-issues, nginx

---

## Problem Statement

Nginx returns 502 Bad Gateway when the web application it's trying to proxy to is not running. This is a common deployment issue where the reverse proxy is healthy but the backend application has crashed or isn't started.

**Error:** 502 Bad Gateway on production domain  
**Impact:** Site completely down, users cannot access application

---

## Root Cause

**Nginx Configuration**: ✅ Working correctly  
**Backend Application**: ❌ NOT RUNNING  

The Next.js web application was not running on port 3000, but Nginx was configured to proxy all requests to `http://localhost:3000`. When Nginx attempted to forward requests, it couldn't connect to the non-existent backend service.

**Chain of Events:**
1. User requests `https://befreefitness.ai`
2. Nginx receives request
3. Nginx tries to proxy to `http://localhost:3000`
4. Connection fails (nothing listening on port 3000)
5. Nginx returns 502 Bad Gateway

---

## Investigation Steps

### Step 1: Test Nginx Status
```bash
curl -I https://befreefitness.ai
# Returns: 502 Bad Gateway
```

### Step 2: Test Backend Port
```bash
# From production server
curl http://localhost:3000
# Connection refused / timeout

# Check if anything is listening
netstat -tuln | grep 3000
# No output = nothing listening
```

### Step 3: Check Process Manager
```bash
# PM2 example
pm2 status
# Shows: web-app status "stopped" or "errored"

# Check logs
pm2 logs web-app
# Shows crash reason or startup errors
```

### Step 4: Verify API (if separate)
```bash
# API on different port
curl http://localhost:4000/healthz
# Status: 200 OK (API is working)

# This confirms Nginx and system are fine
# Problem is specifically the web app on port 3000
```

---

## Solution

### Immediate Fix: Start the Backend

```bash
# Option 1: Start with PM2
pm2 start ecosystem.config.js
# OR
pm2 start web --name web-app

# Option 2: Start directly
cd /path/to/web/app
npm start

# Verify it's running
curl http://localhost:3000
# Should return: 200 OK (or HTML content)
```

### Diagnose Why It Stopped

```bash
# Check PM2 logs for crash reason
pm2 logs web-app --lines 50

# Common causes:
# 1. Missing environment variables
# 2. Build failures (.next/BUILD_ID missing)
# 3. Port already in use
# 4. Memory errors
# 5. Configuration errors
```

### Permanent Fix: Auto-restart

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'web-app',
    script: 'npm',
    args: 'start',
    instances: 1,
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    error_file: './logs/web-error.log',
    out_file: './logs/web-out.log'
  }]
};
```

---

## Prevention

### 1. Health Check Endpoints
```typescript
// Add to Next.js app
// app/api/health/route.ts
export async function GET() {
  return Response.json({ status: 'healthy' }, { status: 200 });
}
```

### 2. Nginx Health Check
```nginx
# nginx.conf
upstream web_backend {
    server localhost:3000;
    
    # Health check
    health_check uri=/api/health;
}

server {
    location /api/health {
        proxy_pass http://web_backend;
    }
}
```

### 3. Monitoring
```bash
# Cron job to check and restart
*/5 * * * * pm2 status | grep -q "stopped.*web-app" && pm2 restart web-app
```

### 4. PM2 Auto-restart
```javascript
// ecosystem.config.js - ensure autorestart is true
autorestart: true,
max_restarts: 10,
min_uptime: '10s'
```

---

## Testing

### Verify Fix
```bash
# 1. Check backend is running
curl http://localhost:3000/api/health
# Expected: {"status":"healthy"}

# 2. Check through Nginx
curl https://yourdomain.com/api/health
# Expected: {"status":"healthy"}

# 3. Check full site
curl -I https://yourdomain.com
# Expected: 200 OK
```

---

## Lessons Learned

1. **502 ≠ Nginx Problem**: 502 usually means backend is down, not Nginx
2. **Always Check Backend First**: Before debugging Nginx config, verify backend is running
3. **Separate Processes**: If API works but web doesn't, check process manager for specific app
4. **Logs Are Critical**: PM2/logs reveal why process stopped
5. **Health Checks Help**: Add endpoints to diagnose quickly

---

## Related Issues

- **Process Manager Not Running App**: PM2 not starting web app
- **Next.js Production Build Failures**: Build errors preventing startup
- **Port Conflicts**: Another process using port 3000
- **Environment Variable Issues**: Missing vars causing startup failures

---

## Quick Diagnostic Checklist

When you see 502 Bad Gateway:

- [ ] Check if backend is running: `curl http://localhost:3000`
- [ ] Check process manager: `pm2 status` or `systemctl status`
- [ ] Check logs: `pm2 logs` or journalctl
- [ ] Check if port is in use: `netstat -tuln | grep 3000`
- [ ] Verify Nginx config is correct
- [ ] Test API separately (if on different port)
- [ ] Check environment variables
- [ ] Verify build files exist

---

**Last Updated**: 2025-10-29  
**Status**: Verified Solution

