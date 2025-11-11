# Deployment Loop Prevention Rule

## 🚨 CRITICAL RULE: NO DEPLOYMENT LOOPS

**PROBLEM**: AI gets stuck in endless loops during deployment, repeatedly:
- Checking SSH connections
- Restarting services
- Checking logs
- Debugging the same issues
- Not making progress

## 🎯 MANDATORY DEPLOYMENT PROTOCOL

### **BEFORE ANY DEPLOYMENT**:
1. **Set Clear Success Criteria**: Define exactly what "working" means
2. **Identify Single Point of Failure**: Focus on ONE issue at a time
3. **Set Maximum Attempts**: Never try the same fix more than 3 times
4. **Use Independent Commands**: Never use watchdogs for deployment commands

### **DEPLOYMENT APPROACH**:
1. **Build Locally First**: Always build applications locally before deploying
2. **Deploy in Order**: API first, then Web, then test
3. **Test Immediately**: After each deployment step, test once
4. **If Test Fails**: Stop, analyze, fix locally, redeploy
5. **Never Debug on Server**: If something fails, fix locally and redeploy

### **LOOP PREVENTION RULES**:
- ❌ **NEVER** check logs more than once per issue
- ❌ **NEVER** restart services more than twice
- ❌ **NEVER** SSH into server more than 3 times per deployment
- ❌ **NEVER** use watchdogs for deployment commands
- ❌ **NEVER** debug the same issue repeatedly

### **SUCCESS CRITERIA**:
- ✅ **API**: Responds to `/health` endpoint
- ✅ **Web**: Serves pages without 404 errors
- ✅ **Database**: Test accounts exist and are accessible
- ✅ **Login**: Returns proper error messages (not "Failed to fetch")

### **IF STUCK**:
1. **STOP IMMEDIATELY**
2. **Identify the ONE specific issue**
3. **Fix it locally**
4. **Deploy the fix**
5. **Test once**
6. **If it works, move to next step**
7. **If it fails, STOP and ask user for guidance**

## 🚀 DEPLOYMENT CHECKLIST

### **Step 1: Build Locally**
```bash
pnpm --filter api build
pnpm --filter web build
```

### **Step 2: Deploy API**
```bash
scp -i "key.pem" -r "apps/api/dist" user@server:/path/
ssh -i "key.pem" user@server "pm2 restart api"
curl -s http://server:4000/health
```

### **Step 3: Deploy Web**
```bash
scp -i "key.pem" -r "apps/web/.next" user@server:/path/
ssh -i "key.pem" user@server "pm2 restart web"
curl -s http://server/
```

### **Step 4: Test Login**
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"email":"test@example.com"}' http://server:4000/api/auth/send-login-code
```

### **Step 5: Verify Success**
- API responds with proper error message (not "Failed to fetch")
- Web serves pages without 404 errors
- Login shows user-friendly error messages

## ⚠️ EMERGENCY STOP CONDITIONS

**STOP IMMEDIATELY IF**:
- Same command fails 3 times
- SSH connection fails 2 times
- API doesn't respond after 2 restarts
- You're checking logs for the same issue twice
- You're restarting the same service twice

## 📋 POST-DEPLOYMENT VERIFICATION

**MUST VERIFY**:
1. API health endpoint responds
2. Web application serves pages
3. Login returns proper error messages
4. Test accounts exist in database
5. No "Failed to fetch" errors shown to users

---

**ENFORCEMENT**: This rule is MANDATORY for all deployments. Violation results in immediate stop and user notification.

**STATUS**: Active
**PRIORITY**: Critical
**APPLIES TO**: All deployment activities
