# AWS Multi-Account Setup Guide
**TASK-001: AWS Account Setup**  
**Status**: Implementation Complete  
**Required Time**: 2-4 hours  

---

## Overview

This guide walks through setting up a secure, scalable multi-account AWS architecture for the Gaming AI Core system. The setup includes AWS Organizations, cross-account roles, and AWS SSO for centralized access management.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Organization Root Account                     │
│                         (Billing & IAM)                         │
├─────────────────────────────────────────────────────────────────┤
│  • AWS Organizations Management                                 │
│  • Consolidated Billing                                       │
│  • AWS SSO Identity Store                                     │
│  • CloudTrail Organization Trail                              │
│  • Service Control Policies (SCPs)                           │
└────────────────────┬───────────────────────┬───────────────────┘
                     │                       │
        ┌────────────┴────────┐   ┌─────────┴────────────────┐
        │                     │   │                          │
┌───────▼────────┐ ┌─────────▼───┐ ┌────────▼────────┐ ┌────▼────┐
│ Development    │ │  Staging    │ │   Production    │ │  Audit  │
│   Account      │ │  Account    │ │    Account      │ │ Account │
├────────────────┤ ├─────────────┤ ├─────────────────┤ ├─────────┤
│ • Dev Env      │ │ • Pre-Prod  │ │ • Prod Workload │ │ • Logs  │
│ • Testing      │ │ • UAT       │ │ • Live Services │ │ • Audit │
│ • Experiments  │ │ • Perf Test │ │ • GPU Clusters  │ │ • Trail │
└────────────────┘ └─────────────┘ └─────────────────┘ └─────────┘
```

## Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws --version  # Should be 2.x
   aws configure  # Set up credentials
   ```

2. **PowerShell** 7+ (for scripts)
   ```bash
   pwsh --version
   ```

3. **Root Account Access** with appropriate permissions:
   - Organizations full access
   - IAM full access  
   - SSO administrator access

4. **Email Addresses** for each sub-account:
   - `aws-dev@gaming-ai-core.com`
   - `aws-staging@gaming-ai-core.com`
   - `aws-prod@gaming-ai-core.com`
   - `aws-audit@gaming-ai-core.com`
   - `aws-billing@gaming-ai-core.com`

## Setup Steps

### Step 1: Create AWS Organizations Structure

Run from the root account:

```powershell
cd infrastructure/aws-setup
pwsh -ExecutionPolicy Bypass -File setup-aws-organizations.ps1
```

This script will:
- Create the AWS Organization (if not exists)
- Create 5 Organizational Units (OUs)
- Create 5 member accounts
- Enable Service Control Policies
- Create baseline security SCPs
- Enable CloudTrail for all accounts
- Enable security services (GuardDuty, Security Hub)

**Expected Output:**
```
✓ Organization created/verified
✓ 5 OUs created
✓ 5 accounts created
✓ Service Control Policies enabled
✓ CloudTrail enabled
Configuration saved to: organization-config.json
```

### Step 2: Setup Cross-Account Roles

Run in the root account first:

```powershell
pwsh -ExecutionPolicy Bypass -File setup-cross-account-roles.ps1
```

This creates:
- IAM users and groups in root account
- Assume role policies for accessing member accounts
- AWS CLI profile configuration

Then run in each member account:

```powershell
# Get account credentials and configure AWS CLI for the member account
aws configure --profile ai-core-dev

# Run the script
pwsh -ExecutionPolicy Bypass -File setup-cross-account-roles.ps1
```

This creates in each member account:
- `OrganizationAccountAccessRole` - Full admin access
- `AICoreDeveloperRole` - Developer access
- `AICoreReadOnlyRole` - Read-only access
- `AICoreMLOpsRole` - ML operations access
- `AICoreSecurityAuditorRole` - Security audit access

### Step 3: Configure AWS SSO

Run from the root account:

```powershell
pwsh -ExecutionPolicy Bypass -File setup-aws-sso.ps1
```

**Note**: AWS SSO must be manually enabled first:
1. Go to [AWS SSO Console](https://console.aws.amazon.com/singlesignon)
2. Click "Enable AWS SSO"
3. Choose identity source (recommend starting with AWS SSO)

The script will then:
- Create 7 permission sets
- Create 6 user groups
- Assign groups to accounts with appropriate permissions
- Generate SSO portal URL

## Account Usage Guide

### For Administrators

1. **Access via SSO Portal**:
   ```
   https://d-1234567890.awsapps.com/start
   ```

2. **Access via CLI with SSO**:
   ```bash
   aws configure sso
   aws sso login --profile ai-core-prod-admin
   aws s3 ls --profile ai-core-prod-admin
   ```

3. **Access via CLI with Assume Role**:
   ```bash
   # Add to ~/.aws/config
   [profile prod-admin]
   role_arn = arn:aws:iam::123456789012:role/OrganizationAccountAccessRole
   source_profile = default
   role_session_name = admin-session
   
   # Use the profile
   aws s3 ls --profile prod-admin
   ```

### For Developers

1. **Development Access**:
   ```bash
   aws sso login --profile ai-core-dev
   # Full access to dev account
   ```

2. **Read-Only Production Access**:
   ```bash
   aws sso login --profile ai-core-prod-readonly
   # View production resources
   ```

### For ML Engineers

1. **Model Deployment**:
   ```bash
   aws sso login --profile ai-core-prod-mlops
   # Deploy models to production
   ```

## Service Control Policies

The baseline SCP enforces:

1. **Regional Restrictions**: Services only in us-east-1, eu-west-1, ap-southeast-1
2. **Termination Protection**: EC2 instances can't be terminated outside the org
3. **Organization Protection**: Accounts can't leave the organization

To add custom SCPs:

```powershell
# Create a new SCP
aws organizations create-policy `
    --name "RequireMFA" `
    --type SERVICE_CONTROL_POLICY `
    --description "Require MFA for sensitive operations" `
    --content file://require-mfa-policy.json

# Attach to an OU
aws organizations attach-policy `
    --policy-id p-xxxxxxxx `
    --target-id ou-xxxx-xxxxxxxx
```

## Billing and Cost Management

### Consolidated Billing Setup

1. **Enable Cost Explorer**:
   ```bash
   aws ce get-cost-and-usage --help  # Verify access
   ```

2. **Create Budget Alerts**:
   ```bash
   aws budgets create-budget `
       --account-id 123456789012 `
       --budget file://budget-config.json `
       --notifications-with-subscribers file://notifications.json
   ```

3. **Tag Resources for Cost Allocation**:
   ```bash
   # Enforce tagging policy
   aws organizations create-policy `
       --name "RequireProjectTags" `
       --type TAG_POLICY `
       --content file://tag-policy.json
   ```

## Security Best Practices

### 1. Enable MFA for All Users

```bash
# Enforce MFA via SCP
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Deny",
        "Action": "*",
        "Resource": "*",
        "Condition": {
            "BoolIfExists": {
                "aws:MultiFactorAuthPresent": "false"
            }
        }
    }]
}
```

### 2. Regular Access Reviews

```powershell
# List all users with access
aws sso-admin list-account-assignments `
    --instance-arn $instanceArn `
    --account-id 123456789012

# Remove unnecessary access
aws sso-admin delete-account-assignment `
    --instance-arn $instanceArn `
    --target-id 123456789012 `
    --target-type AWS_ACCOUNT `
    --principal-id $groupId `
    --principal-type GROUP
```

### 3. CloudTrail Monitoring

```bash
# Query CloudTrail for root account usage
aws cloudtrail lookup-events `
    --lookup-attributes AttributeKey=UserName,AttributeValue=root `
    --start-time 2025-01-01 `
    --region us-east-1
```

## Troubleshooting

### Common Issues

1. **"Organization already exists" error**:
   - This is normal if re-running the script
   - The script will continue with existing resources

2. **"Access Denied" errors**:
   - Ensure you're running from the root account
   - Check IAM permissions for Organizations access

3. **SSO not working**:
   - Verify SSO is enabled in the console
   - Check identity store region matches configuration
   - Ensure users are added to groups

4. **Cross-account role assumption fails**:
   - Verify External ID matches
   - Check trust policy on the role
   - Ensure source account has assume permissions

### Verification Commands

```powershell
# Verify organization structure
aws organizations list-roots
aws organizations list-organizational-units-for-parent --parent-id r-xxxx
aws organizations list-accounts

# Verify SSO configuration  
aws sso-admin list-instances
aws sso-admin list-permission-sets --instance-arn $instanceArn

# Test role assumption
aws sts assume-role `
    --role-arn arn:aws:iam::123456789012:role/OrganizationAccountAccessRole `
    --role-session-name test-session
```

## Next Steps

After completing the multi-account setup:

1. **[TASK-002] Network Foundation**: Create VPCs and networking
2. **[TASK-003] Kubernetes Cluster**: Deploy EKS infrastructure
3. **[TASK-004] Data Layer**: Setup databases and storage
4. **[TASK-041] Team Building**: Add team members to AWS SSO

## Maintenance

### Weekly Tasks
- Review CloudTrail logs for anomalies
- Check for unused IAM resources
- Review cost and usage reports

### Monthly Tasks
- Rotate access keys (if any)
- Review and update SCPs
- Audit cross-account roles
- Update SSO group memberships

### Quarterly Tasks
- Full security audit
- Review organizational structure
- Update account contacts
- Disaster recovery test

---

## Support

For issues or questions:
1. Check CloudTrail logs for detailed error information
2. Review AWS Organizations documentation
3. Contact platform team lead

---

**Remember**: This is the foundation of our infrastructure. Changes here affect all accounts and services. Always test in development first and follow the peer review process.
