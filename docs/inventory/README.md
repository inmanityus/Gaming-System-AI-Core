# 📁 AWS Resource Inventory

**Purpose**: Complete inventory of ALL AWS resources for Gaming System AI Core project  
**Maintained By**: AI Agent (Claude Sonnet 4.5) + Project Team  
**Update Frequency**: After any AWS resource changes  
**Last Updated**: 2025-11-09

---

## 📋 FILES IN THIS DIRECTORY

### **aws-resources-complete.csv**
Complete inventory of all AWS resources with:
- Resource identification (ID, IP, hostname)
- AWS Console locations (exact paths)
- Authentication file paths (local)
- Access methods (SSM, SSH, CLI)
- Owner information
- Purpose descriptions
- Cost estimates

**Format**: CSV with headers  
**Columns**: ResourceType, ResourceName, ResourceID, IP_Address, Hostname, AWS_Console_Location, Status, Purpose, Owner, CreatedDate, MonthlyCost, Auth_File_Path, Access_Method, Notes

---

## 🔑 AUTHENTICATION FILES

### **auth/ Folder**
Contains all authentication files for AWS resources:

**SSH Keys**:
- `gaming-system-ai-core-admin.pem` - Master SSH key for all EC2 instances

**How to Use SSH Keys**:
```bash
# Linux/Mac
chmod 400 docs/inventory/auth/gaming-system-ai-core-admin.pem
ssh -i docs/inventory/auth/gaming-system-ai-core-admin.pem ubuntu@<IP_ADDRESS>

# Windows (PowerShell)
icacls "docs\inventory\auth\gaming-system-ai-core-admin.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
ssh -i "docs\inventory\auth\gaming-system-ai-core-admin.pem" ubuntu@<IP_ADDRESS>
```

**If SSH Key Missing**:
1. Check AWS Console: EC2 > Key Pairs > gaming-system-ai-core-admin
2. Cannot re-download private key (AWS limitation)
3. Create new key pair OR use SSM Session Manager

---

## 🔐 ENVIRONMENT VARIABLES

**Critical variables required for production** (store in `.env` file):

### **Database Access**:
```env
POSTGRES_PASSWORD=<strong-password-16+-chars>
POSTGRES_HOST=localhost
POSTGRES_PORT=5443
POSTGRES_DB=gaming_system_ai_core
POSTGRES_USER=postgres
```

### **Security**:
```env
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
ADMIN_API_KEYS=<generate-secure-admin-key>
KB_API_KEYS=<generate-api-keys>
```

### **Redis**:
```env
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
```

**CRITICAL**: Never commit .env file to git! (Already in .gitignore)

---

## 📊 RESOURCE SUMMARY

### **By Type**:
- **EC2 Instances**: 4 (1 running GPU training, 1 UE5 builder, 2 inference, 2 terminated)
- **S3 Buckets**: 3 (training, memory archive, consciousness)
- **IAM Roles**: 5 (SSM, ECS execution, task roles)
- **Security Groups**: 2 (services, GPU training)
- **ECS Services**: 15+ (all game services)
- **Other**: VPC, Subnets, SNS, SQS, ECR, CloudWatch, RDS, ElastiCache

### **By Owner**:
- **Claude-Sonnet-4.5**: GPU training instances (autonomous work)
- **Project-Team**: All other resources (user-created or pre-existing)
- **AWS-Default**: VPC, Subnets

### **Total Monthly Cost**: ~$2,000-2,500

---

## 🚨 SECURITY NOTES

### **Issues Found (2025-11-09 Foundation Audit)**:
- ✅ **5 CRITICAL fixed**: Hardcoded passwords, CORS vulnerabilities
- ⚠️ **3 CRITICAL open**: Payment exploits, 12 CORS issues  
- ⚠️ **6 HIGH open**: No authentication, race conditions

**See**: `../AUDIT-ISSUES-P0-CRITICAL.csv` for complete list

### **Security Best Practices**:
1. Always use environment variables for secrets
2. Never commit passwords/keys to git
3. Restrict CORS to specific domains
4. Implement authentication on all APIs
5. Use rate limiting
6. Validate all inputs

---

## 🔄 MAINTAINING THIS INVENTORY

### **When to Update**:
- After creating new AWS resources
- After terminating resources
- After changing resource configurations
- After security fixes
- Monthly cost review

### **How to Update**:
1. Edit `aws-resources-complete.csv`
2. Add new row with all columns filled
3. Update "Last Updated" note at bottom
4. Commit to git (but NOT auth files!)

### **Auto-Update Script** (Future):
```powershell
# Create script to auto-generate from AWS CLI
.\scripts\update-aws-inventory.ps1
```

---

## 📞 ACCESS METHODS

### **SSM Session Manager** (Preferred):
```bash
aws ssm start-session --target <INSTANCE_ID>
```
**Pros**: No SSH key needed, works through firewalls, logged  
**Cons**: Requires SSM agent running

### **SSH Direct**:
```bash
ssh -i docs/inventory/auth/gaming-system-ai-core-admin.pem ubuntu@<IP_ADDRESS>
```
**Pros**: Direct access, standard tooling  
**Cons**: Requires key, port 22 open

### **SSM Run Command**:
```bash
aws ssm send-command --instance-ids <INSTANCE_ID> --document-name "AWS-RunShellScript" --parameters commands="ls -la"
```
**Pros**: Remote execution, no interactive session needed  
**Cons**: Less flexible than SSH

---

## 🎯 QUICK REFERENCE

### **Current GPU Training Instance**:
- **ID**: i-0da704b9c213c0839
- **IP**: 54.147.14.199
- **Access**: `aws ssm start-session --target i-0da704b9c213c0839`
- **Purpose**: LoRA adapter training
- **Owner**: Claude Sonnet 4.5 (autonomous session 2025-11-09)

### **Production Services**:
- **ECS Cluster**: gaming-system-cluster
- **Services**: 15+ running
- **Access**: AWS Console > ECS

### **Data Storage**:
- **Training**: s3://body-broker-training-9728
- **Memory**: s3://perpetual-consciousness-memory-6477
- **Database**: perpetual-consciousness-db.cal6eoegigyq.us-east-1.rds.amazonaws.com

---

**Maintained By**: Claude Sonnet 4.5 (AI Agent)  
**Project**: Gaming System AI Core - The Body Broker  
**Last Major Update**: 2025-11-09 (Foundation audit + new GPU instance)

