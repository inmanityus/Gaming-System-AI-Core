# 🏷️ AWS Resource Naming and Tracking - MANDATORY RULE

**Status**: MANDATORY  
**Enforcement**: 100% - Zero tolerance for unnamed resources  
**Applies To**: ALL AWS resources in this project

---

## 🚨 CRITICAL RULE: RESOURCE NAMING CONVENTION

### **ALL AWS Resources MUST Follow This Pattern**:

```
AI-Gaming-<WorkUnit>
```

**Where**:
- `AI-Gaming` = Project identifier (consistent across all resources)
- `<WorkUnit>` = Descriptive name of what the resource does

---

## ✅ NAMING EXAMPLES

### EC2 Instances
- ✅ `AI-Gaming-UE5-Builder` (UE5 build server)
- ✅ `AI-Gaming-Gold-GPU-1` (Gold tier inference)
- ✅ `AI-Gaming-Silver-GPU-1` (Silver tier inference)
- ❌ `instance-123` (NO!)
- ❌ `gpu-server` (NO!)

### ECS Services
- ✅ `AI-Gaming-Weather` (weather manager)
- ✅ `AI-Gaming-Time` (time manager)
- ✅ `AI-Gaming-EventBus` (event bus)
- ❌ `weather-manager` (missing prefix - rename!)
- ❌ `service-1` (NO!)

### Security Groups
- ✅ `AI-Gaming-Services-SG` (ECS services security group)
- ✅ `AI-Gaming-GPU-SG` (GPU instances security group)
- ❌ `default` (NO!)
- ❌ `sg-123abc` (NO!)

### IAM Roles
- ✅ `AI-Gaming-ECS-Execution` (ECS execution role)
- ✅ `AI-Gaming-Weather-Task` (Weather manager task role)
- ❌ `ecsTaskRole` (missing prefix - rename!)

### Load Balancers
- ✅ `AI-Gaming-Public-ALB` (public-facing load balancer)
- ✅ `AI-Gaming-Internal-NLB` (internal network load balancer)

### SNS/SQS
- ✅ `AI-Gaming-Weather-Events` (SNS topic)
- ✅ `AI-Gaming-Weather-Queue` (SQS queue)

---

## 📊 MANDATORY: RESOURCE TRACKING CSV

### **File Location**: `Project-Management/aws-resources.csv`

### **Required Columns**:
1. `ResourceType` - Type of AWS resource (EC2-Instance, ECS-Service, etc.)
2. `ResourceName` - Human-readable name (AI-Gaming-<WorkUnit>)
3. `ResourceID` - AWS ID (i-xxx, sg-xxx, arn:xxx)
4. `IP/Hostname` - IP address or hostname (if applicable)
5. `ConsoleLocation` - Where to find in AWS Console
6. `Status` - Current status (Active, Running, Stopped)
7. `Purpose` - What this resource does
8. `CreatedDate` - When created (YYYY-MM-DD)
9. `Cost` - Estimated monthly cost
10. `Notes` - Additional information

### **CSV MUST BE UPDATED**:

#### When Creating Resources:
```powershell
# Example: After creating EC2 instance
$newRow = "EC2-Instance,AI-Gaming-Gold-GPU-1,i-0abc123,54.123.45.67,EC2 > Instances,Running,Gold tier AI inference,2025-11-07,\$730/mo,g5.xlarge with Qwen2.5-3B"
Add-Content -Path "Project-Management/aws-resources.csv" -Value $newRow
git add Project-Management/aws-resources.csv
git commit -m "docs: Add AI-Gaming-Gold-GPU-1 to resource tracking"
```

#### When Deleting Resources:
```powershell
# Update Status column to "Deleted" with deletion date in Notes
# Keep in CSV for historical tracking
```

#### When Modifying Resources:
```powershell
# Update relevant columns (Status, Cost, Notes, etc.)
git add Project-Management/aws-resources.csv
git commit -m "docs: Update resource tracking - <change description>"
```

---

## 🔍 AUDIT PROCESS (Run Monthly)

### Audit Script Location: `scripts/audit-aws-resources.ps1`

```powershell
# Compare CSV with actual AWS resources
# Report:
# - Resources in AWS not in CSV (NEW - need to add)
# - Resources in CSV not in AWS (DELETED - update status)
# - Resources with name mismatches (RENAME - fix naming)
```

---

## 🚨 ENFORCEMENT

### Before ANY AWS Resource Creation:
1. ✅ Choose proper name: `AI-Gaming-<WorkUnit>`
2. ✅ Apply name tag: `Key=Name,Value=AI-Gaming-<WorkUnit>`
3. ✅ Add to CSV immediately after creation
4. ✅ Commit CSV update to git

### When Discovering Unnamed Resources:
1. ⚠️ Immediately rename with proper convention
2. ⚠️ Update CSV
3. ⚠️ Document in commit message

### Violations:
- ❌ Creating resource without proper name = VIOLATION
- ❌ Not updating CSV = VIOLATION  
- ❌ Using generic names = VIOLATION

---

## 📚 BENEFITS

### For Team:
- **Know what everything is** at a glance
- **Track costs** per component
- **Find resources** easily in Console
- **Audit compliance** automatically

### For Operations:
- **Cost optimization** (know what to scale down)
- **Resource cleanup** (find unused resources)
- **Disaster recovery** (know what to restore)
- **Capacity planning** (track growth)

---

## ✅ INTEGRATION

### With Session Work:
- Update CSV during every AWS operation
- Commit CSV with related code changes
- Review CSV in session handoffs

### With Automation:
- Scripts read CSV to know what exists
- Scripts update CSV after operations
- Scripts validate naming compliance

---

**Rule Created**: 2025-11-07  
**Enforcement**: MANDATORY - All AWS resources  
**File**: Project-Management/aws-resources.csv  
**Pattern**: AI-Gaming-<WorkUnit>  
**Compliance**: 100% required

