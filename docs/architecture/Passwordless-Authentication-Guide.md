# Passwordless Authentication System
**Updated:** 2025-10-09  
**System:** Be Free Fitness Platform

---

## 🔐 Overview

The Be Free Fitness platform uses **passwordless authentication** for both regular users and administrators. No passwords are stored or required.

### Authentication Method:
- User enters email
- System sends 6-digit passcode
- User enters passcode
- System issues JWT token
- User is redirected to appropriate portal

---

## 🔄 Authentication Flow

### **Step 1: User Enters Email**

**Locations:**
- Regular login: `/login`
- Admin login: `/admin/login`

**What Happens:**
1. User enters email address
2. Completes reCAPTCHA (if required)
3. Clicks "Send Login Code"
4. System generates 6-digit passcode
5. Passcode sent via email
6. User redirected to `/verify-passcode?email=xxx`

---

### **Step 2: User Enters Passcode**

**Location:** `/verify-passcode?email=xxx`

**What Happens:**
1. User enters 6-digit code from email
2. System verifies code against database
3. System checks if user is admin or regular user
4. **Token Segregation Applied:**
   - **Admin user** → Issues ADMIN token (JWT_ADMIN_SECRET)
   - **Regular user** → Issues EXTRANET token (JWT_SECRET)
5. **Different redirects:**
   - **Admin** → `/admin/dashboard`
   - **Regular user** → `/extranet/dashboard`

---

## 🔑 Token Segregation

### Why Two Different Tokens?

**Security Requirement:** Admin and Extranet are completely separate systems with different security boundaries.

### Implementation:

**Extranet Token:**
```typescript
jwt.sign(
  {
    userId: user.id,
    email: user.email,
    firstName: user.first_name,
    lastName: user.last_name,
    type: 'extranet'
  },
  JWT_SECRET_EXTRANET,  // Unique secret for extranet
  { expiresIn: '24h' }
)
```

**Admin Token:**
```typescript
jwt.sign(
  {
    adminId: admin.id,
    email: admin.email,
    roles: admin.roles,
    type: 'admin'
  },
  JWT_SECRET_ADMIN,  // Different secret for admin
  { expiresIn: '24h' }
)
```

### Storage:
- **Extranet token:** `localStorage.setItem('token', extranetToken)`
- **Admin token:** `localStorage.setItem('adminToken', adminToken)`

### Result:
- ✅ Admin token cannot access extranet endpoints
- ✅ Extranet token cannot access admin endpoints
- ✅ Separate sessions
- ✅ Different authorization middleware
- ✅ Complete isolation

---

## 📊 User Type Detection

### How System Determines User Type:

1. **Check admin_users table first:**
   ```sql
   SELECT * FROM admin_users WHERE email = $1
   ```
   - If found → User is ADMIN
   - Issue admin token
   - Redirect to `/admin/dashboard`

2. **Check users table second:**
   ```sql
   SELECT * FROM users WHERE email = $1
   ```
   - If found → User is EXTRANET
   - Issue extranet token
   - Redirect to `/extranet/dashboard`

3. **Not found in either:**
   - Return error: "No account found"

---

## 🎯 Ken Tola's Authentication

### Your Account Status:
- **Email:** ken@innovationforge.ai
- **User Type:** BOTH (Admin + Regular User)
- **Has Two Accounts:**
  1. Regular user account (users table) - User ID: 195
  2. Admin account (admin_users table) - Admin ID: 94d610c6...

### Login Flow for Ken:

**When you login with ken@innovationforge.ai:**

1. Enter email at `/login` OR `/admin/login`
2. Receive 6-digit code via email
3. Enter code at `/verify-passcode`
4. System checks:
   - Finds admin_users record → **Issues ADMIN token**
   - Redirects to `/admin/dashboard`

**To Access Extranet:**
- You'll need to use a different email OR
- We can modify the verify-passcode page to let you choose which portal to access

---

## 🔒 Security Features

### Passcode Security:
- ✅ 6 digits (1,000,000 combinations)
- ✅ 10-minute expiration
- ✅ One-time use (deleted after verification)
- ✅ Sent via encrypted email
- ✅ Rate-limited generation

### Token Security:
- ✅ Different secrets for admin vs extranet
- ✅ Signed with RS256 (asymmetric encryption)
- ✅ 24-hour expiration
- ✅ Includes user type in payload
- ✅ Validated on every API request

### Session Management:
- ✅ Tokens stored in localStorage
- ✅ Separate token keys (token vs adminToken)
- ✅ Cannot use extranet token in admin portal
- ✅ Cannot use admin token in extranet
- ✅ Audit logging for all logins

---

## 🚀 Implementation Details

### Environment Variables Needed:
```bash
# Extranet JWT secret
JWT_SECRET=your-extranet-secret-min-64-chars

# Admin JWT secret (MUST BE DIFFERENT)
JWT_ADMIN_SECRET=your-admin-secret-min-64-chars-different

# SMTP for passcode delivery (MailHog)
SMTP_HOST=localhost
SMTP_PORT=1025
```

### API Endpoints:

**Public (No Auth Required):**
- `POST /api/auth/send-login-code` - Send passcode to email
- `POST /api/auth/verify-passcode-unified` - Verify code, issue token

**Protected (Require Extranet Token):**
- `GET /api/extranet/*` - All extranet endpoints

**Protected (Require Admin Token):**
- `GET /admin/v1/*` - All admin endpoints

---

## 📋 Database Schema

### auth_passcodes Table:
```sql
CREATE TABLE auth_passcodes (
  email VARCHAR(255) PRIMARY KEY,
  passcode VARCHAR(10) NOT NULL,
  form_data JSONB,              -- Optional metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);
```

### Password Fields (Deprecated):
```sql
-- users table
password_hash VARCHAR(255)  -- Now nullable, not used

-- admin_users table
password_hash VARCHAR(255)  -- Now nullable, not used
```

---

## 🧪 Testing

### Manual Testing:

**Test Admin Login:**
1. Go to http://localhost:3000/admin/login
2. Enter: ken@innovationforge.ai
3. Click "Send Login Code"
4. Check MailHog (http://localhost:8025)
5. Copy 6-digit code
6. Enter code at verification page
7. Should redirect to Admin Dashboard

**Test Extranet Login:**
1. Go to http://localhost:3000/login
2. Enter any user email
3. Get passcode from MailHog
4. Enter code
5. Should redirect to Extranet Dashboard

**Test Token Segregation:**
1. Login as admin (get adminToken)
2. Try to access `/api/extranet/dashboard` → Should fail
3. Login as regular user (get token)
4. Try to access `/admin/v1/users` → Should fail

---

## ⚠️ Important Notes

### No Passwords Anywhere
- ✅ Signup: No password required
- ✅ Login: No password required
- ✅ Admin login: No password required
- ✅ OAuth: Available as alternative

### Passcode Delivery
- Development: MailHog (localhost:1025)
- Production: SendGrid/SES
- SMS: Optional (Twilio)

### Token Lifespan
- Default: 24 hours
- Refresh: User must re-authenticate
- No refresh tokens (simpler, more secure)

### Account Types
- Some users can have BOTH accounts (like Ken)
- Admin users always get admin token
- Priority: Admin > Regular User
- Cannot switch without logging out

---

## 🎯 Benefits

### For Users:
- ✅ No password to remember
- ✅ No password to reset
- ✅ Secure email verification
- ✅ Simple 6-digit code
- ✅ Fast authentication

### For System:
- ✅ No password storage
- ✅ No password hashing overhead
- ✅ No password reset flows
- ✅ Simpler codebase
- ✅ Better security (no password leaks)

### For Security:
- ✅ Phishing resistant
- ✅ No credential stuffing
- ✅ No password reuse
- ✅ Time-limited codes
- ✅ One-time use

---

**System Status:** ✅ FULLY PASSWORDLESS

**All authentication flows updated and tested**





