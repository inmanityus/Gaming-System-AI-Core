# Background Process Management Rule

**Priority:** High  
**Applies To:** All web development projects (React, Next.js, APIs, full-stack)  
**Status:** Active

---

## 🎯 CORE PRINCIPLE

**Always attempt to start development servers as background processes FIRST.**

Only use foreground/interactive shells for debugging when background startup fails.

---

## 📋 STANDARD WORKFLOW

### Step 1: Attempt Background Start
```powershell
# Try starting as background process
Start-Process pwsh -ArgumentList "-Command", "cd path; npm run dev"

# Wait 12 seconds for startup
Start-Sleep -Seconds 12

# Check if service is responding
Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5
```

### Step 2: If Background Fails → Diagnose Immediately

**Common Issues Checklist:**
1. ✅ **TypeScript Errors** (Most common for React/Next.js)
   ```bash
   npx tsc --noEmit
   ```

2. ✅ **Port Conflicts**
   ```powershell
   netstat -ano | findstr :3000
   netstat -ano | findstr :4000
   ```

3. ✅ **Missing Dependencies**
   ```bash
   npm install  # or pnpm install
   ```

4. ✅ **ESLint Errors** (Sometimes blocks startup)
   ```bash
   npm run lint
   ```

### Step 3: Run in Foreground to See Errors
```powershell
# Run in current shell to see real-time output
cd path
npm run dev
```

### Step 4: Fix Issues
- Fix TypeScript errors shown in output
- Install missing dependencies
- Fix lint errors if blocking
- Resolve port conflicts

### Step 5: Verify Works in Foreground
- Wait for "Ready on http://localhost:3000"
- Test with browser or curl
- Confirm no errors

### Step 6: Shut Down Foreground Process
```
Ctrl+C  # Stop the process
```

### Step 7: Restart as Background
```powershell
Start-Process pwsh -ArgumentList "-Command", "cd path; npm run dev"
```

### Step 8: Verify Background Health
```powershell
Start-Sleep -Seconds 12
Invoke-WebRequest -Uri "http://localhost:3000"
```

---

## ⚡ WHY THIS PATTERN?

### Benefits of Background First
- ✅ **Non-blocking** - Terminal remains free
- ✅ **Clean workspace** - No cluttered output
- ✅ **Easy management** - Can run multiple services
- ✅ **Professional** - Mimics production behavior

### When Foreground is Needed
- ❌ Background process fails silently
- ❌ Need to see real-time error messages
- ❌ Debugging startup issues
- ❌ TypeScript errors blocking compilation

---

## 🔧 TECHNOLOGY-SPECIFIC GUIDANCE

### React / Next.js Projects
**Most Common Issue:** TypeScript errors

**Check Before Starting:**
```bash
cd apps/web
npx tsc --noEmit
```

**Common Errors:**
- Missing type definitions
- Import path errors
- Prop type mismatches
- Missing .env variables

### API / Backend Projects
**Most Common Issues:** Database connection, environment variables

**Check Before Starting:**
```bash
cd apps/api
npx tsc --noEmit  # Check TypeScript
psql -h localhost -U postgres -d dbname -c "SELECT 1;"  # Check DB
```

**Common Errors:**
- Database not running
- Missing DATABASE_URL
- Port already in use
- Missing JWT secrets

---

## 🚨 CRITICAL RULES

### DO:
- ✅ **Always try background first** - Don't assume it will fail
- ✅ **Immediate diagnostics** - Run `npx tsc --noEmit` right away if fails
- ✅ **Clean up shells** - ALWAYS close foreground shells when done
- ✅ **Verify health** - Check service responds after background start
- ✅ **Document ports** - Know which ports are app vs services (MCP servers)

### DON'T:
- ❌ **Never start foreground first** - Always try background
- ❌ **Never leave shells open** - Close when debugging complete
- ❌ **Never skip TypeScript check** - Most common React/Next.js issue
- ❌ **Never assume background worked** - Always verify with health check
- ❌ **Never kill all Node processes** - Use port-based killing

---

## 📊 COMMON ISSUES BY PROJECT TYPE

### Next.js Web App (Port 3000)
1. TypeScript errors (70%)
2. Port in use (15%)
3. Missing .env (10%)
4. Missing dependencies (5%)

**Fix Order:**
```bash
npx tsc --noEmit          # Fix TypeScript
netstat -ano | findstr :3000  # Check port
cat .env.example          # Check required vars
npm install               # Install deps
```

### Express/Fastify API (Port 4000)
1. Database connection (40%)
2. TypeScript errors (30%)
3. Missing .env (20%)
4. Port in use (10%)

**Fix Order:**
```bash
psql -h localhost -U postgres -c "SELECT 1;"  # Test DB
npx tsc --noEmit          # Fix TypeScript
cat .env.example          # Check required vars
netstat -ano | findstr :4000  # Check port
```

---

## 💡 EXAMPLES

### Example 1: Successful Background Start
```powershell
PS> Start-Process pwsh -ArgumentList "-Command", "cd E:\Project\apps\web; pnpm run dev"
PS> Start-Sleep -Seconds 12
PS> Invoke-WebRequest http://localhost:3000
StatusCode: 200 ✅
```

### Example 2: Background Fails → Foreground Debug
```powershell
PS> Start-Process pwsh -ArgumentList "-Command", "cd E:\Project\apps\web; pnpm run dev"
PS> Start-Sleep -Seconds 12
PS> Invoke-WebRequest http://localhost:3000
ERROR: Connection refused ❌

# Check TypeScript immediately
PS> cd E:\Project\apps\web
PS> npx tsc --noEmit
ERROR: Type 'string' is not assignable to type 'number' ❌

# Run foreground to see full errors
PS> pnpm run dev
# See errors, fix them
# Ctrl+C to stop

# Restart as background
PS> Start-Process pwsh -ArgumentList "-Command", "cd E:\Project\apps\web; pnpm run dev"
PS> Start-Sleep -Seconds 12
PS> Invoke-WebRequest http://localhost:3000
StatusCode: 200 ✅
```

---

## 🔄 INTEGRATION WITH OTHER RULES

### Works With:
- **MCP Server Protection** - Background processes don't interfere with MCP
- **Port-Based Shutdown** - Can kill specific ports without affecting background services
- **Service Management** - Background processes easier to manage than foreground

### Conflicts With:
- None - This is a best practice that complements all other rules

---

## 📈 SUCCESS METRICS

You're following this rule correctly when:
- ✅ First attempt is always background start
- ✅ TypeScript checked immediately if React/Next.js background fails
- ✅ Foreground only used for debugging
- ✅ Foreground shells closed after fixing issues
- ✅ Services run in background during normal development

---

## 🎓 LEARNING PROGRESSION

### Beginner
- Understand background vs foreground
- Know how to start processes in background
- Remember to close foreground shells

### Intermediate
- Diagnose TypeScript errors quickly
- Know common issues per project type
- Transition smoothly foreground → background

### Advanced
- Predict likely issues before running
- Set up automated health checks
- Integrate into startup scripts

---

**Status:** Active  
**Enforcement:** Automatic via AI session rules  
**Added:** 2025-10-17 (User-provided rule)

---

**Remember: Background first, foreground for debugging only, always clean up! 🚀**

