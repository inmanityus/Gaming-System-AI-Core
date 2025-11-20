# AWS Resource Naming Convention - MANDATORY

## 🚨 CRITICAL RULE: Project-Based AWS Resource Naming

**ENFORCEMENT LEVEL**: MAXIMUM - Zero tolerance for non-compliant naming
**SCOPE**: All AWS resources created via Terraform, CloudFormation, AWS CLI, or SDK
**EXCEPTION**: Multi-tenant server deployments (do not apply this rule)

---

## Naming Convention

### Pattern
```
<Project-Name>-<Work>
```

### Components

**`<Project-Name>`**:
- Lowercase project identifier
- Must match existing project resources if any exist
- Examples: `befreefitness-phase3`, `gaming-system`, `ai-core`

**`<Work>`**:
- One or two words describing resource purpose
- Lowercase with hyphens
- Must be descriptive and specific
- Examples: `videos`, `models`, `backups`, `ml-intermediate`, `api-server`, `redis-cache`

---

## Detection and Compliance

### Before Creating AWS Resources

1. **Check for Existing Resources**:
   ```bash
   # List S3 buckets
   aws s3 ls
   
   # List RDS instances
   aws rds describe-db-instances --query 'DBInstances[*].DBInstanceIdentifier'
   
   # List EC2 instances
   aws ec2 describe-instances --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value]'
   ```

2. **Extract Project Name**:
   - If resources exist: Extract prefix from first resource name
   - If new project: Use project name from `project-config.md` or repository name

3. **Verify Consistency**:
   - ALL resources MUST use the same `<Project-Name>` prefix
   - NEVER mix naming conventions within a project

---

## Examples

### Current Project: Be Free Fitness
**Project Name**: `befreefitness-phase3`

**Compliant Names**:
- ✅ `befreefitness-phase3-videos` (S3 bucket for user videos)
- ✅ `befreefitness-phase3-models` (S3 bucket for ML models)
- ✅ `befreefitness-phase3-backups` (S3 bucket for backups)
- ✅ `befreefitness-phase3-ml-intermediate` (S3 bucket for processing)
- ✅ `befreefitness-phase3-aurora-cluster` (RDS Aurora cluster)
- ✅ `befreefitness-phase3-redis` (ElastiCache Redis)
- ✅ `befreefitness-phase3-api-server` (EC2 instance)
- ✅ `befreefitness-phase3-ml-worker-profile` (IAM instance profile)
- ✅ `befreefitness-phase3-s3-kms-key` (KMS key for S3)

**Non-Compliant Names** (FORBIDDEN):
- ❌ `videos-bucket` (missing project prefix)
- ❌ `bff-videos` (wrong project prefix)
- ❌ `production-videos` (generic name, missing project)
- ❌ `my-app-videos` (generic name, missing project)
- ❌ `videos` (no project context)

---

## Resource-Specific Guidelines

### S3 Buckets
```terraform
resource "aws_s3_bucket" "videos" {
  bucket = "${var.project_name}-videos"
  
  tags = {
    Name    = "${var.project_name}-videos"
    Purpose = "User uploaded videos for analysis"
  }
}
```

### RDS Instances
```terraform
resource "aws_db_instance" "primary" {
  identifier = "${var.project_name}-db-primary"
  
  tags = {
    Name = "${var.project_name}-db-primary"
  }
}
```

### EC2 Instances
```terraform
resource "aws_instance" "api_server" {
  tags = {
    Name = "${var.project_name}-api-server"
  }
}
```

### Lambda Functions
```terraform
resource "aws_lambda_function" "processor" {
  function_name = "${var.project_name}-video-processor"
  
  tags = {
    Name = "${var.project_name}-video-processor"
  }
}
```

### IAM Roles and Policies
```terraform
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-ecs-task-role"
  
  tags = {
    Name = "${var.project_name}-ecs-task-role"
  }
}

resource "aws_iam_policy" "s3_access" {
  name = "${var.project_name}-s3-access-policy"
  
  tags = {
    Name = "${var.project_name}-s3-access-policy"
  }
}
```

### Security Groups
```terraform
resource "aws_security_group" "api" {
  name        = "${var.project_name}-api-sg"
  description = "Security group for API server"
  
  tags = {
    Name = "${var.project_name}-api-sg"
  }
}
```

### KMS Keys
```terraform
resource "aws_kms_key" "s3" {
  description = "KMS key for S3 bucket encryption"
  
  tags = {
    Name = "${var.project_name}-s3-kms-key"
  }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${var.project_name}-s3"
  target_key_id = aws_kms_key.s3.key_id
}
```

### Auto Scaling Groups
```terraform
resource "aws_autoscaling_group" "ml_workers" {
  name = "${var.project_name}-ml-workers-asg"
  
  tag {
    key                 = "Name"
    value               = "${var.project_name}-ml-worker"
    propagate_at_launch = true
  }
}
```

---

## Terraform Variable Setup

### Required Variable
```terraform
variable "project_name" {
  description = "Project name prefix for all AWS resources"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric with hyphens only"
  }
}
```

### terraform.tfvars
```terraform
project_name = "befreefitness-phase3"
```

### Consistent Usage
```terraform
# ALWAYS use ${var.project_name} prefix
resource "aws_s3_bucket" "example" {
  bucket = "${var.project_name}-example"
}

resource "aws_db_instance" "example" {
  identifier = "${var.project_name}-example-db"
}

resource "aws_lambda_function" "example" {
  function_name = "${var.project_name}-example-function"
}
```

---

## Exception: Multi-Tenant Deployments

**When deploying to multi-tenant infrastructure, DO NOT apply project-specific naming**

### Multi-Tenant Indicators:
- Deploying to shared VPC
- Using centralized database
- Shared application servers
- Centralized authentication
- Multi-tenant SaaS architecture

### Multi-Tenant Approach:
- Use shared resource names provided by infrastructure
- Follow tenant isolation via application logic
- Use database schemas/prefixes for separation
- Respect existing multi-tenant naming conventions

**Example Multi-Tenant Deployment**:
```bash
# DO NOT rename shared resources
# DO NOT create project-specific AWS resources
# Use existing shared infrastructure
# Tenant isolation handled at application layer
```

---

## Verification Checklist

Before deploying AWS resources, verify:

- [ ] Checked for existing project resources
- [ ] Extracted correct `<Project-Name>` prefix
- [ ] All resource names follow `<Project-Name>-<Work>` pattern
- [ ] `<Work>` component is 1-2 descriptive words
- [ ] Used lowercase with hyphens only
- [ ] Terraform variable `project_name` is defined
- [ ] All resources use `${var.project_name}` prefix
- [ ] Tags include `Name` with full resource name
- [ ] NOT deploying to multi-tenant infrastructure
- [ ] Names are consistent across all resources

---

## Enforcement

This rule is enforced:
- ✅ At session startup via `startup.ps1`
- ✅ In all `/aws-*` cursor commands
- ✅ Before any AWS resource creation
- ✅ During code review
- ✅ In Terraform plan review

**Violations will be rejected** and must be corrected before proceeding.

---

## Benefits

1. **Clarity**: Instantly identify which project owns each resource
2. **Cost Tracking**: Filter costs by project name prefix
3. **Security**: Easier to audit and secure project-specific resources
4. **Cleanup**: Delete all project resources by name prefix
5. **Multi-Project**: Clear separation when managing multiple projects
6. **Team Communication**: Everyone knows resource ownership

---

**Status**: Active and Mandatory  
**Enforcement**: Maximum - Zero tolerance  
**Applies To**: All AWS resource creation  
**Exception**: Multi-tenant server deployments only

---

**Last Updated**: 2025-11-12  
**Version**: 1.0.0







