# 🔑 SSH Key Setup Instructions

**Key Name**: gaming-system-ai-core-admin  
**File Location**: `docs/inventory/auth/gaming-system-ai-core-admin.pem`  
**Used For**: All EC2 instance SSH access

---

## ⚠️ IF KEY FILE IS MISSING

### **The Issue**:
AWS EC2 key pairs are generated once and the private key (.pem file) can only be downloaded at creation time. If the file is missing from this folder, it means it was never saved or was deleted.

### **Solution Options**:

#### **Option 1: Check for Existing Key** (Try First)
The key might be in another location:
```powershell
# Search entire system
Get-ChildItem -Path C:\ -Recurse -Filter "*gaming-system-ai-core-admin.pem" -ErrorAction SilentlyContinue

# Common locations
Get-ChildItem -Path "$env:USERPROFILE\.ssh" -Filter "*.pem"
Get-ChildItem -Path ".cursor\aws" -Filter "*.pem"
```

#### **Option 2: Use SSM Session Manager** (No Key Needed)
```bash
# Start interactive session
aws ssm start-session --target <INSTANCE_ID>

# Example
aws ssm start-session --target i-0da704b9c213c0839
```

**Pros**: No key needed, works immediately  
**Cons**: Requires SSM agent running on instance

#### **Option 3: Create New Key Pair**
```bash
# Create new key pair
aws ec2 create-key-pair --key-name gaming-system-new-key --query 'KeyMaterial' --output text > docs/inventory/auth/gaming-system-new-key.pem

# Set permissions
chmod 400 docs/inventory/auth/gaming-system-new-key.pem  # Unix
icacls "docs\inventory\auth\gaming-system-new-key.pem" /inheritance:r  # Windows

# Update instances to use new key (requires stop/start)
```

**Pros**: Fresh start, full control  
**Cons**: Need to update all instances

---

## ✅ KEY SETUP (If You Have The File)

### **Unix/Linux/Mac**:
```bash
# Set correct permissions (required by SSH)
chmod 400 docs/inventory/auth/gaming-system-ai-core-admin.pem

# Test connection
ssh -i docs/inventory/auth/gaming-system-ai-core-admin.pem ubuntu@<IP_ADDRESS>
```

### **Windows**:
```powershell
# Set correct permissions
icacls "docs\inventory\auth\gaming-system-ai-core-admin.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"

# Test connection
ssh -i "docs\inventory\auth\gaming-system-ai-core-admin.pem" ubuntu@<IP_ADDRESS>
```

---

## 📋 INSTANCE ACCESS REFERENCE

### **Current GPU Training Instance**:
```bash
# SSM (recommended)
aws ssm start-session --target i-0da704b9c213c0839

# SSH (if key available)
ssh -i docs/inventory/auth/gaming-system-ai-core-admin.pem ubuntu@54.147.14.199
```

### **UE5 Builder**:
```bash
# SSM
aws ssm start-session --target i-0f27f842a79e1c59e

# SSH
ssh -i docs/inventory/auth/gaming-system-ai-core-admin.pem ubuntu@3.95.183.186
```

### **Gold GPU Instance**:
```bash
aws ssm start-session --target i-02f620203b6ccd334
# OR
ssh -i docs/inventory/auth/gaming-system-ai-core-admin.pem ubuntu@54.234.135.254
```

---

## 🔒 SECURITY BEST PRACTICES

1. **Never commit .pem files to git** (already in .gitignore)
2. **Store keys securely** (encrypted folder, password manager)
3. **Use SSM when possible** (more secure, audited)
4. **Rotate keys periodically** (every 90 days recommended)
5. **Limit key access** (only authorized team members)

---

**Created**: 2025-11-09  
**Purpose**: Help team access AWS resources securely  
**Maintained By**: Claude Sonnet 4.5

